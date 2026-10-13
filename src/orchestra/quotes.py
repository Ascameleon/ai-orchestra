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
    by_id: dict[str, SourceSnapshot] = {}
    for snapshot in snapshots:
        if not snapshot.evidence_id.strip() or not snapshot.content.strip():
            raise ValueError("snapshot evidence_id and content must not be empty")
        if snapshot.evidence_id in by_id:
            raise ValueError(f"duplicate snapshot evidence_id: {snapshot.evidence_id}")
        by_id[snapshot.evidence_id] = snapshot

    checks: list[QuoteCheck] = []
    for reference in references:
        if not reference.claim_id.strip() or not reference.evidence_id.strip():
            raise ValueError("claim_id and evidence_id must not be empty")
        if not reference.quote.strip():
            raise ValueError("quote must not be empty")
        snapshot = by_id.get(reference.evidence_id)
        quote = _normalize(reference.quote)
        source = _normalize(snapshot.content) if snapshot else ""
        found = bool(snapshot and quote in source)
        checks.append(
            QuoteCheck(
                claim_id=reference.claim_id,
                evidence_id=reference.evidence_id,
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
