"""Strict parsing for explicitly model-assessed claim/evidence support.

This is a structured model judgment, not proof of entailment, source authenticity,
or factual truth. Unknown IDs and malformed results fail closed.
"""
import json
from dataclasses import dataclass

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


class _DuplicateJSONKey(ValueError):
    """Raised when JSON objects contain ambiguous duplicate keys."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey("duplicate JSON object key")
        result[key] = value
    return result


def _validate_id_set(value: object, name: str) -> set[str]:
    if not isinstance(value, (set, frozenset)):
        raise TypeError(f"{name} must be a set or frozenset of non-empty strings")
    if any(not isinstance(item, str) for item in value):
        raise TypeError(f"{name} must contain only strings")
    if any(not item.strip() for item in value):
        raise ValueError(f"{name} must not contain empty IDs")
    return {item.strip() for item in value}


def parse_support_assessment(
    response_text: str,
    expected_claim_ids: set[str] | frozenset[str],
    known_evidence_ids: set[str] | frozenset[str],
) -> SupportAssessmentReport:
    """Parse and validate the model's JSON without accepting invented IDs."""
    normalized_claim_ids = _validate_id_set(expected_claim_ids, "expected_claim_ids")
    normalized_evidence_ids = _validate_id_set(known_evidence_ids, "known_evidence_ids")
    if not isinstance(response_text, str):
        raise TypeError("model response must be a string")

    try:
        payload = json.loads(response_text, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, _DuplicateJSONKey):
        raise ValueError("model response was not valid, unambiguous JSON") from None
    if not isinstance(payload, dict) or set(payload) != {"assessments"}:
        raise ValueError("model response has an invalid top-level schema")
    raw_items = payload["assessments"]
    if not isinstance(raw_items, list) or len(raw_items) != len(normalized_claim_ids):
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
        if (
            not isinstance(claim_id, str)
            or not claim_id.strip()
            or claim_id.strip() not in normalized_claim_ids
            or claim_id.strip() in seen
        ):
            raise ValueError("model response contains an unknown or duplicate claim ID")
        claim_id = claim_id.strip()
        if not isinstance(status, str) or status not in _ALLOWED_STATUSES:
            raise ValueError("model response contains an unsupported status")
        if (
            not isinstance(evidence_ids, list)
            or any(
                not isinstance(value, str)
                or not value.strip()
                or value.strip() not in normalized_evidence_ids
                for value in evidence_ids
            )
            or len({value.strip() for value in evidence_ids if isinstance(value, str)})
            != len(evidence_ids)
        ):
            raise ValueError("model response contains unknown or duplicate evidence IDs")
        normalized_refs = tuple(value.strip() for value in evidence_ids)
        if status in {"supported", "contradicted"} and not normalized_refs:
            raise ValueError("non-insufficient assessments must cite at least one evidence ID")
        if not isinstance(rationale, str) or not rationale.strip() or len(rationale) > 300:
            raise ValueError("model response contains an invalid rationale")
        parsed.append(
            ClaimSupportAssessment(claim_id, status, normalized_refs, rationale.strip())
        )
        seen.add(claim_id)

    if seen != normalized_claim_ids:
        raise ValueError("model response omitted one or more claims")
    return SupportAssessmentReport(tuple(parsed))
