from dataclasses import dataclass

from ruletwin.domain.canonical import JsonValue, checksum
from ruletwin.domain.rounding import evaluate_rounding

ENGINE_VERSION = "rounding-engine-v1"


@dataclass(frozen=True, slots=True)
class SimulationResult:
    outcomes: list[dict[str, JsonValue]]
    impact: dict[str, JsonValue]
    result_checksum: str


def compare_rules(
    baseline_rule: JsonValue,
    candidate_rule: JsonValue,
    events: list[dict[str, JsonValue]],
) -> SimulationResult:
    outcomes: list[dict[str, JsonValue]] = []
    changed_count = 0
    total_delta = 0
    maximum_delta = 0
    for event in events:
        baseline = evaluate_rounding(baseline_rule, event)
        candidate = evaluate_rounding(candidate_rule, event)
        baseline_amount = baseline["amount_minor_units"]
        candidate_amount = candidate["amount_minor_units"]
        assert isinstance(baseline_amount, int) and isinstance(candidate_amount, int)
        delta = candidate_amount - baseline_amount
        if delta:
            changed_count += 1
        total_delta += delta
        maximum_delta = max(maximum_delta, abs(delta))
        outcomes.append(
            {
                "event_id": event["event_id"],
                "sequence": event["sequence"],
                "baseline": baseline,
                "candidate": candidate,
                "financial_delta_minor_units": delta,
            }
        )
    impact: dict[str, JsonValue] = {
        "event_count": len(events),
        "changed_event_count": changed_count,
        "unchanged_event_count": len(events) - changed_count,
        "total_financial_delta_minor_units": total_delta,
        "maximum_financial_delta_minor_units": maximum_delta,
        "currency": "USD",
    }
    result_checksum = checksum(
        {"engine_version": ENGINE_VERSION, "outcomes": outcomes, "impact": impact}
    )
    return SimulationResult(outcomes, impact, result_checksum)


def evaluate_risk(
    impact: dict[str, JsonValue], threshold_minor_units: int, policy_version: str
) -> dict[str, JsonValue]:
    maximum = impact.get("maximum_financial_delta_minor_units")
    reasons: list[JsonValue]
    if not isinstance(maximum, int):
        decision = "error"
        reasons = ["Impact evidence is missing or invalid; policy failed closed."]
    elif maximum > threshold_minor_units:
        decision = "block"
        reasons = [
            f"Maximum event delta {maximum} minor units exceeds threshold {threshold_minor_units}."
        ]
    else:
        decision = "allow"
        reasons = [
            f"Maximum event delta {maximum} minor units is within "
            f"threshold {threshold_minor_units}."
        ]
    evidence: dict[str, JsonValue] = {
        "policy_version": policy_version,
        "threshold_minor_units": threshold_minor_units,
        "decision": decision,
        "reasons": reasons,
        "impact": impact,
    }
    evidence["checksum"] = checksum(evidence)
    return evidence
