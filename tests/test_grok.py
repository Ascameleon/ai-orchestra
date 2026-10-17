from types import SimpleNamespace

import pytest

from orchestra.config import Settings
from orchestra.providers.base import ProviderCallError, ProviderConfigurationError
from orchestra.providers.grok import GrokProvider


def settings(key="xai-test-key", max_input_chars=100, max_output_tokens=64):
    return Settings(
        gemini_api_key=None, gemini_model="gemini-test",
        max_input_chars=max_input_chars, max_output_tokens=max_output_tokens,
        grok_api_key=key, grok_model="grok-test",
    )


def test_grok_provider_uses_xai_endpoint_and_returns_validated_result(monkeypatch):
    captured = {}
    class FakeClient:
        def __init__(self, **kwargs): captured["client"] = kwargs
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    captured["request"] = kwargs
                    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))])
    import openai
    monkeypatch.setattr(openai, "OpenAI", FakeClient)
    result = GrokProvider(settings()).generate("hello")
    assert captured["client"]["base_url"] == "https://api.x.ai/v1"
    assert captured["client"]["api_key"] == "xai-test-key"
    assert captured["client"]["max_retries"] == 0
    assert captured["request"]["model"] == "grok-test"
    assert result.provider == "grok" and result.text == "ok"
    assert result.input_chars == 5 and result.output_chars == 2


def test_grok_provider_rejects_missing_key():
    with pytest.raises(ProviderConfigurationError, match="XAI_API_KEY"):
        GrokProvider(settings(key=None))


def test_grok_provider_rejects_oversized_prompt():
    provider = object.__new__(GrokProvider)
    provider._max_input_chars = 2
    with pytest.raises(ValueError, match="exceeds"):
        provider.generate("too long")


def test_grok_provider_wraps_upstream_errors(monkeypatch):
    class FakeClient:
        def __init__(self, **kwargs): pass
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs): raise RuntimeError("sensitive upstream detail")
    import openai
    monkeypatch.setattr(openai, "OpenAI", FakeClient)
    with pytest.raises(ProviderCallError, match="Grok request failed") as error:
        GrokProvider(settings()).generate("hello")
    assert "sensitive upstream detail" not in str(error.value)
