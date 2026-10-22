import uuid

from ruletwin.domain.canonical import JsonValue, checksum

GENERATOR_VERSION = "rounding-events-v1"
EVENT_SCHEMA_VERSION = "business-event-v1"
DATASET_NAMESPACE = uuid.UUID("7af98e0d-ea77-51a3-9664-4f0b9a633064")


def generate_events(seed: int, count: int) -> list[dict[str, JsonValue]]:
    if seed < 0 or not 1 <= count <= 100000:
        raise ValueError("Dataset seed/count are outside supported bounds.")
    events: list[dict[str, JsonValue]] = []
    # A small integer LCG avoids runtime/version-specific random behavior.
    state = seed & 0x7FFFFFFF
    for sequence in range(count):
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        dollars = 10 + state % 490
        cents = (sequence * 17 + seed * 13) % 100
        events.append(
            {
                "event_id": str(uuid.uuid5(DATASET_NAMESPACE, f"{seed}:{sequence}")),
                "sequence": sequence,
                "currency": "USD",
                "amount_minor_units": dollars * 100 + cents,
            }
        )
    return events


def dataset_checksum(seed: int, events: list[dict[str, JsonValue]]) -> str:
    return checksum(
        {
            "generator_version": GENERATOR_VERSION,
            "event_schema_version": EVENT_SCHEMA_VERSION,
            "seed": seed,
            "events": events,
        }
    )
