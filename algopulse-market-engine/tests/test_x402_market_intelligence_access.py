from __future__ import annotations

import json
import time
from collections.abc import Iterator
from datetime import datetime
from datetime import timezone

from fastapi.testclient import TestClient

import algopulse.api as api_module
from algopulse.api import MOCK_X402_REPORT_PROOF
from algopulse.api import app
from algopulse.models import Asset
from algopulse.models import Opportunity
from algopulse.models import Pool
from algopulse.store import MarketStore


FRESH_ROUTE_HASH = "fresh-x402-executable-route"
EXECUTION_ARTIFACT_FRAGMENTS = (
    "signed_transaction",
    "signedtransaction",
    "signed_txn",
    "signedtxn",
    "signed_group",
    "submission_payload",
    "submitted_txid",
    "submitted_transaction",
    "hot_wallet",
    "hot wallet",
    "private_key",
    "privatekey",
    "mnemonic",
    "seed_phrase",
    "seed phrase",
    "wallet_mnemonic",
    "unsigned_group",
    "unsignedtxngroup",
)
RAW_ROUTE_KEYS = {
    "route",
    "routehash",
    "route_hash",
    "routejson",
    "route_json",
    "legs",
    "inputassetid",
    "input_asset_id",
    "outputassetid",
    "output_asset_id",
    "expectedoutput",
    "expected_output",
    "involvedpoolids",
    "involved_pool_ids",
    "involvedassetids",
    "involved_asset_ids",
}
SENSITIVE_METADATA_PATTERNS = (
    "mnemonic",
    "private",
    "secret",
    "key",
    "signature",
    "payment_payload",
    "paymentPayload",
    "paymentGroup",
    "authorization",
    "header",
    ".env",
    "AVM_PRIVATE_KEY",
    "ALGOPULSE_X402_PAYER_MNEMONIC",
    "seed",
    "signer",
    "wallet_secret",
)
SAFE_SENSITIVE_FLAG_KEYS = {"signerCodeTouched", "paymentPayloadLogged", "secretsPrinted"}
LABEL_ONLY_FIELDS = {
    "access",
    "accessTier",
    "delayed",
    "paymentUnlocks",
    "paymentUpgradeAvailable",
    "premium",
    "preview",
    "proofAccepted",
    "reportTier",
    "source",
    "upgradeResource",
}


def _client() -> TestClient:
    return TestClient(app)


