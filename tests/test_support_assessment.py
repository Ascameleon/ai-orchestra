import json

import pytest

from orchestra.support_assessment import parse_support_assessment


def test_parses_complete_assessment_and_normalizes_rationale():
    response = json.dumps({
        "assessments": [{
            "claim_id": "c1",
            "status": "supported",
            "evidence_ids": ["e1"],
            "rationale": "  The source states the same fact.  ",
        }]
    })

    report = parse_support_assessment(response, {"c1"}, {"e1"})

    assert len(report.assessments) == 1
    assert report.assessments[0].status == "supported"
    assert report.assessments[0].evidence_ids == ("e1",)
    assert report.assessments[0].rationale == "The source states the same fact."


def test_normalizes_claim_and_evidence_ids():
    response = json.dumps({
        "assessments": [{
            "claim_id": " c1 ",
            "status": "supported",
            "evidence_ids": [" e1 "],
            "rationale": "Valid source.",
        }]
    })

    report = parse_support_assessment(response, {"c1"}, {"e1"})

    assert report.assessments[0].claim_id == "c1"
    assert report.assessments[0].evidence_ids == ("e1",)


@pytest.mark.parametrize("response", [
    "not json",
    '{"wrong":[]}',
    '{"assessments":[]}',
    '{"assessments":[{"claim_id":"c2","status":"supported","evidence_ids":["e1"],"rationale":"ok"}]}',
    '{"assessments":[{"claim_id":"c1","status":"maybe","evidence_ids":["e1"],"rationale":"ok"}]}',
    '{"assessments":[{"claim_id":"c1","status":"supported","evidence_ids":["made-up"],"rationale":"ok"}]}',
    '{"assessments":[{"claim_id":"c1","status":"supported","evidence_ids":[[]],"rationale":"ok"}]}',
    '{"assessments":[{"claim_id":"c1","status":[],"evidence_ids":["e1"],"rationale":"ok"}]}',
    '{"assessments":[{"claim_id":"c1","status":"supported","evidence_ids":["e1","e1"],"rationale":"ok"}]}',
    '{"assessments":[{"claim_id":"c1","status":"supported","evidence_ids":[],"rationale":"ok"}]}',
    '{"assessments":[{"claim_id":" ","status":"supported","evidence_ids":["e1"],"rationale":"ok"}]}',
])
def test_rejects_malformed_or_invented_assessments(response):
    with pytest.raises(ValueError):
        parse_support_assessment(response, {"c1"}, {"e1"})


@pytest.mark.parametrize("response", [
    '{"assessments":[],"assessments":[{"claim_id":"c1","status":"supported","evidence_ids":["e1"],"rationale":"ok"}]}',
    '{"assessments":[{"claim_id":"c1","claim_id":"c2","status":"supported","evidence_ids":["e1"],"rationale":"ok"}]}',
    '{"assessments":[{"claim_id":"c1","status":"supported","evidence_ids":["e1"],"rationale":"ok","rationale":"forged"}]}',
])
def test_rejects_duplicate_json_object_keys(response):
    with pytest.raises(ValueError, match="unambiguous JSON"):
        parse_support_assessment(response, {"c1"}, {"e1"})


@pytest.mark.parametrize("response,claims,evidence", [
    (None, {"c1"}, {"e1"}),
    ("{}", None, {"e1"}),
    ("{}", {"c1"}, None),
    ("{}", {"c1", 1}, {"e1"}),
    ("{}", {"c1"}, {"e1", 1}),
    ("{}", {""}, {"e1"}),
    ("{}", {"c1"}, {" "}),
])
def test_rejects_invalid_parser_inputs(response, claims, evidence):
    with pytest.raises((TypeError, ValueError)):
        parse_support_assessment(response, claims, evidence)
