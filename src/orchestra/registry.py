"""Provider registry and explicit, deterministic provider selection."""
from collections.abc import Mapping

from orchestra.providers.base import Provider


class UnknownProviderError(LookupError):
    """Raised when a task requests a provider that is not registered."""


class ProviderRegistry:
    """Register adapters by their stable provider name."""

    def __init__(self) -> None:
        self._providers: dict[str, Provider] = {}

    @staticmethod
    def _normalize_name(name: str) -> str:
        if not isinstance(name, str):
            raise ValueError("provider name must be a string")
        normalized = name.strip().lower()
        if not normalized:
            raise ValueError("provider name cannot be empty")
        return normalized

    def register(self, name: str, provider: Provider) -> None:
        normalized = self._normalize_name(name)
        generate = getattr(provider, "generate", None)
        if not callable(generate):
            raise TypeError("provider must implement callable generate(prompt)")
        declared_name = getattr(provider, "name", None)
        if not isinstance(declared_name, str) or not declared_name.strip():
            raise ValueError("provider must declare a non-empty string name")
        if declared_name.strip().lower() != normalized:
            raise ValueError(
                f"provider identity mismatch: registry key '{normalized}' "
                f"does not match adapter name '{declared_name.strip().lower()}'"
            )
        if normalized in self._providers:
            raise ValueError(f"provider already registered: {normalized}")
        self._providers[normalized] = provider

    def get(self, name: str) -> Provider:
        try:
            normalized = self._normalize_name(name)
        except ValueError:
            raise UnknownProviderError("provider is not configured: <invalid name>") from None
        try:
            return self._providers[normalized]
        except KeyError:
            raise UnknownProviderError(f"provider is not configured: {normalized}") from None

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))

    @classmethod
    def from_mapping(cls, providers: Mapping[str, Provider]) -> "ProviderRegistry":
        registry = cls()
        for name, provider in providers.items():
            registry.register(name, provider)
        return registry
