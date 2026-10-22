import hashlib
import json
from collections.abc import Mapping, Sequence

type JsonScalar = str | int | bool | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def canonical_json(value: object) -> str:
    """Return the version-1 canonical JSON representation used for evidence."""
    normalized = normalize_json(value)
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def checksum(value: object) -> str:
    digest = hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def normalize_json(value: object) -> JsonValue:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): normalize_json(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [normalize_json(item) for item in value]
    raise TypeError(f"Unsupported canonical JSON value: {type(value).__name__}")
