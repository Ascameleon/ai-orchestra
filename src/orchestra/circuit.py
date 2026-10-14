from collections.abc import Callable, Iterable
from dataclasses import dataclass
from math import ceil, isfinite
from threading import Lock
from time import monotonic, time


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
        if not isinstance(reset_timeout_seconds, (int, float)) or not isfinite(reset_timeout_seconds) or reset_timeout_seconds <= 0:
            raise ValueError('reset_timeout_seconds must be finite and positive')
        self.failure_threshold = failure_threshold
        self.reset_timeout_seconds = float(reset_timeout_seconds)
        self._clock = clock
        self._states: dict[str, _State] = {}
        self._lock = Lock()

    @staticmethod
    def _name(provider: str) -> str:
        name = provider.strip().lower()
        if not name:
            raise ValueError('provider name must not be empty')
        return name

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


class SQLiteProviderCircuitBreaker:
    """Persistent circuit breaker shared by workers using the same SQLite file.

    A database write lock makes half-open probe reservation exclusive across
    independent application processes on the same host. Use a networked shared
    coordination service instead when workers span multiple hosts.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        reset_timeout_seconds: float = 30.0,
        database_path: str = "",
        *,
        clock: Callable[[], float] = time,
    ) -> None:
        import sqlite3

        if type(failure_threshold) is not int or failure_threshold < 1:
            raise ValueError("failure_threshold must be a positive integer")
        if not isinstance(reset_timeout_seconds, (int, float)) or not isfinite(reset_timeout_seconds) or reset_timeout_seconds <= 0:
            raise ValueError("reset_timeout_seconds must be finite and positive")
        if not isinstance(database_path, str) or not database_path.strip():
            raise ValueError("database_path must be a non-empty path")
        self.failure_threshold = failure_threshold
        self.reset_timeout_seconds = float(reset_timeout_seconds)
        self._clock = clock
        self._lock = Lock()
        self._connection = sqlite3.connect(database_path, check_same_thread=False, timeout=10)
        with self._lock:
            self._connection.execute("PRAGMA busy_timeout = 10000")
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS provider_circuit_state (
                    provider TEXT PRIMARY KEY,
                    failures INTEGER NOT NULL DEFAULT 0 CHECK (failures >= 0),
                    opened_at REAL,
                    probe INTEGER NOT NULL DEFAULT 0 CHECK (probe IN (0, 1))
                )
                """
            )
            self._connection.commit()

    @staticmethod
    def _name(provider: str) -> str:
        name = provider.strip().lower()
        if not name:
            raise ValueError("provider name must not be empty")
        return name

    def allow_request(self, provider: str) -> bool:
        name = self._name(provider)
        now = self._clock()
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._connection.execute(
                    "SELECT failures, opened_at, probe FROM provider_circuit_state WHERE provider = ?",
                    (name,),
                ).fetchone()
                if row is None:
                    self._connection.execute(
                        "INSERT INTO provider_circuit_state(provider) VALUES (?)", (name,)
                    )
                    self._connection.commit()
                    return True
                _failures, opened_at, probe = row
                if opened_at is None:
                    self._connection.commit()
                    return True
                if now - opened_at < self.reset_timeout_seconds or probe:
                    self._connection.commit()
                    return False
                self._connection.execute(
                    "UPDATE provider_circuit_state SET probe = 1 WHERE provider = ?", (name,)
                )
                self._connection.commit()
                return True
            except Exception:
                if self._connection.in_transaction:
                    self._connection.rollback()
                raise

    def record_success(self, provider: str) -> None:
        name = self._name(provider)
        with self._lock:
            self._connection.execute(
                """INSERT INTO provider_circuit_state(provider, failures, opened_at, probe)
                   VALUES (?, 0, NULL, 0)
                   ON CONFLICT(provider) DO UPDATE SET failures = 0, opened_at = NULL, probe = 0""",
                (name,),
            )
            self._connection.commit()

    def record_failure(self, provider: str) -> None:
        name = self._name(provider)
        now = self._clock()
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._connection.execute(
                    "SELECT failures, opened_at, probe FROM provider_circuit_state WHERE provider = ?",
                    (name,),
                ).fetchone()
                failures, opened_at, probe = row if row is not None else (0, None, 0)
                if opened_at is not None or probe:
                    failures = max(failures, self.failure_threshold)
                    opened_at = now
                else:
                    failures += 1
                    if failures >= self.failure_threshold:
                        opened_at = now
                self._connection.execute(
                    """INSERT INTO provider_circuit_state(provider, failures, opened_at, probe)
                       VALUES (?, ?, ?, 0)
                       ON CONFLICT(provider) DO UPDATE SET
                         failures = excluded.failures,
                         opened_at = excluded.opened_at,
                         probe = 0""",
                    (name, failures, opened_at),
                )
                self._connection.commit()
            except Exception:
                if self._connection.in_transaction:
                    self._connection.rollback()
                raise

    def abandon_request(self, provider: str) -> None:
        name = self._name(provider)
        with self._lock:
            self._connection.execute(
                "UPDATE provider_circuit_state SET probe = 0 WHERE provider = ? AND probe = 1",
                (name,),
            )
            self._connection.commit()

    def snapshot(self, providers: Iterable[str] | None = None) -> tuple[CircuitStatus, ...]:
        with self._lock:
            if providers is None:
                rows = self._connection.execute(
                    "SELECT provider, failures, opened_at, probe FROM provider_circuit_state ORDER BY provider"
                ).fetchall()
                states = {name: (failures, opened_at, probe) for name, failures, opened_at, probe in rows}
                names = tuple(states)
            else:
                names = tuple(self._name(provider) for provider in providers)
                states = {}
                for name in names:
                    row = self._connection.execute(
                        "SELECT failures, opened_at, probe FROM provider_circuit_state WHERE provider = ?",
                        (name,),
                    ).fetchone()
                    states[name] = row if row is not None else (0, None, 0)
            now = self._clock()
            result = []
            for name in names:
                failures, opened_at, probe = states[name]
                remaining = 0.0 if opened_at is None else max(
                    0.0, self.reset_timeout_seconds - (now - opened_at)
                )
                state = "closed" if opened_at is None else ("open" if remaining > 0 else "half_open")
                result.append(CircuitStatus(name, state, failures, ceil(remaining)))
            return tuple(result)

    def close(self) -> None:
        with self._lock:
            self._connection.close()
