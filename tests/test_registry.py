import pytest

from orchestra.providers.base import ProviderResult
from orchestra.registry import ProviderRegistry, UnknownProviderError


class StubProvider:
    def __init__(self, name: str = "stub"):
        self.name = name

    def generate(self, prompt: str) -> ProviderResult:
        return ProviderResult(self.name, "test-model", prompt, len(prompt), len(prompt))


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
    with pytest.raises(UnknownProviderError, match="provider is not configured"):
        registry.get("openai")


def test_registry_rejects_empty_name():
    with pytest.raises(ValueError, match="cannot be empty"):
        ProviderRegistry().register("  ", StubProvider())


@pytest.mark.parametrize("name", [None, 1])
def test_registry_rejects_non_string_names(name):
    with pytest.raises(TypeError, match="must be a string"):
        ProviderRegistry().register(name, StubProvider())  # type: ignore[arg-type]


def test_registry_rejects_adapter_identity_mismatch():
    registry = ProviderRegistry()

    with pytest.raises(ValueError, match="identity mismatch"):
        registry.register("gemini", StubProvider("openai"))

    assert registry.names() == ()


def test_registry_rejects_provider_without_generate():
    with pytest.raises(TypeError, match="callable generate"):
        ProviderRegistry().register("stub", object())  # type: ignore[arg-type]


def test_registry_rejects_provider_without_declared_name():
    class UnnamedProvider:
        def generate(self, prompt: str) -> ProviderResult:
            return ProviderResult("unnamed", "test-model", prompt, len(prompt), len(prompt))

    with pytest.raises(ValueError, match="declare a non-empty string name"):
        ProviderRegistry().register("stub", UnnamedProvider())  # type: ignore[arg-type]


def test_registry_from_mapping_rejects_key_adapter_mismatch():
    with pytest.raises(ValueError, match="identity mismatch"):
        ProviderRegistry.from_mapping({"gemini": StubProvider("openai")})


@pytest.mark.parametrize("name", [None, 1, "", "   ", "missing"])
def test_registry_get_reports_unknown_or_invalid_names(name):
    with pytest.raises(UnknownProviderError, match="provider is not configured"):
        ProviderRegistry().get(name)  # type: ignore[arg-type]
