from pathlib import Path

from scripts.pilot import IMAGE_KEYS, PUBLIC_KEYS, sha256_file, validate_release_environment


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
