from abc import ABC, abstractmethod
from typing import Any

class BaseScraper(ABC):
    """
    Abstract base class for all product fetchers.
    Ensures every store normalizes data to the exact same format.
    """
    def __init__(self, store_name: str):
        self.store_name = store_name

    @abstractmethod
    def search_products(self, query: str) -> list[dict[str, Any]]:
        """Must return a list of products matching the query."""
        pass

    def normalize_product(self, title: str, price: float, link: str, image_url: str) -> dict[str, Any]:
        """Standardizes the output format for the Price Comparator."""
        return {
            "store": self.store_name,
            "title": title,
            "price": float(price),
            "link": link,
            "image_url": image_url
        }
