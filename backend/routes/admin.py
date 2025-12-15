from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from checkers.auth_service import verify_api_key
from services.dynamodb import DynamoDBService

router = APIRouter(prefix="/admin", tags=["admin"])
db_service = DynamoDBService()

class SetLimitRequest(BaseModel):
    user_id: str
    max_checks: int

class ResetChecksRequest(BaseModel):
    user_id: str

@router.post("/set-limit")
async def set_limit(
    request: SetLimitRequest,
    api_key: str = Depends(verify_api_key)
):
    """Встановити ліміт для користувача"""
    try:
        db_service.set_user_limit(request.user_id, request.max_checks)
        return {
            "message": f"Ліміт для користувача {request.user_id} встановлено: {request.max_checks}",
            "user_id": request.user_id,
            "new_limit": request.max_checks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-checks")
async def reset_checks(
    request: ResetChecksRequest,
    api_key: str = Depends(verify_api_key)
):
    """Скинути лічильник перевірок користувача"""
    try:
        db_service.reset_user_checks(request.user_id)
        return {
            "message": f"Лічильник для користувача {request.user_id} скинуто",
            "user_id": request.user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-stats/{user_id}")
async def get_user_stats(
    user_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Отримати статистику користувача"""
    try:
        stats = db_service.get_user_stats(user_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))