from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.release_evidence import (
    Artifact,
    EvidenceError,
    build_manifest,
    parse_artifact,
    verify_manifest,
)

COMMIT = "a" * 40


def artifact(tmp_path: Path, name: str = "api-sbom") -> Artifact:
    path = tmp_path / f"{name}.json"
    path.write_text('{"evidence":true}\n', encoding="utf-8")
    return Artifact(name=name, path=path.resolve())


def test_build_and_verify_manifest(tmp_path: Path) -> None:
    first = artifact(tmp_path, "api-sbom")
    second = artifact(tmp_path, "web-scan")
    manifest_path = tmp_path / "manifest.json"

    manifest = build_manifest(
        version="0.4.0-pilot.preflight.1",
        commit=COMMIT,
        output=manifest_path,
        artifacts=[second, first],
    )

    assert [item["name"] for item in manifest["artifacts"]] == ["api-sbom", "web-scan"]
    assert verify_manifest(manifest_path) == manifest


@pytest.mark.parametrize("version", ["v0.4.0", "0.4.0-pilot.0", "0.4.1-pilot.1"])
def test_build_rejects_invalid_version(tmp_path: Path, version: str) -> None:
    with pytest.raises(EvidenceError, match="version"):
        build_manifest(
            version=version,
            commit=COMMIT,
            output=tmp_path / "manifest.json",
            artifacts=[artifact(tmp_path)],
        )


def test_build_rejects_duplicate_artifact(tmp_path: Path) -> None:
    item = artifact(tmp_path)
    with pytest.raises(EvidenceError, match="unique"):
        build_manifest(
            version="0.4.0-pilot.1",
            commit=COMMIT,
            output=tmp_path / "manifest.json",
            artifacts=[item, item],
        )


def test_verify_rejects_tampered_artifact(tmp_path: Path) -> None:
    item = artifact(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    build_manifest(
        version="0.4.0-pilot.preflight.2",
        commit=COMMIT,
        output=manifest_path,
        artifacts=[item],
    )
    item.path.write_text("tampered\n", encoding="utf-8")

    with pytest.raises(EvidenceError, match="checksum mismatch"):
        verify_manifest(manifest_path)


def test_verify_rejects_path_escape(tmp_path: Path) -> None:
    item = artifact(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    build_manifest(
        version="0.4.0-pilot.preflight.3",
        commit=COMMIT,
        output=manifest_path,
        artifacts=[item],
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"][0]["path"] = "../outside.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(EvidenceError, match="escapes"):
        verify_manifest(manifest_path)


def test_parse_artifact_requires_safe_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "report.json"
    path.write_text("{}", encoding="utf-8")
    assert parse_artifact(f"report={path}").name == "report"
    with pytest.raises(EvidenceError, match="safe"):
        parse_artifact(f"Unsafe Name={path}")
