import pytest

from orchestra.circuit import ProviderCircuitBreaker
from orchestra.core import Orchestrator
from orchestra.providers.base import ProviderCallError, ProviderResult


def test_circuit_opens_after_consecutive_failures_and_closes_after_probe():
    now = [100.0]
    breaker = ProviderCircuitBreaker(2, 10, clock=lambda: now[0])
    assert breaker.allow_request(' Primary ')
    breaker.record_failure('primary')
    assert breaker.allow_request('primary')
    breaker.record_failure('primary')
    status = breaker.snapshot(['PRIMARY'])[0]
    assert status.state == 'open'
    assert status.consecutive_failures == 2
    assert status.retry_after_seconds == 10
    assert not breaker.allow_request('primary')
    now[0] += 10
    assert breaker.allow_request('primary')
    assert not breaker.allow_request('primary')
    assert breaker.snapshot(['primary'])[0].state == 'half_open'
    breaker.record_success('primary')
    status = breaker.snapshot(['primary'])[0]
    assert status.state == 'closed'
    assert status.consecutive_failures == 0
    assert status.retry_after_seconds == 0


def test_failed_half_open_probe_restarts_cooldown():
    now = [0.0]
    breaker = ProviderCircuitBreaker(1, 5, clock=lambda: now[0])
    assert breaker.allow_request('provider')
    breaker.record_failure('provider')
    now[0] = 5
    assert breaker.allow_request('provider')
    breaker.record_failure('provider')
    status = breaker.snapshot(['provider'])[0]
    assert status.state == 'open'
    assert status.retry_after_seconds == 5


def test_only_one_half_open_probe_is_allowed_concurrently():
    from concurrent.futures import ThreadPoolExecutor

    now = [0.0]
    breaker = ProviderCircuitBreaker(1, 1, clock=lambda: now[0])
    assert breaker.allow_request('provider')
    breaker.record_failure('provider')
    now[0] = 1
    with ThreadPoolExecutor(max_workers=12) as pool:
        allowed = list(pool.map(breaker.allow_request, ['provider'] * 24))
    assert sum(allowed) == 1


def test_abandoning_probe_releases_it_without_closing_circuit():
    now = [0.0]
    breaker = ProviderCircuitBreaker(1, 1, clock=lambda: now[0])
    assert breaker.allow_request('provider')
    breaker.record_failure('provider')
    now[0] = 1
    assert breaker.allow_request('provider')
    breaker.abandon_request('provider')
    assert breaker.allow_request('provider')


@pytest.mark.parametrize('threshold,timeout', [(0, 1), (-1, 1), (1, 0), (1, float('nan'))])
def test_circuit_rejects_invalid_limits(threshold, timeout):
    with pytest.raises(ValueError):
        ProviderCircuitBreaker(threshold, timeout)


def test_open_provider_is_skipped_and_fallback_attempt_count_is_actual():
    class FailingProvider:
        name = 'primary'
        def __init__(self):
            self.calls = 0
        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            raise ProviderCallError('unavailable')

    class HealthyProvider:
        name = 'backup'
        def __init__(self):
            self.calls = 0
        def generate(self, prompt: str) -> ProviderResult:
            self.calls += 1
            text = 'backup answer'
            return ProviderResult(self.name, 'test-model', text, len(prompt), len(text))

    primary = FailingProvider()
    backup = HealthyProvider()
    orchestrator = Orchestrator([primary, backup], circuit_failure_threshold=2, circuit_reset_timeout_seconds=30)
    first = orchestrator.run('task one')
    second = orchestrator.run('task two')
    third = orchestrator.run('task three')
    assert first.attempts == second.attempts == 2
    assert third.attempts == 1
    assert primary.calls == 2
    assert backup.calls == 3
    assert orchestrator.circuit_breaker.snapshot(['primary'])[0].state == 'open'


def test_open_circuit_does_not_consume_budget_for_skipped_provider():
    class FailingProvider:
        name = 'primary'
        def generate(self, prompt: str):
            raise ProviderCallError('unavailable')
    class HealthyProvider:
        name = 'backup'
        def generate(self, prompt: str) -> ProviderResult:
            text = 'ok'
            return ProviderResult(self.name, 'test-model', text, len(prompt), len(text))
    orchestrator = Orchestrator([FailingProvider(), HealthyProvider()], circuit_failure_threshold=1)
    calls = []
    orchestrator.run('one', before_attempt=lambda: calls.append('call'))
    calls.clear()
    result = orchestrator.run('two', before_attempt=lambda: calls.append('call'))
    assert result.attempts == 1
    assert calls == ['call']


def test_circuit_settings_are_validated(monkeypatch):
    from orchestra.config import load_settings
    monkeypatch.delenv('ORCHESTRA_CIRCUIT_FAILURE_THRESHOLD', raising=False)
    monkeypatch.delenv('ORCHESTRA_CIRCUIT_RESET_SECONDS', raising=False)
    settings = load_settings()
    assert settings.circuit_failure_threshold == 3
    assert settings.circuit_reset_seconds == 30
    monkeypatch.setenv('ORCHESTRA_CIRCUIT_FAILURE_THRESHOLD', '0')
    with pytest.raises(ValueError, match='ORCHESTRA_CIRCUIT_FAILURE_THRESHOLD'):
        load_settings()
    monkeypatch.setenv('ORCHESTRA_CIRCUIT_FAILURE_THRESHOLD', '21')
    with pytest.raises(ValueError, match='ORCHESTRA_CIRCUIT_FAILURE_THRESHOLD'):
        load_settings()
    monkeypatch.setenv('ORCHESTRA_CIRCUIT_FAILURE_THRESHOLD', '3')
    monkeypatch.setenv('ORCHESTRA_CIRCUIT_RESET_SECONDS', '3601')
    with pytest.raises(ValueError, match='ORCHESTRA_CIRCUIT_RESET_SECONDS'):
        load_settings()
