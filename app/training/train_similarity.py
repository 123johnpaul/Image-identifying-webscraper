from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Dict, List

import torch
from sklearn.model_selection import train_test_split
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader
from torchvision import transforms
from tqdm import tqdm

from app.training.dataset import FashionSimilarityDataset, load_fashion_samples
from app.training.model import build_model, save_checkpoint


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)


def accuracy(logits, labels) -> float:
    preds = torch.argmax(logits, dim=1)
    return (preds == labels).float().mean().item()


def build_label_map(samples) -> Dict[str, int]:
    labels = sorted({s.label_name for s in samples})
    return {label: i for i, label in enumerate(labels)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("app/data"))
    parser.add_argument("--out-dir", type=Path, default=Path("app/models/similarity_v1"))
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--embedding-dim", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    set_seed(args.seed)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    samples = load_fashion_samples(args.data_dir)
    label_to_idx = build_label_map(samples)

    stratify = [s.label_name for s in samples]
    train_samples, val_samples = train_test_split(
        samples, test_size=0.15, random_state=args.seed, stratify=stratify
    )

    train_tf = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    val_tf = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    train_ds = FashionSimilarityDataset(train_samples, label_to_idx, transform=train_tf)
    val_ds = FashionSimilarityDataset(val_samples, label_to_idx, transform=val_tf)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    device = torch.device("cpu")
    model = build_model(num_classes=len(label_to_idx), embedding_dim=args.embedding_dim).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = AdamW(model.parameters(), lr=args.lr)

    best_val = 0.0
    best_path = args.out_dir / "best.pt"

    for epoch in range(args.epochs):
        model.train()
        train_loss = 0.0
        train_acc = 0.0
        for images, labels in tqdm(train_loader, desc=f"train epoch {epoch + 1}/{args.epochs}"):
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            logits, _ = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            train_acc += accuracy(logits.detach(), labels)

        model.eval()
        val_loss = 0.0
        val_acc = 0.0
        with torch.no_grad():
            for images, labels in tqdm(val_loader, desc=f"val epoch {epoch + 1}/{args.epochs}"):
                images = images.to(device)
                labels = labels.to(device)
                logits, _ = model(images)
                loss = criterion(logits, labels)
                val_loss += loss.item()
                val_acc += accuracy(logits, labels)

        train_loss /= max(len(train_loader), 1)
        train_acc /= max(len(train_loader), 1)
        val_loss /= max(len(val_loader), 1)
        val_acc /= max(len(val_loader), 1)

        print(
            json.dumps(
                {
                    "epoch": epoch + 1,
                    "train_loss": round(train_loss, 4),
                    "train_acc": round(train_acc, 4),
                    "val_loss": round(val_loss, 4),
                    "val_acc": round(val_acc, 4),
                }
            )
        )

        if val_acc > best_val:
            best_val = val_acc
            save_checkpoint(
                best_path,
                model,
                label_to_idx,
                {
                    "embedding_dim": args.embedding_dim,
                    "image_size": 224,
                },
            )

    with (args.out_dir / "summary.json").open("w", encoding="utf-8") as fp:
        json.dump(
            {
                "best_val_acc": best_val,
                "num_samples": len(samples),
                "num_train": len(train_samples),
                "num_val": len(val_samples),
                "num_labels": len(label_to_idx),
            },
            fp,
            indent=2,
        )
    print(f"training complete. best checkpoint: {best_path}")


if __name__ == "__main__":
    main()

