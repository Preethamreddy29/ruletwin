from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def test_runtime_containers_are_non_root() -> None:
    api = (ROOT / "apps/api/Dockerfile").read_text(encoding="utf-8")
    web = (ROOT / "apps/web/Dockerfile").read_text(encoding="utf-8")
    assert "USER 10001:10001" in api
    assert "USER 101:101" in web


def test_compose_uses_read_only_runtime_filesystems() -> None:
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    assert compose.count("read_only: true") >= 3
    assert compose.count('security_opt: ["no-new-privileges:true"]') >= 3
