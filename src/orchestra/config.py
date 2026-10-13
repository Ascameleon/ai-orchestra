"""Environment configuration with validated, conservative request limits."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None
    gemini_model: str
    max_input_chars: int
    max_output_tokens: int
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-haiku-latest"
    provider_name: str = "gemini"
    max_requests_per_process: int = 100
    audit_capacity: int = 1000


def load_settings() -> Settings:
    def positive_int(name: str, default: int, maximum: int) -> int:
        raw = os.getenv(name, str(default))
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError(f"{name} must be an integer") from exc
        if not 1 <= value <= maximum:
            raise ValueError(f"{name} must be between 1 and {maximum}")
        return value

    key = os.getenv("GEMINI_API_KEY", "").strip() or None
    openai_key = os.getenv("OPENAI_API_KEY", "").strip() or None
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    if not openai_model:
        raise ValueError("OPENAI_MODEL cannot be empty")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip() or None
    anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest").strip()
    if not anthropic_model:
        raise ValueError("ANTHROPIC_MODEL cannot be empty")
    provider_name = os.getenv("ORCHESTRA_PROVIDER", "gemini").strip().lower()
    if not provider_name:
        raise ValueError("ORCHESTRA_PROVIDER cannot be empty")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    if not model:
        raise ValueError("GEMINI_MODEL cannot be empty")
    return Settings(
        gemini_api_key=key,
        openai_api_key=openai_key,
        openai_model=openai_model,
        anthropic_api_key=anthropic_key,
        anthropic_model=anthropic_model,
        provider_name=provider_name,
        gemini_model=model,
        max_input_chars=positive_int("ORCHESTRA_MAX_INPUT_CHARS", 12000, 100000),
        max_output_tokens=positive_int("ORCHESTRA_MAX_OUTPUT_TOKENS", 1024, 8192),
        max_requests_per_process=positive_int("ORCHESTRA_MAX_REQUESTS", 100, 100000),
        audit_capacity=positive_int("ORCHESTRA_AUDIT_CAPACITY", 1000, 10000),
    )
