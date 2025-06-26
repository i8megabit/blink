from app.api.v1 import router as api_router
from fastapi import FastAPI

app = FastAPI(title="SEO Link Recommender")

app.include_router(api_router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
