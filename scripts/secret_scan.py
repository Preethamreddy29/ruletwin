from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

PATTERNS = (
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{50,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
SKIP_PARTS = {".git", ".venv", "node_modules", "dist", "coverage", "__pycache__"}
TEXT_SUFFIXES = {
    "",
    ".env",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True, slots=True)
class Finding:
    path: Path
    line: int
    pattern: str


def find_secrets(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in root.rglob("*"):
        if not path.is_file() or SKIP_PARTS.intersection(path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, start=1):
            for pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(Finding(path, number, pattern.pattern))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Reject common committed credential formats")
    parser.add_argument("path", nargs="?", default=".")
    args = parser.parse_args()
    findings = find_secrets(Path(args.path).resolve())
    for finding in findings:
        print(f"{finding.path}:{finding.line}: possible secret matching {finding.pattern}")
    if findings:
        print(f"Secret scan failed with {len(findings)} finding(s).")
        return 1
    print("Secret scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
