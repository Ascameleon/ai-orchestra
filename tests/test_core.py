import pytest

from orchestra.core import AllProvidersFailed, Orchestrator
from orchestra.providers.base import ProviderCallError, ProviderResult


class StubProvider:
    def generate(self, prompt: str) -> ProviderResult:
        return ProviderResult("stub", "test-model", f"answer:{prompt}", len(prompt), len(prompt) + 7)


def test_orchestrator_returns_result_and_metrics():
    result = Orchestrator(StubProvider()).run("hello")
    assert result.provider == "stub"
    assert result.model == "test-model"
    assert result.text == "answer:hello"
    assert result.input_chars == 5
    assert result.output_chars == len(result.text)
    assert result.duration_ms >= 0
    assert result.request_id


def test_each_task_gets_a_distinct_request_id():
    orchestrator = Orchestrator(StubProvider())
    assert orchestrator.run("a").request_id != orchestrator.run("b").request_id


class FailingProvider:
    def __init__(self, name="failing"):
        self.name = name
        self.calls = 0

    def generate(self, prompt: str) -> ProviderResult:
        self.calls += 1
        raise ProviderCallError(f"{self.name} unavailable")


class NamedProvider:
    def __init__(self, name, text):
        self.name = name
        self.text = text
        self.calls = 0

    def generate(self, prompt: str) -> ProviderResult:
        self.calls += 1
        return ProviderResult(self.name, "test-model", self.text, len(prompt), len(self.text))


def test_orchestrator_fails_over_to_next_provider():
    first = FailingProvider()
    second = NamedProvider("backup", "backup answer")
    result = Orchestrator([first, second]).run("hello")
    assert result.provider == "backup"
    assert result.text == "backup answer"
    assert result.attempts == 2
    assert first.calls == second.calls == 1


def test_orchestrator_does_not_call_later_providers_after_success():
    first = NamedProvider("primary", "primary answer")
    second = NamedProvider("backup", "backup answer")
    result = Orchestrator([first, second]).run("hello")
    assert result.provider == "primary"
    assert result.attempts == 1
    assert first.calls == 1
    assert second.calls == 0


def test_orchestrator_fails_closed_when_all_providers_fail():
    first = FailingProvider("one")
    second = FailingProvider("two")
    with pytest.raises(AllProvidersFailed, match="all configured providers failed"):
        Orchestrator([first, second]).run("hello")
    assert first.calls == second.calls == 1


def test_orchestrator_requires_at_least_one_provider():
    with pytest.raises(ValueError, match="at least one provider"):
        Orchestrator([])


def test_orchestrator_memory_records_success_and_failed_attempts_without_content():
    primary = FailingProvider()
    backup = NamedProvider("backup", "private answer")
    orchestrator = Orchestrator([primary, backup])
    orchestrator.run("private prompt")
    outcomes = {item.provider: item for item in orchestrator.memory.snapshot()}
    assert outcomes["failing"].failures == 1
    assert outcomes["backup"].successes == 1
    assert outcomes["backup"].failures == 0
    assert all(not hasattr(item, "prompt") and not hasattr(item, "text") for item in outcomes.values())


def test_explicit_provider_preference_moves_requested_provider_first():
    primary = NamedProvider("primary", "primary answer")
    backup = NamedProvider("backup", "backup answer")
    result = Orchestrator([primary, backup]).run("hello", preferred_provider=" BACKUP ")
    assert result.provider == "backup"
    assert result.text == "backup answer"
    assert result.attempts == 1
    assert primary.calls == 0
    assert backup.calls == 1


def test_unknown_explicit_provider_is_rejected_without_calling_providers():
    primary = NamedProvider("primary", "answer")
    with pytest.raises(ValueError, match="provider is not configured"):
        Orchestrator(primary).run("hello", preferred_provider="missing")
    assert primary.calls == 0
