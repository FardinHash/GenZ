from __future__ import annotations
from typing import Tuple

try:
    import tiktoken  # type: ignore
except Exception:
    tiktoken = None  # type: ignore


def estimate_tokens_openai(text: str, model: str) -> int:
    if not text:
        return 0
    if tiktoken is None:
        return max(1, len(text) // 4)
    try:
        enc = tiktoken.encoding_for_model(model)  # may fallback
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def estimate_tokens(provider: str, text: str, model: str) -> int:
    if provider == "openai":
        return estimate_tokens_openai(text, model)
    # Simple fallback for others
    return max(1, len(text) // 4)


# USD per 1K tokens rough rates (example values; adjust as needed)
OPENAI_RATES = {
    # model: (prompt_per_1k, completion_per_1k)
    "gpt-4o-mini": (0.005, 0.015),
}
ANTHROPIC_RATES = {
    # model: (prompt_per_1k, completion_per_1k)
    "claude-3-haiku-20240307": (0.00025, 0.00125),
}
GEMINI_RATES = {
    # model: (prompt_per_1k, completion_per_1k)
    "gemini-1.5-flash": (0.00075, 0.003),
}


def get_rates(provider: str, model: str) -> Tuple[float, float]:
    if provider == "openai":
        return OPENAI_RATES.get(model, (0.005, 0.015))
    if provider == "anthropic":
        return ANTHROPIC_RATES.get(model, (0.00025, 0.00125))
    if provider == "gemini":
        return GEMINI_RATES.get(model, (0.00075, 0.003))
    return (0.001, 0.001)


def compute_cost_usd(provider: str, model: str, tokens_in: int, tokens_out: int) -> float:
    pin, pout = get_rates(provider, model)
    return round((tokens_in / 1000.0) * pin + (tokens_out / 1000.0) * pout, 6) 