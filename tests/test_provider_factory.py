from orchestra.config import Settings
from orchestra.providers import factory


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
    except factory.ProviderConfigurationError as exc:
        assert "GEMINI_API_KEY" in str(exc)
    else:
        raise AssertionError("Missing Gemini key should be rejected")


def test_factory_rejects_unimplemented_provider():
    try:
        factory.build_provider_registry(settings("openai"))
    except factory.ProviderConfigurationError as exc:
        assert "Unsupported ORCHESTRA_PROVIDER" in str(exc)
    else:
        raise AssertionError("Unsupported provider should be rejected")
