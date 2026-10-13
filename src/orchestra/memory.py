"""Bounded, process-local provider outcome memory; never stores user content."""
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class ProviderOutcome:
    provider: str
    successes: int
    failures: int
    total_duration_ms: int


class ProviderMemory:
    """Remember aggregate outcomes only, for operational feedback within this process."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._outcomes: dict[str, list[int]] = {}

    def record(self, provider: str, *, succeeded: bool, duration_ms: int) -> None:
        name = provider.strip().lower() or "unknown"
        with self._lock:
            counters = self._outcomes.setdefault(name, [0, 0, 0])
            counters[0 if succeeded else 1] += 1
            counters[2] += max(0, duration_ms)

    def snapshot(self) -> tuple[ProviderOutcome, ...]:
        with self._lock:
            return tuple(
                ProviderOutcome(name, values[0], values[1], values[2])
                for name, values in sorted(self._outcomes.items())
            )
