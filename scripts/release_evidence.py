from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

PRODUCT = "RuleTwin"
SCHEMA_VERSION = 1
VERSION_PATTERN = re.compile(r"^0\.4\.0-pilot\.(?:preflight\.)?[1-9][0-9]*$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
ARTIFACT_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class EvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class Artifact:
    name: str
    path: Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_artifact(value: str) -> Artifact:
    name, separator, raw_path = value.partition("=")
    if not separator or not ARTIFACT_NAME_PATTERN.fullmatch(name):
        raise EvidenceError("artifact must use a safe name=path value")
    path = Path(raw_path).resolve()
    if not path.is_file() or path.is_symlink():
        raise EvidenceError(f"artifact is not a regular file: {raw_path}")
    return Artifact(name=name, path=path)


def build_manifest(
    *, version: str, commit: str, output: Path, artifacts: Sequence[Artifact]
) -> dict[str, object]:
    if not VERSION_PATTERN.fullmatch(version):
        raise EvidenceError("version must match 0.4.0-pilot.N or 0.4.0-pilot.preflight.N")
    if not COMMIT_PATTERN.fullmatch(commit):
        raise EvidenceError("commit must be a lowercase 40-character Git SHA")
    if not artifacts:
        raise EvidenceError("at least one artifact is required")

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    names: set[str] = set()
    paths: set[Path] = set()
    records: list[dict[str, object]] = []
    for artifact in sorted(artifacts, key=lambda item: item.name):
        if artifact.name in names or artifact.path in paths:
            raise EvidenceError("artifact names and paths must be unique")
        names.add(artifact.name)
        paths.add(artifact.path)
        try:
            relative_path = artifact.path.relative_to(output.parent)
        except ValueError as error:
            raise EvidenceError("artifacts must be stored beside or below the manifest") from error
        records.append(
            {
                "name": artifact.name,
                "path": relative_path.as_posix(),
                "sha256": sha256_file(artifact.path),
                "size_bytes": artifact.path.stat().st_size,
            }
        )

    manifest: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "product": PRODUCT,
        "version": version,
        "commit": commit,
        "artifacts": records,
    }
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def verify_manifest(path: Path) -> dict[str, object]:
    path = path.resolve()
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EvidenceError(f"manifest cannot be read: {error}") from error
    if not isinstance(manifest, dict):
        raise EvidenceError("manifest root must be an object")
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("product") != PRODUCT:
        raise EvidenceError("manifest schema or product is unsupported")
    version = manifest.get("version")
    commit = manifest.get("commit")
    if not isinstance(version, str) or not VERSION_PATTERN.fullmatch(version):
        raise EvidenceError("manifest version is invalid")
    if not isinstance(commit, str) or not COMMIT_PATTERN.fullmatch(commit):
        raise EvidenceError("manifest commit is invalid")
    records = manifest.get("artifacts")
    if not isinstance(records, list) or not records:
        raise EvidenceError("manifest must contain artifacts")

    names: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise EvidenceError("artifact record must be an object")
        name = record.get("name")
        relative_path = record.get("path")
        expected_hash = record.get("sha256")
        expected_size = record.get("size_bytes")
        if not isinstance(name, str) or not ARTIFACT_NAME_PATTERN.fullmatch(name) or name in names:
            raise EvidenceError("artifact name is invalid or duplicated")
        names.add(name)
        if not isinstance(relative_path, str):
            raise EvidenceError("artifact path is invalid")
        artifact_path = (path.parent / relative_path).resolve()
        try:
            artifact_path.relative_to(path.parent)
        except ValueError as error:
            raise EvidenceError("artifact path escapes the evidence directory") from error
        if not artifact_path.is_file() or artifact_path.is_symlink():
            raise EvidenceError(f"artifact is missing: {relative_path}")
        if (
            artifact_path.stat().st_size != expected_size
            or sha256_file(artifact_path) != expected_hash
        ):
            raise EvidenceError(f"artifact checksum mismatch: {relative_path}")
    return manifest


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Build and verify RuleTwin release evidence")
    commands = root.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build-manifest")
    build.add_argument("--version", required=True)
    build.add_argument("--commit", required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--artifact", action="append", default=[], type=parse_artifact)
    verify = commands.add_parser("verify-manifest")
    verify.add_argument("--manifest", type=Path, required=True)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "build-manifest":
            build_manifest(
                version=args.version,
                commit=args.commit,
                output=args.output,
                artifacts=args.artifact,
            )
        else:
            verify_manifest(args.manifest)
    except EvidenceError as error:
        parser().error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
