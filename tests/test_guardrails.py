import pytest

from orchestra.guardrails import AuditEvent, AuditTrail, BudgetExceeded, CostGuard, SQLiteAuditTrail


def test_cost_guard_stops_at_configured_limit():
    guard = CostGuard(2)
    assert guard.reserve() == 1
    assert guard.reserve() == 2
    with pytest.raises(BudgetExceeded):
        guard.reserve()
    assert guard.used == 2
    assert guard.limit == 2


def test_audit_trail_is_bounded_and_keeps_metadata_only():
    trail = AuditTrail(capacity=2)
    for index in range(3):
        trail.record(
            AuditEvent(
                timestamp=float(index),
                request_id=f"request-{index}",
                provider="stub",
                model="test-model",
                input_chars=10,
                output_chars=20,
                duration_ms=1,
                outcome="success",
            )
        )
    events = trail.snapshot()
    assert len(events) == 2
    assert [event.request_id for event in events] == ["request-1", "request-2"]


def test_invalid_limits_are_rejected():
    with pytest.raises(ValueError):
        CostGuard(0)
    with pytest.raises(ValueError):
        CostGuard(True)
    with pytest.raises(ValueError):
        CostGuard("2")
    with pytest.raises(ValueError):
        AuditTrail(0)


def test_cost_guard_is_thread_safe_under_concurrent_reservations():
    from concurrent.futures import ThreadPoolExecutor

    guard = CostGuard(10)

    def reserve():
        try:
            return guard.reserve()
        except BudgetExceeded:
            return None

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(lambda _: reserve(), range(100)))

    accepted = [value for value in results if value is not None]
    assert sorted(accepted) == list(range(1, 11))
    assert guard.used == 10


def test_sqlite_audit_trail_persists_only_bounded_metadata(tmp_path):
    import sqlite3

    database = tmp_path / "audit.sqlite3"
    trail = SQLiteAuditTrail(str(database), capacity=2)
    trail.record(AuditEvent(1.0, "r1", "gemini", "model-a", 10, 20, 30, "success"))
    trail.record(AuditEvent(2.0, "r2", "openai", "model-b", 11, 21, 31, "failure"))
    trail.record(AuditEvent(3.0, "r3", "anthropic", "model-c", 12, 22, 32, "success"))
    assert [event.request_id for event in trail.snapshot()] == ["r2", "r3"]
    trail.close()

    reopened = SQLiteAuditTrail(str(database), capacity=2)
    assert [event.request_id for event in reopened.snapshot()] == ["r2", "r3"]
    reopened.close()
    with sqlite3.connect(database) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(audit_events)")}
    assert columns == {
        "id", "timestamp", "request_id", "provider", "model", "input_chars",
        "output_chars", "duration_ms", "outcome",
    }
    assert not {"prompt", "completion", "text", "api_key", "credentials"} & columns


def test_sqlite_audit_trail_rejects_empty_path_and_invalid_capacity(tmp_path):
    with pytest.raises(ValueError, match="database_path"):
        SQLiteAuditTrail(" ")
    with pytest.raises(ValueError, match="capacity"):
        SQLiteAuditTrail(str(tmp_path / "audit.sqlite3"), capacity=0)


def test_sqlite_daily_budget_persists_across_instances_and_enforces_limit(tmp_path):
    from orchestra.guardrails import SQLiteDailyCostGuard

    database = str(tmp_path / "daily-budget.sqlite3")
    first = SQLiteDailyCostGuard(database, 2)
    second = SQLiteDailyCostGuard(database, 2)

    assert first.reserve() == 1
    assert second.reserve() == 2
    with pytest.raises(BudgetExceeded, match="Daily"):
        first.reserve()
    assert first.used == 2
    assert second.used == 2

    first.close()
    second.close()
    reopened = SQLiteDailyCostGuard(database, 2)
    assert reopened.used == 2
    with pytest.raises(BudgetExceeded):
        reopened.reserve()
    reopened.close()


def test_sqlite_daily_budget_readiness_queries_database(tmp_path):
    from orchestra.guardrails import SQLiteDailyCostGuard

    guard = SQLiteDailyCostGuard(str(tmp_path / "daily-budget.sqlite3"), 3)
    guard.check_ready()
    guard.close()


