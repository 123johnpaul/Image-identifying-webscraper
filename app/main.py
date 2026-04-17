from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.identify import router as identify_router

app = FastAPI(title="Price Compare AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(identify_router, tags=["identify"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/compare")
def compare_placeholder(payload: dict):
    # Placeholder for Uzochi's endpoint; keeps frontend wiring stable.
    return {
        "status": "placeholder",
        "message": "compare endpoint not implemented yet",
        "query": payload,
    }
