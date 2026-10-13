import pytest

from orchestra.config import Settings
from orchestra.providers.anthropic import AnthropicProvider
from orchestra.providers.base import ProviderConfigurationError


def make_settings(key="test-key", max_input=12):
    return Settings(
        gemini_api_key=None,
        gemini_model="unused",
        anthropic_api_key=key,
        anthropic_model="test-model",
        max_input_chars=max_input,
        max_output_tokens=32,
        provider_name="anthropic",
    )


def test_missing_anthropic_key_fails_before_client_creation():
    with pytest.raises(ProviderConfigurationError, match="ANTHROPIC_API_KEY"):
        AnthropicProvider(make_settings(key=None))


def test_anthropic_generation_uses_configured_model_and_limits():
    calls = []

    class FakeMessages:
        def create(self, **kwargs):
            calls.append(kwargs)
            text_block = type("TextBlock", (), {"type": "text", "text": "answer"})()
            other_block = type("OtherBlock", (), {"type": "tool_use", "text": ""})()
            return type("Response", (), {"content": [text_block, other_block]})()

    provider = AnthropicProvider.__new__(AnthropicProvider)
    provider._model = "test-model"
    provider._max_input_chars = 12
    provider._max_output_tokens = 32
    provider._client = type("Client", (), {"messages": FakeMessages()})()
    result = provider.generate("hello")
    assert result.provider == "anthropic"
    assert result.model == "test-model"
    assert result.text == "answer"
    assert calls[0]["max_tokens"] == 32
    assert calls[0]["messages"] == [{"role": "user", "content": "hello"}]


def test_anthropic_sdk_failure_is_normalized_for_failover():
    from orchestra.providers.base import ProviderCallError

    class FakeMessages:
        def create(self, **kwargs):
            raise LookupError("secret upstream error")

    provider = AnthropicProvider.__new__(AnthropicProvider)
    provider._model = "test-model"
    provider._max_input_chars = 12
    provider._max_output_tokens = 32
    provider._client = type("Client", (), {"messages": FakeMessages()})()
    with pytest.raises(ProviderCallError, match="Anthropic request failed"):
        provider.generate("hello")


def test_anthropic_rejects_invalid_prompt_without_network():
    provider = AnthropicProvider.__new__(AnthropicProvider)
    provider._max_input_chars = 3
    with pytest.raises(ValueError, match="empty"):
        provider.generate(" ")
    with pytest.raises(ValueError, match="exceeds 3"):
        provider.generate("long")
