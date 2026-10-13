"""In-process request budget and metadata-only audit trail.

These safeguards are process-local, not a substitute for provider billing quotas
or a shared production rate limiter.
"""
from collections import deque
from dataclasses import dataclass
from threading import Lock
from time import time


class BudgetExceeded(RuntimeError):
    """Raised when the configured per-process request budget is exhausted."""


@dataclass(frozen=True)
class AuditEvent:
    timestamp: float
    request_id: str
    provider: str
    model: str
    input_chars: int
    output_chars: int
    duration_ms: int
    outcome: str


class CostGuard:
    """Bound the number of provider calls made by this process."""

    def __init__(self, max_requests: int):
        if max_requests < 1:
            raise ValueError("max_requests must be greater than zero")
        self._limit = max_requests
        self._used = 0
        self._lock = Lock()

    def reserve(self) -> int:
        with self._lock:
            if self._used >= self._limit:
                raise BudgetExceeded("Per-process request budget exhausted")
            self._used += 1
            return self._used

    @property
    def used(self) -> int:
        with self._lock:
            return self._used

    @property
    def limit(self) -> int:
        return self._limit


class AuditTrail:
    """Keep bounded metadata; never store prompts, completions, or API keys."""

    def __init__(self, capacity: int = 1000):
        if capacity < 1:
            raise ValueError("capacity must be greater than zero")
        self._events: deque[AuditEvent] = deque(maxlen=capacity)
        self._lock = Lock()

    def record(self, event: AuditEvent) -> None:
        with self._lock:
            self._events.append(event)

    def snapshot(self) -> tuple[AuditEvent, ...]:
        with self._lock:
            return tuple(self._events)

    @staticmethod
    def now() -> float:
        return time()
