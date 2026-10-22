from dataclasses import dataclass
from typing import Literal, cast

from ruletwin.domain.canonical import JsonValue

RoundingMode = Literal["half_up", "down", "up"]


@dataclass(frozen=True, slots=True)
class RoundingRule:
    increment_minor_units: int
    mode: RoundingMode

    @classmethod
    def from_json(cls, value: JsonValue) -> "RoundingRule":
        if not isinstance(value, dict) or set(value) != {"increment_minor_units", "mode"}:
            raise ValueError("Rounding rule requires only increment_minor_units and mode.")
        increment = value["increment_minor_units"]
        mode = value["mode"]
        if (
            not isinstance(increment, int)
            or isinstance(increment, bool)
            or not 1 <= increment <= 10000
        ):
            raise ValueError("increment_minor_units must be an integer from 1 through 10000.")
        if mode not in {"half_up", "down", "up"}:
            raise ValueError("mode must be half_up, down, or up.")
        return cls(increment, cast(RoundingMode, mode))

    def apply(self, amount_minor_units: int) -> int:
        if amount_minor_units < 0:
            raise ValueError("amount_minor_units cannot be negative.")
        quotient, remainder = divmod(amount_minor_units, self.increment_minor_units)
        if self.mode == "down":
            return quotient * self.increment_minor_units
        if self.mode == "up":
            return (quotient + (1 if remainder else 0)) * self.increment_minor_units
        if remainder * 2 >= self.increment_minor_units:
            quotient += 1
        return quotient * self.increment_minor_units


def evaluate_rounding(rule: JsonValue, event: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(event, dict):
        raise ValueError("Event must be an object.")
    amount = event.get("amount_minor_units")
    currency = event.get("currency")
    if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
        raise ValueError("Event amount_minor_units must be a non-negative integer.")
    if currency != "USD":
        raise ValueError("Phase 3 supports USD events only.")
    result = RoundingRule.from_json(rule).apply(amount)
    return {
        "amount_minor_units": result,
        "currency": currency,
        "workflow_state": "priced",
        "error": None,
        "emitted_events": [],
    }
