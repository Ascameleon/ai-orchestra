"""Provider contract shared by interchangeable LLM adapters."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    model: str
    text: str
    input_chars: int
    output_chars: int


class Provider(Protocol):
    def generate(self, prompt: str) -> ProviderResult:
        """Generate one response or raise a provider-specific exception."""
