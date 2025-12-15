from fastapi import APIRouter
from routes import health, check, auth, admin

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(check.router, tags=["check"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(admin.router, tags=["admin"])