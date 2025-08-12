from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = "Genz API"
    environment: str = "development"
    version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "*"  # comma-separated or '*'

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/genz"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    refresh_jwt_secret_key: str | None = None
    refresh_token_expire_minutes: int = 60 * 24 * 30

    # Encryption for provider API keys (PBKDF2 -> Fernet)
    encryption_secret: str = "change-this-dev-secret"
    encryption_salt: str = "genz-salt"

    # Rate limiting / cache
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_requests_per_minute: int = 30

    # Admin
    admin_api_secret: str = "change-admin-secret"

    # Stripe
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_basic: str | None = None
    stripe_price_pro: str | None = None
    stripe_price_premium: str | None = None

    # Observability
    sentry_dsn: str | None = None

    def get_cors_origins(self) -> List[str]:
        raw = (self.cors_origins or "").strip()
        if raw == "*" or raw == "":
            return ["*"]
        return [part.strip() for part in raw.split(",") if part.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings() 