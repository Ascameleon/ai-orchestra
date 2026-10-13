"""Conservative freshness and source-independence assessment for supplied evidence.

This module evaluates metadata only. It does not fetch URLs, verify publishers, or
establish that a cited source supports a claim.
"""
import datetime as dt
from dataclasses import dataclass, field
from urllib.parse import urlsplit, urlunsplit


FRESH = "fresh"
STALE = "stale"
UNDATED = "undated"
FUTURE_DATED = "future_dated"


def _require_aware(value: dt.datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("url must be an absolute http(s) URL")
    # Normalize only obvious URL variants. Query parameters are retained because
    # they can identify distinct resources; fragments do not identify server content.
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), netloc, path, parts.query, ""))


@dataclass(frozen=True)
class EvidenceRecord:
    """Metadata supplied by a caller for one evidence item; no source is fetched."""

    evidence_id: str
    source_name: str
    source_group: str
    url: str
    published_at: dt.datetime | None = None
    retrieved_at: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.UTC))

    def __post_init__(self) -> None:
        for name in ("evidence_id", "source_name", "source_group"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must not be empty")
        if not isinstance(self.url, str):
            raise TypeError("url must be a string")
        _canonical_url(self.url)
        _require_aware(self.retrieved_at, "retrieved_at")
        if self.published_at is not None:
            _require_aware(self.published_at, "published_at")


@dataclass(frozen=True)
class EvidenceAssessment:
    """Summary counts; independence depends on caller-supplied source groups."""

    total_records: int
    unique_urls: int
    duplicate_url_records: int
    fresh_records: int
    stale_records: int
    undated_records: int
    future_dated_records: int
    independent_source_groups: tuple[str, ...]
    fresh_independent_source_groups: tuple[str, ...]
    minimum_independent_sources: int
    has_enough_fresh_independent_sources: bool


def assess_evidence(
    records: list[EvidenceRecord] | tuple[EvidenceRecord, ...],
    *,
    now: dt.datetime | None = None,
    max_age: dt.timedelta = dt.timedelta(days=30),
    minimum_independent_sources: int = 2,
) -> EvidenceAssessment:
    """Assess evidence freshness and declared source diversity without network calls.

    Published timestamps determine freshness. Missing dates are unknown, not fresh.
    URLs are deduplicated for independence counts, while freshness counts are
    record-level. Source groups must be assigned by the caller and are not verified.
    """
    reference_time = now or dt.datetime.now(dt.UTC)
    _require_aware(reference_time, "now")
    if max_age < dt.timedelta(0):
        raise ValueError("max_age must not be negative")
    if minimum_independent_sources < 1:
        raise ValueError("minimum_independent_sources must be at least 1")

    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    all_groups: set[str] = set()
    fresh_groups: set[str] = set()
    fresh_count = stale_count = undated_count = future_count = 0

    for record in records:
        if record.evidence_id in seen_ids:
            raise ValueError(f"duplicate evidence_id: {record.evidence_id}")
        seen_ids.add(record.evidence_id)
        canonical_url = _canonical_url(record.url)
        unique_url = canonical_url not in seen_urls
        seen_urls.add(canonical_url)

        if record.published_at is None:
            undated_count += 1
            status = UNDATED
        else:
            age = reference_time - record.published_at
            if age < dt.timedelta(0):
                future_count += 1
                status = FUTURE_DATED
            elif age <= max_age:
                fresh_count += 1
                status = FRESH
            else:
                stale_count += 1
                status = STALE

        if unique_url:
            group = record.source_group.strip().casefold()
            all_groups.add(group)
            if status == FRESH:
                fresh_groups.add(group)

    return EvidenceAssessment(
        total_records=len(records),
        unique_urls=len(seen_urls),
        duplicate_url_records=len(records) - len(seen_urls),
        fresh_records=fresh_count,
        stale_records=stale_count,
        undated_records=undated_count,
        future_dated_records=future_count,
        independent_source_groups=tuple(sorted(all_groups)),
        fresh_independent_source_groups=tuple(sorted(fresh_groups)),
        minimum_independent_sources=minimum_independent_sources,
        has_enough_fresh_independent_sources=len(fresh_groups) >= minimum_independent_sources,
    )
