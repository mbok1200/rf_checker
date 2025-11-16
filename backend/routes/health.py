from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

router = APIRouter(tags=["Health"])
limiter = Limiter(key_func=get_remote_address)

@router.get("/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Перевірка стану сервісу"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.get("/")
async def root():
    """Кореневий маршрут"""
    return {
        "message": "RF Checker API",
        "version": "1.0.0",
        "docs": "/docs (disabled in production)"
    }