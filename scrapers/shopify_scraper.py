import requests
from typing import Any
from .base_scraper import BaseScraper

# A robust, curated registry of UK Shopify stores across different categories
UK_SHOPIFY_STORES = [
    {"name": "Allbirds UK", "url": "https://www.allbirds.co.uk"},          # Footwear
    {"name": "Gymshark UK", "url": "https://www.gymshark.com"},             # Athletic Apparel
    {"name": "Ooni UK", "url": "https://uk.ooni.com"},                     # Home & Garden
    {"name": "Spoke London", "url": "https://spoke-london.com"},           # Menswear
    {"name": "Passenger Clothing", "url": "https://www.passenger-clothing.com"}, # Outdoors
    {"name": "Finisterre", "url": "https://finisterre.com"},               # Surf & Outerwear
    {"name": "Huel UK", "url": "https://huel.com"},                     # Food & Nutrition
    {"name": "Skinnydip London", "url": "https://www.skinnydiplondon.com"},# Accessories & Tech
    {"name": "Emma Bridgewater", "url": "https://www.emmabridgewater.co.uk"}, # Ceramics/Home
    {"name": "Cambridge Satchel", "url": "https://www.cambridgesatchel.com"}, # Bags/Leather
    {"name": "Rains UK", "url": "https://www.uk.rains.com"},               # Rainwear
    {"name": "Lounge Underwear", "url": "https://loungeunderwear.com"},    # Intimates
    {"name": "BullDog Skincare", "url": "https://www.bulldogskincare.com"},# Cosmetics
    {"name": "The Couture Club", "url": "https://www.thecoutureclub.com"}, # Streetwear
    {"name": "TALA", "url": "https://www.wearetala.com"}                   # Sustainable Activewear
]

class ShopifyScraper(BaseScraper):
    def __init__(self, store_url: str, store_name: str):
        super().__init__(store_name=store_name)
        self.base_url = store_url.rstrip('/')
        self.api_endpoint = f"{self.base_url}/products.json"

    def search_products(self, query: str) -> list[dict[str, Any]]:
        try:
            # Using standard timeout to prevent hanging on bad connections
            response = requests.get(f"{self.api_endpoint}?limit=250", timeout=10)
            response.raise_for_status()
            data = response.json()
            products = data.get('products', [])
        except (requests.RequestException, ValueError) as e:
            print(f"Error fetching from {self.store_name}: {e}")
            return []

        # Split the query into a list of individual words
        query_words = query.lower().split()
        normalized_results = []

        for p in products:
            title = p.get('title', '').lower()
            body_html = (p.get('body_html', '') or '').lower()
            
            # Check if ALL words in the query exist in the title or description
            # This allows "black running shoe" to match "Black Runner Shoe"
            if all(word in title or word in body_html for word in query_words):
                images = p.get('images', [])
                image_url = images[0].get('src', '') if images else ''
                
                variants = p.get('variants', [])
                price = 0.0
                if variants:
                    try:
                        price = float(variants[0].get('price', 0.0))
                    except (ValueError, TypeError):
                        pass

                if price > 0.0:
                    normalized_item = self.normalize_product(
                        title=p.get('title', ''), # Use original casing for the final output
                        price=price,
                        link=f"{self.base_url}/products/{p.get('handle')}",
                        image_url=image_url
                    )
                    normalized_results.append(normalized_item)
                
        return normalized_results
