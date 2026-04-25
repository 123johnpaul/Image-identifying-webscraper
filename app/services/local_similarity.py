from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import torch
from PIL import Image
from torchvision import transforms

from app.training.model import build_model


class LocalSimilarityEngine:
    def __init__(
        self,
        checkpoint_path: str = "app/models/similarity_v1/best.pt",
        index_path: str = "app/models/similarity_v1/index.npz",
    ) -> None:
        self.checkpoint_path = Path(checkpoint_path)
        self.index_path = Path(index_path)
        self.ready = self.checkpoint_path.exists() and self.index_path.exists()
        self.model = None
        self.index_embeddings = None
        self.index_paths = None
        self.index_meta = None
        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )
        if self.ready:
            self._load()

    def _load(self) -> None:
        payload = torch.load(self.checkpoint_path, map_location="cpu")
        self.model = build_model(
            num_classes=len(payload["label_to_idx"]),
            embedding_dim=payload["config"]["embedding_dim"],
        )
        self.model.load_state_dict(payload["model_state"])
        self.model.eval()

        index = np.load(self.index_path, allow_pickle=True)
        self.index_embeddings = index["embeddings"]
        self.index_paths = index["image_paths"]
        self.index_meta = [json.loads(item) for item in index["metadata"]]

    def infer(self, image_path: str, top_k: int = 5) -> Dict:
        if not self.ready:
            return {
                "ready": False,
                "error": "Local similarity model/index not found. Train first.",
                "matches": [],
            }

        image = Image.open(image_path).convert("RGB")
        tensor = self.transform(image).unsqueeze(0)
        with torch.no_grad():
            _, emb = self.model(tensor)
        query = emb.cpu().numpy()[0]
        sims = self.index_embeddings @ query
        top_idx = np.argsort(-sims)[:top_k]

        matches: List[Dict] = []
        for idx in top_idx:
            matches.append(
                {
                    "score": float(sims[idx]),
                    "image_path": str(self.index_paths[idx]),
                    "metadata": self.index_meta[idx],
                }
            )
        best = matches[0] if matches else {}
        return {"ready": True, "best_match": best, "matches": matches}

