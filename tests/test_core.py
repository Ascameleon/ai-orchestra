import pytest

from orchestra.core import AllProvidersFailed, Orchestrator
from orchestra.providers.base import ProviderCallError, ProviderResult


class StubProvider:
    name = "stub"

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


def test_configured_task_route_selects_provider_and_explicit_choice_overrides_it():
    primary = NamedProvider("primary", "primary answer")
    backup = NamedProvider("backup", "backup answer")
    orchestrator = Orchestrator([primary, backup], routes=(("code", "backup"),))
    routed = orchestrator.run("write code", task_type="code")
    assert routed.provider == "backup"
    explicit = orchestrator.run("general task", preferred_provider="primary", task_type="code")
    assert explicit.provider == "primary"


class MalformedProvider:
    def __init__(self, result, name="malformed"):
        self.name = name
        self.result = result
        self.calls = 0

    def generate(self, prompt: str):
        self.calls += 1
        return self.result


def test_malformed_provider_result_fails_over_and_is_recorded_as_failure():
    primary = MalformedProvider(ProviderResult("malformed", "test-model", "   ", 5, 3))
    backup = NamedProvider("backup", "valid answer")
    orchestrator = Orchestrator([primary, backup])

    result = orchestrator.run("hello")

    assert result.provider == "backup"
    assert result.text == "valid answer"
    assert result.attempts == 2
    outcomes = {item.provider: item for item in orchestrator.memory.snapshot()}
    assert outcomes["malformed"].failures == 1
    assert outcomes["malformed"].successes == 0
    assert outcomes["backup"].successes == 1


@pytest.mark.parametrize(
    "invalid_result",
    [
        None,
        ProviderResult("", "test-model", "answer", 5, 6),
        ProviderResult("provider", " ", "answer", 5, 6),
        ProviderResult("provider", "test-model", "answer", 4, 6),
        ProviderResult("provider", "test-model", "answer", 5, 99),
        ProviderResult("provider", "test-model", "   ", 5, 3),
    ],
)
def test_malformed_provider_results_never_count_as_success(invalid_result):
    provider = MalformedProvider(invalid_result)

    orchestrator = Orchestrator(provider)
    with pytest.raises(AllProvidersFailed, match="all configured providers failed"):
        orchestrator.run("hello")

    outcomes = orchestrator.memory.snapshot()
    assert len(outcomes) == 1
    assert outcomes[0].provider == "malformed"
    assert outcomes[0].failures == 1
    assert outcomes[0].successes == 0


class UnexpectedFailureProvider:
    name = "unexpected"

    def generate(self, prompt: str) -> ProviderResult:
        raise ValueError("internal provider detail")


def test_unexpected_provider_exception_triggers_failover_without_leaking_details():
    primary = UnexpectedFailureProvider()
    backup = NamedProvider("backup", "recovered answer")
    orchestrator = Orchestrator([primary, backup])

    result = orchestrator.run("hello")

    assert result.provider == "backup"
    assert result.text == "recovered answer"
    assert result.attempts == 2
    outcomes = {item.provider: item for item in orchestrator.memory.snapshot()}
    assert outcomes["unexpected"].failures == 1
    assert outcomes["backup"].successes == 1


def test_provider_result_cannot_claim_a_different_adapter_identity():
    primary = MalformedProvider(
        ProviderResult("backup", "test-model", "forged attribution", 5, 18),
        name="primary",
    )
    backup = NamedProvider("backup", "correctly attributed answer")

    orchestrator = Orchestrator([primary, backup])
    result = orchestrator.run("hello")

    assert result.provider == "backup"
    assert result.text == "correctly attributed answer"
    assert result.attempts == 2
    outcomes = {item.provider: item for item in orchestrator.memory.snapshot()}
    assert outcomes["primary"].failures == 1
    assert outcomes["primary"].successes == 0
    assert outcomes["backup"].successes == 1


class BrokenMemory:
    def record(self, provider: str, *, succeeded: bool, duration_ms: int) -> None:
        raise OSError("simulated persistent-memory write failure")

    def snapshot(self):
        return ()


def test_memory_write_failure_does_not_retry_successful_provider():
    primary = NamedProvider("primary", "primary answer")
    backup = NamedProvider("backup", "backup answer")

    result = Orchestrator([primary, backup], memory=BrokenMemory()).run("hello")

    assert result.provider == "primary"
    assert result.text == "primary answer"
    assert result.attempts == 1
    assert primary.calls == 1
    assert backup.calls == 0


def test_memory_write_failure_does_not_interrupt_provider_failover():
    primary = FailingProvider()
    backup = NamedProvider("backup", "backup answer")

    result = Orchestrator([primary, backup], memory=BrokenMemory()).run("hello")

    assert result.provider == "backup"
    assert result.text == "backup answer"
    assert result.attempts == 2
    assert primary.calls == backup.calls == 1
