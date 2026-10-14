"""Strict parsing for explicitly model-assessed claim/evidence support.

This is a structured model judgment, not proof of entailment, source authenticity,
or factual truth. Unknown IDs and malformed results fail closed.
"""
from dataclasses import dataclass
import json


_ALLOWED_STATUSES = frozenset({"supported", "contradicted", "insufficient"})


@dataclass(frozen=True)
class ClaimSupportAssessment:
    claim_id: str
    status: str
    evidence_ids: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class SupportAssessmentReport:
    assessments: tuple[ClaimSupportAssessment, ...]


def parse_support_assessment(
    response_text: str,
    expected_claim_ids: set[str] | frozenset[str],
    known_evidence_ids: set[str] | frozenset[str],
) -> SupportAssessmentReport:
    """Parse and validate the model's JSON without accepting invented IDs."""
    try:
        payload = json.loads(response_text)
    except (TypeError, json.JSONDecodeError):
        raise ValueError("model response was not valid JSON") from None
    if not isinstance(payload, dict) or set(payload) != {"assessments"}:
        raise ValueError("model response has an invalid top-level schema")
    raw_items = payload["assessments"]
    if not isinstance(raw_items, list) or len(raw_items) != len(expected_claim_ids):
        raise ValueError("model response has an incomplete assessment list")

    parsed: list[ClaimSupportAssessment] = []
    seen: set[str] = set()
    for item in raw_items:
        if not isinstance(item, dict) or set(item) != {
            "claim_id", "status", "evidence_ids", "rationale"
        }:
            raise ValueError("model response contains an invalid assessment schema")
        claim_id = item["claim_id"]
        status = item["status"]
        evidence_ids = item["evidence_ids"]
        rationale = item["rationale"]
        if not isinstance(claim_id, str) or claim_id not in expected_claim_ids or claim_id in seen:
            raise ValueError("model response contains an unknown or duplicate claim ID")
        if not isinstance(status, str) or status not in _ALLOWED_STATUSES:
            raise ValueError("model response contains an unsupported status")
        if (
            not isinstance(evidence_ids, list)
            or any(
                not isinstance(value, str) or value not in known_evidence_ids
                for value in evidence_ids
            )
            or len(set(evidence_ids)) != len(evidence_ids)
        ):
            raise ValueError("model response contains unknown or duplicate evidence IDs")
        if not isinstance(rationale, str) or not rationale.strip() or len(rationale) > 1000:
            raise ValueError("model response contains an invalid rationale")
        parsed.append(
            ClaimSupportAssessment(claim_id, status, tuple(evidence_ids), rationale.strip())
        )
        seen.add(claim_id)

    if seen != set(expected_claim_ids):
        raise ValueError("model response omitted one or more claims")
    return SupportAssessmentReport(tuple(parsed))
