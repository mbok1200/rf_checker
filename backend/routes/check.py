import json
from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import sys
from pathlib import Path
from datetime import datetime
import os
import uuid

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.checkers.auth_service import AuthService
from backend.checkers.check_request import CheckRequest
from ai_core.main import AICoreMain
from backend.services.dynamodb import DynamoDBService

router = APIRouter(prefix="/api", tags=["Content Check"])
limiter = Limiter(key_func=get_remote_address)
db_service = DynamoDBService()

def get_ai_provider():
    """Визначити який AI провайдер використовувати"""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    
    if anthropic_key:
        return "anthropic"
    elif gemini_key:
        return "gemini"
    else:
        raise HTTPException(status_code=500, detail="No AI API keys configured")

def analyze_with_anthropic(prompt: str) -> str:
    """Аналіз з Anthropic"""
    try:
        import anthropic
        
        client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text
    except Exception as e:
        print(f"Anthropic error: {str(e)}")
        raise

def analyze_with_gemini(ai_core: AICoreMain, data) -> str:
    """Аналіз з Gemini"""
    try:
        response = ai_core.ai_machines.gemeni_generate_text(ai_core.state.metadata)
        return str(response)
    except Exception as e:
        print(f"Gemini error: {str(e)}")
        raise

@router.post("/check")
@limiter.limit("10/minute")
async def check_content(
    request: Request,
    data: CheckRequest,
    user: str = Depends(AuthService.verify_api_key)
):
    """Перевірити контент на наявність російської пропаганди"""
    
    # Генеруємо унікальний ID запиту
    request_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Перевірка user_id
    if not data.user_id:
        raise HTTPException(status_code=400, detail="user_id обов'язковий")
    user_id = data.user_id
    
    # Перевірка ліміту користувача
    user_limit = db_service.get_user_limit(user_id)
    current_checks = db_service.get_user_checks_count(user_id)
    
    # if current_checks >= user_limit:
    #     raise HTTPException(
    #         status_code=429,
    #         detail=f"Ліміт перевірок вичерпано ({current_checks}/{user_limit}). Зверніться до адміністратора для збільшення ліміту."
    #     )
    
    try:
        # Визначення AI провайдера
        ai_provider = get_ai_provider()
        print(f"[{request_id}] Using AI provider: {ai_provider}")
        
        ai_core = AICoreMain()
        steam_url = None
        steam_info = {}
        skipAll = False
        
        # Визначення типу перевірки та підготовка даних
        check_type = None
        check_data = {}
        urls_checked = []
        
        if data.text:
            ai_core.state.insert_metadata("text", data.text)
            skipAll = True
            check_type = "text"
            check_data = {"text": data.text[:100] + "..."}
        
        # Обробка Steam гри
        if skipAll is False and data.game_name:
            print(f"[{request_id}] Processing game: {data.game_name}")
            check_type = "game"
            check_data = {"game_name": data.game_name}
            try:
                ai_core.steam_process(data.game_name)
                steam_info = ai_core.state.metadata.get("steam_game_info", {})
                steam_url = steam_info.get("website")
            except Exception as e:
                print(f"[{request_id}] Steam processing error: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # Додаємо URL тільки якщо він не None та не порожній
            if steam_url and isinstance(steam_url, str) and steam_url.strip():
                data.urls.append(steam_url)
                urls_checked.append(steam_url)
        
        # Обробка URLs тільки якщо список не порожній
        if skipAll is False and data.urls and len(data.urls) > 0:
            check_type = "url"
            check_data = {"urls": data.urls}
            urls_checked = data.urls
            try:
                print(f"[{request_id}] Processing URLs: {data.urls}")
                ai_core.request_handle(data.urls)
            except Exception as e:
                print(f"[{request_id}] Error in request_handle: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
        else:
            pass  # Пропускаємо обробку, якщо список URLs порожні
        
        # Формування промпту
        prompt = f"""Ти експерт з виявлення російської пропаганди та контенту, пов'язаного з російською федерацією.

Проаналізуй наступний контент та визнач, чи містить він:
- Російську пропаганду
- Підтримку російської федерації або її дій
- Контент від російських розробників/компаній
- Зв'язки з російськими організаціями

"""
        
        if data.game_name:
            prompt += f"Назва гри: {data.game_name}\n"
        if data.urls and len(data.urls) > 0:
            prompt += f"URL: {', '.join(data.urls)}\n"
        if data.text:
            prompt += f"Текст: {data.text}\n"
        
        prompt += """
Дай відповідь у форматі JSON:
{
    "is_russian_content": true/false,
    "text": "Детальне пояснення українською мовою"
}
"""
        
        # Вибір провайдера для аналізу
        print(f"[{request_id}] Starting analysis with {ai_provider}...")
        if ai_provider == "anthropic":
            ai_response = analyze_with_anthropic(prompt)
        else:  # gemini
            ai_core.state.insert_metadata("analysis_prompt", prompt)
            ai_response = analyze_with_gemini(ai_core, data)
        
        print(f"[{request_id}] Analysis completed")
        
        # Збільшуємо лічильник тільки після успішної перевірки
        new_count = db_service.increment_user_checks(user_id)
        
        # Зберігаємо історію перевірки
        if check_type:
            db_service.save_check_history(
                user_id=user_id,
                check_type=check_type,
                data=check_data,
                result={
                    "message": str(ai_response),
                    "provider": ai_provider,
                    "request_id": request_id,
                    "timestamp": timestamp
                }
            )
        ai_response = json.loads(ai_response)
        
        result = {
            "ai_core": str(ai_core.state.metadata),
            "request_id": request_id,
            "timestamp": timestamp,
            "check_type": check_type,   
            "is_russian_content": ai_response.get("is_russian_content", False),
            "text": ai_response.get("text", ""),
            "message": str(ai_response),
            "checks_used": new_count,
            "checks_remaining": user_limit - new_count,
            "provider": ai_provider,
            "details": {
                "game_name": data.game_name,
                "urls_checked": urls_checked,
                "text_length": len(data.text) if data.text else 0,
                "steam_info": steam_info if check_type == "game" else None
            }
        }
        
        print(f"[{request_id}] Check completed successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[{request_id}] Error in check_content: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/history/{user_id}")
@limiter.limit("30/minute")
async def get_history(
    user_id: str,
    request: Request,
    user: str = Depends(AuthService.verify_api_key),
    limit: int = 10
):
    """Отримати історію перевірок користувача"""
    try:
        auth_user_id = user.get('user_id') if isinstance(user, dict) else getattr(user, 'user_id', None)
        
        if not auth_user_id:
            raise HTTPException(status_code=400, detail="user_id not found in auth")
        
        # Перевірити що користувач може бачити тільки свою історію
        if auth_user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        stats = db_service.get_user_stats(user_id)
        
        return {
            "user_id": user_id,
            "stats": stats,
            "history": [],
            "message": "History retrieval not fully implemented yet"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching history")

@router.get("/ai-provider")
async def get_current_provider():
    """Отримати інформацію про поточного AI провайдера"""
    try:
        provider = get_ai_provider()
        return {
            "provider": provider,
            "message": f"Використовується {provider.upper()} для аналізу",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException as e:
        return {
            "provider": None,
            "message": str(e.detail),
            "timestamp": datetime.utcnow().isoformat()
        }