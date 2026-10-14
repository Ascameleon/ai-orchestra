import pytest

from orchestra.guardrails import (
    AuditEvent,
    AuditTrail,
    BudgetExceeded,
    CostGuard,
    SQLiteAuditTrail,
    SQLiteCostGuard,
)


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


def test_sqlite_cost_guard_shares_atomic_budget_between_instances(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    database = str(tmp_path / "shared-budget.sqlite3")
    guards = [SQLiteCostGuard(10, database) for _ in range(4)]

    def reserve(index):
        try:
            return guards[index % len(guards)].reserve()
        except BudgetExceeded:
            return None

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(reserve, range(100)))

    accepted = [value for value in results if value is not None]
    assert len(accepted) == 10
    assert all(guard.used == 10 for guard in guards)
    assert all(guard.limit == 10 for guard in guards)
    for guard in guards:
        guard.close()


def test_sqlite_cost_guard_persists_reservations_after_reopen(tmp_path):
    database = str(tmp_path / "persistent-budget.sqlite3")
    first = SQLiteCostGuard(2, database)
    assert first.reserve() == 1
    first.close()

    second = SQLiteCostGuard(2, database)
    assert second.used == 1
    assert second.reserve() == 2
    with pytest.raises(BudgetExceeded):
        second.reserve()
    second.close()


def test_sqlite_cost_guard_rejects_invalid_configuration(tmp_path):
    with pytest.raises(ValueError, match="database_path"):
        SQLiteCostGuard(1, " ")
    with pytest.raises(ValueError, match="max_requests"):
        SQLiteCostGuard(0, str(tmp_path / "budget.sqlite3"))
    with pytest.raises(ValueError, match="window_seconds"):
        SQLiteCostGuard(1, str(tmp_path / "budget.sqlite3"), window_seconds=0)


def test_sqlite_cost_guard_expires_reservations_outside_rolling_window(monkeypatch, tmp_path):
    from orchestra import guardrails

    clock = [1000.0]
    monkeypatch.setattr(guardrails, "time", lambda: clock[0])
    guard = SQLiteCostGuard(1, str(tmp_path / "rolling-budget.sqlite3"), window_seconds=60)
    assert guard.reserve() == 1
    with pytest.raises(BudgetExceeded):
        guard.reserve()

    clock[0] += 61
    assert guard.used == 0
    assert guard.reserve() == 1
    guard.close()


@pytest.mark.parametrize("value", [1.5, True, "2"])
def test_guardrails_reject_non_integer_limits(value, tmp_path):
    database = str(tmp_path / "invalid-limit.sqlite3")
    with pytest.raises(ValueError, match="max_requests"):
        CostGuard(value)
    with pytest.raises(ValueError, match="max_requests"):
        SQLiteCostGuard(value, database)
    with pytest.raises(ValueError, match="window_seconds"):
        SQLiteCostGuard(1, database, window_seconds=value)
    with pytest.raises(ValueError, match="capacity"):
        AuditTrail(capacity=value)
    with pytest.raises(ValueError, match="capacity"):
        SQLiteAuditTrail(database, capacity=value)
