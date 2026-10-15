import pytest

from orchestra.citation_audit import audit_citation_coverage

VALID = "ev_aaaaaaaaaaaaaaaaaaaaaaaa"
UNKNOWN = "ev_bbbbbbbbbbbbbbbbbbbbbbbb"


def test_citation_coverage_counts_valid_and_uncited_sentences():
    answer = (
        f"Supported fact [{VALID}]. "
        "This second statement has no source.\n"
        f"Another supported statement [{VALID}]."
    )

    result = audit_citation_coverage(answer, {VALID})

    assert result.sentence_count == 3
    assert result.sentences_with_valid_citations == 2
    assert result.uncited_sentence_count == 1
    assert result.coverage_ratio == pytest.approx(2 / 3)
    assert result.invalid_citation_ids == ()


def test_citation_coverage_flags_unknown_ids_even_with_valid_ids():
    result = audit_citation_coverage(
        f"Claim [{VALID}] and unrelated claim [{UNKNOWN}].",
        {VALID},
    )

    assert result.sentence_count == 1
    assert result.sentences_with_valid_citations == 1
    assert result.invalid_citation_ids == (UNKNOWN,)


def test_citation_coverage_empty_answer_has_zero_ratio():
    result = audit_citation_coverage(" \n ", {VALID})

    assert result.sentence_count == 0
    assert result.uncited_sentence_count == 0
    assert result.coverage_ratio == 0.0


def test_citation_coverage_rejects_empty_known_ids():
    with pytest.raises(ValueError, match="non-empty strings"):
        audit_citation_coverage("Answer.", {""})


@pytest.mark.parametrize("known_ids", [None, [VALID], "not-an-id-set"])
def test_citation_coverage_rejects_invalid_registry_types(known_ids):
    with pytest.raises(TypeError, match="set or frozenset"):
        audit_citation_coverage("Answer.", known_ids)


def test_citation_coverage_rejects_non_string_registry_ids():
    with pytest.raises(TypeError, match="must be strings"):
        audit_citation_coverage("Answer.", {VALID, 1})


def test_citation_coverage_rejects_normalized_registry_collisions():
    with pytest.raises(ValueError, match="collide"):
        audit_citation_coverage("Answer.", {VALID, f" {VALID} "})


def test_citation_coverage_normalizes_registry_whitespace():
    result = audit_citation_coverage(f"Fact [{VALID}].", {f" {VALID} "})

    assert result.sentences_with_valid_citations == 1
    assert result.invalid_citation_ids == ()


def test_citation_coverage_splits_lowercase_sentence_starts():
    result = audit_citation_coverage(
        f"Supported fact [{VALID}]. this next sentence is uncited.",
        {VALID},
    )

    assert result.sentence_count == 2
    assert result.sentences_with_valid_citations == 1
    assert result.uncited_sentence_count == 1
    assert result.coverage_ratio == pytest.approx(0.5)


def test_citation_coverage_splits_after_closing_quotes():
    result = audit_citation_coverage(
        f"“Supported fact [{VALID}].” this next sentence is uncited.",
        {VALID},
    )

    assert result.sentence_count == 2
    assert result.sentences_with_valid_citations == 1
    assert result.uncited_sentence_count == 1
    assert result.coverage_ratio == pytest.approx(0.5)


@pytest.mark.parametrize("punctuation", ["؟", "！", "？", "。", "｡"])
def test_citation_coverage_splits_unicode_sentence_terminators(punctuation):
    result = audit_citation_coverage(
        f"حقيقة مدعومة [{VALID}]{punctuation} جملة أخرى بلا مصدر.",
        {VALID},
    )

    assert result.sentence_count == 2
    assert result.sentences_with_valid_citations == 1
    assert result.uncited_sentence_count == 1
    assert result.coverage_ratio == pytest.approx(0.5)
