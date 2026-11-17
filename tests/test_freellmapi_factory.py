from orchestra.config import Settings
from orchestra.providers import factory
from orchestra.providers.base import ProviderConfigurationError


class FactoryProviderStub:
    def generate(self, prompt: str):
        raise AssertionError("factory construction tests must not call providers")


def test_factory_registers_freellmapi_without_live_calls(monkeypatch):
    class FakeFreeLLMAPIProvider(FactoryProviderStub):
        name = "freellmapi"

        def __init__(self, settings):
            self.settings = settings

    monkeypatch.setattr(factory, "FreeLLMAPIProvider", FakeFreeLLMAPIProvider)
    configured = Settings(
        gemini_api_key=None,
        gemini_model="unused",
        max_input_chars=12000,
        max_output_tokens=100,
        freellmapi_api_key="test-unified-key",
        freellmapi_base_url="http://127.0.0.1:3001/v1",
        freellmapi_model="auto",
        provider_name="freellmapi",
    )
    registry = factory.build_provider_registry(configured)
    assert registry.names() == ("freellmapi",)
    assert registry.get("freellmapi").settings.freellmapi_model == "auto"


def test_factory_rejects_missing_freellmapi_key():
    configured = Settings(
        gemini_api_key=None,
        gemini_model="unused",
        max_input_chars=12000,
        max_output_tokens=100,
        provider_name="freellmapi",
    )
    try:
        factory.build_provider_registry(configured)
    except ProviderConfigurationError as exc:
        assert "FREELLMAPI_API_KEY" in str(exc)
    else:
        raise AssertionError("Missing FreeLLMAPI key should be rejected")
