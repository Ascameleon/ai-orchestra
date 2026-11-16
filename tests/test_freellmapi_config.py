import pytest

from orchestra.config import load_settings


def test_freellmapi_can_be_selected_as_primary(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", "freellmapi")
    monkeypatch.setenv("FREELLMAPI_API_KEY", "test-unified-key")
    monkeypatch.setenv("FREELLMAPI_MODEL", "auto")
    settings = load_settings()
    assert settings.provider_name == "freellmapi"
    assert settings.freellmapi_api_key == "test-unified-key"
    assert settings.freellmapi_model == "auto"
    assert settings.freellmapi_base_url == "http://127.0.0.1:3001/v1"


def test_freellmapi_can_be_configured_as_fallback(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", "gemini")
    monkeypatch.setenv("ORCHESTRA_PROVIDER_FALLBACKS", "freellmapi")
    monkeypatch.setenv("FREELLMAPI_API_KEY", "test-unified-key")
    assert load_settings().provider_fallbacks == ("freellmapi",)


def test_freellmapi_requires_key_when_selected(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", "freellmapi")
    monkeypatch.delenv("FREELLMAPI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="FREELLMAPI_API_KEY"):
        load_settings()


@pytest.mark.parametrize("url", [
    "ftp://example.com/v1",
    "https://user:pass@example.com/v1",
    "https://example.com/v1?token=secret",
    "http://example.com/v1",
])
def test_freellmapi_rejects_unsafe_base_urls(monkeypatch, url):
    monkeypatch.setenv("FREELLMAPI_BASE_URL", url)
    with pytest.raises(ValueError, match="FREELLMAPI_BASE_URL"):
        load_settings()


def test_freellmapi_accepts_https_remote_gateway(monkeypatch):
    monkeypatch.setenv("FREELLMAPI_BASE_URL", "https://gateway.example/v1/")
    assert load_settings().freellmapi_base_url == "https://gateway.example/v1"


@pytest.mark.parametrize("provider,fallbacks", [
    ("freellmapi", ""),
    ("gemini", "freellmapi"),
])
def test_freellmapi_requires_key_when_selected_or_fallback(monkeypatch, provider, fallbacks):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", provider)
    monkeypatch.setenv("ORCHESTRA_PROVIDER_FALLBACKS", fallbacks)
    monkeypatch.delenv("FREELLMAPI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="FREELLMAPI_API_KEY"):
        load_settings()


@pytest.mark.parametrize("url", [
    "http://192.168.1.20:3001/v1",
    "/v1",
    "https://example.com/v1#fragment",
])
def test_freellmapi_rejects_additional_unsafe_base_urls(monkeypatch, url):
    monkeypatch.setenv("FREELLMAPI_BASE_URL", url)
    with pytest.raises(ValueError, match="FREELLMAPI_BASE_URL"):
        load_settings()


@pytest.mark.parametrize("url", [
    "http://127.0.0.1:3001/v1",
    "http://localhost:3001/v1",
    "http://[::1]:3001/v1",
])
def test_freellmapi_accepts_loopback_http_gateway(monkeypatch, url):
    monkeypatch.setenv("FREELLMAPI_BASE_URL", url)
    assert load_settings().freellmapi_base_url == url
