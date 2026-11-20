from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import ssl
import subprocess
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

IMAGE_PATTERN = re.compile(r"^[^\s]+@sha256:[0-9a-f]{64}$")
IMAGE_KEYS = (
    "RULETWIN_API_IMAGE",
    "RULETWIN_WEB_IMAGE",
    "RULETWIN_POSTGRES_IMAGE",
    "RULETWIN_PROMETHEUS_IMAGE",
    "RULETWIN_GATEWAY_IMAGE",
)
FILE_KEYS = (
    "RULETWIN_POSTGRES_ADMIN_PASSWORD_SECRET_FILE",
    "RULETWIN_POSTGRES_APP_PASSWORD_SECRET_FILE",
    "RULETWIN_ADMIN_DATABASE_URL_SECRET_FILE",
    "RULETWIN_APP_DATABASE_URL_SECRET_FILE",
    "RULETWIN_TLS_CERT_FILE",
    "RULETWIN_TLS_KEY_FILE",
)
PUBLIC_KEYS = (
    "RULETWIN_RELEASE_VERSION",
    "RULETWIN_HOSTNAME",
    "RULETWIN_BASE_URL",
    "RULETWIN_OIDC_ISSUER",
    "RULETWIN_OIDC_AUDIENCE",
    "RULETWIN_OIDC_JWKS_URL",
)

REQUIRED_PILOT_ROLES = {
    "analyst",
    "qa_reviewer",
    "release_approver",
    "auditor",
}
PLACEHOLDER_VALUES = {"", "pending", "required", "tbd", "todo", "unknown"}

FINGERPRINT_SQL = """
SELECT jsonb_build_object(
  'migration', (SELECT version_num FROM alembic_version LIMIT 1),
  'counts', jsonb_build_object(
    'tenants', (SELECT count(*) FROM tenants),
    'users', (SELECT count(*) FROM users),
    'memberships', (SELECT count(*) FROM user_tenant_roles),
    'rule_versions', (SELECT count(*) FROM rule_versions),
    'datasets', (SELECT count(*) FROM dataset_manifests),
    'business_events', (SELECT count(*) FROM business_events),
    'simulations', (SELECT count(*) FROM simulations),
    'simulation_runs', (SELECT count(*) FROM simulation_runs),
    'impact_deltas', (SELECT count(*) FROM impact_deltas),
    'risk_evaluations', (SELECT count(*) FROM risk_evaluations),
    'approvals', (SELECT count(*) FROM approvals),
    'release_gates', (SELECT count(*) FROM release_gates),
    'audit_events', (SELECT count(*) FROM audit_events),
    'outbox_events', (SELECT count(*) FROM outbox_events)
  ),
  'checksums', jsonb_build_object(
    'rules', (SELECT coalesce(
      md5(string_agg(checksum, '|' ORDER BY checksum)), md5('')) FROM rule_versions),
    'datasets', (SELECT coalesce(
      md5(string_agg(checksum, '|' ORDER BY checksum)), md5('')) FROM dataset_manifests),
    'impact', (SELECT coalesce(
      md5(string_agg(checksum, '|' ORDER BY checksum)), md5('')) FROM impact_deltas),
    'risk', (SELECT coalesce(
      md5(string_agg(checksum, '|' ORDER BY checksum)), md5('')) FROM risk_evaluations),
    'gates', (SELECT coalesce(
      md5(string_agg(evidence_checksum, '|' ORDER BY evidence_checksum)), md5(''))
      FROM release_gates)
  )
)::text;
""".strip()


def utc_now() -> datetime:
    return datetime.now(UTC)


def load_env_file(path: Path | None) -> dict[str, str]:
    values = dict(os.environ)
    if path is None:
        return values
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        values.setdefault(name.strip(), value.strip())
    return values


