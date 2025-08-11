from abc import ABC, abstractmethod
from typing import Iterator, Optional
import uuid

from openai import OpenAI
import anthropic
import google.generativeai as genai

from app.models.user import User
from app.schemas.generate import GenerationRequest, GenerationResponse


def build_prompt(req: GenerationRequest) -> str:
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
    return "\n".join(parts)


class ModelAdapter(ABC):
    @abstractmethod
    def generate(self, user: User, req: GenerationRequest, api_key: Optional[str]) -> GenerationResponse:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    def generate_stream(self, user: User, req: GenerationRequest, api_key: Optional[str]) -> Iterator[str]:  # pragma: no cover - interface
        raise NotImplementedError


class OpenAIAdapter(ModelAdapter):
    provider = "openai"

    def generate(self, user: User, req: GenerationRequest, api_key: Optional[str]) -> GenerationResponse:
        if not api_key:
            raise ValueError("OpenAI API key is required")
        client = OpenAI(api_key=api_key)
        full_prompt = build_prompt(req)
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
        return GenerationResponse(id=str(uuid.uuid4()), output_text=text, model=req.model, provider=self.provider)

    def generate_stream(self, user: User, req: GenerationRequest, api_key: Optional[str]) -> Iterator[str]:
        if not api_key:
            raise ValueError("OpenAI API key is required")
        client = OpenAI(api_key=api_key)
        full_prompt = build_prompt(req)
        stream = client.chat.completions.create(
            model=req.model,
            messages=[
                {"role": "system", "content": "You write concise, context-aware replies."},
                {"role": "user", "content": full_prompt},
            ],
            temperature=(req.options.temperature if req.options and req.options.temperature is not None else 0.7),
            max_tokens=(req.options.max_tokens if req.options and req.options.max_tokens is not None else 512),
            stream=True,
        )
        for event in stream:  # type: ignore[assignment]
            delta = event.choices[0].delta.content or ""
            if delta:
                yield delta


class AnthropicAdapter(ModelAdapter):
    provider = "anthropic"

    def generate(self, user: User, req: GenerationRequest, api_key: Optional[str]) -> GenerationResponse:
        if not api_key:
            raise ValueError("Anthropic API key is required")
        client = anthropic.Anthropic(api_key=api_key)
        full_prompt = build_prompt(req)
        msg = client.messages.create(
            model=req.model,
            max_tokens=(req.options.max_tokens if req.options and req.options.max_tokens is not None else 512),
            temperature=(req.options.temperature if req.options and req.options.temperature is not None else 0.7),
            messages=[{"role": "user", "content": full_prompt}],
        )
        # content is a list of blocks; take text blocks
        text = "".join([c.text for c in msg.content if getattr(c, "text", None)])
        return GenerationResponse(id=str(uuid.uuid4()), output_text=text, model=req.model, provider=self.provider)

    def generate_stream(self, user: User, req: GenerationRequest, api_key: Optional[str]) -> Iterator[str]:
        if not api_key:
            raise ValueError("Anthropic API key is required")
        client = anthropic.Anthropic(api_key=api_key)
        full_prompt = build_prompt(req)
        with client.messages.stream(
            model=req.model,
            max_tokens=(req.options.max_tokens if req.options and req.options.max_tokens is not None else 512),
            temperature=(req.options.temperature if req.options and req.options.temperature is not None else 0.7),
            messages=[{"role": "user", "content": full_prompt}],
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta":
                    delta = getattr(event.delta, "text", "")
                    if delta:
                        yield delta


class GeminiAdapter(ModelAdapter):
    provider = "gemini"

    def _configure(self, api_key: str):
        genai.configure(api_key=api_key)

    def generate(self, user: User, req: GenerationRequest, api_key: Optional[str]) -> GenerationResponse:
        if not api_key:
            raise ValueError("Gemini API key is required")
        self._configure(api_key)
        full_prompt = build_prompt(req)
        model = genai.GenerativeModel(req.model)
        res = model.generate_content(full_prompt)
        text = getattr(res, "text", None) or ""
        return GenerationResponse(id=str(uuid.uuid4()), output_text=text, model=req.model, provider=self.provider)

    def generate_stream(self, user: User, req: GenerationRequest, api_key: Optional[str]) -> Iterator[str]:
        if not api_key:
            raise ValueError("Gemini API key is required")
        self._configure(api_key)
        full_prompt = build_prompt(req)
        model = genai.GenerativeModel(req.model)
        for chunk in model.generate_content(full_prompt, stream=True):
            delta = getattr(chunk, "text", None) or ""
            if delta:
                yield delta


def get_adapter(provider: str) -> ModelAdapter:
    if provider == "openai":
        return OpenAIAdapter()
    if provider == "anthropic":
        return AnthropicAdapter()
    if provider == "gemini":
        return GeminiAdapter()
    raise ValueError(f"Unsupported provider: {provider}") 