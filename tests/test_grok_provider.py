from types import SimpleNamespace

import pytest

from orchestra.config import Settings
from orchestra.providers.base import ProviderCallError, ProviderConfigurationError
from orchestra.providers.grok import GrokProvider


def settings(**overrides):
    values = dict(
        gemini_api_key=None,
        gemini_model="unused",
        max_input_chars=20,
        max_output_tokens=32,
        xai_api_key="test-key",
        grok_model="test-grok",
    )
    values.update(overrides)
    return Settings(**values)


def test_grok_requires_xai_key():
    with pytest.raises(ProviderConfigurationError, match="XAI_API_KEY"):
        GrokProvider(settings(xai_api_key=None))


def test_grok_uses_xai_endpoint_and_returns_result(monkeypatch):
    calls = {}

    class FakeCompletions:
        def create(self, **kwargs):
            calls.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="hello"))]
            )

    class FakeClient:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr("openai.OpenAI", FakeClient)
    result = GrokProvider(settings()).generate("hi")
    assert calls["client"]["base_url"] == "https://api.x.ai/v1"
    assert calls["client"]["api_key"] == "test-key"
    assert calls["model"] == "test-grok"
    assert result.provider == "grok"
    assert result.text == "hello"


def test_grok_rejects_empty_and_oversized_prompts(monkeypatch):
    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: None))

    monkeypatch.setattr("openai.OpenAI", FakeClient)
    provider = GrokProvider(settings())
    with pytest.raises(ValueError, match="must not be empty"):
        provider.generate(" ")
    with pytest.raises(ValueError, match="exceeds"):
        provider.generate("x" * 21)


def test_grok_wraps_api_errors(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            raise RuntimeError("secret upstream detail")

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr("openai.OpenAI", FakeClient)
    provider = GrokProvider(settings())
    with pytest.raises(ProviderCallError, match="Grok request failed") as exc:
        provider.generate("hi")
    assert "secret upstream detail" not in str(exc.value)
