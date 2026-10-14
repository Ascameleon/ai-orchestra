import pytest

from orchestra.traceability import (
    ClaimTrace,
    SourceAssertion,
    screen_potential_conflicts,
    trace_conclusions,
)


def test_conflict_screen_flags_only_same_topic_opposite_stances():
    result = screen_potential_conflicts(
        [
            SourceAssertion("a1", "e1", "Inflation rate", "supports"),
            SourceAssertion("a2", "e2", " inflation   rate ", "opposes"),
            SourceAssertion("a3", "e3", "Inflation rate", "neutral"),
            SourceAssertion("a4", "e4", "Employment rate", "opposes"),
        ]
    )
    assert result.assertions_checked == 4
    assert len(result.potential_conflicts) == 1
    conflict = result.potential_conflicts[0]
    assert (conflict.assertion_a, conflict.assertion_b) == ("a1", "a2")
    assert (conflict.evidence_a, conflict.evidence_b) == ("e1", "e2")
    assert conflict.status == "potential_conflict"


def test_conflict_screen_rejects_duplicate_ids_and_blank_fields():
    with pytest.raises(ValueError, match="duplicate assertion_id"):
        screen_potential_conflicts(
            [
                SourceAssertion("a1", "e1", "topic", "supports"),
                SourceAssertion("a1", "e2", "topic", "opposes"),
            ]
        )
    with pytest.raises(ValueError, match="must not be empty"):
        screen_potential_conflicts([SourceAssertion("a1", "e1", " ", "supports")])


def test_conclusion_traceability_resolves_claims_to_evidence_and_reports_gaps():
    result = trace_conclusions(
        [
            ("d1", "Conclusion with citations", ("c1", "c2", "c1")),
            ("d2", "Conclusion with one missing claim", ("c1", "unknown")),
            ("d3", "Conclusion without references", ()),
            ("d4", "Conclusion with only unknown references", ("unknown",)),
        ],
        [
            ClaimTrace("c1", ("e1", "e2")),
            ClaimTrace("c2", ("e2", "e3")),
        ],
    )
    assert result.conclusions_checked == 4
    assert result.fully_traceable == 1
    assert result.partially_traceable == 1
    assert result.untraceable == 2
    assert result.results[0].linked_claim_ids == ("c1", "c2")
    assert result.results[0].evidence_ids == ("e1", "e2", "e3")
    assert result.results[1].missing_claim_ids == ("unknown",)
    assert result.results[1].traceability_status == "partially_traceable"


def test_traceability_rejects_duplicate_claim_and_conclusion_ids():
    with pytest.raises(ValueError, match="duplicate claim_id"):
        trace_conclusions([], [ClaimTrace("c1", ()), ClaimTrace("c1", ())])
    with pytest.raises(ValueError, match="duplicate conclusion_id"):
        trace_conclusions([("d1", "first", ()), ("d1", "second", ())], [])


def test_traceability_flags_unknown_evidence_and_claims_without_evidence():
    result = trace_conclusions(
        [("d1", "Conclusion", ("c1", "c2"))],
        [ClaimTrace("c1", ("e1", "unknown")), ClaimTrace("c2", ())],
        known_evidence_ids=["e1", "e2"],
    )
    item = result.results[0]
    assert item.traceability_status == "partially_traceable"
    assert item.evidence_ids == ("e1", "unknown")
    assert item.unknown_evidence_ids == ("unknown",)
    assert item.claims_without_evidence == ("c2",)
    assert result.partially_traceable == 1


def test_traceability_validates_evidence_registry():
    with pytest.raises(ValueError, match="must be unique"):
        trace_conclusions([], [], known_evidence_ids=["e1", "e1"])
    with pytest.raises(ValueError, match="must not contain empty"):
        trace_conclusions([], [], known_evidence_ids=[" "])


def test_conflict_screen_normalizes_ids_before_duplicate_detection():
    with pytest.raises(ValueError, match="duplicate assertion_id: a1"):
        screen_potential_conflicts(
            [
                SourceAssertion("a1", "e1", "topic", "supports"),
                SourceAssertion(" a1 ", "e2", "topic", "opposes"),
            ]
        )


def test_traceability_normalizes_ids_and_rejects_duplicates_after_normalization():
    with pytest.raises(ValueError, match="duplicate claim_id: c1"):
        trace_conclusions(
            [],
            [ClaimTrace("c1", ()), ClaimTrace(" c1 ", ())],
        )

    result = trace_conclusions(
        [(" d1 ", "Conclusion", (" c1 ",))],
        [ClaimTrace(" c1 ", (" e1 ",))],
        known_evidence_ids=["e1"],
    )
    assert result.results[0].conclusion_id == "d1"
    assert result.results[0].linked_claim_ids == ("c1",)
    assert result.results[0].evidence_ids == ("e1",)
