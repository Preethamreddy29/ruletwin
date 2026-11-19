from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg


class ResourceSafetyError(RuntimeError):
    pass


def _request(
    base_url: str,
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    request_headers = {"Accept": "application/json", **(headers or {})}
    if token:
        request_headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        request_headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(  # noqa: S310 - caller constrains the local base URL
        f"{base_url.rstrip('/')}{path}", data=data, headers=request_headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as decode_error:
            raise ResourceSafetyError(
                f"{method} {path} returned unreadable HTTP {error.code}"
            ) from decode_error
        if not isinstance(payload, dict):
            raise ResourceSafetyError(
                f"{method} {path} returned a non-object HTTP error"
            ) from error
        return error.code, payload


def _expect(status: int, expected: int, payload: dict[str, Any], label: str) -> dict[str, Any]:
    if status != expected:
        raise ResourceSafetyError(f"{label} expected HTTP {expected}, received {status}: {payload}")
    return payload


def _compose(*arguments: str) -> None:
    docker = shutil.which("docker")
    if docker is None:
        raise ResourceSafetyError("docker is required")
    subprocess.run(  # noqa: S603 - resolved trusted executable and fixed arguments
        [*_compose_prefix(docker), *arguments], check=True
    )


def _compose_prefix(docker: str) -> list[str]:
    command = [docker, "compose"]
    if env_file := os.getenv("RULETWIN_COMPOSE_ENV_FILE"):
        command.extend(["--env-file", env_file])
    command.extend(["--profile", "core"])
    return command


def _wait_for_simulations(
    base_url: str, token: str, simulation_ids: list[str], *, timeout_seconds: float
) -> list[dict[str, Any]]:
    pending = set(simulation_ids)
    results: dict[str, dict[str, Any]] = {}
    deadline = time.monotonic() + timeout_seconds
    while pending and time.monotonic() < deadline:
        for simulation_id in list(pending):
            status, payload = _request(
                base_url, "GET", f"/v1/simulations/{simulation_id}", token=token
            )
            _expect(status, 200, payload, "simulation read")
            state = payload.get("status")
            if state == "failed":
                raise ResourceSafetyError(f"simulation {simulation_id} failed")
            if state == "completed":
                results[simulation_id] = payload
                pending.remove(simulation_id)
        if pending:
            time.sleep(0.1)
    if pending:
        raise ResourceSafetyError(f"simulations did not drain: {sorted(pending)}")
    return [results[simulation_id] for simulation_id in simulation_ids]


def _container_stats() -> list[dict[str, object]]:
    docker = shutil.which("docker")
    if docker is None:
        raise ResourceSafetyError("docker is required")
    ids = subprocess.run(  # noqa: S603
        [*_compose_prefix(docker), "ps", "-q", "api", "worker"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    if not ids:
        raise ResourceSafetyError("API and worker containers are not running")
    result = subprocess.run(  # noqa: S603
        [docker, "stats", "--no-stream", "--format", "{{json .}}", *ids],
        check=True,
        capture_output=True,
        text=True,
    )
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def _git_commit() -> str:
    if configured := os.getenv("GITHUB_SHA"):
        return configured
    git = shutil.which("git")
    if git is None:
        raise ResourceSafetyError("git is required")
    return subprocess.run(  # noqa: S603
        [git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def run(args: argparse.Namespace) -> dict[str, object]:
    run_id = uuid.uuid4().hex
    token_status, token_payload = _request(
        args.base_url, "POST", "/v1/dev/token", body={"identity_key": "novabill-analyst"}
    )
    token = str(_expect(token_status, 200, token_payload, "development token")["access_token"])
    scenario_status, scenario_payload = _request(args.base_url, "GET", "/v1/scenarios", token=token)
    scenario = _expect(scenario_status, 200, scenario_payload, "scenario")["items"][0]
    candidate_status, candidate = _request(
        args.base_url,
        "POST",
        f"/v1/tenants/{scenario['tenant_id']}/rule-versions",
        token=token,
        headers={"Idempotency-Key": f"resource-rule-{run_id}"},
        body={
            "definition_id": scenario["rule_definition_id"],
            "family": "rounding",
            "effective_from": "2026-11-19",
            "timezone": "UTC",
            "rule": {"increment_minor_units": 7, "mode": "half_up"},
            "dependency_version_ids": [],
        },
    )
    _expect(candidate_status, 201, candidate, "candidate rule")

    def simulation_body() -> dict[str, object]:
        return {
            "tenant_id": scenario["tenant_id"],
            "baseline_rule_version_id": scenario["baseline_rule_version_id"],
            "candidate_rule_version_id": candidate["id"],
            "dataset_manifest_id": scenario["dataset_manifest_id"],
            "engine_version": scenario["engine_version"],
            "risk_policy_version_id": scenario["risk_policy_version_id"],
        }

    _compose("stop", "worker")
    try:
        saturation_started = time.perf_counter()
        simulations: list[dict[str, Any]] = []
        keys: list[str] = []
        for index in range(args.saturation_limit):
            key = f"resource-saturation-{run_id}-{index}"
            status, payload = _request(
                args.base_url,
                "POST",
                "/v1/simulations",
                token=token,
                headers={"Idempotency-Key": key},
                body=simulation_body(),
            )
            simulations.append(_expect(status, 202, payload, "saturation admission"))
            keys.append(key)
        rejected_status, rejected = _request(
            args.base_url,
            "POST",
            "/v1/simulations",
            token=token,
            headers={"Idempotency-Key": f"resource-saturation-{run_id}-rejected"},
            body=simulation_body(),
        )
        _expect(rejected_status, 429, rejected, "saturation rejection")
        if rejected.get("code") != "queue-capacity-exceeded":
            raise ResourceSafetyError(f"unexpected saturation response: {rejected}")
        retry_status, retry = _request(
            args.base_url,
            "POST",
            "/v1/simulations",
            token=token,
            headers={"Idempotency-Key": keys[0]},
            body=simulation_body(),
        )
        _expect(retry_status, 202, retry, "idempotent saturated retry")
        if retry["id"] != simulations[0]["id"]:
            raise ResourceSafetyError("idempotent retry changed the simulation identifier")
        _compose("start", "worker")
        completed = _wait_for_simulations(
            args.base_url,
            token,
            [str(item["id"]) for item in simulations],
            timeout_seconds=args.drain_timeout_seconds,
        )
        saturation_seconds = time.perf_counter() - saturation_started

        _compose("stop", "worker")
        timeout_key = f"resource-timeout-{run_id}"
        timeout_status, timeout_simulation = _request(
            args.base_url,
            "POST",
            "/v1/simulations",
            token=token,
            headers={"Idempotency-Key": timeout_key},
            body=simulation_body(),
        )
        _expect(timeout_status, 202, timeout_simulation, "timeout simulation")
        timeout_id = str(timeout_simulation["id"])
        timeout_observed = False
        with psycopg.connect(args.database_url) as lock_connection:
            lock_connection.execute(
                "SELECT id FROM simulations WHERE id=%s FOR UPDATE", (timeout_id,)
            )
            _compose("start", "worker")
            deadline = time.monotonic() + args.timeout_observation_seconds
            while time.monotonic() < deadline:
                with psycopg.connect(args.database_url) as observation:
                    row = observation.execute(
                        "SELECT attempts, last_error FROM outbox_events WHERE aggregate_id=%s",
                        (timeout_id,),
                    ).fetchone()
                if row and int(row[0]) >= 1 and row[1] == "TimeoutError":
                    timeout_observed = True
                    break
                time.sleep(0.1)
            if not timeout_observed:
                raise ResourceSafetyError(
                    "worker timeout was not recorded while the row lock was held"
                )
        recovered = _wait_for_simulations(
            args.base_url, token, [timeout_id], timeout_seconds=args.drain_timeout_seconds
        )[0]
        with psycopg.connect(args.database_url) as evidence:
            retry_row = evidence.execute(
                "SELECT attempts, status, last_error FROM outbox_events WHERE aggregate_id=%s",
                (timeout_id,),
            ).fetchone()
        if retry_row is None or int(retry_row[0]) < 2 or retry_row[1] != "processed":
            raise ResourceSafetyError(f"timeout recovery evidence is incomplete: {retry_row}")

        return {
            "schema_version": "ruletwin-resource-safety-v1",
            "recorded_at": datetime.now(UTC).isoformat(),
            "commit": _git_commit(),
            "profile": {
                "name": args.profile_name,
                "platform": platform.platform(),
                "logical_cpu_count": os.cpu_count(),
            },
            "saturation": {
                "configured_limit": args.saturation_limit,
                "accepted": len(simulations),
                "rejected_code": rejected["code"],
                "idempotent_retry_preserved_id": True,
                "drained_completed": len(completed),
                "elapsed_seconds": round(saturation_seconds, 3),
                "result_checksums": sorted({str(item["result_checksum"]) for item in completed}),
            },
            "timeout_recovery": {
                "simulation_id": timeout_id,
                "timeout_error_recorded": timeout_observed,
                "attempts": int(retry_row[0]),
                "final_outbox_status": retry_row[1],
                "final_simulation_status": recovered["status"],
                "result_checksum": recovered["result_checksum"],
            },
            "container_stats": _container_stats(),
        }
    finally:
        _compose("start", "worker")


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture RuleTwin pilot resource-safety evidence")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--database-url", default=os.getenv("RULETWIN_RESOURCE_DATABASE_URL"))
    parser.add_argument(
        "--compose-env-file",
        type=Path,
        default=os.getenv("RULETWIN_COMPOSE_ENV_FILE"),
        help="Optional environment file used by Docker Compose",
    )
    parser.add_argument("--profile-name", required=True)
    parser.add_argument("--saturation-limit", type=int, default=5)
    parser.add_argument("--drain-timeout-seconds", type=float, default=120)
    parser.add_argument("--timeout-observation-seconds", type=float, default=15)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.database_url:
        parser.error("--database-url or RULETWIN_RESOURCE_DATABASE_URL is required")
    if args.saturation_limit < 1:
        parser.error("--saturation-limit must be positive")
    if args.compose_env_file:
        os.environ["RULETWIN_COMPOSE_ENV_FILE"] = str(args.compose_env_file.resolve())
    report = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
