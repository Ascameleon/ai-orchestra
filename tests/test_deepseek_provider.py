import sys
from types import SimpleNamespace

import pytest

from orchestra.config import Settings
from orchestra.providers.base import ProviderCallError, ProviderConfigurationError
from orchestra.providers.deepseek import DeepSeekProvider


def settings(**overrides):
    values = {
        "gemini_api_key": None,
        "gemini_model": "unused",
        "max_input_chars": 20,
        "max_output_tokens": 32,
        "deepseek_api_key": "test-key",
        "deepseek_model": "test-deepseek",
    }
    values.update(overrides)
    return Settings(**values)


def install_fake_openai(monkeypatch, client_class):
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=client_class))


def test_deepseek_requires_api_key():
    with pytest.raises(ProviderConfigurationError, match="DEEPSEEK_API_KEY"):
        DeepSeekProvider(settings(deepseek_api_key=None))


def test_deepseek_uses_official_endpoint_and_returns_result(monkeypatch):
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

    install_fake_openai(monkeypatch, FakeClient)
    result = DeepSeekProvider(settings()).generate("hi")
    assert calls["client"]["base_url"] == "https://api.deepseek.com"
    assert calls["client"]["api_key"] == "test-key"
    assert calls["client"]["max_retries"] == 0
    assert calls["model"] == "test-deepseek"
    assert calls["max_tokens"] == 32
    assert result.provider == "deepseek"
    assert result.text == "hello"


def test_deepseek_rejects_empty_and_oversized_prompts(monkeypatch):
    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=lambda **kw: None)
            )

    install_fake_openai(monkeypatch, FakeClient)
    provider = DeepSeekProvider(settings())
    with pytest.raises(ValueError, match="must not be empty"):
        provider.generate(" ")
    with pytest.raises(ValueError, match="exceeds"):
        provider.generate("x" * 21)


def test_deepseek_wraps_api_errors(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            raise RuntimeError("secret upstream detail")

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    install_fake_openai(monkeypatch, FakeClient)
    provider = DeepSeekProvider(settings())
    with pytest.raises(ProviderCallError, match="DeepSeek request failed") as exc:
        provider.generate("hi")
    assert "secret upstream detail" not in str(exc.value)
