from __future__ import annotations

import os
from typing import Dict, Optional

from app.services.local_similarity import LocalSimilarityEngine


class ImageRecognitionClient:
    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or os.getenv("VISION_PROVIDER") or "local_similarity").lower()
        self.local_engine = LocalSimilarityEngine()

    def identify(self, image_path: str, description: Optional[str] = None) -> Dict:
        if self.provider in {"local", "local_similarity"}:
            result = self._local_identify(image_path)
            if result.get("confidence", 0.0) <= 0 and description:
                return self._mock_identify(image_path, description)
            return result
        if self.provider == "mock":
            return self._mock_identify(image_path, description)

        # Placeholder for future hosted providers.
        return self._mock_identify(image_path, description)

    def _local_identify(self, image_path: str) -> Dict:
        inference = self.local_engine.infer(image_path, top_k=5)
        if not inference.get("ready"):
            return {
                "name": "unknown product",
                "category": None,
                "brand": None,
                "color": None,
                "attributes": [],
                "labels": [],
                "confidence": 0.0,
                "raw": {"provider": "local_similarity", "error": inference.get("error")},
            }

        best = inference.get("best_match", {})
        meta = best.get("metadata", {})
        score = float(best.get("score", 0.0))
        confidence = max(0.0, min(1.0, (score + 1.0) / 2.0))

        name = meta.get("title") or "fashion item"
        brand = meta.get("brand")
        category = meta.get("category")
        color = meta.get("color")

        attributes = []
        if brand and brand != "unknown":
            attributes.append({"key": "brand", "value": brand, "confidence": confidence})
        if color and color != "unknown":
            attributes.append({"key": "color", "value": color, "confidence": confidence})
        if category and category != "unknown":
            attributes.append({"key": "category", "value": category, "confidence": confidence})

        labels = [x for x in [name, brand, category, color] if x and x != "unknown"]

        return {
            "name": name,
            "category": category if category != "unknown" else None,
            "brand": brand if brand != "unknown" else None,
            "color": color if color != "unknown" else None,
            "attributes": attributes,
            "labels": labels,
            "confidence": confidence,
            "raw": {
                "provider": "local_similarity",
                "matches": inference.get("matches", []),
            },
        }

    def _mock_identify(self, image_path: str, description: Optional[str]) -> Dict:
        name = "unknown product"
        category = None
        brand = None
        color = None
        attributes = []
        labels = []
        confidence = 0.2

        if description:
            name = description.strip()
            labels = description.split()
            confidence = 0.35

        return {
            "name": name,
            "category": category,
            "brand": brand,
            "color": color,
            "attributes": attributes,
            "labels": labels,
            "confidence": confidence,
            "raw": {"provider": "mock"},
        }
