from orchestra.providers.base import ProviderConfigurationError
import pytest

from orchestra.config import Settings
from orchestra.providers.openai import OpenAIProvider


def make_settings(key="test-key", max_input=12):
    return Settings(
        gemini_api_key=None,
        gemini_model="unused",
        openai_api_key=key,
        openai_model="test-model",
        max_input_chars=max_input,
        max_output_tokens=32,
        provider_name="openai",
    )


def test_missing_openai_key_fails_before_client_creation():
    with pytest.raises(ProviderConfigurationError, match="OPENAI_API_KEY"):
        OpenAIProvider(make_settings(key=None))


def test_openai_generation_uses_limits_and_configured_model():
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            message = type("Message", (), {"content": "test answer"})()
            choice = type("Choice", (), {"message": message})()
            return type("Response", (), {"choices": [choice]})()

    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider._model = "test-model"
    provider._max_input_chars = 12
    provider._max_output_tokens = 32
    provider._client = type(
        "Client", (), {"chat": type("Chat", (), {"completions": FakeCompletions()})()}
    )()

    result = provider.generate("hello")

    assert result.provider == "openai"
    assert result.model == "test-model"
    assert result.text == "test answer"
    assert result.input_chars == 5
    assert calls[0]["model"] == "test-model"
    assert calls[0]["messages"] == [{"role": "user", "content": "hello"}]
    assert calls[0]["max_tokens"] == 32


def test_openai_rejects_empty_or_oversized_prompt_before_network():
    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider._max_input_chars = 3
    with pytest.raises(ValueError, match="empty"):
        provider.generate("  ")
    with pytest.raises(ValueError, match="exceeds 3"):
        provider.generate("long")
