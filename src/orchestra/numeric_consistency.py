"""Deterministic screening for inconsistent structured numeric assertions.

This flags differing supplied values for the same normalized metric, unit, and
period. It does not extract facts from prose or decide which source is correct.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class NumericAssertion:
    assertion_id: str
    claim_id: str
    evidence_id: str
    metric: str
    value: str
    unit: str
    period: str


@dataclass(frozen=True)
class NumericDisagreement:
    metric: str
    unit: str
    period: str
    assertion_a: str
    claim_a: str
    evidence_a: str
    value_a: str
    assertion_b: str
    claim_b: str
    evidence_b: str
    value_b: str
    status: str = "potential_numeric_disagreement"


@dataclass(frozen=True)
class NumericConsistencyReport:
    assertions_checked: int
    potential_disagreement_count: int
    potential_disagreements: tuple[NumericDisagreement, ...]


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _parse_value(value: str, assertion_id: str) -> Decimal:
    try:
        parsed = Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        raise ValueError(f"assertion {assertion_id} has an invalid numeric value") from None
    if not parsed.is_finite():
        raise ValueError(f"assertion {assertion_id} must have a finite numeric value")
    return parsed


def screen_numeric_consistency(
    assertions: list[NumericAssertion] | tuple[NumericAssertion, ...],
) -> NumericConsistencyReport:
    """Flag unequal values sharing the same normalized metric, unit, and period."""
    seen: set[str] = set()
    parsed: list[tuple[NumericAssertion, str, str, str, Decimal]] = []
    for item in assertions:
        fields = (
            item.assertion_id,
            item.claim_id,
            item.evidence_id,
            item.metric,
            item.value,
            item.unit,
            item.period,
        )
        if any(not field.strip() for field in fields):
            raise ValueError("assertion fields must not be empty")
        if item.assertion_id in seen:
            raise ValueError(f"duplicate assertion_id: {item.assertion_id}")
        seen.add(item.assertion_id)
        parsed.append((
            item,
            _normalize(item.metric),
            _normalize(item.unit),
            _normalize(item.period),
            _parse_value(item.value, item.assertion_id),
        ))

    disagreements: list[NumericDisagreement] = []
    for index, left in enumerate(parsed):
        left_item, left_metric, left_unit, left_period, left_value = left
        for right in parsed[index + 1:]:
            right_item, right_metric, right_unit, right_period, right_value = right
            if (left_metric, left_unit, left_period) != (right_metric, right_unit, right_period):
                continue
            if left_value == right_value:
                continue
            disagreements.append(
                NumericDisagreement(
                    metric=left_metric,
                    unit=left_unit,
                    period=left_period,
                    assertion_a=left_item.assertion_id,
                    claim_a=left_item.claim_id,
                    evidence_a=left_item.evidence_id,
                    value_a=str(left_value),
                    assertion_b=right_item.assertion_id,
                    claim_b=right_item.claim_id,
                    evidence_b=right_item.evidence_id,
                    value_b=str(right_value),
                )
            )

    return NumericConsistencyReport(
        assertions_checked=len(parsed),
        potential_disagreement_count=len(disagreements),
        potential_disagreements=tuple(disagreements),
    )
