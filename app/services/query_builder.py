from __future__ import annotations

from typing import Dict, List


def _normalize_category(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().lower().replace("_", "-")
    if v in {"tshirt", "t-shirt", "t shirt", "tee", "tees", "tshirts", "t-shirts"}:
        return "T-shirt"
    return value.strip().title()


def build_queries(product: Dict) -> List[str]:
    brand = (product.get("brand") or "").strip()
    name = (product.get("name") or "").strip()
    category = _normalize_category(product.get("category"))
    product_type = (product.get("product_type") or "").strip()
    color = (product.get("color") or "").strip()

    parts = []
    if brand:
        parts.append(brand)
    if name:
        parts.append(name)
    if category:
        parts.append(category)
    if product_type:
        parts.append(product_type)
    if color:
        parts.append(color)

    queries = []
    base = " ".join([p for p in parts if p]).strip()
    if base:
        queries.append(base)

    # Ensure category-driven query exists, especially for normalized categories like T-shirt.
    if category and name:
        queries.append(f"{name} {category}")
    if category and brand:
        queries.append(f"{brand} {category}")
    if product_type and category:
        queries.append(f"{product_type} {category}")

    # De-dup preserving order.
    seen = set()
    uniq = []
    for q in queries:
        if q and q not in seen:
            seen.add(q)
            uniq.append(q)

    return uniq
