import uuid
from dataclasses import dataclass

NAMESPACE = uuid.UUID("8ba28604-8eb4-59df-926c-68e814b89b47")
SEED_VALUE = "ruletwin-dev-v1"


def identifier(kind: str, name: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"{SEED_VALUE}:{kind}:{name}")


TENANT_ID = identifier("tenant", "novabill-sandbox")
AUTHOR_ID = identifier("user", "analyst@novabill.example")
REVIEWER_ID = identifier("user", "reviewer@novabill.example")
APPROVER_ID = identifier("user", "approver@novabill.example")
AUDITOR_ID = identifier("user", "auditor@novabill.example")
RULE_DEFINITION_ID = identifier("rule-definition", "invoice-rounding")
BASELINE_RULE_VERSION_ID = identifier("rule-version", "invoice-rounding-v1")
DATASET_ID = identifier("dataset", "rounding-boundaries-v1")
POLICY_ID = identifier("risk-policy", "phase3-financial-threshold-v1")

SECOND_TENANT_ID = identifier("tenant", "brightline-sandbox")
SECOND_AUTHOR_ID = identifier("user", "analyst@brightline.example")
SECOND_REVIEWER_ID = identifier("user", "reviewer@brightline.example")
SECOND_APPROVER_ID = identifier("user", "approver@brightline.example")
SECOND_AUDITOR_ID = identifier("user", "auditor@brightline.example")
SECOND_RULE_DEFINITION_ID = identifier("rule-definition", "brightline-invoice-rounding")
SECOND_BASELINE_RULE_VERSION_ID = identifier("rule-version", "brightline-invoice-rounding-v1")
SECOND_DATASET_ID = identifier("dataset", "brightline-rounding-boundaries-v1")
SECOND_POLICY_ID = identifier("risk-policy", "brightline-financial-threshold-v1")


@dataclass(frozen=True)
class SyntheticTenant:
    id: uuid.UUID
    slug: str
    display_name: str
    rule_definition_id: uuid.UUID
    baseline_rule_version_id: uuid.UUID
    dataset_id: uuid.UUID
    policy_id: uuid.UUID


@dataclass(frozen=True)
class SyntheticIdentity:
    key: str
    id: uuid.UUID
    email: str
    display_name: str
    tenant_id: uuid.UUID
    role: str


TENANTS = (
    SyntheticTenant(
        TENANT_ID,
        "novabill-sandbox",
        "NovaBill Sandbox",
        RULE_DEFINITION_ID,
        BASELINE_RULE_VERSION_ID,
        DATASET_ID,
        POLICY_ID,
    ),
    SyntheticTenant(
        SECOND_TENANT_ID,
        "brightline-sandbox",
        "Brightline Sandbox",
        SECOND_RULE_DEFINITION_ID,
        SECOND_BASELINE_RULE_VERSION_ID,
        SECOND_DATASET_ID,
        SECOND_POLICY_ID,
    ),
)

IDENTITIES = (
    SyntheticIdentity(
        "novabill-analyst",
        AUTHOR_ID,
        "analyst@novabill.example",
        "NovaBill Analyst",
        TENANT_ID,
        "author",
    ),
    SyntheticIdentity(
        "novabill-reviewer",
        REVIEWER_ID,
        "reviewer@novabill.example",
        "NovaBill QA Reviewer",
        TENANT_ID,
        "reviewer",
    ),
    SyntheticIdentity(
        "novabill-approver",
        APPROVER_ID,
        "approver@novabill.example",
        "NovaBill Release Approver",
        TENANT_ID,
        "release_approver",
    ),
    SyntheticIdentity(
        "novabill-auditor",
        AUDITOR_ID,
        "auditor@novabill.example",
        "NovaBill Auditor",
        TENANT_ID,
        "auditor",
    ),
    SyntheticIdentity(
        "brightline-analyst",
        SECOND_AUTHOR_ID,
        "analyst@brightline.example",
        "Brightline Analyst",
        SECOND_TENANT_ID,
        "author",
    ),
    SyntheticIdentity(
        "brightline-reviewer",
        SECOND_REVIEWER_ID,
        "reviewer@brightline.example",
        "Brightline QA Reviewer",
        SECOND_TENANT_ID,
        "reviewer",
    ),
    SyntheticIdentity(
        "brightline-approver",
        SECOND_APPROVER_ID,
        "approver@brightline.example",
        "Brightline Release Approver",
        SECOND_TENANT_ID,
        "release_approver",
    ),
    SyntheticIdentity(
        "brightline-auditor",
        SECOND_AUDITOR_ID,
        "auditor@brightline.example",
        "Brightline Auditor",
        SECOND_TENANT_ID,
        "auditor",
    ),
)


def tenant_by_id(tenant_id: uuid.UUID) -> SyntheticTenant | None:
    return next((tenant for tenant in TENANTS if tenant.id == tenant_id), None)


def identity_by_key(key: str) -> SyntheticIdentity | None:
    return next((identity for identity in IDENTITIES if identity.key == key), None)