def _walk_json(value: object, path: str = "$") -> Iterator[tuple[str, object]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_json(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_json(child, f"{path}[{index}]")


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _without_label_only_fields(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _without_label_only_fields(child)
            for key, child in value.items()
            if key not in LABEL_ONLY_FIELDS
        }
    if isinstance(value, list):
        return [_without_label_only_fields(child) for child in value]
    return value


def _normalize_for_sensitive_scan(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _assert_no_execution_artifacts(payload: object) -> None:
    serialized = json.dumps(payload, sort_keys=True).lower()
    for fragment in EXECUTION_ARTIFACT_FRAGMENTS:
        assert fragment not in serialized


def _assert_no_raw_route_payload(payload: object) -> None:
    for path, _value in _walk_json(payload):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0]
        normalized = key.replace("-", "_").lower()
        assert normalized not in RAW_ROUTE_KEYS, path


def _assert_no_sensitive_metadata(payload: object) -> None:
    normalized_patterns = {
        _normalize_for_sensitive_scan(pattern): pattern for pattern in SENSITIVE_METADATA_PATTERNS
    }
    for path, value in _walk_json(payload):
        if path != "$":
            key = path.rsplit(".", 1)[-1].split("[", 1)[0]
            if key not in SAFE_SENSITIVE_FLAG_KEYS:
                normalized_key = _normalize_for_sensitive_scan(key)
                for pattern, raw_pattern in normalized_patterns.items():
                    assert pattern not in normalized_key, f"{path} contains sensitive key pattern {raw_pattern}"
        if isinstance(value, str):
            normalized_value = _normalize_for_sensitive_scan(value)
            for pattern, raw_pattern in normalized_patterns.items():
                assert pattern not in normalized_value, f"{path} contains sensitive value pattern {raw_pattern}"


def _opportunity(created_at: float) -> Opportunity:
    return Opportunity(
        route_hash=FRESH_ROUTE_HASH,
        route=[
            {
                "venue": "tinyman",
                "pool_id": "tinyman:ALGO-USDC",
                "input_asset_id": 0,
                "output_asset_id": 31566704,
                "input_amount": 5.0,
                "expected_output": 1.1,
                "price_impact_bps": 12.0,
            },
            {
                "venue": "pact",
                "pool_id": "pact:USDC-ALGO",
                "input_asset_id": 31566704,
                "output_asset_id": 0,
                "input_amount": 1.1,
                "expected_output": 5.2,
                "price_impact_bps": 10.0,
            },
        ],
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=5.2,
        expected_net_profit=0.18,
        expected_profit_bps=360.0,
        max_price_impact_bps=12.0,
        involved_pool_ids=["tinyman:ALGO-USDC", "pact:USDC-ALGO"],
        involved_asset_ids=[0, 31566704],
        status="approved",
        skip_reason=None,
        confidence_score=80.0,
        risk_rules={"profit_bps_ok": True},
        created_at=created_at,
    )


def _seed_report_store(tmp_path, monkeypatch) -> str:
    store = MarketStore(tmp_path / "x402-market-pulse.db")
    store.initialize()
    now = time.time() - 60
    report_date = datetime.fromtimestamp(now, tz=timezone.utc).date().isoformat()
    store.upsert_assets([Asset(0, "ALGO", "Algorand", 6), Asset(31566704, "USDC", "USD Coin", 6)])
    store.record_pool_snapshots(
        [
            Pool(
                pool_id="tinyman:ALGO-USDC",
                venue_id="tinyman",
                app_id=1,
                asset_a_id=0,
                asset_b_id=31566704,
                reserve_a=100_000.0,
                reserve_b=20_000.0,
                fee_bps=30,
                block_round=100,
                captured_at=now - 20,
            )
        ]
    )
    store.record_opportunities([_opportunity(now)])
    store.record_service_health("market_scanner", "ok", detail="x402 readiness test", metrics={"opportunities": 1})
    monkeypatch.setattr(api_module, "store", store)
    return report_date


def test_x402_market_pulse_unpaid_request_returns_payment_required():
    response = _client().get("/api/x402/reports/market-pulse/daily")

    assert response.status_code == 402
    assert response.headers["x-algopulse-payment-required"] == "mock-x402-readiness"
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "X402_PAYMENT_REQUIRED"
    details = payload["error"]["details"]
    assert details["mode"] == "mock-testnet-readiness"
    assert details["acceptedProofHeader"] == "X-Algopulse-Mock-X402-Proof"
    assert details["acceptedProofValue"] == MOCK_X402_REPORT_PROOF
    payment_requirements = details["paymentRequirements"]
    assert payment_requirements["mode"] == "mock-testnet-readiness"
    assert payment_requirements["resource"] == "algopulse.market_pulse.daily.v0"
    assert payment_requirements["scheme"] == "mock-x402-readiness"
    assert payment_requirements["network"] == "algorand-testnet-readiness"
    assert payment_requirements["proofHeader"] == "X-Algopulse-Mock-X402-Proof"
    assert payment_requirements["settlement"] == "not-performed"
    assert details["paymentUnlocks"] == "delayed market intelligence report only"
    assert details["noCustody"] is True
    assert details["noSigning"] is True
    assert details["noSubmission"] is True
    assert details["liveExecutionTouched"] is False
    assert details["signerCodeTouched"] is False


def test_x402_market_pulse_rejects_wrong_mock_proof():
    response = _client().get(
        "/api/x402/reports/market-pulse/daily",
        headers={"X-Algopulse-Mock-X402-Proof": "wrong-proof"},
    )

    assert response.status_code == 402
    assert response.json()["error"]["code"] == "X402_PAYMENT_REQUIRED"


def test_x402_market_pulse_mock_paid_request_returns_redacted_report(tmp_path, monkeypatch):
    report_date = _seed_report_store(tmp_path, monkeypatch)

    response = _client().get(
        f"/api/x402/reports/market-pulse/daily?date={report_date}",
        headers={"X-Algopulse-Mock-X402-Proof": MOCK_X402_REPORT_PROOF},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    data = payload["data"]
    assert data["resource"] == "algopulse.market_pulse.daily.v0"
    assert data["mode"] == "mock-testnet-readiness"
    assert data["accessTier"] == "premium-delayed-intelligence"
    assert data["proofAccepted"] is True
    assert data["paymentUnlocks"] == "premium delayed market intelligence report"
    assert data["publicSafe"] is True
    assert data["liveExecutionTouched"] is False
    assert data["signerCodeTouched"] is False

    report = data["report"]
    assert report["reportTier"] == "premium-delayed-intelligence"
    assert report["premium"] is True
    assert report["access"] == "x402-paid"
    assert report["delayed"] is True
    assert report["publicSafe"] is True
    assert report["liveExecutionTouched"] is False
    assert report["signerCodeTouched"] is False
    assert {"topSpreads", "routePerformance"}.issubset(report["premiumSections"])
    assert report["exportMetadata"]["resource"] == "algopulse.market_pulse.daily.v0"
    assert report["redactionPolicy"]["custodyFields"] == "excluded"
    assert report["redactionPolicy"]["paymentMaterial"] == "excluded"
    assert report["redactionPolicy"]["freshExecutableRoutes"] is False
    assert {"marketSummary", "topPairs", "topSpreads", "opportunityCounts", "routePerformance"}.issubset(report)
    assert FRESH_ROUTE_HASH not in json.dumps(payload, sort_keys=True)
    _assert_no_raw_route_payload(report)
    _assert_no_execution_artifacts(payload)


def test_x402_paid_vs_public_content_divergence(tmp_path, monkeypatch):
    report_date = _seed_report_store(tmp_path, monkeypatch)
    client = _client()

    public_response = client.get(f"/api/reports/market/daily?date={report_date}")
    paid_response = client.get(
        f"/api/x402/reports/market-pulse/daily?date={report_date}",
        headers={"X-Algopulse-Mock-X402-Proof": MOCK_X402_REPORT_PROOF},
    )

    assert public_response.status_code == 200
    assert paid_response.status_code == 200
    public_data = public_response.json()["data"]
    paid_data = paid_response.json()["data"]
    paid_report = paid_data["report"]

    assert _canonical_json(public_data) != _canonical_json(paid_report)
    assert _canonical_json(_without_label_only_fields(public_data)) != _canonical_json(
        _without_label_only_fields(paid_report)
    )
    for shared_field in ("reportDate", "publicSafe", "liveExecutionTouched", "signerCodeTouched"):
        assert public_data[shared_field] == paid_report[shared_field]

    assert public_data["reportTier"] == "public-preview"
    assert public_data["preview"] is True
    assert public_data["paymentUpgradeAvailable"] is True
    assert public_data["upgradeResource"] == "algopulse.market_pulse.daily.v0"
    premium_only_fields = {
        "topSpreads",
        "liquidityChanges",
        "routePerformance",
        "paperTradePerformance",
        "riskEvents",
        "premiumSections",
        "exportMetadata",
        "redactionPolicy",
    }
    assert {"topSpreads", "routePerformance"}.issubset(public_data["excludedDetailSections"])
    assert premium_only_fields.isdisjoint(public_data)

    assert paid_data["accessTier"] == "premium-delayed-intelligence"
    assert paid_report["reportTier"] == "premium-delayed-intelligence"
    assert paid_report["premium"] is True
    assert {"topSpreads", "routePerformance", "premiumSections", "exportMetadata"}.issubset(paid_report)
    assert {"topSpreads", "routePerformance"}.issubset(paid_report["premiumSections"])
    assert paid_report != public_data

    assert paid_data["publicSafe"] is True
    assert paid_data["liveExecutionTouched"] is False
    assert paid_data["signerCodeTouched"] is False
    assert paid_report["publicSafe"] is True
    assert paid_report["liveExecutionTouched"] is False
    assert paid_report["signerCodeTouched"] is False
    assert FRESH_ROUTE_HASH not in json.dumps({"public": public_data, "paid": paid_data}, sort_keys=True)
    _assert_no_raw_route_payload(public_data)
    _assert_no_raw_route_payload(paid_report)
    _assert_no_execution_artifacts({"public": public_data, "paid": paid_data})


def test_x402_no_sensitive_keys_in_paid_payload(tmp_path, monkeypatch):
    report_date = _seed_report_store(tmp_path, monkeypatch)

    response = _client().get(
        f"/api/x402/reports/market-pulse/daily?date={report_date}",
        headers={"X-Algopulse-Mock-X402-Proof": MOCK_X402_REPORT_PROOF},
    )

    assert response.status_code == 200
    paid_payload = response.json()["data"]
    assert paid_payload["report"]["publicSafe"] is True
    assert paid_payload["report"]["liveExecutionTouched"] is False
    assert paid_payload["report"]["signerCodeTouched"] is False
    _assert_no_sensitive_metadata(paid_payload)
