"""Health check router."""
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    """GET /api/health — liveness probe."""
    return {"status": "ok"}
