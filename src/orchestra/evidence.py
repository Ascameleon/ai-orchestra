"""Conservative freshness and source-independence assessment for supplied evidence.

This module evaluates metadata only. It does not fetch URLs, verify publishers, or
establish that a cited source supports a claim.
"""
# isort: skip_file
import datetime as dt
from dataclasses import dataclass, field
from urllib.parse import urlsplit, urlunsplit


FRESH = "fresh"
STALE = "stale"
UNDATED = "undated"
FUTURE_DATED = "future_dated"


def _require_aware(value: dt.datetime, field_name: str) -> None:
    if not isinstance(value, dt.datetime):
        suffix = " or None" if field_name == "published_at" else ""
        raise TypeError(f"{field_name} must be a datetime{suffix}")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _canonical_url(url: str) -> str:
    try:
        parts = urlsplit(url.strip())
        port = parts.port  # Access validates malformed and out-of-range ports.
    except ValueError:
        raise ValueError("url must be an absolute http(s) URL") from None
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("url must be an absolute http(s) URL")
    if parts.username is not None or parts.password is not None:
        raise ValueError("url must not contain embedded credentials")
    hostname = parts.hostname.lower()
    # A trailing DNS root dot is equivalent to the same hostname without it.
    # Strip it for URL deduplication, but reject a host made only of dots.
    if ":" not in hostname:
        hostname = hostname.rstrip(".")
    # urlsplit accepts whitespace and control characters inside hostnames; reject
    # these instead of treating malformed input as a valid source URL.
    if not hostname or any(
        character.isspace() or ord(character) < 32 or ord(character) == 127
        for character in hostname
    ):
        raise ValueError("url must be an absolute http(s) URL")
    # Normalize default ports so equivalent origins do not inflate URL diversity.
    if (parts.scheme.lower(), port) in {("http", 80), ("https", 443)}:
        port = None
    # Normalize only obvious URL variants. Query parameters are retained because
    # they can identify distinct resources; fragments do not identify server content.
    netloc = hostname
    if port is not None:
        netloc = f"{netloc}:{port}"
    if ":" in parts.hostname and not parts.hostname.startswith("["):
        netloc = f"[{parts.hostname.lower()}]" + (f":{port}" if port is not None else "")
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
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")
            if not value.strip():
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
    if not isinstance(records, (list, tuple)):
        raise TypeError("records must be a list or tuple")
    reference_time = now if now is not None else dt.datetime.now(dt.UTC)
    if not isinstance(reference_time, dt.datetime):
        raise TypeError("now must be a datetime or None")
    _require_aware(reference_time, "now")
    if not isinstance(max_age, dt.timedelta):
        raise TypeError("max_age must be a timedelta")
    if isinstance(minimum_independent_sources, bool) or not isinstance(minimum_independent_sources, int):
        raise TypeError("minimum_independent_sources must be an integer")
    if max_age < dt.timedelta(0):
        raise ValueError("max_age must not be negative")
    if minimum_independent_sources < 1:
        raise ValueError("minimum_independent_sources must be at least 1")

    seen_ids: set[str] = set()
    url_groups: dict[str, set[str]] = {}
    fresh_urls: set[str] = set()
    fresh_count = stale_count = undated_count = future_count = 0

    for record in records:
        if not isinstance(record, EvidenceRecord):
            raise TypeError("records must contain EvidenceRecord instances")
        evidence_id = record.evidence_id.strip()
        if evidence_id in seen_ids:
            raise ValueError(f"duplicate evidence_id after whitespace normalization: {evidence_id}")
        seen_ids.add(evidence_id)
        canonical_url = _canonical_url(record.url)
        group = " ".join(record.source_group.split()).casefold()
        url_groups.setdefault(canonical_url, set()).add(group)

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
        if status == FRESH:
            fresh_urls.add(canonical_url)

    # A URL repeated with conflicting source-group labels is ambiguous. Exclude
    # it from independence counts rather than letting input order choose a label.
    unambiguous_urls = {
        url: next(iter(groups))
        for url, groups in url_groups.items()
        if len(groups) == 1
    }
    all_groups = set(unambiguous_urls.values())
    fresh_groups = {
        unambiguous_urls[url] for url in fresh_urls if url in unambiguous_urls
    }
    seen_urls = set(url_groups)

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
