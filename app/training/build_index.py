from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from app.training.dataset import load_fashion_samples
from app.training.model import build_model


class InferenceDataset(Dataset):
    def __init__(self, samples, transform):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        from PIL import Image

        sample = self.samples[idx]
        image = Image.open(sample.image_path).convert("RGB")
        return self.transform(image), str(sample.image_path), sample.metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("app/data"))
    parser.add_argument("--checkpoint", type=Path, default=Path("app/models/similarity_v1/best.pt"))
    parser.add_argument("--out-index", type=Path, default=Path("app/models/similarity_v1/index.npz"))
    args = parser.parse_args()

    payload = torch.load(args.checkpoint, map_location="cpu")
    model = build_model(
        num_classes=len(payload["label_to_idx"]),
        embedding_dim=payload["config"]["embedding_dim"],
    )
    model.load_state_dict(payload["model_state"])
    model.eval()

    samples = load_fashion_samples(args.data_dir)
    tf = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    ds = InferenceDataset(samples, transform=tf)
    loader = DataLoader(ds, batch_size=64, shuffle=False, num_workers=0)

    all_embs = []
    all_paths = []
    all_meta = []
    with torch.no_grad():
        for images, paths, metas in loader:
            _, embs = model(images)
            all_embs.append(embs.cpu().numpy())
            all_paths.extend(list(paths))
            # DataLoader collates dict of lists
            count = len(paths)
            for i in range(count):
                all_meta.append(
                    {
                        "title": metas["title"][i],
                        "brand": metas["brand"][i],
                        "category": metas["category"][i],
                        "color": metas["color"][i],
                    }
                )

    embeddings = np.concatenate(all_embs, axis=0).astype(np.float32)
    args.out_index.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.out_index,
        embeddings=embeddings,
        image_paths=np.array(all_paths),
        metadata=np.array([json.dumps(m) for m in all_meta]),
    )
    print(f"saved index -> {args.out_index} ({len(all_paths)} entries)")


if __name__ == "__main__":
    main()

