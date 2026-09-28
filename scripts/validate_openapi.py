import json
from pathlib import Path
from typing import Any

REQUIRED_PATHS = {
    "/v1/audit-events",
    "/v1/release-gates/evaluate",
    "/v1/replay-datasets",
    "/v1/rule-versions/{version_id}",
    "/v1/rule-versions/{version_id}/diff",
    "/v1/simulations",
    "/v1/simulations/{simulation_id}",
    "/v1/simulations/{simulation_id}/approvals",
    "/v1/simulations/{simulation_id}/impact",
    "/v1/tenants/{tenant_id}/rule-versions",
}


def walk_references(value: Any) -> list[str]:
    references: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str):
                references.append(child)
            references.extend(walk_references(child))
    elif isinstance(value, list):
        for child in value:
            references.extend(walk_references(child))
    return references


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    specification = json.loads(
        (root / "packages/contracts/openapi.json").read_text(encoding="utf-8")
    )
    assert specification["openapi"] == "3.1.0"
    assert REQUIRED_PATHS == set(specification["paths"])
    operation_ids: list[str] = []
    for path_item in specification["paths"].values():
        for method in ("get", "post", "put", "patch", "delete"):
            if method in path_item:
                operation_ids.append(path_item[method]["operationId"])
    assert len(operation_ids) == 10
    assert len(set(operation_ids)) == 10
    references = walk_references(specification)
    for reference in references:
        assert reference.startswith("#/"), reference
        target: Any = specification
        for raw_part in reference[2:].split("/"):
            part = raw_part.replace("~1", "/").replace("~0", "~")
            target = target[part]
    print(
        f"OpenAPI validation passed: {len(REQUIRED_PATHS)} paths, "
        f"{len(operation_ids)} operations, {len(references)} references."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
