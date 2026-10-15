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


class SQLiteProviderMemory:
    """Persist aggregate provider outcomes in SQLite without storing task content.

    The database contains provider names, success/failure counts, and cumulative
    latency only. A single lock protects the shared connection across API threads.
    """

    def __init__(self, database_path: str) -> None:
        import sqlite3

        if not isinstance(database_path, str) or not database_path.strip():
            raise ValueError("database_path must be a non-empty path")
        self._lock = Lock()
        self._connection = sqlite3.connect(database_path, check_same_thread=False, timeout=5)
        with self._lock:
            self._connection.execute("PRAGMA busy_timeout = 5000")
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS provider_outcomes (
                    provider TEXT PRIMARY KEY,
                    successes INTEGER NOT NULL DEFAULT 0 CHECK (successes >= 0),
                    failures INTEGER NOT NULL DEFAULT 0 CHECK (failures >= 0),
                    total_duration_ms INTEGER NOT NULL DEFAULT 0 CHECK (total_duration_ms >= 0)
                )
                """
            )
            self._connection.commit()

    def record(self, provider: str, *, succeeded: bool, duration_ms: int) -> None:
        name = provider.strip().lower() or "unknown"
        success_delta = 1 if succeeded else 0
        failure_delta = 0 if succeeded else 1
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO provider_outcomes
                    (provider, successes, failures, total_duration_ms)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(provider) DO UPDATE SET
                    successes = successes + excluded.successes,
                    failures = failures + excluded.failures,
                    total_duration_ms = total_duration_ms + excluded.total_duration_ms
                """,
                (name, success_delta, failure_delta, max(0, duration_ms)),
            )
            self._connection.commit()

    def snapshot(self) -> tuple[ProviderOutcome, ...]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT provider, successes, failures, total_duration_ms
                FROM provider_outcomes
                ORDER BY provider
                """
            ).fetchall()
        return tuple(ProviderOutcome(*row) for row in rows)

    def close(self) -> None:
        """Close the database connection; callers should stop using this instance afterward."""
        with self._lock:
            self._connection.close()
