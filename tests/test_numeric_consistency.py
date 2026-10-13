import pytest

from orchestra.numeric_consistency import NumericAssertion, screen_numeric_consistency


def test_flags_different_values_for_same_metric_unit_and_period():
    result = screen_numeric_consistency([
        NumericAssertion("a1", "c1", "e1", "GDP growth", "2.5", "%", "2025"),
        NumericAssertion("a2", "c2", "e2", " gdp   growth ", "3.0", "%", "2025"),
        NumericAssertion("a3", "c3", "e3", "GDP growth", "2.5", "%", "2024"),
        NumericAssertion("a4", "c4", "e4", "GDP growth", "2.500", "%", "2025"),
    ])
    assert result.assertions_checked == 4
    assert result.potential_disagreement_count == 2
    item = result.potential_disagreements[0]
    assert item.assertion_a == "a1"
    assert item.assertion_b == "a2"
    assert item.value_a == "2.5"
    assert item.value_b == "3.0"
    assert item.status == "potential_numeric_disagreement"


def test_rejects_duplicate_ids_blank_fields_and_invalid_numbers():
    with pytest.raises(ValueError, match="duplicate assertion_id"):
        screen_numeric_consistency([
            NumericAssertion("a1", "c1", "e1", "metric", "1", "kg", "2025"),
            NumericAssertion("a1", "c2", "e2", "metric", "2", "kg", "2025"),
        ])
    with pytest.raises(ValueError, match="must not be empty"):
        screen_numeric_consistency([NumericAssertion("a1", "c1", "e1", " ", "1", "kg", "2025")])
    with pytest.raises(ValueError, match="invalid numeric value"):
        screen_numeric_consistency([NumericAssertion("a1", "c1", "e1", "metric", "one", "kg", "2025")])
    with pytest.raises(ValueError, match="finite"):
        screen_numeric_consistency([NumericAssertion("a1", "c1", "e1", "metric", "NaN", "kg", "2025")])


def test_same_value_different_format_is_not_a_disagreement():
    result = screen_numeric_consistency([
        NumericAssertion("a1", "c1", "e1", "rate", "100.00", "percent", "Q1 2025"),
        NumericAssertion("a2", "c2", "e2", " RATE ", "100", " PERCENT ", "q1   2025"),
    ])
    assert result.potential_disagreement_count == 0
