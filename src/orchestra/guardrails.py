"""Provider-call budgets and metadata-only audit trail.

The in-memory budget is process-local. The optional SQLite daily budget persists across
restarts on one host; neither replaces provider billing quotas or multi-host rate limiting.
"""
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
from time import time


class BudgetExceeded(RuntimeError):
    """Raised when the configured provider-call budget is exhausted."""


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
            raise ValueError("max_requests must be a positive integer")
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


class SQLiteDailyCostGuard:
    """Persist an atomic UTC-day provider-call budget across restarts on one host.

    Multiple processes using the same local SQLite file share the same daily limit.
    Do not place the database on a network filesystem or treat it as a multi-host quota.
    """

    def __init__(
        self,
        database_path: str,
        max_requests: int,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        import sqlite3

        if not isinstance(database_path, str) or not database_path.strip():
            raise ValueError("database_path must be a non-empty path")
        if type(max_requests) is not int or max_requests < 1:
            raise ValueError("max_requests must be a positive integer")
        self._limit = max_requests
        self._clock = clock or (lambda: datetime.now(UTC))
        self._lock = Lock()
        self._connection = sqlite3.connect(
            database_path,
            check_same_thread=False,
            timeout=5,
            isolation_level=None,
        )
        with self._lock:
            self._connection.execute("PRAGMA busy_timeout = 5000")
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_provider_budget (
                    budget_day TEXT PRIMARY KEY,
                    used INTEGER NOT NULL CHECK (used >= 0)
                )
                """
            )

    def _today(self) -> str:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("budget clock must return a timezone-aware datetime")
        return now.astimezone(UTC).date().isoformat()

    def check_ready(self) -> None:
        """Raise if the persistent SQLite budget database cannot be queried."""
        with self._lock:
            self._connection.execute("SELECT 1").fetchone()

    def reserve(self) -> int:
        """Atomically reserve one provider attempt or raise when today's limit is reached."""
        with self._lock:
            day = self._today()
            cutoff = (datetime.fromisoformat(day).date() - timedelta(days=30)).isoformat()
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                row = self._connection.execute(
                    "SELECT used FROM daily_provider_budget WHERE budget_day = ?",
                    (day,),
                ).fetchone()
                used = int(row[0]) if row else 0
                if used >= self._limit:
                    raise BudgetExceeded("Daily provider-call budget exhausted")
                next_used = used + 1
                self._connection.execute(
                    """
                    INSERT INTO daily_provider_budget (budget_day, used)
                    VALUES (?, ?)
                    ON CONFLICT(budget_day) DO UPDATE SET used = excluded.used
                    """,
                    (day, next_used),
                )
                self._connection.execute(
                    "DELETE FROM daily_provider_budget WHERE budget_day < ?",
                    (cutoff,),
                )
                self._connection.commit()
                return next_used
            except Exception:
                if self._connection.in_transaction:
                    self._connection.rollback()
                raise

    @property
    def used(self) -> int:
        with self._lock:
            row = self._connection.execute(
                "SELECT used FROM daily_provider_budget WHERE budget_day = ?",
                (self._today(),),
            ).fetchone()
            return int(row[0]) if row else 0

    @property
    def limit(self) -> int:
        return self._limit

    def close(self) -> None:
        """Close the SQLite connection on application shutdown."""
        with self._lock:
            self._connection.close()


class RedisDailyCostGuard:
    """Enforce an atomic UTC-day budget using a shared Redis instance.

    This supports multiple application hosts that share the same Redis endpoint.
    Redis availability is required for readiness and reservations; failures are fail-closed.
    """

    _RESERVE_SCRIPT = """
    local used = tonumber(redis.call('GET', KEYS[1]) or '0')
    local limit = tonumber(ARGV[1])
    if used >= limit then
        return -1
    end
    local next_used = redis.call('INCR', KEYS[1])
    if next_used == 1 then
        redis.call('EXPIRE', KEYS[1], tonumber(ARGV[2]))
    end
    return next_used
    """

    def __init__(
        self,
        redis_url: str,
        max_requests: int,
        *,
        key_prefix: str = "ai-orchestra:provider-budget",
        clock: Callable[[], datetime] | None = None,
        client: object | None = None,
    ) -> None:
        if not isinstance(redis_url, str) or not redis_url.strip():
            raise ValueError("redis_url must be a non-empty URL")
        if type(max_requests) is not int or max_requests < 1:
            raise ValueError("max_requests must be a positive integer")
        if not isinstance(key_prefix, str) or not key_prefix.strip():
            raise ValueError("key_prefix must not be empty")
        if client is None:
            from redis import Redis

            client = Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
                health_check_interval=30,
            )
        self._client = client
        self._limit = max_requests
        self._key_prefix = key_prefix.strip().rstrip(":")
        self._clock = clock or (lambda: datetime.now(UTC))

    def _today(self) -> str:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("budget clock must return a timezone-aware datetime")
        return now.astimezone(UTC).date().isoformat()

    def _key(self) -> str:
        return f"{self._key_prefix}:{self._today()}"

    def check_ready(self) -> None:
        """Raise if the shared quota backend is unreachable."""
        if not self._client.ping():
            raise RuntimeError("Redis budget backend did not respond to ping")

    def reserve(self) -> int:
        """Atomically reserve one provider attempt or raise when today's limit is reached."""
        key = self._key()
        result = self._client.eval(
            self._RESERVE_SCRIPT,
            1,
            key,
            self._limit,
            35 * 24 * 60 * 60,
        )
        if result == -1:
            raise BudgetExceeded("Daily provider-call budget exhausted")
        if type(result) is not int or result < 1:
            raise RuntimeError("Redis returned an invalid budget reservation result")
        return result

    @property
    def used(self) -> int:
        value = self._client.get(self._key())
        return int(value) if value is not None else 0

    @property
    def limit(self) -> int:
        return self._limit

    def close(self) -> None:
        """Close the Redis client connection pool."""
        self._client.close()


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


class SQLiteAuditTrail:
    """Persist a bounded audit trail containing operational metadata only."""

    def __init__(self, database_path: str, capacity: int = 1000) -> None:
        import sqlite3

        if not isinstance(database_path, str) or not database_path.strip():
            raise ValueError("database_path must be a non-empty path")
        if capacity < 1:
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
