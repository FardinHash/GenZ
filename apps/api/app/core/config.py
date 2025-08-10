from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "Genz API"
    environment: str = "development"
    version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    cors_origins: List[str] = ["*"]


@lru_cache()
def get_settings() -> Settings:
    return Settings() 