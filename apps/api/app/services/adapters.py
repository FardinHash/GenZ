from abc import ABC, abstractmethod
from typing import Optional
import uuid

from openai import OpenAI

from app.models.user import User
from app.models.key import ApiKey
from app.schemas.generate import GenerationRequest, GenerationResponse


class ModelAdapter(ABC):
    @abstractmethod
    def generate(self, user: User, req: GenerationRequest, api_key: Optional[str]) -> GenerationResponse:  # pragma: no cover - interface
        raise NotImplementedError


class OpenAIAdapter(ModelAdapter):
    def generate(self, user: User, req: GenerationRequest, api_key: Optional[str]) -> GenerationResponse:
        if not api_key:
            raise ValueError("OpenAI API key is required")
        client = OpenAI(api_key=api_key)

        # Build prompt with optional context and tone prefix
        parts: list[str] = []
        if req.options and req.options.tone:
            parts.append(f"Tone: {req.options.tone}\n")
        parts.append(req.prompt)
        if req.context:
            ctx_bits = []
            if req.context.selected_text:
                ctx_bits.append(f"Selected:\n{req.context.selected_text}")
            if req.context.page_text:
                ctx_bits.append(f"Context:\n{req.context.page_text[:2000]}")
            if ctx_bits:
                parts.append("\n\n" + "\n".join(ctx_bits))
        full_prompt = "\n".join(parts)

        # Use chat.completions for broader model support
        completion = client.chat.completions.create(
            model=req.model,
            messages=[
                {"role": "system", "content": "You write concise, context-aware replies."},
                {"role": "user", "content": full_prompt},
            ],
            temperature=(req.options.temperature if req.options and req.options.temperature is not None else 0.7),
            max_tokens=(req.options.max_tokens if req.options and req.options.max_tokens is not None else 512),
        )
        text = completion.choices[0].message.content or ""
        return GenerationResponse(
            id=str(uuid.uuid4()),
            output_text=text,
            model=req.model,
            provider="openai",
        )


def get_adapter(provider: str) -> ModelAdapter:
    if provider == "openai":
        return OpenAIAdapter()
    # Placeholders for later providers
    raise ValueError(f"Unsupported provider: {provider}") 