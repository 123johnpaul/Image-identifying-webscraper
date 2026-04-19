import requests
from typing import List, Dict, Any

FAKESTORE_API_URL = "https://fakestoreapi.com/products"

def fetch_fake_products() -> List[Dict[str, Any]]:
    """Retrieves all product listings from the FakeStore API."""
    try:
        response = requests.get(FAKESTORE_API_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from FakeStore API: {e}")
        return []

def filter_products_by_keyword(keyword: str) -> List[Dict[str, Any]]:
    """Filters retrieved products by a specific keyword in the title or description."""
    products = fetch_fake_products()
    if not products:
        return []

    keyword_lower = keyword.lower()
    filtered_products = []

    for product in products:
        title = product.get('title', '').lower()
        description = product.get('description', '').lower()

        if keyword_lower in title or keyword_lower in description:
            filtered_products.append(product)

    return filtered_products
