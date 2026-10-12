"""Provider registry and explicit, deterministic provider selection."""
from collections.abc import Mapping

from orchestra.providers.base import Provider


class UnknownProviderError(LookupError):
    """Raised when a task requests a provider that is not registered."""


class ProviderRegistry:
    """Register adapters by their stable provider name."""

    def __init__(self) -> None:
        self._providers: dict[str, Provider] = {}

    def register(self, name: str, provider: Provider) -> None:
        normalized = name.strip().lower()
        if not normalized:
            raise ValueError("provider name cannot be empty")
        if normalized in self._providers:
            raise ValueError(f"provider already registered: {normalized}")
        self._providers[normalized] = provider

    def get(self, name: str) -> Provider:
        normalized = name.strip().lower()
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
