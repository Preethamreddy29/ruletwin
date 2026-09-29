from itertools import permutations

import pytest

from ruletwin.domain.canonical import canonical_json, checksum
from ruletwin.domain.datasets import dataset_checksum, generate_events
from ruletwin.domain.rounding import RoundingRule, evaluate_rounding
from ruletwin.domain.simulation import compare_rules, evaluate_risk


def test_rule_canonicalization_is_order_independent() -> None:
    items = [("mode", "half_up"), ("increment_minor_units", 5)]
    serializations = {canonical_json(dict(order)) for order in permutations(items)}
    checksums = {checksum(dict(order)) for order in permutations(items)}
    assert len(serializations) == 1
    assert len(checksums) == 1


@pytest.mark.parametrize("increment", [1, 2, 5, 10, 25, 100, 1000, 10000])
def test_rounding_properties_hold_across_money_domain(increment: int) -> None:
    rule = RoundingRule(increment, "half_up")
    for amount in range(0, increment * 5 + 1):
        rounded = rule.apply(amount)
        assert rounded % increment == 0
        assert abs(rounded - amount) <= (increment + 1) // 2
        assert rule.apply(rounded) == rounded


@pytest.mark.parametrize(
    ("amount", "increment", "expected"),
    [(0, 5, 0), (2, 5, 0), (3, 5, 5), (12, 10, 10), (15, 10, 20), (9999, 100, 10000)],
)
def test_half_up_rounding_boundaries(amount: int, increment: int, expected: int) -> None:
    assert RoundingRule(increment, "half_up").apply(amount) == expected


def test_money_evaluation_uses_integer_minor_units_only() -> None:
    outcome = evaluate_rounding(
        {"mode": "half_up", "increment_minor_units": 5},
        {"event_id": "event", "sequence": 0, "currency": "USD", "amount_minor_units": 103},
    )
    assert outcome["amount_minor_units"] == 105
    with pytest.raises(ValueError, match="integer"):
        evaluate_rounding(
            {"mode": "half_up", "increment_minor_units": 5},
            {"currency": "USD", "amount_minor_units": 1.03},  # type: ignore[dict-item]
        )


def test_dataset_and_result_checksums_are_reproducible() -> None:
    first = generate_events(314159, 100)
    second = generate_events(314159, 100)
    assert first == second
    assert dataset_checksum(314159, first) == dataset_checksum(314159, second)
    baseline = {"increment_minor_units": 1, "mode": "half_up"}
    candidate = {"increment_minor_units": 10, "mode": "half_up"}
    assert (
        compare_rules(baseline, candidate, first).result_checksum
        == compare_rules(baseline, candidate, second).result_checksum
    )


def test_financial_threshold_policy_allows_and_blocks_deterministically() -> None:
    allow = evaluate_risk({"maximum_financial_delta_minor_units": 2}, 2, "policy-v1")
    block = evaluate_risk({"maximum_financial_delta_minor_units": 3}, 2, "policy-v1")
    error = evaluate_risk({}, 2, "policy-v1")
    assert allow["decision"] == "allow"
    assert block["decision"] == "block"
    assert error["decision"] == "error"
