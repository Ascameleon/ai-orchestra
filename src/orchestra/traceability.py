"""Deterministic conflict screening and conclusion traceability.

Conflict results are review flags based on caller-supplied topics and stances,
not semantic inference or proof that either source is correct.
"""
from typing import Literal
from dataclasses import dataclass


Stance = Literal["supports", "opposes", "neutral"]


@dataclass(frozen=True)
class SourceAssertion:
    assertion_id: str
    evidence_id: str
    topic: str
    stance: Stance


@dataclass(frozen=True)
class PotentialConflict:
    topic: str
    assertion_a: str
    evidence_a: str
    stance_a: Stance
    assertion_b: str
    evidence_b: str
    stance_b: Stance
    status: str = "potential_conflict"


@dataclass(frozen=True)
class ConflictScreen:
    assertions_checked: int
    potential_conflicts: tuple[PotentialConflict, ...]


@dataclass(frozen=True)
class ClaimTrace:
    claim_id: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class ConclusionTrace:
    conclusion_id: str
    linked_claim_ids: tuple[str, ...]
    missing_claim_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    traceability_status: str


@dataclass(frozen=True)
class TraceabilityReport:
    conclusions_checked: int
    fully_traceable: int
    partially_traceable: int
    untraceable: int
    results: tuple[ConclusionTrace, ...]


def screen_potential_conflicts(
    assertions: list[SourceAssertion] | tuple[SourceAssertion, ...],
) -> ConflictScreen:
    """Flag same-topic assertions with opposite explicit caller-supplied stances."""
    seen: set[str] = set()
    for item in assertions:
        if not item.assertion_id.strip() or not item.evidence_id.strip() or not item.topic.strip():
            raise ValueError("assertion_id, evidence_id, and topic must not be empty")
        if item.assertion_id in seen:
            raise ValueError(f"duplicate assertion_id: {item.assertion_id}")
        seen.add(item.assertion_id)
        if item.stance not in ("supports", "opposes", "neutral"):
            raise ValueError(f"invalid stance for assertion {item.assertion_id}")

    conflicts: list[PotentialConflict] = []
    for index, left in enumerate(assertions):
        if left.stance == "neutral":
            continue
        left_topic = " ".join(left.topic.casefold().split())
        for right in assertions[index + 1 :]:
            if right.stance == "neutral" or left.stance == right.stance:
                continue
            if left_topic != " ".join(right.topic.casefold().split()):
                continue
            conflicts.append(
                PotentialConflict(
                    topic=left_topic,
                    assertion_a=left.assertion_id,
                    evidence_a=left.evidence_id,
                    stance_a=left.stance,
                    assertion_b=right.assertion_id,
                    evidence_b=right.evidence_id,
                    stance_b=right.stance,
                )
            )
    return ConflictScreen(len(assertions), tuple(conflicts))


def trace_conclusions(
    conclusions: list[tuple[str, str, tuple[str, ...]]] | tuple[tuple[str, str, tuple[str, ...]], ...],
    claims: list[ClaimTrace] | tuple[ClaimTrace, ...],
) -> TraceabilityReport:
    """Resolve conclusion -> claim -> evidence links without judging truth or entailment.

    Each conclusion tuple is (conclusion_id, text, claim_ids). Duplicate IDs and
    blank fields are rejected. Evidence IDs are deduplicated in first-seen order.
    """
    claim_by_id: dict[str, ClaimTrace] = {}
    for claim in claims:
        if not claim.claim_id.strip():
            raise ValueError("claim_id must not be empty")
        if claim.claim_id in claim_by_id:
            raise ValueError(f"duplicate claim_id: {claim.claim_id}")
        if any(not evidence_id.strip() for evidence_id in claim.evidence_ids):
            raise ValueError(f"claim {claim.claim_id} contains an empty evidence reference")
        claim_by_id[claim.claim_id] = claim

    seen_conclusions: set[str] = set()
    results: list[ConclusionTrace] = []
    for conclusion_id, text, claim_ids in conclusions:
        if not conclusion_id.strip() or not text.strip():
            raise ValueError("conclusion_id and text must not be empty")
        if conclusion_id in seen_conclusions:
            raise ValueError(f"duplicate conclusion_id: {conclusion_id}")
        seen_conclusions.add(conclusion_id)
        if any(not claim_id.strip() for claim_id in claim_ids):
            raise ValueError(f"conclusion {conclusion_id} contains an empty claim reference")
        unique_claim_ids = tuple(dict.fromkeys(claim_ids))
        linked = tuple(claim_id for claim_id in unique_claim_ids if claim_id in claim_by_id)
        missing = tuple(claim_id for claim_id in unique_claim_ids if claim_id not in claim_by_id)
        evidence_ids = tuple(
            dict.fromkeys(
                evidence_id
                for claim_id in linked
                for evidence_id in claim_by_id[claim_id].evidence_ids
            )
        )
        if not unique_claim_ids or not linked:
            status = "untraceable"
        elif missing:
            status = "partially_traceable"
        else:
            status = "fully_traceable"
        results.append(
            ConclusionTrace(
                conclusion_id=conclusion_id,
                linked_claim_ids=linked,
                missing_claim_ids=missing,
                evidence_ids=evidence_ids,
                traceability_status=status,
            )
        )

    return TraceabilityReport(
        conclusions_checked=len(results),
        fully_traceable=sum(item.traceability_status == "fully_traceable" for item in results),
        partially_traceable=sum(item.traceability_status == "partially_traceable" for item in results),
        untraceable=sum(item.traceability_status == "untraceable" for item in results),
        results=tuple(results),
    )
