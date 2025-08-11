from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class RequestPublic(BaseModel):
    id: UUID
    domain: Optional[str] = None
    path: Optional[str] = None
    model: str
    model_provider: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True 