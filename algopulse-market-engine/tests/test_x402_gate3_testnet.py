"""Gate 3 — x402 TestNet implementation tests.

Covers the offline-verifiable behaviors:
  - config loader fails closed (disabled / missing / placeholder / unconfirmed)
  - valid config converts price to base units
  - no configured values are logged on failure
  - the real middleware returns 402 when unpaid and for fake retry headers
  - mock mode still works and stays fail-closed
  - the module imports no signer/wallet/trading/execution code

The paid 200 path and settlement-failure 402 path require a real signed TestNet
payment (package-/client-owned payload + an operator wallet) and are exercised by
the operator smoke script, not here — see scripts/x402_gate3_smoke.py.
"""

from __future__ import annotations

import ast
import logging
import pathlib

from fastapi import FastAPI
from fastapi.testclient import TestClient

from algopulse import x402_testnet

ROUTE = "/api/x402/reports/market-pulse/daily"
RECEIVER = "CIVTUU6KLTYO26SPVEBDFBKP3UMZM2DPEO5RINODUVCI5NVIFC6HVNWS7E"

BASE_ENV = {
    "ALGOPULSE_X402_TESTNET_ENABLED": "true",
    "ALGOPULSE_X402_TESTNET_CONFIG_CONFIRMED": "true",
    "ALGOPULSE_X402_FACILITATOR_URL": "https://facilitator.goplausible.xyz",
    "ALGOPULSE_X402_NETWORK": "algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=",
    "ALGOPULSE_X402_ASSET_ID": "10458941",
    "ALGOPULSE_X402_ASSET_SYMBOL": "USDC",
    "ALGOPULSE_X402_ASSET_DECIMALS": "6",
    "ALGOPULSE_X402_AMOUNT": "$0.01",
    "ALGOPULSE_X402_RECEIVER": RECEIVER,
    "ALGOPULSE_X402_RESOURCE": "algopulse.market_pulse.daily.v0",
}


def _env(**overrides):
    env = dict(BASE_ENV)
    env.update(overrides)
    return env


# --- config loader: fail closed -------------------------------------------------

def test_disabled_by_default():
    assert x402_testnet.load_testnet_config({}) is None


def test_missing_required_fails_closed():
    env = _env()
    del env["ALGOPULSE_X402_RECEIVER"]
    assert x402_testnet.load_testnet_config(env) is None


def test_placeholder_fails_closed():
    assert x402_testnet.load_testnet_config(_env(ALGOPULSE_X402_RECEIVER="TESTNET_RECEIVER_PLACEHOLDER")) is None


def test_unconfirmed_fails_closed():
    assert x402_testnet.load_testnet_config(_env(ALGOPULSE_X402_TESTNET_CONFIG_CONFIRMED="false")) is None


def test_enabled_false_fails_closed():
    assert x402_testnet.load_testnet_config(_env(ALGOPULSE_X402_TESTNET_ENABLED="false")) is None


def test_enabled_confirmed_bad_config_fails_closed():
    evaluation = x402_testnet.evaluate_testnet_config(
        _env(ALGOPULSE_X402_NETWORK="algorand:wGHE2Pwdvd7S12BL5FaOP20EGYesN73ktiC1qzkkit8=")
    )

    assert evaluation.config is None
    assert evaluation.enabled is True
    assert evaluation.confirmed is True
    assert evaluation.fail_closed is True


def test_mainnet_network_rejected():
    evaluation = x402_testnet.evaluate_testnet_config(
        _env(ALGOPULSE_X402_NETWORK="algorand:wGHE2Pwdvd7S12BL5FaOP20EGYesN73ktiC1qzkkit8=")
    )

    assert "ALGOPULSE_X402_NETWORK:not-allowed" in evaluation.errors


def test_wrong_facilitator_rejected():
    evaluation = x402_testnet.evaluate_testnet_config(
        _env(ALGOPULSE_X402_FACILITATOR_URL="https://facilitator.example.invalid")
    )

    assert "ALGOPULSE_X402_FACILITATOR_URL:not-allowed" in evaluation.errors


