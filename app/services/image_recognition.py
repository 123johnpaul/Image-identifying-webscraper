from __future__ import annotations

import os
from typing import Dict, Optional


class ImageRecognitionClient:
    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or os.getenv("VISION_PROVIDER") or "mock").lower()

    def identify(self, image_path: str, description: Optional[str] = None) -> Dict:
        if self.provider == "mock":
            return self._mock_identify(image_path, description)

        # Placeholder for real providers. Keep API surface stable.
        # When integrating a provider, return a dict with keys:
        # name, category, brand, color, attributes(list), confidence, labels(list)
        return self._mock_identify(image_path, description)

    def _mock_identify(self, image_path: str, description: Optional[str]) -> Dict:
        # Simple heuristic using description; keeps pipeline testable without data.
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
            "raw": {"provider": self.provider},
        }
