import secrets, os, pathlib
from dotenv import load_dotenv
BASE_DIR = pathlib.Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env") 
class SecurityConfig:
    """Конфігурація безпеки"""
    API_KEYS = {
        os.getenv("API_KEY_1", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc2MzIzNzUxNH0.UKvk6j936tMm_RrQF26iptZx2MDBpuN-InpCGnea6lc"): "admin",
        os.getenv("API_KEY_2", "dev-key-2"): "user2"
    }
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM = "HS256"
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
