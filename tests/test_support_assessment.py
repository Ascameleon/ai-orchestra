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
])
def test_rejects_malformed_or_invented_assessments(response):
    with pytest.raises(ValueError):
        parse_support_assessment(response, {"c1"}, {"e1"})
