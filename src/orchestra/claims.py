"""Deterministic integrity checks for claim-to-evidence references.

This module validates links only. It does not determine whether a source entails,
contradicts, or otherwise substantiates the text of a claim.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    text: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class ClaimLinkAssessment:
    claim_id: str
    linked_evidence_ids: tuple[str, ...]
    unknown_evidence_ids: tuple[str, ...]
    has_valid_evidence_link: bool
    has_unknown_references: bool


@dataclass(frozen=True)
class ClaimVerification:
    total_claims: int
    linked_claims: int
    unlinked_claims: int
    claims_with_unknown_references: int
    results: tuple[ClaimLinkAssessment, ...]


def assess_claim_links(
    claims: list[ClaimRecord] | tuple[ClaimRecord, ...],
    evidence_ids: set[str] | frozenset[str],
) -> ClaimVerification:
    """Check that claim references point to known evidence IDs.

    Claim IDs must be unique. Duplicate references within one claim are collapsed
    while preserving order. Evidence metadata and claim semantics are not validated.
    """
    seen_claim_ids: set[str] = set()
    results: list[ClaimLinkAssessment] = []
    for claim in claims:
        if not claim.claim_id.strip() or not claim.text.strip():
            raise ValueError("claim_id and text must not be empty")
        if claim.claim_id in seen_claim_ids:
            raise ValueError(f"duplicate claim_id: {claim.claim_id}")
        seen_claim_ids.add(claim.claim_id)
        if any(not item.strip() for item in claim.evidence_ids):
            raise ValueError(f"claim {claim.claim_id} contains an empty evidence reference")
        references = tuple(dict.fromkeys(item.strip() for item in claim.evidence_ids))
        linked = tuple(item for item in references if item in evidence_ids)
        unknown = tuple(item for item in references if item not in evidence_ids)
        results.append(
            ClaimLinkAssessment(
                claim_id=claim.claim_id,
                linked_evidence_ids=linked,
                unknown_evidence_ids=unknown,
                has_valid_evidence_link=bool(linked),
                has_unknown_references=bool(unknown),
            )
        )

    linked_count = sum(result.has_valid_evidence_link for result in results)
    return ClaimVerification(
        total_claims=len(results),
        linked_claims=linked_count,
        unlinked_claims=len(results) - linked_count,
        claims_with_unknown_references=sum(result.has_unknown_references for result in results),
        results=tuple(results),
    )
