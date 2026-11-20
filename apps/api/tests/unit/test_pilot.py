from pathlib import Path

from scripts.pilot import (
    IMAGE_KEYS,
    PUBLIC_KEYS,
    sha256_file,
    validate_owner_decisions,
    validate_release_environment,
)


def test_release_environment_requires_digest_images_and_https(tmp_path: Path) -> None:
    secret = tmp_path / "secret"
    secret.write_text("value", encoding="utf-8")
    values = {key: "configured" for key in PUBLIC_KEYS}
    values.update({key: f"example/image@sha256:{'a' * 64}" for key in IMAGE_KEYS})
    values.update(
        {
            "RULETWIN_POSTGRES_ADMIN_PASSWORD_SECRET_FILE": str(secret.resolve()),
            "RULETWIN_POSTGRES_APP_PASSWORD_SECRET_FILE": str(secret.resolve()),
            "RULETWIN_ADMIN_DATABASE_URL_SECRET_FILE": str(secret.resolve()),
            "RULETWIN_APP_DATABASE_URL_SECRET_FILE": str(secret.resolve()),
            "RULETWIN_TLS_CERT_FILE": str(secret.resolve()),
            "RULETWIN_TLS_KEY_FILE": str(secret.resolve()),
            "RULETWIN_BASE_URL": "https://pilot.example",
            "RULETWIN_OIDC_ISSUER": "https://identity.example/",
            "RULETWIN_OIDC_JWKS_URL": "https://identity.example/jwks.json",
        }
    )

    assert validate_release_environment(values) == []

    values["RULETWIN_API_IMAGE"] = "example/image:latest"
    values["RULETWIN_OIDC_ISSUER"] = "http://identity.example/"
    errors = validate_release_environment(values)
    assert "RULETWIN_API_IMAGE must use an immutable @sha256 digest" in errors
    assert "RULETWIN_OIDC_ISSUER must use HTTPS" in errors


def test_sha256_file_is_stable(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    artifact.write_bytes(b"ruletwin-pilot-evidence")
    assert (
        sha256_file(artifact) == "9075770b4c6b82d92ee3bc3d311e7323e36665864f9ccadea8f7774777b14556"
    )


def valid_owner_decisions() -> dict[str, object]:
    return {
        "schema_version": 1,
        "scope": {
            "data_classification": "synthetic-only",
            "access_model": "invitation-only",
            "hosted_visibility": "private",
        },
        "hosting": {
            "provider": "Example Cloud",
            "region": "india-south",
            "budget_owner": "Pilot owner",
            "operator": "Pilot operator",
        },
        "domain": {"hostname": "pilot.example.test", "tls_owner": "Pilot owner"},
        "identity": {
            "provider": "Auth0",
            "tenant": "example.us.auth0.com",
            "client_id": "public-spa-client-id",
            "api_audience": "https://api.pilot.example.test",
            "tenant_claim": "https://pilot.example.test/tenant_id",
            "owner": "Identity owner",
            "invited_identities": [
                {"subject": "auth0|nova-analyst", "tenant": "NovaBill", "role": "analyst"},
                {
                    "subject": "auth0|nova-reviewer",
                    "tenant": "NovaBill",
                    "role": "qa_reviewer",
                },
                {
                    "subject": "auth0|brightline-approver",
                    "tenant": "Brightline",
                    "role": "release_approver",
                },
                {
                    "subject": "auth0|brightline-auditor",
                    "tenant": "Brightline",
                    "role": "auditor",
                },
            ],
        },
        "secrets": {
            "provider": "Example secret store",
            "access_identity": "deployment identity",
            "owner": "Security owner",
        },
        "recovery": {
            "backup_storage": "Encrypted object storage",
            "retention_days": 30,
            "rpo_minutes": 60,
            "rto_minutes": 120,
            "owner": "Recovery owner",
        },
        "operations": {
            "support_window": "09:00-17:00 Asia/Kolkata",
            "alert_receiver": "Pilot operations queue",
            "incident_owner": "Pilot operator",
        },
        "acceptance": {
            "operator": "Independent pilot operator",
            "scheduled_at": "2026-12-01T10:00:00+05:30",
        },
    }


def test_owner_decisions_accept_complete_non_secret_record() -> None:
    assert validate_owner_decisions(valid_owner_decisions()) == []


def test_owner_decisions_fail_closed_on_scope_and_missing_roles() -> None:
    decisions = valid_owner_decisions()
    scope = decisions["scope"]
    assert isinstance(scope, dict)
    scope["data_classification"] = "production"
    identity = decisions["identity"]
    assert isinstance(identity, dict)
    invited = identity["invited_identities"]
    assert isinstance(invited, list)
    identity["invited_identities"] = invited[:1]

    errors = validate_owner_decisions(decisions)

    assert "scope.data_classification must be synthetic-only" in errors
    assert any("missing roles" in error for error in errors)
    assert "identity.invited_identities must cover at least two synthetic tenants" in errors
