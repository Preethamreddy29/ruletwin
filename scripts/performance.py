from __future__ import annotations

import argparse
import json
import math
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


class PerformanceError(RuntimeError):
    pass


def percentile_nearest_rank(values: list[float], percentile: float) -> float:
    if not values:
        raise ValueError("at least one sample is required")
    if not 0 < percentile <= 100:
        raise ValueError("percentile must be in (0, 100]")
    ordered = sorted(values)
    rank = max(1, math.ceil((percentile / 100) * len(ordered)))
    return ordered[rank - 1]


def _request_json(
    base_url: str,
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 120,
) -> dict[str, Any]:
    request_headers = {"Accept": "application/json", **(headers or {})}
    data = None
    if token:
        request_headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        request_headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(  # noqa: S310 - base URL is constrained by the caller
        f"{base_url.rstrip('/')}{path}", data=data, headers=request_headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise PerformanceError(
            f"{method} {path} failed with HTTP {error.code}: {detail}"
        ) from error
    except (OSError, TimeoutError, json.JSONDecodeError) as error:
        raise PerformanceError(f"{method} {path} failed: {error}") from error
    if not isinstance(payload, dict):
        raise PerformanceError(f"{method} {path} returned a non-object response")
    return payload


def _git_commit() -> str:
    configured = os.getenv("GITHUB_SHA")
    if configured:
        return configured
    git = shutil.which("git")
    if git is None:
        raise PerformanceError("git is required to bind the report to a commit")
    result = subprocess.run(  # noqa: S603 - executable is resolved from the trusted local PATH
        [git, "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def machine_profile(profile_name: str) -> dict[str, object]:
    profile: dict[str, object] = {
        "name": profile_name,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
        "python": platform.python_version(),
    }
    memory_path = Path("/proc/meminfo")
    if memory_path.is_file():
        first_line = memory_path.read_text(encoding="utf-8").splitlines()[0]
        profile["memory"] = first_line.partition(":")[2].strip()
    runner = {
        key: value
        for key in ("RUNNER_OS", "RUNNER_ARCH", "ImageOS", "ImageVersion", "GITHUB_RUN_ID")
        if (value := os.getenv(key))
    }
    if runner:
        profile["runner"] = runner
    return profile


def _wait_for_completion(
    base_url: str, token: str, simulation_id: str, *, timeout_seconds: float
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        simulation = _request_json(base_url, "GET", f"/v1/simulations/{simulation_id}", token=token)
        status = simulation.get("status")
        if status == "completed":
            return simulation
        if status == "failed":
            raise PerformanceError(f"simulation {simulation_id} failed")
        time.sleep(0.1)
    raise PerformanceError(f"simulation {simulation_id} exceeded {timeout_seconds:g}s")


def _create_dataset(
    base_url: str, token: str, scenario: dict[str, Any], *, seed: int, event_count: int
) -> dict[str, Any]:
    return _request_json(
        base_url,
        "POST",
        "/v1/replay-datasets",
        token=token,
        headers={"Idempotency-Key": f"performance-dataset-{seed}"},
        body={
            "tenant_id": scenario["tenant_id"],
            "seed": seed,
            "generator_version": scenario["generator_version"],
            "event_schema_version": scenario["event_schema_version"],
            "event_count": event_count,
        },
    )


def _create_candidate_rule(base_url: str, token: str, scenario: dict[str, Any]) -> dict[str, Any]:
    return _request_json(
        base_url,
        "POST",
        f"/v1/tenants/{scenario['tenant_id']}/rule-versions",
        token=token,
        headers={"Idempotency-Key": "performance-candidate-rule-v1"},
        body={
            "definition_id": scenario["rule_definition_id"],
            "family": "rounding",
            "effective_from": "2026-02-01",
            "timezone": "UTC",
            "rule": {"increment_minor_units": 5, "mode": "half_up"},
            "dependency_version_ids": [],
        },
    )


def _accept_simulation(
    base_url: str,
    token: str,
    scenario: dict[str, Any],
    *,
    candidate_id: str,
    dataset_id: str,
) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    simulation = _request_json(
        base_url,
        "POST",
        "/v1/simulations",
        token=token,
        headers={"Idempotency-Key": f"performance-simulation-{uuid.uuid4()}"},
        body={
            "tenant_id": scenario["tenant_id"],
            "baseline_rule_version_id": scenario["baseline_rule_version_id"],
            "candidate_rule_version_id": candidate_id,
            "dataset_manifest_id": dataset_id,
            "engine_version": scenario["engine_version"],
            "risk_policy_version_id": scenario["risk_policy_version_id"],
        },
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    return simulation, elapsed_ms


def run(args: argparse.Namespace) -> dict[str, object]:
    base_url = args.base_url.rstrip("/")
    token_response = _request_json(
        base_url,
        "POST",
        "/v1/dev/token",
        body={"identity_key": args.identity_key},
    )
    token = token_response.get("access_token")
    if not isinstance(token, str) or not token:
        raise PerformanceError("development token response did not contain an access token")
    scenarios = _request_json(base_url, "GET", "/v1/scenarios", token=token).get("items")
    if not isinstance(scenarios, list) or len(scenarios) != 1 or not isinstance(scenarios[0], dict):
        raise PerformanceError("expected exactly one tenant-scoped synthetic scenario")
    scenario = scenarios[0]
    candidate = _create_candidate_rule(base_url, token, scenario)
    candidate_id = str(candidate["id"])
    acceptance_dataset = _create_dataset(
        base_url, token, scenario, seed=args.acceptance_seed, event_count=1
    )
    replay_dataset = _create_dataset(
        base_url,
        token,
        scenario,
        seed=args.replay_seed,
        event_count=args.replay_events,
    )

    acceptance_ms: list[float] = []
    for _ in range(args.acceptance_samples):
        simulation, elapsed_ms = _accept_simulation(
            base_url,
            token,
            scenario,
            candidate_id=candidate_id,
            dataset_id=str(acceptance_dataset["id"]),
        )
        acceptance_ms.append(round(elapsed_ms, 3))
        _wait_for_completion(
            base_url,
            token,
            str(simulation["id"]),
            timeout_seconds=args.simulation_timeout_seconds,
        )

    replay_samples: list[dict[str, object]] = []
    for _ in range(args.replay_samples):
        started = time.perf_counter()
        simulation, acknowledgement_ms = _accept_simulation(
            base_url,
            token,
            scenario,
            candidate_id=candidate_id,
            dataset_id=str(replay_dataset["id"]),
        )
        completed = _wait_for_completion(
            base_url,
            token,
            str(simulation["id"]),
            timeout_seconds=args.simulation_timeout_seconds,
        )
        replay_samples.append(
            {
                "simulation_id": str(simulation["id"]),
                "acknowledgement_ms": round(acknowledgement_ms, 3),
                "end_to_end_ms": round((time.perf_counter() - started) * 1000, 3),
                "result_checksum": completed.get("result_checksum"),
            }
        )

    p95_ms = round(percentile_nearest_rank(acceptance_ms, 95), 3)
    checksums = {sample["result_checksum"] for sample in replay_samples}
    assertions = {
        "acceptance_p95_within_target": p95_ms <= args.acceptance_p95_target_ms,
        "replay_checksums_identical": len(checksums) == 1 and None not in checksums,
    }
    report: dict[str, object] = {
        "schema_version": "ruletwin-performance-evidence-v1",
        "measured_at": datetime.now(UTC).isoformat(),
        "commit": _git_commit(),
        "machine_profile": machine_profile(args.profile_name),
        "synthetic_profile": {
            "identity_key": args.identity_key,
            "tenant_id": scenario["tenant_id"],
            "acceptance_dataset": {
                "seed": args.acceptance_seed,
                "event_count": 1,
                "checksum": acceptance_dataset.get("checksum"),
            },
            "replay_dataset": {
                "seed": args.replay_seed,
                "event_count": args.replay_events,
                "checksum": replay_dataset.get("checksum"),
            },
        },
        "acceptance": {
            "sample_count": args.acceptance_samples,
            "target_p95_ms": args.acceptance_p95_target_ms,
            "p95_ms": p95_ms,
            "minimum_ms": min(acceptance_ms),
            "maximum_ms": max(acceptance_ms),
            "raw_ms": acceptance_ms,
        },
        "replay": {
            "sample_count": args.replay_samples,
            "event_count": args.replay_events,
            "samples": replay_samples,
        },
        "assertions": assertions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not all(assertions.values()):
        raise PerformanceError(f"performance gate failed: {assertions}")
    return report


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Measure RuleTwin's synthetic pilot profile")
    root.add_argument("--base-url", default="http://127.0.0.1:8000")
    root.add_argument("--identity-key", default="novabill-analyst")
    root.add_argument("--profile-name", default="local-reference")
    root.add_argument("--acceptance-samples", type=int, default=30)
    root.add_argument("--acceptance-p95-target-ms", type=float, default=750)
    root.add_argument("--acceptance-seed", type=int, default=910001)
    root.add_argument("--replay-events", type=int, default=10000)
    root.add_argument("--replay-samples", type=int, default=3)
    root.add_argument("--replay-seed", type=int, default=910002)
    root.add_argument("--simulation-timeout-seconds", type=float, default=120)
    root.add_argument("--output", type=Path, default=Path("artifacts/performance/report.json"))
    return root


def main() -> int:
    args = parser().parse_args()
    if args.acceptance_samples < 1 or args.replay_samples < 1:
        parser().error("sample counts must be positive")
    if not 1 <= args.replay_events <= 100000:
        parser().error("replay events must be between 1 and 100000")
    try:
        report = run(args)
    except PerformanceError as error:
        parser().error(str(error))
    acceptance = report["acceptance"]
    replay = report["replay"]
    assert isinstance(acceptance, dict) and isinstance(replay, dict)
    print(
        f"acceptance_p95_ms={acceptance['p95_ms']} "
        f"replay_samples={replay['sample_count']} replay_events={replay['event_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
