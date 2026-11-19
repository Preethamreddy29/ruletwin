from scripts.resource_safety import _compose_prefix


def test_compose_prefix_uses_default_environment(monkeypatch) -> None:
    monkeypatch.delenv("RULETWIN_COMPOSE_ENV_FILE", raising=False)

    assert _compose_prefix("docker") == ["docker", "compose", "--profile", "core"]


def test_compose_prefix_supports_explicit_environment_file(monkeypatch) -> None:
    monkeypatch.setenv("RULETWIN_COMPOSE_ENV_FILE", "C:/RuleTwin/.env")

    assert _compose_prefix("docker") == [
        "docker",
        "compose",
        "--env-file",
        "C:/RuleTwin/.env",
        "--profile",
        "core",
    ]
