import pytest

from orchestra.config import load_settings


def test_load_settings_defaults_to_gemini_without_credentials(monkeypatch):
    for name in (
        "GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "XAI_API_KEY",
        "KIMI_API_KEY", "MOONSHOT_API_KEY", "DEEPSEEK_API_KEY", "FREELLMAPI_API_KEY", "MANUS_API_KEY",
        "MANUS_ALLOW_PAID_CALLS", "MANUS_ALLOW_AGENT_TOOLS", "MANUS_AGENT_PROFILE", "MANUS_TIMEOUT_SECONDS", "MANUS_POLL_INTERVAL_SECONDS",
        "ORCHESTRA_PROVIDER", "ORCHESTRA_PROVIDER_FALLBACKS", "GEMINI_MODEL", "OPENAI_MODEL",
        "ANTHROPIC_MODEL", "GROK_MODEL", "KIMI_MODEL", "DEEPSEEK_MODEL",
        "FREELLMAPI_BASE_URL", "FREELLMAPI_MODEL",
        "ORCHESTRA_MAX_INPUT_CHARS", "ORCHESTRA_MAX_OUTPUT_TOKENS",
        "ORCHESTRA_MAX_REQUESTS", "ORCHESTRA_AUDIT_CAPACITY", "ORCHESTRA_MEMORY_DB",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = load_settings()
    assert settings.provider_name == "gemini"
    assert settings.gemini_model == "gemini-3.8-flash"
    assert settings.openai_model == "gpt-5.6-luna"
    assert settings.anthropic_model == "claude-haiku-4-5-20251001"
    assert settings.gemini_api_key is None
    assert settings.openai_api_key is None
    assert settings.anthropic_api_key is None
    assert settings.max_requests_per_process == 100
    assert settings.memory_db_path is None
    assert settings.manus_api_key is None
    assert settings.manus_allow_paid_calls is False
    assert settings.manus_allow_agent_tools is False
    assert settings.manus_agent_profile == "lite"


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


@pytest.mark.parametrize("name", ["GEMINI_MODEL", "OPENAI_MODEL", "ANTHROPIC_MODEL", "GROK_MODEL", "KIMI_MODEL", "DEEPSEEK_MODEL", "FREELLMAPI_MODEL"])
def test_load_settings_rejects_empty_model_names(monkeypatch, name):
    monkeypatch.setenv(name, "   ")
    with pytest.raises(ValueError, match="cannot be empty"):
        load_settings()


@pytest.mark.parametrize("name", ["GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "XAI_API_KEY", "KIMI_API_KEY", "DEEPSEEK_API_KEY", "FREELLMAPI_API_KEY"])
def test_load_settings_treats_example_secrets_as_missing(monkeypatch, name):
    monkeypatch.setenv(name, "REPLACE_WITH_A_LONG_RANDOM_SECRET")
    settings = load_settings()
    attribute = {
        "GEMINI_API_KEY": "gemini_api_key",
        "OPENAI_API_KEY": "openai_api_key",
        "ANTHROPIC_API_KEY": "anthropic_api_key",
        "XAI_API_KEY": "xai_api_key",
        "KIMI_API_KEY": "kimi_api_key",
        "DEEPSEEK_API_KEY": "deepseek_api_key",
        "FREELLMAPI_API_KEY": "freellmapi_api_key",
        "MANUS_API_KEY": "manus_api_key",
    }[name]
    assert getattr(settings, attribute) is None


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


def test_grok_provider_selection_and_fallback(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", "grok")
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setenv("GROK_MODEL", "test-grok")
    settings = load_settings()
    assert settings.provider_name == "grok"
    assert settings.xai_api_key == "test-key"
    assert settings.grok_model == "test-grok"


def test_kimi_provider_selection_and_fallback(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", "kimi")
    monkeypatch.setenv("KIMI_API_KEY", "test-kimi-key")
    monkeypatch.setenv("KIMI_MODEL", "test-kimi")
    settings = load_settings()
    assert settings.provider_name == "kimi"
    assert settings.kimi_api_key == "test-kimi-key"
    assert settings.kimi_model == "test-kimi"


def test_moonshot_api_key_is_accepted_as_kimi_alias(monkeypatch):
    monkeypatch.delenv("KIMI_API_KEY", raising=False)
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-moonshot-key")
    settings = load_settings()
    assert settings.kimi_api_key == "test-moonshot-key"


def test_deepseek_provider_selection_and_fallback(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")
    monkeypatch.setenv("DEEPSEEK_MODEL", "test-deepseek")
    settings = load_settings()
    assert settings.provider_name == "deepseek"
    assert settings.deepseek_api_key == "test-deepseek-key"
    assert settings.deepseek_model == "test-deepseek"


def test_grok_can_be_configured_as_fallback(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", "gemini")
    monkeypatch.setenv("ORCHESTRA_PROVIDER_FALLBACKS", "grok")
    assert load_settings().provider_fallbacks == ("grok",)


def test_manus_requires_explicit_credit_opt_in(monkeypatch):
    monkeypatch.setenv("ORCHESTRA_PROVIDER", "manus")
    monkeypatch.setenv("MANUS_API_KEY", "test-manus-key")
    monkeypatch.setenv("MANUS_ALLOW_PAID_CALLS", "false")
    monkeypatch.setenv("MANUS_ALLOW_AGENT_TOOLS", "false")
    with pytest.raises(ValueError, match="MANUS_ALLOW_PAID_CALLS"):
        load_settings()

    monkeypatch.setenv("MANUS_ALLOW_PAID_CALLS", "true")
    with pytest.raises(ValueError, match="MANUS_ALLOW_AGENT_TOOLS"):
        load_settings()

    monkeypatch.setenv("MANUS_ALLOW_AGENT_TOOLS", "true")
    settings = load_settings()
    assert settings.provider_name == "manus"
    assert settings.manus_api_key == "test-manus-key"
    assert settings.manus_allow_paid_calls is True
    assert settings.manus_agent_profile == "lite"


@pytest.mark.parametrize("value", ["yes", "on", "enabled", ""])
def test_manus_paid_opt_in_rejects_ambiguous_boolean_values(monkeypatch, value):
    monkeypatch.setenv("MANUS_ALLOW_PAID_CALLS", value)
    with pytest.raises(ValueError, match="MANUS_ALLOW_PAID_CALLS"):
        load_settings()


def test_manus_profile_and_poll_limits_are_validated(monkeypatch):
    monkeypatch.setenv("MANUS_AGENT_PROFILE", "unknown")
    with pytest.raises(ValueError, match="MANUS_AGENT_PROFILE"):
        load_settings()
    monkeypatch.delenv("MANUS_AGENT_PROFILE")
    monkeypatch.setenv("MANUS_TIMEOUT_SECONDS", "901")
    with pytest.raises(ValueError, match="MANUS_TIMEOUT_SECONDS"):
        load_settings()
    monkeypatch.delenv("MANUS_TIMEOUT_SECONDS")
    monkeypatch.setenv("MANUS_POLL_INTERVAL_SECONDS", "31")
    with pytest.raises(ValueError, match="MANUS_POLL_INTERVAL_SECONDS"):
        load_settings()


@pytest.mark.parametrize("value", ["yes", "on", "enabled", ""])
def test_manus_agent_tools_acknowledgement_rejects_ambiguous_boolean_values(monkeypatch, value):
    monkeypatch.setenv("MANUS_ALLOW_AGENT_TOOLS", value)
    with pytest.raises(ValueError, match="MANUS_ALLOW_AGENT_TOOLS"):
        load_settings()

