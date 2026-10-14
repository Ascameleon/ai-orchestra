# isort: skip_file
import datetime as dt

import pytest

from orchestra.evidence import EvidenceRecord, assess_evidence


NOW = dt.datetime(2026, 10, 13, 12, 0, tzinfo=dt.UTC)


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
        item("fresh", "alpha", "https://alpha.example/report", NOW - dt.timedelta(days=2)),
        item("stale", "beta", "https://beta.example/report", NOW - dt.timedelta(days=31)),
        item("undated", "gamma", "https://gamma.example/report"),
        item("future", "delta", "https://delta.example/report", NOW + dt.timedelta(days=1)),
    ]

    result = assess_evidence(records, now=NOW, max_age=dt.timedelta(days=30))

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
        item("three", "stale-source", "https://old.example/report", NOW - dt.timedelta(days=90)),
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


@pytest.mark.parametrize(
    "url",
    [
        "",
        "/relative/path",
        "ftp://example.com/file",
        "https:///missing-host",
        "https://example.com:bad/path",
        "https://example.com:99999/path",
        "https://user:password@example.com/path",
        "https://exa mple.com/path",
    ],
)
def test_invalid_urls_are_rejected(url):
    with pytest.raises(ValueError, match="absolute http|embedded credentials"):
        item("bad", "alpha", url)


def test_naive_datetimes_are_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        item("naive", "alpha", "https://a.example", dt.datetime(2026, 10, 13))


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"max_age": dt.timedelta(seconds=-1)}, "max_age"),
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


def test_evidence_assessment_rejects_malformed_collection_and_records():
    with pytest.raises(TypeError, match="records must be a list or tuple"):
        assess_evidence("not-records", now=NOW)
    with pytest.raises(TypeError, match="EvidenceRecord instances"):
        assess_evidence([object()], now=NOW)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"max_age": 30}, "max_age must be a timedelta"),
        ({"minimum_independent_sources": True}, "must be an integer"),
        ({"now": "2026-10-13"}, "now must be a datetime"),
    ],
)
def test_evidence_assessment_rejects_wrong_option_types(kwargs, message):
    with pytest.raises(TypeError, match=message):
        assess_evidence([], **({"now": NOW} | kwargs))


def test_evidence_record_rejects_non_datetime_timestamps():
    with pytest.raises(TypeError, match="retrieved_at must be a datetime"):
        EvidenceRecord("e1", "Publisher", "group", "https://example.com", retrieved_at="today")
    with pytest.raises(TypeError, match="published_at must be a datetime or None"):
        EvidenceRecord("e1", "Publisher", "group", "https://example.com", published_at="today", retrieved_at=NOW)


def test_evidence_assessment_rejects_normalized_identifier_collisions():
    with pytest.raises(ValueError, match="after whitespace normalization"):
        assess_evidence(
            [
                item("e1", "alpha", "https://alpha.example"),
                item(" e1 ", "beta", "https://beta.example"),
            ],
            now=NOW,
        )



def test_default_ports_are_normalized_for_url_deduplication():
    result = assess_evidence(
        [
            item("e1", "alpha", "http://example.com:80/report", NOW),
            item("e2", "alpha", "http://example.com/report#section", NOW),
            item("e3", "beta", "https://example.com:443/report", NOW),
            item("e4", "beta", "https://example.com/report", NOW),
        ],
        now=NOW,
    )

    assert result.unique_urls == 2
    assert result.duplicate_url_records == 2


@pytest.mark.parametrize(
    "field, value",
    [
        ("evidence_id", 7),
        ("source_name", None),
        ("source_group", ["group"]),
    ],
)
def test_evidence_record_rejects_non_string_identity_fields(field, value):
    kwargs = {
        "evidence_id": "e1",
        "source_name": "Publisher",
        "source_group": "group",
        "url": "https://example.com",
        "retrieved_at": NOW,
    }
    kwargs[field] = value
    with pytest.raises(TypeError, match=f"{field} must be a string"):
        EvidenceRecord(**kwargs)


def test_evidence_record_rejects_blank_identity_fields():
    for field in ("evidence_id", "source_name", "source_group"):
        kwargs = {
            "evidence_id": "e1",
            "source_name": "Publisher",
            "source_group": "group",
            "url": "https://example.com",
            "retrieved_at": NOW,
        }
        kwargs[field] = "  "
        with pytest.raises(ValueError, match=f"{field} must not be empty"):
            EvidenceRecord(**kwargs)
