"""Deterministic conflict screening and conclusion traceability.

Conflict results are review flags based on caller-supplied topics and stances,
not semantic inference or proof that either source is correct.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceAssertion:
    assertion_id: str
    evidence_id: str
    topic: str
    stance: str


@dataclass(frozen=True)
class PotentialConflict:
    topic: str
    assertion_a: str
    evidence_a: str
    stance_a: str
    assertion_b: str
    evidence_b: str
    stance_b: str
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
    unknown_evidence_ids: tuple[str, ...]
    claims_without_evidence: tuple[str, ...]
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
    if not isinstance(assertions, (list, tuple)):
        raise TypeError("assertions must be a list or tuple")
    normalized_assertions: list[SourceAssertion] = []
    seen: set[str] = set()
    for item in assertions:
        if not isinstance(item, SourceAssertion):
            raise TypeError("assertions must contain SourceAssertion instances")
        if any(not isinstance(value, str) for value in (
            item.assertion_id, item.evidence_id, item.topic, item.stance
        )):
            raise TypeError("assertion fields must be strings")
        assertion_id = item.assertion_id.strip()
        evidence_id = item.evidence_id.strip()
        topic = " ".join(item.topic.split())
        if not assertion_id or not evidence_id or not topic:
            raise ValueError("assertion_id, evidence_id, and topic must not be empty")
        if assertion_id in seen:
            raise ValueError(f"duplicate assertion_id: {assertion_id}")
        seen.add(assertion_id)
        if item.stance not in ("supports", "opposes", "neutral"):
            raise ValueError(f"invalid stance for assertion {assertion_id}")
        normalized_assertions.append(
            SourceAssertion(assertion_id, evidence_id, topic, item.stance)
        )

    conflicts: list[PotentialConflict] = []
    for index, left in enumerate(normalized_assertions):
        if left.stance == "neutral":
            continue
        left_topic = " ".join(left.topic.casefold().split())
        for right in normalized_assertions[index + 1 :]:
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
    known_evidence_ids: list[str] | tuple[str, ...] | set[str] | None = None,
) -> TraceabilityReport:
    """Resolve conclusion -> claim -> evidence links without judging truth or entailment.

    Each conclusion tuple is (conclusion_id, text, claim_ids). Duplicate IDs and
    blank fields are rejected. Evidence IDs are deduplicated in first-seen order.
    """
    known_evidence: set[str] | None = None
    if known_evidence_ids is not None:
        if not isinstance(known_evidence_ids, (list, tuple, set, frozenset)):
            raise TypeError("known_evidence_ids must be a list, tuple, set, or frozenset")
        if any(not isinstance(item, str) for item in known_evidence_ids):
            raise TypeError("known_evidence_ids must contain only strings")
        normalized_evidence = [item.strip() for item in known_evidence_ids]
        if any(not item for item in normalized_evidence):
            raise ValueError("known_evidence_ids must not contain empty values")
        if len(set(normalized_evidence)) != len(normalized_evidence):
            raise ValueError("known_evidence_ids must be unique after whitespace normalization")
        known_evidence = set(normalized_evidence)

    if not isinstance(claims, (list, tuple)):
        raise TypeError("claims must be a list or tuple")
    claim_by_id: dict[str, ClaimTrace] = {}
    for claim in claims:
        if not isinstance(claim, ClaimTrace):
            raise TypeError("claims must contain ClaimTrace instances")
        if not isinstance(claim.claim_id, str):
            raise TypeError("claim_id must be a string")
        if not isinstance(claim.evidence_ids, (list, tuple)):
            raise TypeError(f"claim {claim.claim_id!r} evidence_ids must be a list or tuple")
        if any(not isinstance(item, str) for item in claim.evidence_ids):
            raise TypeError(f"claim {claim.claim_id!r} evidence_ids must contain only strings")
        claim_id = claim.claim_id.strip()
        evidence_ids = tuple(item.strip() for item in claim.evidence_ids)
        if not claim_id:
            raise ValueError("claim_id must not be empty")
        if claim_id in claim_by_id:
            raise ValueError(f"duplicate claim_id: {claim_id}")
        if any(not evidence_id for evidence_id in evidence_ids):
            raise ValueError(f"claim {claim_id} contains an empty evidence reference")
        claim_by_id[claim_id] = ClaimTrace(claim_id, evidence_ids)

    if not isinstance(conclusions, (list, tuple)):
        raise TypeError("conclusions must be a list or tuple")
    seen_conclusions: set[str] = set()
    results: list[ConclusionTrace] = []
    for item in conclusions:
        if not isinstance(item, (list, tuple)) or len(item) != 3:
            raise TypeError("each conclusion must be a 3-item tuple/list")
        raw_conclusion_id, text, raw_claim_ids = item
        if not isinstance(raw_conclusion_id, str) or not isinstance(text, str):
            raise TypeError("conclusion_id and text must be strings")
        if not isinstance(raw_claim_ids, (list, tuple)):
            raise TypeError("conclusion claim_ids must be a list or tuple")
        if any(not isinstance(claim_id, str) for claim_id in raw_claim_ids):
            raise TypeError("conclusion claim_ids must contain only strings")
        conclusion_id = raw_conclusion_id.strip()
        claim_ids = tuple(item.strip() for item in raw_claim_ids)
        if not conclusion_id or not text.strip():
            raise ValueError("conclusion_id and text must not be empty")
        if conclusion_id in seen_conclusions:
            raise ValueError(f"duplicate conclusion_id: {conclusion_id}")
        seen_conclusions.add(conclusion_id)
        if any(not claim_id for claim_id in claim_ids):
            raise ValueError(f"conclusion {conclusion_id} contains an empty claim reference")
        unique_claim_ids = tuple(dict.fromkeys(claim_ids))
        linked = tuple(claim_id for claim_id in unique_claim_ids if claim_id in claim_by_id)
        missing = tuple(claim_id for claim_id in unique_claim_ids if claim_id not in claim_by_id)
        evidence_ids = tuple(
            dict.fromkeys(
                evidence_id.strip()
                for claim_id in linked
                for evidence_id in claim_by_id[claim_id].evidence_ids
            )
        )
        unknown_evidence = (
            tuple(item for item in evidence_ids if item not in known_evidence)
            if known_evidence is not None
            else ()
        )
        claims_without_evidence = tuple(
            claim_id for claim_id in linked if not claim_by_id[claim_id].evidence_ids
        )
        if not unique_claim_ids or not linked:
            status = "untraceable"
        elif missing or unknown_evidence or claims_without_evidence:
            status = "partially_traceable"
        else:
            status = "fully_traceable"
        results.append(
            ConclusionTrace(
                conclusion_id=conclusion_id,
                linked_claim_ids=linked,
                missing_claim_ids=missing,
                evidence_ids=evidence_ids,
                unknown_evidence_ids=unknown_evidence,
                claims_without_evidence=claims_without_evidence,
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
