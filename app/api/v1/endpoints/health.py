"""Health check."""
from fastapi import APIRouter
from datetime import datetime
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "time": datetime.utcnow().isoformat(),
    }
