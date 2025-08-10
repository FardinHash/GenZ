from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_validator


class ApiKeyCreate(BaseModel):
    provider: str
    key: str
    key_type: str = "user_provided"

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        allowed = {"openai", "anthropic", "gemini"}
        if v not in allowed:
            raise ValueError(f"provider must be one of {sorted(allowed)}")
        return v


class ApiKeyPublic(BaseModel):
    id: UUID
    provider: str
    key_type: str
    created_at: datetime

    class Config:
        from_attributes = True 