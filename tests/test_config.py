import pytest

from orchestra.config import load_settings


def test_load_settings_defaults_to_gemini_without_credentials(monkeypatch):
    for name in (
        "GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "XAI_API_KEY",
        "ORCHESTRA_PROVIDER", "ORCHESTRA_PROVIDER_FALLBACKS", "GEMINI_MODEL", "OPENAI_MODEL", "ANTHROPIC_MODEL",
        "ORCHESTRA_MAX_INPUT_CHARS", "ORCHESTRA_MAX_OUTPUT_TOKENS",
        "ORCHESTRA_MAX_REQUESTS", "ORCHESTRA_AUDIT_CAPACITY", "ORCHESTRA_MEMORY_DB",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = load_settings()
    assert settings.provider_name == "gemini"
    assert settings.gemini_api_key is None
    assert settings.openai_api_key is None
    assert settings.anthropic_api_key is None
    assert settings.grok_api_key is None
    assert settings.grok_model == "grok-3-mini"
    assert settings.max_requests_per_process == 100
    assert settings.memory_db_path is None


@pytest.mark.parametrize("name,value", [
    ("ORCHESTRA_MAX_INPUT_CHARS", "0"),
    ("ORCHESTRA_MAX_OUTPUT_TOKENS", "not-a-number"),
    ("ORCHESTRA_MAX_REQUESTS", "-1"),
    ("ORCHESTRA_AUDIT_CAPACITY", "10001"),
])
def test_load_settings_rejects_invalid_limits(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=name):
        load_settings()


@pytest.mark.parametrize("name", ["GEMINI_MODEL", "OPENAI_MODEL", "ANTHROPIC_MODEL", "GROK_MODEL"])
def test_load_settings_rejects_empty_model_names(monkeypatch, name):
    monkeypatch.setenv(name, "   ")
    with pytest.raises(ValueError, match="cannot be empty"):
        load_settings()


def test_provider_selection_is_normalized(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", " OPENAI ")
    settings = load_settings()
    assert settings.provider_name == "openai"


def test_empty_provider_selection_is_rejected(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", " ")
    with pytest.raises(ValueError, match="ORCHESTRA_PROVIDER"):
        load_settings()


def test_provider_fallbacks_are_normalized_and_ordered(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", " GEMINI ")
    monkeypatch.setenv("ORCHESTRA_PROVIDER_FALLBACKS", " OPENAI, anthropic ")
    settings = load_settings()
    assert settings.provider_name == "gemini"
    assert settings.provider_fallbacks == ("openai", "anthropic")


@pytest.mark.parametrize("fallbacks", [
    "gemini",
    "openai,OPENAI",
    "grok",
])
def test_provider_fallbacks_reject_primary_duplicates_or_unknown_names(monkeypatch, fallbacks):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", "gemini")
    monkeypatch.setenv("ORCHESTRA_PROVIDER_FALLBACKS", fallbacks)
    with pytest.raises(ValueError, match="fallback|unsupported"):
        load_settings()


def test_task_routes_are_validated_and_ordered(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", "gemini")
    monkeypatch.setenv("ORCHESTRA_PROVIDER_FALLBACKS", "openai,anthropic")
    monkeypatch.setenv("ORCHESTRA_TASK_ROUTES", "code=openai,writing=anthropic,planner=gemini,reviewer=openai,writer=anthropic")
    assert load_settings().task_routes == (("code", "openai"), ("writing", "anthropic"), ("planner", "gemini"), ("reviewer", "openai"), ("writer", "anthropic"))


@pytest.mark.parametrize("routes", ["code=grok", "unknown=openai", "code", "code=openai,code=anthropic"])
def test_invalid_task_routes_are_rejected(monkeypatch, routes):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", "gemini")
    monkeypatch.setenv("ORCHESTRA_PROVIDER_FALLBACKS", "openai,anthropic")
    monkeypatch.setenv("ORCHESTRA_TASK_ROUTES", routes)
    with pytest.raises(ValueError, match="ORCHESTRA_TASK_ROUTES"):
        load_settings()


def test_optional_memory_database_path_is_trimmed(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_MEMORY_DB", " /tmp/orchestra.sqlite3 ")
    assert load_settings().memory_db_path == "/tmp/orchestra.sqlite3"
