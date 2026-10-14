from types import SimpleNamespace

from orchestra.providers.base import ProviderResult
from scripts import live_provider_smoke


class StubProvider:
    def __init__(self, name, *, fail=False):
        self.name = name
        self.fail = fail
        self.calls = 0

    def generate(self, prompt):
        self.calls += 1
        if self.fail:
            raise RuntimeError("private upstream error and secret")
        return ProviderResult(self.name, "test-model", "PRIVATE GENERATED OUTPUT", len(prompt), len("PRIVATE GENERATED OUTPUT"))


class StubRegistry:
    def __init__(self, providers):
        self.providers = providers

    def get(self, name):
        return self.providers[name]


def test_live_smoke_calls_each_provider_once_and_redacts_output(monkeypatch, capsys):
    providers = {
        "gemini": StubProvider("gemini"),
        "openai": StubProvider("openai"),
    }
    monkeypatch.setattr(
        live_provider_smoke,
        "load_settings",
        lambda: SimpleNamespace(provider_name="gemini", provider_fallbacks=("openai",)),
    )
    monkeypatch.setattr(
        live_provider_smoke, "build_provider_registry", lambda _settings: StubRegistry(providers)
    )

    assert live_provider_smoke.main() == 0

    output = capsys.readouterr().out
    assert '"status": "passed"' in output
    assert '"provider": "gemini"' in output
    assert '"provider": "openai"' in output
    assert "PRIVATE GENERATED OUTPUT" not in output
    assert providers["gemini"].calls == providers["openai"].calls == 1


def test_live_smoke_continues_after_failure_without_leaking_exception(monkeypatch, capsys):
    providers = {
        "gemini": StubProvider("gemini", fail=True),
        "openai": StubProvider("openai"),
    }
    monkeypatch.setattr(
        live_provider_smoke,
        "load_settings",
        lambda: SimpleNamespace(provider_name="gemini", provider_fallbacks=("openai",)),
    )
    monkeypatch.setattr(
        live_provider_smoke, "build_provider_registry", lambda _settings: StubRegistry(providers)
    )

    assert live_provider_smoke.main() == 1

    output = capsys.readouterr().out
    assert '"status": "failed"' in output
    assert '"error_type": "RuntimeError"' in output
    assert "private upstream error" not in output
    assert "secret" not in output
    assert providers["gemini"].calls == providers["openai"].calls == 1