def test_wrong_asset_id_rejected():
    evaluation = x402_testnet.evaluate_testnet_config(_env(ALGOPULSE_X402_ASSET_ID="31566704"))

    assert "ALGOPULSE_X402_ASSET_ID:not-allowed" in evaluation.errors


def test_wrong_asset_symbol_rejected():
    evaluation = x402_testnet.evaluate_testnet_config(_env(ALGOPULSE_X402_ASSET_SYMBOL="PNET"))

    assert "ALGOPULSE_X402_ASSET_SYMBOL:not-allowed" in evaluation.errors


def test_wrong_decimals_rejected():
    evaluation = x402_testnet.evaluate_testnet_config(_env(ALGOPULSE_X402_ASSET_DECIMALS="7"))

    assert "ALGOPULSE_X402_ASSET_DECIMALS:not-allowed" in evaluation.errors


def test_zero_and_negative_amount_rejected():
    zero = x402_testnet.evaluate_testnet_config(_env(ALGOPULSE_X402_AMOUNT="0"))
    negative = x402_testnet.evaluate_testnet_config(_env(ALGOPULSE_X402_AMOUNT="-0.01"))

    assert "ALGOPULSE_X402_AMOUNT:not-positive" in zero.errors
    assert "ALGOPULSE_X402_AMOUNT:not-positive" in negative.errors


def test_wrong_resource_rejected():
    evaluation = x402_testnet.evaluate_testnet_config(_env(ALGOPULSE_X402_RESOURCE="algopulse.other"))

    assert "ALGOPULSE_X402_RESOURCE:not-allowed" in evaluation.errors


# --- config loader: valid -------------------------------------------------------

def test_valid_config_converts_dollar_to_base_units():
    cfg = x402_testnet.load_testnet_config(_env())
    assert cfg is not None
    assert cfg.amount_base_units == "10000"
    assert cfg.asset_id == 10458941
    assert cfg.asset_decimals == 6
    assert cfg.receiver == RECEIVER


def test_valid_config_accepts_raw_base_units():
    cfg = x402_testnet.load_testnet_config(_env(ALGOPULSE_X402_AMOUNT="10000"))
    assert cfg is not None and cfg.amount_base_units == "10000"


# --- no-secret handling ---------------------------------------------------------

def test_failclosed_logs_no_configured_values(caplog):
    with caplog.at_level(logging.WARNING, logger="algopulse.x402"):
        x402_testnet.load_testnet_config(
            _env(ALGOPULSE_X402_TESTNET_CONFIG_CONFIRMED="false")
        )
    logged = " ".join(record.getMessage() for record in caplog.records)
    # Variable names / reasons may appear; configured VALUES must not.
    assert RECEIVER not in logged
    assert "10000" not in logged
    assert "SGO1GKSzyE7" not in logged


def test_status_summary_prints_no_values():
    summary = x402_testnet.status_summary(active=True)
    text = str(summary)
    assert RECEIVER not in text
    assert summary["valuesPrinted"] is False


# --- active middleware: negative paths (real package, offline) ------------------

def _active_app():
    app = FastAPI()

    @app.get(ROUTE)
    def handler():  # pragma: no cover - only reached after a verified payment
        return {"ok": True, "report": "delayed", "publicSafe": True}

    active = x402_testnet.attach_payment_middleware(app, env=_env())
    return app, active


def test_active_unpaid_returns_402():
    app, state = _active_app()
    assert state.active is True
    client = TestClient(app, raise_server_exceptions=False)
    assert client.get(ROUTE).status_code == 402


def test_active_fake_x_payment_stays_402():
    app, _ = _active_app()
    client = TestClient(app, raise_server_exceptions=False)
    assert client.get(ROUTE, headers={"X-PAYMENT": "not-a-real-payment"}).status_code == 402


