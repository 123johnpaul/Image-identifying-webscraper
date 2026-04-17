from __future__ import annotations

from typing import Dict, List


def build_queries(product: Dict) -> List[str]:
    parts = []
    if product.get("brand"):
        parts.append(product["brand"])
    if product.get("name"):
        parts.append(product["name"])
    if product.get("category"):
        parts.append(product["category"])
    if product.get("color"):
        parts.append(product["color"])

    base = " ".join(parts).strip()
    queries = []

    if base:
        queries.append(base)

    # Fallback query if only name exists or minimal data.
    if product.get("name") and product.get("category"):
        queries.append(f"{product['name']} {product['category']}")

    # De-dup preserving order.
    seen = set()
    uniq = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            uniq.append(q)

    return uniq
