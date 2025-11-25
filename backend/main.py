import sys, pathlib
from dotenv import load_dotenv

# Додати корінь проєкту в sys.path
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Завантажити .env з кореня проєкту
load_dotenv(dotenv_path=ROOT / ".env")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .checkers.security_config import SecurityConfig
from .services.dynamodb import DynamoDBService

# Імпорт роутів
from .routes import auth_router, check_router, health_router

class RFCheckerAPI:
    """Головний клас API"""
    
    def __init__(self):
        self.limiter = Limiter(key_func=get_remote_address)
        self.app = self._create_app()
        self.db = DynamoDBService()
        self._setup_middleware()
        self._setup_routes()
    
    def _create_app(self) -> FastAPI:
        """Створення FastAPI додатку"""
        app = FastAPI(
            title="RF Checker API",
            version="1.0.0",
            description="API для перевірки контенту на наявність російської пропаганди",
            docs_url=None,  # Вимкнути в продакшені
            redoc_url=None,
            openapi_url=None
        )
        app.state.limiter = self.limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        return app
    
    def _setup_middleware(self):
        """Налаштування middleware"""
        
        # Security headers
        @self.app.middleware("http")
        async def add_security_headers(request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'"
            return response
        
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=SecurityConfig.ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Trusted hosts
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=SecurityConfig.ALLOWED_HOSTS
        )
        
        # Gzip
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    def _setup_routes(self):
        """Підключення роутів"""
        self.app.include_router(health_router)
        self.app.include_router(auth_router)
        self.app.include_router(check_router)
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Запуск сервера"""
        import uvicorn
        uvicorn.run("backend.main:app", host=host, port=port, reload=True)

# Створення екземплярів для експорту
api = RFCheckerAPI()
app = api.app

if __name__ == "__main__":
    api.run()