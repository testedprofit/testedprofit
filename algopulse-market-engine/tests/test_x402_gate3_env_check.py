from __future__ import annotations

import json
import os
import subprocess
import sys

from scripts.x402_gate3_env_check import CONFIRMATION_VAR
from scripts.x402_gate3_env_check import REQUIRED_VARS
from scripts.x402_gate3_env_check import evaluate_env


def _ready_env() -> dict[str, str]:
    return {
        "ALGOPULSE_X402_TESTNET_ENABLED": "true",
        "ALGOPULSE_X402_FACILITATOR_URL": "https://facilitator.goplausible.xyz",
        "ALGOPULSE_X402_NETWORK": "algorand-testnet-network-id",
        "ALGOPULSE_X402_ASSET_ID": "10458941",
        "ALGOPULSE_X402_ASSET_SYMBOL": "USDC",
        "ALGOPULSE_X402_ASSET_DECIMALS": "6",
        "ALGOPULSE_X402_AMOUNT": "1000",
        "ALGOPULSE_X402_RECEIVER": "TESTNETRECEIVERADDRESSVALUEWITHOUTSENSITIVEVALUES",
        "ALGOPULSE_X402_RESOURCE": "algopulse.market_pulse.daily.v0",
        CONFIRMATION_VAR: "true",
    }


def test_gate3_env_check_fails_closed_when_missing_values():
    result = evaluate_env({})

    assert result["ok"] is False
    statuses = {check["name"]: check["status"] for check in result["checks"]}
    assert set(statuses) == set(REQUIRED_VARS)
    assert all(status == "missing" for status in statuses.values())
    assert result["networkAccess"] is False
    assert result["paymentSubmitted"] is False
    assert result["walletOrSignerImported"] is False
    assert result["valuesPrinted"] is False


def test_gate3_env_check_rejects_placeholders():
    env = {name: "PLACEHOLDER" for name in REQUIRED_VARS}
    env["ALGOPULSE_X402_TESTNET_ENABLED"] = "true"
    env[CONFIRMATION_VAR] = "true"

    result = evaluate_env(env)

    assert result["ok"] is False
    statuses = {check["name"]: check["status"] for check in result["checks"]}
    assert statuses["ALGOPULSE_X402_RECEIVER"] == "placeholder"
    assert statuses["ALGOPULSE_X402_FACILITATOR_URL"] == "placeholder"


def test_gate3_env_check_requires_confirmation_for_real_looking_values():
    env = _ready_env()
    env.pop(CONFIRMATION_VAR)

    result = evaluate_env(env)

    assert result["ok"] is False
    assert any(CONFIRMATION_VAR in error for error in result["errors"])


def test_gate3_env_check_accepts_confirmed_real_looking_values():
    result = evaluate_env(_ready_env())

    assert result["ok"] is True
    assert result["errors"] == []
    assert all(check["status"] == "set" for check in result["checks"])


def test_gate3_env_check_cli_json_does_not_print_values():
    env = {**os.environ, **_ready_env()}
    sentinel_receiver = "DO_NOT_PRINT_THIS_TESTNET_RECEIVER_VALUE"
    env["ALGOPULSE_X402_RECEIVER"] = sentinel_receiver
    completed = subprocess.run(
        [sys.executable, "scripts/x402_gate3_env_check.py", "--json"],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert sentinel_receiver not in completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["valuesPrinted"] is False
