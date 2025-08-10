from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = "Genz API"
    environment: str = "development"
    version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "*"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/genz"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    def get_cors_origins(self) -> List[str]:
        raw = (self.cors_origins or "").strip()
        if raw == "*" or raw == "":
            return ["*"]
        return [part.strip() for part in raw.split(",") if part.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings() 