from orchestra.config import Settings
from orchestra.providers import factory
from orchestra.providers.base import ProviderConfigurationError


def settings(provider_name: str, api_key: str | None = "test-key") -> Settings:
    return Settings(
        gemini_api_key=api_key,
        provider_name=provider_name,
        gemini_model="test-model",
        max_input_chars=12000,
        max_output_tokens=100,
    )


def test_factory_registers_configured_gemini_without_live_calls(monkeypatch):
    class FakeGeminiProvider:
        name = "gemini"

        def __init__(self, settings):
            self.settings = settings

    monkeypatch.setattr(factory, "GeminiProvider", FakeGeminiProvider)
    registry = factory.build_provider_registry(settings("gemini"))
    assert registry.names() == ("gemini",)
    assert registry.get("gemini").settings.gemini_model == "test-model"


def test_factory_rejects_missing_gemini_key():
    try:
        factory.build_provider_registry(settings("gemini", api_key=None))
    except ProviderConfigurationError as exc:
        assert "GEMINI_API_KEY" in str(exc)
    else:
        raise AssertionError("Missing Gemini key should be rejected")


def test_factory_registers_configured_openai(monkeypatch):
    class FakeOpenAIProvider:
        name = "openai"

        def __init__(self, settings):
            self.settings = settings

    monkeypatch.setattr(factory, "OpenAIProvider", FakeOpenAIProvider)
    configured = Settings(
        gemini_api_key=None,
        gemini_model="unused",
        openai_api_key="test-key",
        openai_model="test-openai",
        max_input_chars=12000,
        max_output_tokens=100,
        provider_name="openai",
    )
    registry = factory.build_provider_registry(configured)
    assert registry.names() == ("openai",)
    assert registry.get("openai").settings.openai_model == "test-openai"


def test_factory_rejects_missing_openai_key():
    configured = Settings(
        gemini_api_key=None,
        gemini_model="unused",
        max_input_chars=12000,
        max_output_tokens=100,
        provider_name="openai",
    )
    try:
        factory.build_provider_registry(configured)
    except factory.ProviderConfigurationError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("Missing OpenAI key should be rejected")


def test_factory_rejects_unimplemented_provider():
    try:
        factory.build_provider_registry(settings("grok"))
    except factory.ProviderConfigurationError as exc:
        assert "Unsupported ORCHESTRA_PROVIDER" in str(exc)
    else:
        raise AssertionError("Unsupported provider should be rejected")


def test_factory_registers_configured_anthropic(monkeypatch):
    class FakeAnthropicProvider:
        name = "anthropic"

        def __init__(self, settings):
            self.settings = settings

    monkeypatch.setattr(factory, "AnthropicProvider", FakeAnthropicProvider)
    configured = Settings(
        gemini_api_key=None,
        gemini_model="unused",
        anthropic_api_key="test-key",
        anthropic_model="test-anthropic",
        max_input_chars=12000,
        max_output_tokens=100,
        provider_name="anthropic",
    )
    registry = factory.build_provider_registry(configured)
    assert registry.names() == ("anthropic",)
    assert registry.get("anthropic").settings.anthropic_model == "test-anthropic"


def test_factory_rejects_missing_anthropic_key():
    configured = Settings(
        gemini_api_key=None,
        gemini_model="unused",
        max_input_chars=12000,
        max_output_tokens=100,
        provider_name="anthropic",
    )
    try:
        factory.build_provider_registry(configured)
    except ProviderConfigurationError as exc:
        assert "ANTHROPIC_API_KEY" in str(exc)
    else:
        raise AssertionError("Missing Anthropic key should be rejected")
