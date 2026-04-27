from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np

from app.training.features import extract_feature_vector


class LocalSimilarityEngine:
    def __init__(
        self,
        checkpoint_path: str = "app/models/similarity_v1/model.joblib",
        index_path: str = "app/models/similarity_v1/index.npz",
    ) -> None:
        self.checkpoint_path = Path(checkpoint_path)
        self.index_path = Path(index_path)
        self.ready = self.checkpoint_path.exists() and self.index_path.exists()

        self.scaler = None
        self.pca = None
        self.index_embeddings = None
        self.index_paths = None
        self.index_meta = None

        if self.ready:
            self._load()

    def _load(self) -> None:
        payload = joblib.load(self.checkpoint_path)
        self.scaler = payload["scaler"]
        self.pca = payload["pca"]

        index = np.load(self.index_path, allow_pickle=True)
        self.index_embeddings = index["embeddings"].astype(np.float32)
        self.index_paths = index["image_paths"]
        self.index_meta = [json.loads(item) for item in index["metadata"]]

    def infer(self, image_path: str, top_k: int = 5) -> Dict:
        if not self.ready:
            return {
                "ready": False,
                "error": "Local similarity model/index not found. Train first.",
                "matches": [],
            }

        query = extract_feature_vector(Path(image_path))[None, :]
        query = self.scaler.transform(query)
        query = self.pca.transform(query).astype(np.float32)
        query /= np.linalg.norm(query, axis=1, keepdims=True) + 1e-8
        q = query[0]

        sims = self.index_embeddings @ q
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
