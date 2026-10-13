import hashlib

import pytest

from orchestra.quotes import QuoteReference, SourceSnapshot, audit_quotes


def test_audit_quotes_matches_whitespace_and_case_and_hashes_snapshot():
    source = "AI Orchestra\n builds a modular system."
    quote = "ai   orchestra builds a modular system."
    result = audit_quotes([SourceSnapshot("e1", source)], [QuoteReference("c1", "e1", quote)])

    assert result.total_quotes == 1
    assert result.quotes_found == 1
    assert result.quotes_missing == 0
    assert result.checks[0].quote_found is True
    assert result.checks[0].source_sha256 == hashlib.sha256(source.encode()).hexdigest()
    assert result.checks[0].quote_sha256 == hashlib.sha256(quote.encode()).hexdigest()


def test_audit_quotes_flags_missing_and_unknown_sources():
    result = audit_quotes(
        [SourceSnapshot("e1", "A captured source passage.")],
        [
            QuoteReference("c1", "e1", "passage absent"),
            QuoteReference("c2", "missing", "any quote"),
        ],
    )

    assert result.quotes_found == 0
    assert result.quotes_missing == 2
    assert result.unknown_evidence_references == 1
    assert result.checks[0].source_sha256 is not None
    assert result.checks[1].source_sha256 is None


def test_duplicate_snapshot_ids_and_empty_quotes_are_rejected():
    with pytest.raises(ValueError, match="duplicate snapshot"):
        audit_quotes(
            [SourceSnapshot("e1", "first"), SourceSnapshot("e1", "second")],
            [],
        )
    with pytest.raises(ValueError, match="quote must not be empty"):
        audit_quotes([SourceSnapshot("e1", "text")], [QuoteReference("c1", "e1", " ")])


def test_partial_substring_is_not_found():
    result = audit_quotes(
        [SourceSnapshot("e1", "The result was 42 percent.")],
        [QuoteReference("c1", "e1", "result was 43 percent")],
    )
    assert result.checks[0].quote_found is False
