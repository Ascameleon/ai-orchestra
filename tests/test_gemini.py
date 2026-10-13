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


def test_missing_api_key_fails_before_client_creation():
    with pytest.raises(ProviderConfigurationError, match="GEMINI_API_KEY"):
        GeminiProvider(settings(key=None))


def test_empty_prompt_is_rejected_before_provider_call():
    provider = GeminiProvider.__new__(GeminiProvider)
    provider._max_input_chars = 12
    with pytest.raises(ValueError, match="empty"):
        provider.generate("   ")


def test_prompt_over_limit_is_rejected_before_provider_call():
    provider = GeminiProvider.__new__(GeminiProvider)
    provider._max_input_chars = 3
    with pytest.raises(ValueError, match="exceeds 3"):
        provider.generate("long prompt")


def test_successful_generation_uses_configured_model_and_limits():
    calls = []

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            return type("Response", (), {"text": "  answer  "})()

    class FakeClient:
        models = FakeModels()

    provider = GeminiProvider.__new__(GeminiProvider)
    provider._max_input_chars = 12
    provider._max_output_tokens = 32
    provider._model = "test-model"
    provider._client = FakeClient()

    result = provider.generate("hello")

    assert result.provider == "gemini"
    assert result.model == "test-model"
    assert result.text == "  answer  "
    assert result.input_chars == 5
    assert result.output_chars == len("  answer  ")
    assert calls[0]["model"] == "test-model"
    assert calls[0]["contents"] == "hello"
    assert calls[0]["config"].max_output_tokens == 32


def test_sdk_failure_is_normalized_for_failover():
    from orchestra.providers.base import ProviderCallError

    class FakeModels:
        def generate_content(self, **kwargs):
            raise LookupError("secret upstream error")

    class FakeClient:
        models = FakeModels()

    provider = GeminiProvider.__new__(GeminiProvider)
    provider._max_input_chars = 12
    provider._max_output_tokens = 32
    provider._model = "test-model"
    provider._client = FakeClient()
    with pytest.raises(ProviderCallError, match="Gemini request failed"):
        provider.generate("hello")


def test_empty_provider_response_is_reported():
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


def test_malformed_sdk_response_is_normalized_for_failover():
    from orchestra.providers.base import ProviderCallError

    class FakeResponse:
        @property
        def text(self):
            raise ValueError("response has no readable candidate")

    class FakeModels:
        def generate_content(self, **kwargs):
            return FakeResponse()

    class FakeClient:
        models = FakeModels()

    provider = GeminiProvider.__new__(GeminiProvider)
    provider._max_input_chars = 12
    provider._max_output_tokens = 32
    provider._model = "test-model"
    provider._client = FakeClient()
    with pytest.raises(ProviderCallError, match="invalid response"):
        provider.generate("hello")
