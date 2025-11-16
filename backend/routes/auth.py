from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.services.dynamodb import DynamoDBService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Pydantic моделі для валідації
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str

class RegenerateKeyRequest(BaseModel):
    username: str
    password: str

# Ініціалізація DynamoDB сервісу
db = DynamoDBService()

@router.post("/login")
async def login(data: LoginRequest):
    """Логін і отримання API ключа"""
    user = db.verify_credentials(data.username, data.password)
    if user:
        return {
            "message": "Login successful",
            "username": user['username'],
            "created_at": user.get('created_at')
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/register")
async def register(data: RegisterRequest):
    """Реєстрація нового користувача"""
    # Валідація
    if len(data.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    try:
        result = db.create_user(data.username, data.password)
        return {
            "message": "User created successfully",
            "username": result['username'],
            "api_key": result['api_key']  # Показати тільки раз!
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error creating user")

@router.post("/regenerate-key")
async def regenerate_key(data: RegenerateKeyRequest):
    """Згенерувати новий API ключ"""
    user = db.verify_credentials(data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    try:
        new_api_key = db.regenerate_api_key(data.username)
        return {
            "message": "API key regenerated successfully",
            "api_key": new_api_key
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error regenerating API key")

@router.get("/verify")
async def verify_token(username: str):
    """Перевірити чи користувач існує"""
    # Можна використати для перевірки доступності username
    try:
        # Тут можна додати логіку перевірки
        return {"available": True}
    except:
        return {"available": False}