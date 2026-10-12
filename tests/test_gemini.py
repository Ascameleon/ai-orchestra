import pytest

from orchestra.config import Settings
from orchestra.providers.gemini import GeminiProvider, ProviderConfigurationError


def settings(key="test-key", max_input=12):
    return Settings(
        gemini_api_key=key,
        gemini_model="test-model",
        max_input_chars=max_input,
        max_output_tokens=32,
    )


def test_missing_api_key_fails_before_network_call():
    with pytest.raises(ProviderConfigurationError, match="GEMINI_API_KEY"):
        GeminiProvider(settings(key=None))


def test_empty_prompt_is_rejected():
    provider = GeminiProvider.__new__(GeminiProvider)
    provider._max_input_chars = 12
    with pytest.raises(ValueError, match="empty"):
        provider.generate("   ")


def test_prompt_over_limit_is_rejected_before_network_call():
    provider = GeminiProvider.__new__(GeminiProvider)
    provider._max_input_chars = 3
    with pytest.raises(ValueError, match="exceeds 3"):
        provider.generate("long prompt")


def test_empty_provider_response_is_reported(monkeypatch):
    class FakeModels:
        def generate_content(self, **kwargs):
            return type("Response", (), {"text": "  "})()

    class FakeClient:
        models = FakeModels()

    provider = GeminiProvider.__new__(GeminiProvider)
    provider._max_input_chars = 12
    provider._max_output_tokens = 32
    provider._model = "test-model"
    provider._client = FakeClient()
    with pytest.raises(RuntimeError, match="empty response"):
        provider.generate("hello")
