from .auth import router as auth_router
from .check import router as check_router
from .health import router as health_router

__all__ = ['auth_router', 'check_router', 'health_router']