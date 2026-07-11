from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]

SECRET_FILE_SUFFIXES = (".mnemonic", ".seed", ".key")
GENERATED_FILE_SUFFIXES = (".pyc", ".pyo", ".log", ".db", ".sqlite")
GENERATED_PATH_PARTS = {"__pycache__", ".pytest_cache", ".venv", "htmlcov", "dist", "build"}
GENERATED_PATH_SUFFIXES = (".egg-info",)
ALLOWED_ENV_FILES = {".env.example", ".env.live.example", ".env.tiny-live.example"}
SCAN_SKIP_FILES = {".github/workflows/ci.yml", "scripts/repo_guard.py"}

QUOTED_SECRET_RE = re.compile(
    r"(?i)\b("
    r"mnemonic|private[_-]?key|secret[_-]?key|api[_-]?key|"
    r"access[_-]?token|algod[_-]?token|indexer[_-]?token"
    r")\b\s*[:=]\s*['\"]([^'\"]{16,})['\"]"
)
ENV_SECRET_RE = re.compile(
    r"(?i)^\s*("
    r".*mnemonic.*|.*private.*key.*|.*secret.*key.*|.*api.*key.*|"
    r".*access.*token.*|algod_token|indexer_token"
    r")\s*=\s*([A-Za-z0-9_./+=:-]{16,})\s*$"
)
ALLOWED_PLACEHOLDERS = {
    "changeme",
    "placeholder",
    "example",
    "pending",
    "review",
    "local",
    "mock",
    "your_value_here",
    "not-a-real-secret",
}


def tracked_files() -> list[str]:
    output = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    return [line.strip() for line in output.splitlines() if line.strip()]


def is_forbidden_secret_file(path: str) -> bool:
    posix = pathlib.PurePosixPath(path)
    lower = path.lower()
    name = posix.name.lower()
    if name == "secrets.json" or lower.endswith(SECRET_FILE_SUFFIXES):
        return True
    if name == ".env":
        return True
    if name.startswith(".env.") and name not in ALLOWED_ENV_FILES:
        return True
    return False


def is_generated_artifact(path: str) -> bool:
    posix = pathlib.PurePosixPath(path)
    lower = path.lower()
    if any(part.lower() in GENERATED_PATH_PARTS for part in posix.parts):
        return True
    if any(part.lower().endswith(GENERATED_PATH_SUFFIXES) for part in posix.parts):
        return True
    return lower.endswith(GENERATED_FILE_SUFFIXES)


def likely_secret_assignments(files: list[str]) -> list[str]:
    matches: list[str] = []
    for path in files:
        if path in SCAN_SKIP_FILES:
            continue
        full_path = ROOT / path
        try:
            text = full_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            match = QUOTED_SECRET_RE.search(line) or ENV_SECRET_RE.search(line)
            if not match:
                continue
            value = match.group(2).strip().strip("'\"")
            if value.lower() in ALLOWED_PLACEHOLDERS:
                continue
            matches.append(f"{path}:{line_number}")
    return matches


def run_checks() -> int:
    files = tracked_files()
    failures: list[tuple[str, list[str]]] = []

    secret_files = [path for path in files if is_forbidden_secret_file(path)]
    if secret_files:
        failures.append(("Forbidden secret-bearing files are committed", secret_files))

    generated_artifacts = [path for path in files if is_generated_artifact(path)]
    if generated_artifacts:
        failures.append(("Generated/runtime artifacts are committed", generated_artifacts))

    secret_values = likely_secret_assignments(files)
    if secret_values:
        failures.append(("Likely secret assignments were found", secret_values))

    if not failures:
        print("Repo guard passed: no forbidden secret files, generated artifacts, or likely secret assignments.")
        return 0

    for heading, paths in failures:
        print(f"{heading}:")
        for path in paths:
            print(f"- {path}")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run repository hygiene and secret-safety checks.")
    parser.parse_args()
    raise SystemExit(run_checks())


if __name__ == "__main__":
    main()
