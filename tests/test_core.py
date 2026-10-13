import pytest

from orchestra.core import AllProvidersFailed, Orchestrator
from orchestra.providers.base import ProviderResult


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
        raise RuntimeError(f"{self.name} unavailable")


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
