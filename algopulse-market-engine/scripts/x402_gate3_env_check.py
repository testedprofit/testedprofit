from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Mapping


REQUIRED_VARS = (
    "ALGOPULSE_X402_TESTNET_ENABLED",
    "ALGOPULSE_X402_FACILITATOR_URL",
    "ALGOPULSE_X402_NETWORK",
    "ALGOPULSE_X402_ASSET_ID",
    "ALGOPULSE_X402_ASSET_SYMBOL",
    "ALGOPULSE_X402_ASSET_DECIMALS",
    "ALGOPULSE_X402_AMOUNT",
    "ALGOPULSE_X402_RECEIVER",
    "ALGOPULSE_X402_RESOURCE",
)
CONFIRMATION_VAR = "ALGOPULSE_X402_TESTNET_CONFIG_CONFIRMED"

PLACEHOLDER_MARKERS = (
    "placeholder",
    "replace",
    "todo",
    "changeme",
    "example",
    "dummy",
    "mock",
    "fake",
    "do_not_commit",
    "<",
    ">",
)


@dataclass(frozen=True)
class EnvCheck:
    name: str
    status: str


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Gate 3 x402 TestNet env readiness without printing values, "
            "connecting to any network, importing wallet/signer modules, or submitting payments."
        )
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable sanitized output.")
    args = parser.parse_args()

    result = evaluate_env(os.environ)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_text(result)
    return 0 if result["ok"] else 1


def evaluate_env(env: Mapping[str, str]) -> dict[str, object]:
    checks = [_check_var(env, name) for name in REQUIRED_VARS]
    errors: list[str] = []

    missing = [check.name for check in checks if check.status == "missing"]
    placeholders = [check.name for check in checks if check.status == "placeholder"]
    if missing:
        errors.append("Missing required Gate 3 env names: " + ", ".join(missing))
    if placeholders:
        errors.append("Placeholder-like Gate 3 env names must be replaced before TestNet: " + ", ".join(placeholders))

    enabled = _normalized(env.get("ALGOPULSE_X402_TESTNET_ENABLED", ""))
    if enabled != "true":
        errors.append("ALGOPULSE_X402_TESTNET_ENABLED must be explicitly true for Gate 3 TestNet readiness.")

    confirmation = _normalized(env.get(CONFIRMATION_VAR, ""))
    real_looking_values = all(check.status == "set" for check in checks)
    if real_looking_values and confirmation != "true":
        errors.append(
            f"{CONFIRMATION_VAR}=true is required before real-looking TestNet values are accepted."
        )

    return {
        "ok": not errors,
        "checks": [{"name": check.name, "status": check.status} for check in checks],
        "confirmation": "set" if confirmation == "true" else "missing_or_false",
        "errors": errors,
        "networkAccess": False,
        "paymentSubmitted": False,
        "walletOrSignerImported": False,
        "valuesPrinted": False,
    }


def _check_var(env: Mapping[str, str], name: str) -> EnvCheck:
    raw = env.get(name)
    if raw is None or not raw.strip():
        return EnvCheck(name, "missing")
    if _is_placeholder(raw):
        return EnvCheck(name, "placeholder")
    return EnvCheck(name, "set")


def _is_placeholder(value: str) -> bool:
    normalized = _normalized(value)
    return any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def _normalized(value: str) -> str:
    return value.strip().lower()


def _print_text(result: dict[str, object]) -> None:
    status = "passed" if result["ok"] else "failed"
    print(f"x402 Gate 3 env check {status}")
    for check in result["checks"]:
        assert isinstance(check, dict)
        print(f"- {check['name']}: {check['status']}")
    errors = result.get("errors") or []
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    print("- network access: not attempted")
    print("- payment submission: not attempted")
    print("- wallet/signer imports: not attempted")
    print("- configured values: not printed")


if __name__ == "__main__":
    raise SystemExit(main())
