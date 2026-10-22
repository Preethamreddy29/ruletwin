import uuid

NAMESPACE = uuid.UUID("8ba28604-8eb4-59df-926c-68e814b89b47")
SEED_VALUE = "ruletwin-dev-v1"


def identifier(kind: str, name: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"{SEED_VALUE}:{kind}:{name}")


TENANT_ID = identifier("tenant", "novabill-sandbox")
AUTHOR_ID = identifier("user", "analyst@novabill.example")
APPROVER_ID = identifier("user", "approver@novabill.example")
RULE_DEFINITION_ID = identifier("rule-definition", "invoice-rounding")
BASELINE_RULE_VERSION_ID = identifier("rule-version", "invoice-rounding-v1")
DATASET_ID = identifier("dataset", "rounding-boundaries-v1")
POLICY_ID = identifier("risk-policy", "phase3-financial-threshold-v1")
