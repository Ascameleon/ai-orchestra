from datetime import UTC, datetime, timedelta

import pytest

from orchestra.evidence import EvidenceRecord, assess_evidence


NOW = datetime(2026, 10, 13, 12, 0, tzinfo=UTC)


def item(evidence_id, source_group, url, published_at=None):
    return EvidenceRecord(
        evidence_id=evidence_id,
        source_name=f"Publisher {source_group}",
        source_group=source_group,
        url=url,
        published_at=published_at,
        retrieved_at=NOW,
    )


def test_freshness_distinguishes_fresh_stale_undated_and_future():
    records = [
        item("fresh", "alpha", "https://alpha.example/report", NOW - timedelta(days=2)),
        item("stale", "beta", "https://beta.example/report", NOW - timedelta(days=31)),
        item("undated", "gamma", "https://gamma.example/report"),
        item("future", "delta", "https://delta.example/report", NOW + timedelta(days=1)),
    ]

    result = assess_evidence(records, now=NOW, max_age=timedelta(days=30))

    assert result.total_records == 4
    assert result.fresh_records == 1
    assert result.stale_records == 1
    assert result.undated_records == 1
    assert result.future_dated_records == 1
    assert not result.has_enough_fresh_independent_sources


def test_independence_counts_distinct_declared_groups_and_deduplicates_urls():
    records = [
        item("one", "wire-service", "https://news.example/story/", NOW),
        item("duplicate-url", "another-label", "https://NEWS.example/story#section", NOW),
        item("two", "independent-paper", "https://paper.example/report", NOW),
        item("three", "stale-source", "https://old.example/report", NOW - timedelta(days=90)),
    ]

    result = assess_evidence(records, now=NOW)

    assert result.total_records == 4
    assert result.unique_urls == 3
    assert result.duplicate_url_records == 1
    assert result.independent_source_groups == ("independent-paper", "stale-source", "wire-service")
    assert result.fresh_independent_source_groups == ("independent-paper", "wire-service")
    assert result.has_enough_fresh_independent_sources


def test_duplicate_evidence_ids_are_rejected():
    with pytest.raises(ValueError, match="duplicate evidence_id"):
        assess_evidence(
            [item("same", "alpha", "https://a.example"), item("same", "beta", "https://b.example")],
            now=NOW,
        )


@pytest.mark.parametrize("url", ["", "/relative/path", "ftp://example.com/file", "https:///missing-host"])
def test_invalid_urls_are_rejected(url):
    with pytest.raises(ValueError, match="absolute http"):
        item("bad", "alpha", url)


def test_naive_datetimes_are_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        item("naive", "alpha", "https://a.example", datetime(2026, 10, 13))


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"max_age": timedelta(seconds=-1)}, "max_age"),
        ({"minimum_independent_sources": 0}, "minimum_independent_sources"),
    ],
)
def test_invalid_assessment_options_are_rejected(kwargs, message):
    with pytest.raises(ValueError, match=message):
        assess_evidence([], now=NOW, **kwargs)


def test_empty_evidence_does_not_claim_source_coverage():
    result = assess_evidence([], now=NOW)

    assert result.total_records == 0
    assert result.unique_urls == 0
    assert result.independent_source_groups == ()
    assert not result.has_enough_fresh_independent_sources
