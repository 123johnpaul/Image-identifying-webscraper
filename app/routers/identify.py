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


@router.post("/identify-product", response_model=IdentifyResponse)
async def identify_product(
    image: UploadFile = File(...),
    description: Optional[str] = Form(None),
):
    # Save image to a temp file for processing.
    suffix = os.path.splitext(image.filename or "")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await image.read()
        tmp.write(contents)
        tmp_path = tmp.name

    client = ImageRecognitionClient()
    result = client.identify(tmp_path, description=description)

    extracted = extract_attributes(result.get("labels", []), description=description)

    # Merge extracted attributes if model output is missing them.
    result.setdefault("brand", extracted.get("brand"))
    result.setdefault("color", extracted.get("color"))
    result.setdefault("category", extracted.get("category"))
    if extracted.get("attributes"):
        result["attributes"] = (result.get("attributes") or []) + extracted["attributes"]

    attributes = [
        IdentifiedAttribute(key=a.get("key"), value=a.get("value"), confidence=a.get("confidence"))
        for a in result.get("attributes", [])
        if isinstance(a, dict)
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
            "error": result.get("raw", {}).get("error"),
        },
    )
