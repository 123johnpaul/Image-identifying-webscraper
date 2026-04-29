from __future__ import annotations

import os
import tempfile
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile

from app.schemas.identify import IdentifyResponse, IdentifiedAttribute, IdentifiedProduct
from app.services.attribute_extraction import extract_attributes
from app.services.image_recognition import ImageRecognitionClient
from app.services.query_builder import build_queries

router = APIRouter()


def _dedupe_attributes(items):
    best = {}
    for a in items:
        if not isinstance(a, dict):
            continue
        key = str(a.get("key", "")).strip().lower()
        value = str(a.get("value", "")).strip()
        if not key or not value:
            continue
        conf = float(a.get("confidence") or 0.0)
        identity = (key, value.lower())
        if identity not in best or conf > float(best[identity].get("confidence") or 0.0):
            best[identity] = {"key": key, "value": value, "confidence": conf}
    return list(best.values())


@router.post("/identify-product", response_model=IdentifyResponse)
async def identify_product(
    image: UploadFile = File(...),
    description: Optional[str] = Form(None),
):
    suffix = os.path.splitext(image.filename or "")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await image.read()
        tmp.write(contents)
        tmp_path = tmp.name

    client = ImageRecognitionClient()
    result = client.identify(tmp_path, description=description)

    extracted = extract_attributes(result.get("labels", []), description=description)

    # Only fill missing fields from text extraction, never overwrite model fields.
    if not result.get("brand") and extracted.get("brand"):
        result["brand"] = extracted.get("brand")
    if not result.get("color") and extracted.get("color"):
        result["color"] = extracted.get("color").title()
    if not result.get("category") and extracted.get("category"):
        result["category"] = extracted.get("category")

    merged_attributes = (result.get("attributes") or []) + (extracted.get("attributes") or [])
    merged_attributes = _dedupe_attributes(merged_attributes)

    # Keep product color/category aligned with highest-confidence deduped attributes.
    top_color = next((a["value"] for a in sorted(merged_attributes, key=lambda x: x.get("confidence", 0), reverse=True) if a["key"] == "color"), None)
    top_category = next((a["value"] for a in sorted(merged_attributes, key=lambda x: x.get("confidence", 0), reverse=True) if a["key"] == "category"), None)
    if top_color:
        result["color"] = top_color
    if top_category:
        result["category"] = top_category

    attributes = [
        IdentifiedAttribute(key=a.get("key"), value=a.get("value"), confidence=a.get("confidence"))
        for a in merged_attributes
    ]

    product = IdentifiedProduct(
        name=result.get("name") or "unknown product",
        category=result.get("category"),
        brand=result.get("brand"),
        color=result.get("color"),
        attributes=attributes,
        confidence=result.get("confidence"),
    )

    queries = build_queries(result)

    return IdentifyResponse(
        product=product,
        search_queries=queries,
        debug={
            "provider": result.get("raw", {}).get("provider", "mock"),
            "model_ready": bool(result.get("raw", {}).get("matches")),
            "top_matches": result.get("raw", {}).get("matches", []),
            "image_color": result.get("raw", {}).get("image_color"),
            "voted_color": result.get("raw", {}).get("voted_color"),
            "error": result.get("raw", {}).get("error"),
        },
    )
