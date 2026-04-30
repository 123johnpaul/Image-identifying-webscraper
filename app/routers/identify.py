from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, File, Form, UploadFile

from app.schemas.identify import IdentifyResponse, IdentifiedAttribute, IdentifiedProduct
from app.services.attribute_extraction import extract_attributes
from app.services.image_recognition import ImageRecognitionClient
from app.services.query_builder import build_queries

router = APIRouter()


def _normalize_category(value: str) -> str:
    v = value.strip().lower().replace("_", "-")
    if v in {"tshirt", "t-shirt", "t shirt", "tee", "tees", "tshirts", "t-shirts"}:
        return "T-shirt"
    return value.strip().title()


@router.post("/identify-product", response_model=IdentifyResponse)
async def identify_product(
    image: UploadFile = File(...),
    product_name: str = Form(...),
    category: str = Form(...),
    product_type: str = Form(...),
    brand: str = Form(...),
    color: str = Form(...),
):
    # Mandatory structured description fields from user (authoritative values).
    user_payload = {
        "name": product_name.strip(),
        "category": _normalize_category(category),
        "product_type": product_type.strip(),
        "brand": brand.strip(),
        "color": color.strip().title(),
    }

    suffix = os.path.splitext(image.filename or "")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await image.read()
        tmp.write(contents)
        tmp_path = tmp.name

    description = " ".join([
        user_payload["brand"],
        user_payload["name"],
        user_payload["category"],
        user_payload["product_type"],
        user_payload["color"],
    ]).strip()

    client = ImageRecognitionClient(provider="local_similarity")
    model_result = client.identify(tmp_path, description=description)

    extracted = extract_attributes(model_result.get("labels", []), description=description)

    # Final output uses user-provided structured fields as ground truth context.
    final_result = {
        "name": user_payload["name"],
        "category": user_payload["category"],
        "product_type": user_payload["product_type"],
        "brand": user_payload["brand"],
        "color": user_payload["color"],
        "confidence": model_result.get("confidence"),
        "raw": model_result.get("raw", {}),
    }

    attributes = [
        IdentifiedAttribute(key="category", value=user_payload["category"], confidence=0.99),
        IdentifiedAttribute(key="product_type", value=user_payload["product_type"], confidence=0.99),
        IdentifiedAttribute(key="brand", value=user_payload["brand"], confidence=0.99),
        IdentifiedAttribute(key="color", value=user_payload["color"], confidence=0.99),
    ]

    # Keep model/extracted hints in debug only to avoid contradictory user-facing fields.
    debug_hints = {
        "model_name": model_result.get("name"),
        "model_category": model_result.get("category"),
        "model_brand": model_result.get("brand"),
        "model_color": model_result.get("color"),
        "extracted": extracted,
    }

    product = IdentifiedProduct(
        name=final_result["name"],
        category=final_result["category"],
        brand=final_result["brand"],
        color=final_result["color"],
        attributes=attributes,
        confidence=final_result["confidence"],
    )

    queries = build_queries(final_result)

    return IdentifyResponse(
        product=product,
        search_queries=queries,
        debug={
            "provider": final_result.get("raw", {}).get("provider", "local_similarity"),
            "model_ready": bool(final_result.get("raw", {}).get("matches")),
            "top_matches": final_result.get("raw", {}).get("matches", []),
            "image_color": final_result.get("raw", {}).get("image_color"),
            "voted_color": final_result.get("raw", {}).get("voted_color"),
            "user_payload": user_payload,
            "model_hints": debug_hints,
            "error": final_result.get("raw", {}).get("error"),
        },
    )
