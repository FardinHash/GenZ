from typing import Literal, Optional
from pydantic import BaseModel, Field, HttpUrl


class GenerationContext(BaseModel):
    selected_text: Optional[str] = None
    page_text: Optional[str] = None
    url: Optional[HttpUrl] = None
    title: Optional[str] = None


class GenerationOptions(BaseModel):
    tone: Optional[str] = Field(default=None, description="Tone preset or freeform")
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7


class GenerationRequest(BaseModel):
    model: str
    model_provider: Literal["openai", "anthropic", "gemini"]
    prompt: str
    context: Optional[GenerationContext] = None
    options: Optional[GenerationOptions] = None
    use_user_key: bool = True


class GenerationResponse(BaseModel):
    id: str
    output_text: str
    model: str
    provider: str 