def validate_release_environment(values: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for key in PUBLIC_KEYS + IMAGE_KEYS + FILE_KEYS:
        if not values.get(key, "").strip():
            errors.append(f"{key} is required")
    for key in IMAGE_KEYS:
        value = values.get(key, "")
        if value and not IMAGE_PATTERN.fullmatch(value):
            errors.append(f"{key} must use an immutable @sha256 digest")
    for key in ("RULETWIN_BASE_URL", "RULETWIN_OIDC_ISSUER", "RULETWIN_OIDC_JWKS_URL"):
        value = values.get(key, "")
        if value and not value.startswith("https://"):
            errors.append(f"{key} must use HTTPS")
    for key in FILE_KEYS:
        raw_path = values.get(key, "")
        if not raw_path:
            continue
        path = Path(raw_path)
        if not path.is_absolute():
            errors.append(f"{key} must be an absolute path")
        elif not path.is_file():
            errors.append(f"{key} does not reference a readable file")
        elif path.stat().st_size == 0:
            errors.append(f"{key} references an empty file")
    return errors


def load_owner_decisions(path: Path) -> dict[str, Any]:
    decisions = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(decisions, dict):
        raise ValueError("owner decisions must be a JSON object")
    return decisions


def _decision_value(decisions: dict[str, Any], path: str) -> Any:
    value: Any = decisions
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _is_decided(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return value.strip().lower() not in PLACEHOLDER_VALUES


def validate_owner_decisions(decisions: dict[str, Any]) -> list[str]:
    """Validate non-secret owner inputs required before a hosted pilot can start."""
    errors: list[str] = []
    if decisions.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    required_strings = (
        "hosting.provider",
        "hosting.region",
        "hosting.budget_owner",
        "hosting.operator",
        "domain.hostname",
        "domain.tls_owner",
        "identity.provider",
        "identity.tenant",
        "identity.client_id",
        "identity.api_audience",
        "identity.tenant_claim",
        "identity.owner",
        "secrets.provider",
        "secrets.access_identity",
        "secrets.owner",
        "recovery.backup_storage",
        "recovery.owner",
        "operations.support_window",
        "operations.alert_receiver",
        "operations.incident_owner",
        "acceptance.operator",
        "acceptance.scheduled_at",
    )
    for path in required_strings:
        if not _is_decided(_decision_value(decisions, path)):
            errors.append(f"{path} requires an owner decision")

    if _decision_value(decisions, "scope.data_classification") != "synthetic-only":
        errors.append("scope.data_classification must be synthetic-only")
    if _decision_value(decisions, "scope.access_model") != "invitation-only":
        errors.append("scope.access_model must be invitation-only")
    if _decision_value(decisions, "scope.hosted_visibility") not in {"private", "unlisted"}:
        errors.append("scope.hosted_visibility must be private or unlisted")
    if _decision_value(decisions, "identity.provider") != "Auth0":
        errors.append("identity.provider must remain Auth0 for the implemented pilot integration")

    hostname = _decision_value(decisions, "domain.hostname")
    if _is_decided(hostname) and "://" in hostname:
        errors.append("domain.hostname must be a hostname, not a URL")
    for path in ("identity.api_audience", "identity.tenant_claim"):
        value = _decision_value(decisions, path)
        if _is_decided(value) and not value.startswith("https://"):
            errors.append(f"{path} must use an HTTPS namespace")

    for path in ("recovery.retention_days", "recovery.rpo_minutes", "recovery.rto_minutes"):
        value = _decision_value(decisions, path)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"{path} must be a positive integer")

    identities = _decision_value(decisions, "identity.invited_identities")
    if not isinstance(identities, list) or not identities:
        errors.append("identity.invited_identities must contain the invitation-only pilot users")
    else:
        subjects: set[str] = set()
        roles: set[str] = set()
        tenants: set[str] = set()
        for index, identity in enumerate(identities):
            if not isinstance(identity, dict):
                errors.append(f"identity.invited_identities[{index}] must be an object")
                continue
            for field in ("subject", "tenant", "role"):
                if not _is_decided(identity.get(field)):
                    errors.append(f"identity.invited_identities[{index}].{field} requires a value")
            subject = identity.get("subject")
            role = identity.get("role")
            tenant = identity.get("tenant")
            if isinstance(subject, str) and subject:
                if subject in subjects:
                    errors.append(f"identity subject {subject!r} is duplicated")
                subjects.add(subject)
            if isinstance(role, str):
                roles.add(role)
            if isinstance(tenant, str) and tenant:
                tenants.add(tenant)
        missing_roles = sorted(REQUIRED_PILOT_ROLES - roles)
        if missing_roles:
            errors.append(
                "identity.invited_identities is missing roles: " + ", ".join(missing_roles)
            )
        if len(tenants) < 2:
            errors.append("identity.invited_identities must cover at least two synthetic tenants")
    return errors


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class PilotRuntime:
    def __init__(
        self,
        *,
        repository: Path,
        compose_file: Path,
        env_file: Path | None,
        database: str,
        user: str,
    ) -> None:
        self.repository = repository
        self.compose_file = compose_file
        self.env_file = env_file
        self.database = database
        self.user = user

    def compose(self, *arguments: str, capture: bool = False) -> str:
        command = ["docker", "compose"]
        if self.env_file is not None:
            command.extend(("--env-file", str(self.env_file)))
        command.extend(("-f", str(self.compose_file), *arguments))
        result = subprocess.run(  # noqa: S603
            command,
            cwd=self.repository,
            check=True,
            text=True,
            capture_output=capture,
        )
        return result.stdout.strip() if capture else ""

    def postgres(self, *arguments: str, input_bytes: bytes | None = None) -> bytes:
        command = ["docker", "compose"]
        if self.env_file is not None:
            command.extend(("--env-file", str(self.env_file)))
        command.extend(("-f", str(self.compose_file), "exec", "-T", "postgres", *arguments))
        result = subprocess.run(  # noqa: S603
            command,
            cwd=self.repository,
            check=True,
            input=input_bytes,
            capture_output=True,
        )
        return result.stdout

    def fingerprint(self, database: str | None = None) -> dict[str, Any]:
        output = self.postgres(
            "psql",
            "--username",
            self.user,
            "--dbname",
            database or self.database,
            "--tuples-only",
            "--no-align",
            "--command",
            FINGERPRINT_SQL,
        )
        return json.loads(output.decode("utf-8").strip())


def create_backup(runtime: PilotRuntime, output_directory: Path) -> tuple[Path, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    timestamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    backup_path = output_directory / f"ruletwin-{timestamp}.dump"
    started = time.perf_counter()
    dump = runtime.postgres(
        "pg_dump",
        "--username",
        runtime.user,
        "--dbname",
        runtime.database,
        "--format=custom",
        "--no-owner",
        "--no-privileges",
    )
    backup_path.write_bytes(dump)
    manifest = {
        "schema_version": 1,
        "created_at": utc_now().isoformat(),
        "source_database": runtime.database,
        "backup_file": backup_path.name,
        "backup_sha256": sha256_file(backup_path),
        "backup_bytes": backup_path.stat().st_size,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            cwd=runtime.repository,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip(),
        "fingerprint": runtime.fingerprint(),
    }
    manifest_path = backup_path.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return backup_path, manifest_path


def rehearse_restore(
    runtime: PilotRuntime,
    backup_path: Path,
    manifest_path: Path,
    output_directory: Path,
    *,
    restart_worker: bool,
) -> Path:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("backup_sha256") != sha256_file(backup_path):
        raise ValueError("backup checksum does not match its manifest")
    restore_database = f"ruletwin_restore_{secrets.token_hex(6)}"
    started = time.perf_counter()
    created = False
    try:
        runtime.postgres("createdb", "--username", runtime.user, restore_database)
        created = True
        runtime.postgres(
            "pg_restore",
            "--username",
            runtime.user,
            "--dbname",
            restore_database,
            "--exit-on-error",
            "--no-owner",
            "--no-privileges",
            input_bytes=backup_path.read_bytes(),
        )
        restored_fingerprint = runtime.fingerprint(restore_database)
        if restored_fingerprint != manifest.get("fingerprint"):
            raise ValueError("restored database fingerprint does not match the source")
        worker_restart = "not-requested"
        if restart_worker:
            runtime.compose("restart", "worker")
            services = runtime.compose("ps", "--status", "running", "--services", capture=True)
            if "worker" not in services.splitlines():
                raise RuntimeError("worker did not return to the running state")
            worker_restart = "passed"
        created_at = datetime.fromisoformat(str(manifest["created_at"]))
        result = {
            "schema_version": 1,
            "completed_at": utc_now().isoformat(),
            "backup_sha256": manifest["backup_sha256"],
            "source_fingerprint": manifest["fingerprint"],
            "restored_fingerprint": restored_fingerprint,
            "fingerprint_match": True,
            "restore_duration_seconds": round(time.perf_counter() - started, 3),
            "observed_rpo_seconds": round((utc_now() - created_at).total_seconds(), 3),
            "worker_restart": worker_restart,
            "temporary_database_removed": True,
        }
    finally:
        if created:
            runtime.postgres(
                "dropdb",
                "--username",
                runtime.user,
                "--force",
                restore_database,
            )
    output_directory.mkdir(parents=True, exist_ok=True)
    result_path = (
        output_directory / f"restore-rehearsal-{utc_now().strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result_path


def smoke_https(base_url: str, ca_file: Path | None) -> dict[str, int]:
    context = ssl.create_default_context(cafile=str(ca_file) if ca_file else None)
    results: dict[str, int] = {}
    for path in ("/", "/api/health/live", "/api/health/ready", "/api/version"):
        with urllib.request.urlopen(  # noqa: S310
            f"{base_url.rstrip('/')}{path}", context=context, timeout=10
        ) as response:
            results[path] = response.status
    return results


def deployment_record(
    runtime: PilotRuntime,
    values: dict[str, str],
    output_directory: Path,
    ca_file: Path | None,
) -> Path:
    errors = validate_release_environment(values)
    if errors:
        raise ValueError("; ".join(errors))
    runtime.compose("config", "--quiet")
    services = runtime.compose("ps", "--format", "json", capture=True)
    record = {
        "schema_version": 1,
        "recorded_at": utc_now().isoformat(),
        "release_version": values["RULETWIN_RELEASE_VERSION"],
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            cwd=runtime.repository,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip(),
        "images": {key: values[key] for key in IMAGE_KEYS},
        "migration": runtime.fingerprint()["migration"],
        "smoke": smoke_https(values["RULETWIN_BASE_URL"], ca_file),
        "compose_services": [json.loads(line) for line in services.splitlines() if line],
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    path = output_directory / f"deployment-{utc_now().strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and rehearse RuleTwin pilot operations")
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--compose-file", type=Path, default=Path("deploy/pilot/compose.yaml"))
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--database", default="ruletwin")
    parser.add_argument("--user", default="ruletwin_admin")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-config")
    decisions = subparsers.add_parser("validate-owner-decisions")
    decisions.add_argument("--decisions-file", type=Path, required=True)
    backup = subparsers.add_parser("backup")
    backup.add_argument("--output", type=Path, default=Path("artifacts/backups"))
    restore = subparsers.add_parser("restore-rehearsal")
    restore.add_argument("--backup", type=Path, required=True)
    restore.add_argument("--manifest", type=Path, required=True)
    restore.add_argument("--output", type=Path, default=Path("artifacts/recovery"))
    restore.add_argument("--restart-worker", action="store_true")
    record = subparsers.add_parser("deployment-record")
    record.add_argument("--output", type=Path, default=Path("artifacts/releases"))
    record.add_argument("--ca-file", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repository = args.repository.resolve()
    compose_file = (repository / args.compose_file).resolve()
    env_file = (repository / args.env_file).resolve() if args.env_file else None
    values = load_env_file(env_file)
    runtime = PilotRuntime(
        repository=repository,
        compose_file=compose_file,
        env_file=env_file,
        database=args.database,
        user=args.user,
    )
    if args.command == "validate-config":
        errors = validate_release_environment(values)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        runtime.compose("config", "--quiet")
        print("Pilot configuration is valid; no secret values were displayed.")
        return 0
    if args.command == "validate-owner-decisions":
        decisions_path = (repository / args.decisions_file).resolve()
        try:
            decisions = load_owner_decisions(decisions_path)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 1
        errors = validate_owner_decisions(decisions)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print("Pilot owner decisions are complete; no secret values were displayed.")
        return 0
    if args.command == "backup":
        backup, manifest = create_backup(runtime, (repository / args.output).resolve())
        print(f"Backup created: {backup}")
        print(f"Manifest created: {manifest}")
        return 0
    if args.command == "restore-rehearsal":
        result = rehearse_restore(
            runtime,
            (repository / args.backup).resolve(),
            (repository / args.manifest).resolve(),
            (repository / args.output).resolve(),
            restart_worker=args.restart_worker,
        )
        print(f"Restore rehearsal passed: {result}")
        return 0
    if args.command == "deployment-record":
        result = deployment_record(
            runtime,
            values,
            (repository / args.output).resolve(),
            (repository / args.ca_file).resolve() if args.ca_file else None,
        )
        print(f"Deployment record created: {result}")
        return 0
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())