def test_active_fake_payment_signature_stays_402():
    app, _ = _active_app()
    client = TestClient(app, raise_server_exceptions=False)
    assert client.get(ROUTE, headers={"PAYMENT-SIGNATURE": "not-a-real-signature"}).status_code == 402


def test_attach_fails_closed_when_invalid():
    app = FastAPI()
    assert x402_testnet.attach_payment_middleware(app, env={}).active is False
    state = x402_testnet.attach_payment_middleware(
        app, env=_env(ALGOPULSE_X402_RECEIVER="changeme")
    )
    assert state.active is False
    assert state.fail_closed is True


def test_attach_failure_sanitizes_logs_and_disables_mock(monkeypatch, caplog):
    def explode(_config):
        raise RuntimeError(
            "bad values "
            + RECEIVER
            + " "
            + BASE_ENV["ALGOPULSE_X402_NETWORK"]
            + " "
            + BASE_ENV["ALGOPULSE_X402_FACILITATOR_URL"]
        )

    monkeypatch.setattr(x402_testnet, "build_routes_and_server", explode)
    with caplog.at_level(logging.ERROR, logger="algopulse.x402"):
        state = x402_testnet.attach_payment_middleware(FastAPI(), env=_env())

    logged = " ".join(record.getMessage() for record in caplog.records)
    assert state.active is False
    assert state.fail_closed is True
    assert state.reason == "attach_failed"
    assert "RuntimeError" in logged
    assert RECEIVER not in logged
    assert BASE_ENV["ALGOPULSE_X402_NETWORK"] not in logged
    assert BASE_ENV["ALGOPULSE_X402_FACILITATOR_URL"] not in logged


# --- mock mode still works (default; fail-closed) -------------------------------

def test_mock_mode_unpaid_402_and_proof_200():
    from algopulse.api import app as real_app, MOCK_X402_REPORT_PROOF, X402_TESTNET_ACTIVE

    # Tests run with TestNet disabled => mock mode.
    assert X402_TESTNET_ACTIVE is False
    client = TestClient(real_app, raise_server_exceptions=False)

    assert client.get(ROUTE).status_code == 402

    paid = client.get(ROUTE, headers={"X-Algopulse-Mock-X402-Proof": MOCK_X402_REPORT_PROOF})
    assert paid.status_code == 200
    data = paid.json()["data"]
    assert data["mode"] == "mock-testnet-readiness"
    assert data["report"] is not None
    assert data["liveExecutionTouched"] is False
    assert data["signerCodeTouched"] is False


def test_api_failclosed_does_not_expose_mock_or_unlock(monkeypatch):
    import algopulse.api as api_module

    monkeypatch.setattr(api_module, "X402_TESTNET_ACTIVE", False)
    monkeypatch.setattr(api_module, "X402_TESTNET_FAIL_CLOSED", True)
    client = TestClient(api_module.app, raise_server_exceptions=False)

    unpaid = client.get(ROUTE)
    mock_paid = client.get(ROUTE, headers={"X-Algopulse-Mock-X402-Proof": api_module.MOCK_X402_REPORT_PROOF})

    assert unpaid.status_code == 503
    assert mock_paid.status_code == 503
    unpaid_text = unpaid.text
    paid_text = mock_paid.text
    assert "acceptedProofValue" not in unpaid_text
    assert api_module.MOCK_X402_REPORT_PROOF not in unpaid_text
    assert api_module.MOCK_X402_REPORT_PROOF not in paid_text
    assert unpaid.json()["error"]["code"] == "X402_TESTNET_UNAVAILABLE"


# --- guardrail: no signer/wallet/trading/execution imports ----------------------

def test_module_imports_nothing_forbidden():
    tree = ast.parse(pathlib.Path(x402_testnet.__file__).read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    joined = " ".join(modules).lower()
    for forbidden in ("signer", "wallet", "custody", "trading", "execution", "mnemonic", "submit"):
        assert forbidden not in joined, f"forbidden import substring: {forbidden}"
