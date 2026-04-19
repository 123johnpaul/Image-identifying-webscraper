from fastapi import FastAPI, HTTPException
from scrapers.fakestore_scraper import filter_products_by_keyword

app = FastAPI(title="Price Comparison API")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Price Comparison API"}

@app.get("/test-fakestore")
def test_fakestore(keyword: str):
    """Test endpoint to filter FakeStore products by keyword."""
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword parameter is required")

    results = filter_products_by_keyword(keyword)
    return {
            "keyword": keyword,
            "count": len(results),
            "results": results
    }

@app.post("/compare")
def compare_prices():
    return {"status": "Not implemented yet"}
