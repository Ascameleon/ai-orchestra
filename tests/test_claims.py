import pytest

from orchestra.claims import ClaimRecord, assess_claim_links


def test_claim_link_assessment_distinguishes_linked_unlinked_and_unknown():
    result = assess_claim_links(
        [
            ClaimRecord("c1", "A cited claim", ("e1", "e1")),
            ClaimRecord("c2", "An uncited claim", ()),
            ClaimRecord("c3", "A broken citation", ("missing",)),
            ClaimRecord("c4", "Mixed references", ("e1", "missing")),
        ],
        {"e1", "e2"},
    )

    assert result.total_claims == 4
    assert result.linked_claims == 2
    assert result.unlinked_claims == 2
    assert result.claims_with_unknown_references == 2
    assert result.results[0].linked_evidence_ids == ("e1",)
    assert result.results[0].unknown_evidence_ids == ()
    assert result.results[2].has_valid_evidence_link is False
    assert result.results[2].unknown_evidence_ids == ("missing",)
    assert result.results[3].has_valid_evidence_link is True
    assert result.results[3].has_unknown_references is True


def test_duplicate_claim_ids_are_rejected():
    with pytest.raises(ValueError, match="duplicate claim_id"):
        assess_claim_links(
            [ClaimRecord("same", "First", ("e1",)), ClaimRecord("same", "Second", ("e1",))],
            {"e1"},
        )


def test_blank_claim_fields_are_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        assess_claim_links([ClaimRecord("c1", " ", ("e1",))], {"e1"})


def test_empty_evidence_reference_is_rejected():
    with pytest.raises(ValueError, match="empty evidence reference"):
        assess_claim_links([ClaimRecord("c1", "Claim", (" ",))], {"e1"})


def test_claim_ids_are_normalized_before_duplicate_detection():
    with pytest.raises(ValueError, match="duplicate claim_id: c1"):
        assess_claim_links(
            [ClaimRecord("c1", "First", ("e1",)), ClaimRecord(" c1 ", "Second", ("e1",))],
            {"e1"},
        )


def test_claim_and_evidence_ids_are_normalized_for_link_resolution():
    result = assess_claim_links(
        [ClaimRecord(" c1 ", "Claim", (" e1 ",))],
        {" e1 "},
    )
    assert result.results[0].claim_id == "c1"
    assert result.results[0].linked_evidence_ids == ("e1",)
    assert result.results[0].has_unknown_references is False


@pytest.mark.parametrize("claims,evidence_ids", [
    (None, {"e1"}),
    ("not claims", {"e1"}),
    ([object()], {"e1"}),
    ([ClaimRecord(None, "Claim", ("e1",))], {"e1"}),
    ([ClaimRecord("c1", None, ("e1",))], {"e1"}),
    ([ClaimRecord("c1", "Claim", ["e1"])], {"e1"}),
    ([ClaimRecord("c1", "Claim", (None,))], {"e1"}),
    ([ClaimRecord("c1", "Claim", ("e1",))], None),
    ([ClaimRecord("c1", "Claim", ("e1",))], {"e1", None}),
])
def test_malformed_input_types_are_rejected_with_value_error(claims, evidence_ids):
    with pytest.raises(ValueError):
        assess_claim_links(claims, evidence_ids)
