from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from typing import Optional
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.services.dynamodb import DynamoDBService

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

class AuthService:
    try:
        db = DynamoDBService()
    except Exception as e:
        print(f"⚠️ DynamoDB initialization failed: {str(e)}")
        db = None
    
    @staticmethod
    async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
        """Перевірка API ключа через DynamoDB"""
        if not AuthService.db:
            raise HTTPException(
                status_code=503, 
                detail="Database service unavailable. Run: python -m backend.services.init_dynamodb"
            )
        
        if not api_key:
            raise HTTPException(status_code=401, detail="API Key required")
        
        username = AuthService.db.verify_api_key(api_key)
        
        if not username:
            raise HTTPException(status_code=401, detail="Invalid API Key")
        
        return username
    
    @staticmethod
    def verify_credentials(username: str, password: str) -> Optional[dict]:
        """Перевірка логіну та паролю"""
        if not AuthService.db:
            return None
        return AuthService.db.verify_credentials(username, password)
