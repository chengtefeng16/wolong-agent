from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://localhost/wolong_saas"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Meta / WhatsApp
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_webhook_verify_token: str = "wolong_webhook_token"
    meta_api_version: str = "v20.0"

    # Encryption key for access tokens at rest (Fernet)
    token_encryption_key: str = ""  # base64 32-byte key; generate: Fernet.generate_key()

    # Gemini
    gemini_api_key: str = ""

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # App
    frontend_url: str = "http://localhost:5174"
    environment: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
