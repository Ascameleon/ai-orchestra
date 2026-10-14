from collections.abc import Callable, Iterable
from dataclasses import dataclass
from math import ceil, isfinite
from threading import Lock
from time import monotonic


@dataclass(frozen=True)
class CircuitStatus:
    provider: str
    state: str
    consecutive_failures: int
    retry_after_seconds: int

@dataclass
class _State:
    failures: int = 0
    opened_at: float | None = None
    probe: bool = False

class ProviderCircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout_seconds: float = 30.0, *, clock: Callable[[], float] = monotonic) -> None:
        if type(failure_threshold) is not int or failure_threshold < 1:
            raise ValueError('failure_threshold must be a positive integer')
        if isinstance(reset_timeout_seconds, bool) or not isinstance(reset_timeout_seconds, (int, float)) or not isfinite(reset_timeout_seconds) or reset_timeout_seconds <= 0:
            raise ValueError('reset_timeout_seconds must be finite and positive')
        self.failure_threshold = failure_threshold
        self.reset_timeout_seconds = float(reset_timeout_seconds)
        self._clock = clock
        self._states: dict[str, _State] = {}
        self._lock = Lock()

    @staticmethod
    def _name(provider: str) -> str:
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("provider name must not be empty")
        return provider.strip().lower()

    def allow_request(self, provider: str) -> bool:
        name = self._name(provider)
        with self._lock:
            state = self._states.get(name)
            if state is None or state.opened_at is None:
                return True
            if self._clock() - state.opened_at < self.reset_timeout_seconds or state.probe:
                return False
            state.probe = True
            return True

    def record_success(self, provider: str) -> None:
        name = self._name(provider)
        with self._lock:
            self._states[name] = _State()

    def record_failure(self, provider: str) -> None:
        name = self._name(provider)
        with self._lock:
            now = self._clock()
            state = self._states.setdefault(name, _State())
            if state.opened_at is not None or state.probe:
                state.failures = max(state.failures, self.failure_threshold)
                state.opened_at = now
                state.probe = False
            else:
                state.failures += 1
                if state.failures >= self.failure_threshold:
                    state.opened_at = now

    def abandon_request(self, provider: str) -> None:
        name = self._name(provider)
        with self._lock:
            state = self._states.get(name)
            if state is not None and state.probe:
                state.probe = False

    def snapshot(self, providers: Iterable[str] | None = None) -> tuple[CircuitStatus, ...]:
        names = tuple(providers) if providers is not None else tuple(sorted(self._states))
        result = []
        with self._lock:
            now = self._clock()
            for raw in names:
                name = self._name(raw)
                state = self._states.get(name, _State())
                remaining = 0 if state.opened_at is None else max(0.0, self.reset_timeout_seconds - (now - state.opened_at))
                state_name = 'closed' if state.opened_at is None else ('open' if remaining > 0 else 'half_open')
                result.append(CircuitStatus(name, state_name, state.failures, ceil(remaining)))
        return tuple(result)
