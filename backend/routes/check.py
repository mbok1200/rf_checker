from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import sys
from pathlib import Path
import hashlib
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.checkers.auth_service import AuthService
from backend.checkers.check_request import CheckRequest
from ai_core.main import AICoreMain

router = APIRouter(prefix="/api", tags=["Content Check"])
limiter = Limiter(key_func=get_remote_address)

@router.post("/check")
@limiter.limit("10/minute")
async def check_content(
    request: Request,
    data: CheckRequest,
    user: str = Depends(AuthService.verify_api_key)
):
    """Перевірити контент на наявність російської пропаганди"""
    try:
        ai_core = AICoreMain()
         # Обробка Steam гри
        if data.game_name:
            print(f"Processing game: {data.game_name}")
            try:
                ai_core.steam_process(data.game_name)
                print(f"Steam process completed")
            except Exception as e:
                print(f"Error in steam_process: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
            
            steam_url = ai_core.state.metadata.get("steam_game_info", {}).get("website")
            # Додаємо URL тільки якщо він не None та не порожній
            if steam_url:
                data.urls.append(steam_url)
        
        # Обробка URLs
        if len(data.urls) > 0:
            print(f"Steam URL: {steam_url} {data.urls}")
            
            try:
                ai_core.request_handle(data.urls)
                print(f"URL processing completed")
            except Exception as e:
                print(f"Error in request_handle: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
            print(f"Steam URL: {ai_core.state.metadata}")
        print(f"Processing URLs: {ai_core.state.metadata}")
            
        # Генерація аналізу
        response = ai_core.ai_machines.gemeni_generate_text(ai_core.state.metadata)
        
        return {
            "message": response,
            "urls_metadata": ai_core.state.metadata.get("urls_metadata", []),
            "steam_info": ai_core.state.metadata.get("steam_game_info"),
            "request_id": hashlib.sha256(f"{user}{datetime.now()}".encode()).hexdigest()[:16],
            "timestamp": datetime.now().isoformat(),
            "user": user
        }
        
    except Exception as e:
        print(f"Error in check_content: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/history")
@limiter.limit("30/minute")
async def get_history(
    request: Request,
    user: str = Depends(AuthService.verify_api_key),
    limit: int = 10
):
    """Отримати історію перевірок користувача"""
    try:
        # Тут можна додати логіку отримання історії з DynamoDB
        return {
            "user": user,
            "history": [],
            "message": "History retrieval not implemented yet"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching history")