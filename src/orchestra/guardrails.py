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
        if type(max_requests) is not int or max_requests < 1:
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


class SQLiteCostGuard:
    """Atomic shared provider-call budget backed by a SQLite database.

    Reservations are shared by all application workers that use the same database.
    Calls are counted in a rolling time window; a reservation is never refunded
    after a provider attempt begins, because that attempt may already be billable.
    """

    def __init__(self, max_requests: int, database_path: str, window_seconds: int = 86400):
        import sqlite3

        if type(max_requests) is not int or max_requests < 1:
            raise ValueError("max_requests must be greater than zero")
        if not isinstance(database_path, str) or not database_path.strip():
            raise ValueError("database_path must be a non-empty path")
        if type(window_seconds) is not int or window_seconds < 1:
            raise ValueError("window_seconds must be greater than zero")
        self._limit = max_requests
        self._window_seconds = window_seconds
        self._lock = Lock()
        self._connection = sqlite3.connect(database_path, check_same_thread=False, timeout=10)
        with self._lock:
            self._connection.execute("PRAGMA busy_timeout = 10000")
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS provider_call_reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reserved_at REAL NOT NULL
                )
                """
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_provider_call_reservations_time "
                "ON provider_call_reservations(reserved_at)"
            )
            self._connection.commit()

    def reserve(self) -> int:
        """Atomically reserve one call, or raise when the shared window is full."""
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                # Timestamp only after acquiring SQLite's cross-process write lock.
                # Otherwise lock contention can make a fresh reservation appear expired.
                now = time()
                cutoff = now - self._window_seconds
                self._connection.execute(
                    "DELETE FROM provider_call_reservations WHERE reserved_at <= ?", (cutoff,)
                )
                used = int(self._connection.execute(
                    "SELECT COUNT(*) FROM provider_call_reservations WHERE reserved_at > ?",
                    (cutoff,),
                ).fetchone()[0])
                if used >= self._limit:
                    self._connection.rollback()
                    raise BudgetExceeded("Shared provider-call budget exhausted")
                self._connection.execute(
                    "INSERT INTO provider_call_reservations(reserved_at) VALUES (?)", (now,)
                )
                self._connection.commit()
                return used + 1
            except Exception:
                if self._connection.in_transaction:
                    self._connection.rollback()
                raise

    @property
    def used(self) -> int:
        with self._lock:
            cutoff = time() - self._window_seconds
            row = self._connection.execute(
                "SELECT COUNT(*) FROM provider_call_reservations WHERE reserved_at > ?",
                (cutoff,),
            ).fetchone()
        return int(row[0])

    @property
    def limit(self) -> int:
        return self._limit

    def close(self) -> None:
        """Close this worker's connection after request handling has stopped."""
        with self._lock:
            self._connection.close()


class AuditTrail:
    """Keep bounded metadata; never store prompts, completions, or API keys."""

    def __init__(self, capacity: int = 1000):
        if type(capacity) is not int or capacity < 1:
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


class SQLiteAuditTrail:
    """Persist a bounded audit trail containing operational metadata only."""

    def __init__(self, database_path: str, capacity: int = 1000) -> None:
        import sqlite3

        if not isinstance(database_path, str) or not database_path.strip():
            raise ValueError("database_path must be a non-empty path")
        if type(capacity) is not int or capacity < 1:
            raise ValueError("capacity must be greater than zero")
        self._capacity = capacity
        self._lock = Lock()
        self._connection = sqlite3.connect(database_path, check_same_thread=False, timeout=5)
        with self._lock:
            self._connection.execute("PRAGMA busy_timeout = 5000")
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    request_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_chars INTEGER NOT NULL CHECK (input_chars >= 0),
                    output_chars INTEGER NOT NULL CHECK (output_chars >= 0),
                    duration_ms INTEGER NOT NULL CHECK (duration_ms >= 0),
                    outcome TEXT NOT NULL
                )
                """
            )
            self._connection.commit()

    def record(self, event: AuditEvent) -> None:
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO audit_events
                    (timestamp, request_id, provider, model, input_chars,
                     output_chars, duration_ms, outcome)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event.timestamp, event.request_id, event.provider, event.model,
                 max(0, event.input_chars), max(0, event.output_chars),
                 max(0, event.duration_ms), event.outcome),
            )
            self._connection.execute(
                """
                DELETE FROM audit_events
                WHERE id NOT IN (
                    SELECT id FROM audit_events ORDER BY id DESC LIMIT ?
                )
                """,
                (self._capacity,),
            )
            self._connection.commit()

    def snapshot(self) -> tuple[AuditEvent, ...]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT timestamp, request_id, provider, model, input_chars,
                       output_chars, duration_ms, outcome
                FROM audit_events ORDER BY id ASC
                """
            ).fetchall()
        return tuple(AuditEvent(*row) for row in rows)

    def close(self) -> None:
        """Close the database connection after the application stops using this trail."""
        with self._lock:
            self._connection.close()
