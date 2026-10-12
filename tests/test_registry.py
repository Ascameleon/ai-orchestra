import pytest

from orchestra.providers.base import ProviderResult
from orchestra.registry import ProviderRegistry, UnknownProviderError


class StubProvider:
    def generate(self, prompt: str) -> ProviderResult:
        return ProviderResult("stub", "test-model", prompt, len(prompt), len(prompt))


def test_registry_normalizes_names_and_selects_explicit_provider():
    provider = StubProvider()
    registry = ProviderRegistry()
    registry.register(" Stub ", provider)
    assert registry.get("STUB") is provider
    assert registry.names() == ("stub",)


def test_registry_rejects_missing_and_duplicate_providers():
    registry = ProviderRegistry()
    registry.register("stub", StubProvider())
    with pytest.raises(ValueError, match="already registered"):
        registry.register("STUB", StubProvider())
    with pytest.raises(UnknownProviderError):
        registry.get("openai")


def test_registry_rejects_empty_name():
    with pytest.raises(ValueError, match="cannot be empty"):
        ProviderRegistry().register("  ", StubProvider())
