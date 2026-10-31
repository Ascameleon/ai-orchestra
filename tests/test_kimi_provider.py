import sys
from types import SimpleNamespace

import pytest

from orchestra.config import Settings
from orchestra.providers.base import ProviderCallError, ProviderConfigurationError
from orchestra.providers.kimi import KimiProvider


def settings(**overrides):
    values = {
        "gemini_api_key": None,
        "gemini_model": "unused",
        "max_input_chars": 20,
        "max_output_tokens": 32,
        "kimi_api_key": "test-key",
        "kimi_model": "test-kimi",
    }
    values.update(overrides)
    return Settings(**values)


def install_fake_openai(monkeypatch, client_class):
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=client_class))


def test_kimi_requires_api_key():
    with pytest.raises(ProviderConfigurationError, match="KIMI_API_KEY"):
        KimiProvider(settings(kimi_api_key=None))


def test_kimi_uses_international_endpoint_and_returns_result(monkeypatch):
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
    result = KimiProvider(settings()).generate("hi")
    assert calls["client"]["base_url"] == "https://api.moonshot.ai/v1"
    assert calls["client"]["api_key"] == "test-key"
    assert calls["client"]["max_retries"] == 0
    assert calls["model"] == "test-kimi"
    assert calls["max_tokens"] == 32
    assert result.provider == "kimi"
    assert result.text == "hello"


def test_kimi_rejects_empty_and_oversized_prompts(monkeypatch):
    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=lambda **kw: None)
            )

    install_fake_openai(monkeypatch, FakeClient)
    provider = KimiProvider(settings())
    with pytest.raises(ValueError, match="must not be empty"):
        provider.generate(" ")
    with pytest.raises(ValueError, match="exceeds"):
        provider.generate("x" * 21)


def test_kimi_wraps_api_errors(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            raise RuntimeError("secret upstream detail")

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    install_fake_openai(monkeypatch, FakeClient)
    provider = KimiProvider(settings())
    with pytest.raises(ProviderCallError, match="Kimi request failed") as exc:
        provider.generate("hi")
    assert "secret upstream detail" not in str(exc.value)