def test_sqlite_daily_budget_resets_at_utc_day_boundary(tmp_path):
    from datetime import UTC, datetime, timedelta

    from orchestra.guardrails import SQLiteDailyCostGuard

    current = [datetime(2026, 10, 15, 23, 59, tzinfo=UTC)]
    guard = SQLiteDailyCostGuard(
        str(tmp_path / "daily-budget.sqlite3"),
        1,
        clock=lambda: current[0],
    )
    assert guard.reserve() == 1
    with pytest.raises(BudgetExceeded):
        guard.reserve()

    current[0] += timedelta(minutes=2)
    assert guard.used == 0
    assert guard.reserve() == 1
    guard.close()


def test_sqlite_daily_budget_reservations_are_atomic_across_connections(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    from orchestra.guardrails import SQLiteDailyCostGuard

    database = str(tmp_path / "daily-budget.sqlite3")
    guards = [SQLiteDailyCostGuard(database, 5) for _ in range(12)]

    def reserve(guard):
        try:
            return guard.reserve()
        except BudgetExceeded:
            return None

    with ThreadPoolExecutor(max_workers=len(guards)) as pool:
        results = list(pool.map(reserve, guards))

    accepted = [value for value in results if value is not None]
    assert sorted(accepted) == [1, 2, 3, 4, 5]
    assert all(guard.used == 5 for guard in guards)
    for guard in guards:
        guard.close()


def test_sqlite_daily_budget_rejects_invalid_configuration(tmp_path):
    from orchestra.guardrails import SQLiteDailyCostGuard

    with pytest.raises(ValueError, match="database_path"):
        SQLiteDailyCostGuard(" ", 1)
    with pytest.raises(ValueError, match="max_requests"):
        SQLiteDailyCostGuard(str(tmp_path / "budget.sqlite3"), 0)
    from datetime import datetime

    guard = SQLiteDailyCostGuard(
        str(tmp_path / "budget.sqlite3"),
        1,
        clock=lambda: datetime(2026, 10, 15),
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        guard.reserve()
    guard.close()

def test_redis_daily_budget_is_atomic_persistent_and_day_scoped():
    from datetime import UTC, datetime, timedelta

    from orchestra.guardrails import RedisDailyCostGuard

    class FakeRedis:
        def __init__(self, shared):
            self.shared = shared
            self.ttls = {}
            self.closed = False
            self.available = True

        def ping(self):
            return self.available

        def eval(self, script, numkeys, key, limit, ttl):
            assert numkeys == 1
            assert "redis.call('INCR'" in script
            used = int(self.shared.get(key, 0))
            if used >= int(limit):
                return -1
            next_used = used + 1
            self.shared[key] = str(next_used)
            if next_used == 1:
                self.ttls[key] = int(ttl)
            return next_used

        def get(self, key):
            return self.shared.get(key)

        def close(self):
            self.closed = True

    shared = {}
    current = [datetime(2026, 10, 15, 23, 59, tzinfo=UTC)]
    first_client = FakeRedis(shared)
    second_client = FakeRedis(shared)
    first = RedisDailyCostGuard(
        "redis://test",
        2,
        clock=lambda: current[0],
        client=first_client,
    )
    second = RedisDailyCostGuard(
        "redis://test",
        2,
        clock=lambda: current[0],
        client=second_client,
    )

    first.check_ready()
    assert first.reserve() == 1
    assert second.reserve() == 2
    with pytest.raises(BudgetExceeded, match="Daily"):
        first.reserve()
    assert second.used == 2
    assert first_client.ttls["ai-orchestra:provider-budget:2026-10-15"] == 35 * 24 * 60 * 60

    current[0] += timedelta(minutes=2)
    assert first.used == 0
    assert first.reserve() == 1
    first.close()
    second.close()
    assert first_client.closed and second_client.closed


def test_redis_daily_budget_fails_readiness_when_backend_is_unavailable():
    from orchestra.guardrails import RedisDailyCostGuard

    class OfflineRedis:
        def ping(self):
            raise ConnectionError("private connection detail")

        def close(self):
            pass

    guard = RedisDailyCostGuard("redis://test", 1, client=OfflineRedis())
    with pytest.raises(ConnectionError):
        guard.check_ready()
    guard.close()


def test_redis_daily_budget_rejects_invalid_configuration():
    from orchestra.guardrails import RedisDailyCostGuard

    with pytest.raises(ValueError, match="redis_url"):
        RedisDailyCostGuard(" ", 1, client=object())
    with pytest.raises(ValueError, match="max_requests"):
        RedisDailyCostGuard("redis://test", 0, client=object())
    with pytest.raises(ValueError, match="key_prefix"):
        RedisDailyCostGuard("redis://test", 1, key_prefix=" ", client=object())
