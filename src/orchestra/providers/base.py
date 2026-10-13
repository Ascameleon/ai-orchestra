"""Provider contracts and shared adapter errors."""
from dataclasses import dataclass
from typing import Protocol


class ProviderConfigurationError(RuntimeError):
    """Raised when a provider cannot be constructed from available configuration."""


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
