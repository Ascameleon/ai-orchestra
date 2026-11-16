import sys
from types import SimpleNamespace

import pytest

from orchestra.config import Settings
from orchestra.providers.base import ProviderCallError, ProviderConfigurationError
from orchestra.providers.freellmapi import FreeLLMAPIProvider


def settings(**overrides):
    values = {
        "gemini_api_key": None,
        "gemini_model": "unused",
        "max_input_chars": 20,
        "max_output_tokens": 32,
        "freellmapi_api_key": "test-unified-key",
        "freellmapi_base_url": "http://127.0.0.1:3001/v1",
        "freellmapi_model": "auto",
    }
    values.update(overrides)
    return Settings(**values)


def install_fake_openai(monkeypatch, client_class):
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=client_class))


def test_freellmapi_requires_unified_key():
    with pytest.raises(ProviderConfigurationError, match="FREELLMAPI_API_KEY"):
        FreeLLMAPIProvider(settings(freellmapi_api_key=None))


def test_freellmapi_uses_configured_openai_compatible_endpoint(monkeypatch):
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
    result = FreeLLMAPIProvider(settings()).generate("hi")
    assert calls["client"]["base_url"] == "http://127.0.0.1:3001/v1"
    assert calls["client"]["api_key"] == "test-unified-key"
    assert calls["client"]["max_retries"] == 0
    assert calls["model"] == "auto"
    assert calls["max_tokens"] == 32
    assert result.provider == "freellmapi"
    assert result.model == "auto"
    assert result.text == "hello"


def test_freellmapi_rejects_empty_and_oversized_prompts(monkeypatch):
    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=lambda **kw: None)
            )

    install_fake_openai(monkeypatch, FakeClient)
    provider = FreeLLMAPIProvider(settings())
    with pytest.raises(ValueError, match="must not be empty"):
        provider.generate(" ")
    with pytest.raises(ValueError, match="exceeds"):
        provider.generate("x" * 21)


def test_freellmapi_wraps_upstream_errors_without_leaking_details(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            raise RuntimeError("sensitive upstream detail")

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    install_fake_openai(monkeypatch, FakeClient)
    with pytest.raises(ProviderCallError, match="FreeLLMAPI request failed") as exc:
        FreeLLMAPIProvider(settings()).generate("hi")
    assert "sensitive upstream detail" not in str(exc.value)
