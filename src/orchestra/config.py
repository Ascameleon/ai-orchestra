"""Environment configuration with conservative request limits."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None
    gemini_model: str
    max_input_chars: int
    max_output_tokens: int


def load_settings() -> Settings:
    def positive_int(name: str, default: int) -> int:
        raw = os.getenv(name, str(default))
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError(f"{name} must be an integer") from exc
        if value < 1:
            raise ValueError(f"{name} must be greater than zero")
        return value

    key = os.getenv("GEMINI_API_KEY", "").strip() or None
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    if not model:
        raise ValueError("GEMINI_MODEL cannot be empty")
    return Settings(key, model, positive_int("ORCHESTRA_MAX_INPUT_CHARS", 12000), positive_int("ORCHESTRA_MAX_OUTPUT_TOKENS", 1024))
