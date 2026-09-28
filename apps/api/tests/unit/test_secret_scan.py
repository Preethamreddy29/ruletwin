from pathlib import Path

from scripts.secret_scan import find_secrets


def test_secret_scanner_rejects_controlled_fixture(tmp_path: Path) -> None:
    planted = "gh" + "p_" + ("A" * 36)
    fixture = tmp_path / "controlled-fixture.txt"
    fixture.write_text(f"token={planted}\n", encoding="utf-8")
    findings = find_secrets(tmp_path)
    assert len(findings) == 1
    assert findings[0].path == fixture


def test_secret_scanner_accepts_normal_configuration_names(tmp_path: Path) -> None:
    fixture = tmp_path / ".env.example"
    fixture.write_text("POSTGRES_PASSWORD=\nRULETWIN_DATABASE_URL=\n", encoding="utf-8")
    assert find_secrets(tmp_path) == []
