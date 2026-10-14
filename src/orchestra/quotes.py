"""Offline quoted-passage checks for caller-supplied source snapshots.

This module can confirm that a quotation occurs in supplied text. It cannot
confirm that the snapshot came from the claimed publisher or that the quote
semantically supports a claim.
"""
import hashlib
from dataclasses import dataclass


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


@dataclass(frozen=True)
class SourceSnapshot:
    evidence_id: str
    content: str


@dataclass(frozen=True)
class QuoteReference:
    claim_id: str
    evidence_id: str
    quote: str


@dataclass(frozen=True)
class QuoteCheck:
    claim_id: str
    evidence_id: str
    quote_sha256: str
    quote_found: bool
    source_sha256: str | None


@dataclass(frozen=True)
class QuoteAudit:
    total_quotes: int
    quotes_found: int
    quotes_missing: int
    unknown_evidence_references: int
    checks: tuple[QuoteCheck, ...]


def audit_quotes(
    snapshots: list[SourceSnapshot] | tuple[SourceSnapshot, ...],
    references: list[QuoteReference] | tuple[QuoteReference, ...],
) -> QuoteAudit:
    """Check normalized literal quote presence and hash supplied source snapshots."""
    if not isinstance(snapshots, (list, tuple)):
        raise TypeError("snapshots must be a list or tuple")
    if not isinstance(references, (list, tuple)):
        raise TypeError("references must be a list or tuple")
    by_id: dict[str, SourceSnapshot] = {}
    for snapshot in snapshots:
        if not isinstance(snapshot, SourceSnapshot):
            raise TypeError("snapshots must contain SourceSnapshot instances")
        if not isinstance(snapshot.evidence_id, str) or not isinstance(snapshot.content, str):
            raise TypeError("snapshot evidence_id and content must be strings")
        evidence_id = snapshot.evidence_id.strip()
        if not evidence_id or not snapshot.content.strip():
            raise ValueError("snapshot evidence_id and content must not be empty")
        if evidence_id in by_id:
            raise ValueError(f"duplicate snapshot evidence_id after whitespace normalization: {evidence_id}")
        by_id[evidence_id] = SourceSnapshot(evidence_id, snapshot.content)

    checks: list[QuoteCheck] = []
    for reference in references:
        if not isinstance(reference, QuoteReference):
            raise TypeError("references must contain QuoteReference instances")
        if any(not isinstance(value, str) for value in (
            reference.claim_id, reference.evidence_id, reference.quote
        )):
            raise TypeError("quote reference fields must be strings")
        claim_id = reference.claim_id.strip()
        evidence_id = reference.evidence_id.strip()
        if not claim_id or not evidence_id:
            raise ValueError("claim_id and evidence_id must not be empty")
        if not reference.quote.strip():
            raise ValueError("quote must not be empty")
        snapshot = by_id.get(evidence_id)
        quote = _normalize(reference.quote)
        source = _normalize(snapshot.content) if snapshot else ""
        found = bool(snapshot and quote in source)
        checks.append(
            QuoteCheck(
                claim_id=claim_id,
                evidence_id=evidence_id,
                quote_sha256=hashlib.sha256(reference.quote.encode("utf-8")).hexdigest(),
                quote_found=found,
                source_sha256=(
                    hashlib.sha256(snapshot.content.encode("utf-8")).hexdigest()
                    if snapshot
                    else None
                ),
            )
        )

    found_count = sum(check.quote_found for check in checks)
    unknown_count = sum(check.source_sha256 is None for check in checks)
    return QuoteAudit(
        total_quotes=len(checks),
        quotes_found=found_count,
        quotes_missing=len(checks) - found_count,
        unknown_evidence_references=unknown_count,
        checks=tuple(checks),
    )
