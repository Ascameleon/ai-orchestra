import pytest

from orchestra.guardrails import AuditEvent, AuditTrail, BudgetExceeded, CostGuard


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
