from __future__ import annotations

import json
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import algopulse.api as api_module
from algopulse.api import app
from algopulse.models import Opportunity
from algopulse.store import MarketStore


CONTRACT_PATH = Path("docs/PUBLIC_RECORD_REDACTION_CONTRACT.md")
REQUIRED_RECORD_TYPES = {
    "paper_trade_report",
    "market_daily_report",
    "market_archive_report",
    "live_trade_receipt",
    "reconciliation_record",
    "pnet_fee_payment",
    "refund_case",
    "failed_trade",
    "execution_queue_item",
    "route_detail",
    "dry_run_summary",
    "admin_audit_event",
}
REQUIRED_CLASSIFICATIONS = {
    "public",
    "delayed_public",
    "user_owned",
    "admin_only",
    "redacted",
    "never_expose",
}
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "signed_transaction",
    "signed_txn",
    "signed_group",
    "submission_payload",
    "submitted_txid",
    "hot_wallet",
    "private_key",
    "mnemonic",
    "seed_phrase",
    "execution_queue",
    "signer_secret",
)
RAW_ROUTE_KEYS = {
    "route",
    "route_hash",
    "route_json",
    "input_asset_id",
    "output_asset_id",
    "expected_output",
    "involved_pool_ids",
    "involved_asset_ids",
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


def _assert_no_forbidden_public_fragments(payload: object | str) -> None:
    serialized = payload.lower() if isinstance(payload, str) else json.dumps(payload, sort_keys=True).lower()
    for fragment in FORBIDDEN_PUBLIC_FRAGMENTS:
        assert fragment not in serialized


def _assert_no_raw_route_payload(payload: object) -> None:
    for path, _value in _walk_json(payload):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0]
        assert key.replace("-", "_").lower() not in RAW_ROUTE_KEYS, path


def _opportunity(created_at: float) -> Opportunity:
    return Opportunity(
        route_hash="contract-fresh-route",
        route=[
            {
                "venue": "tinyman",
                "pool_id": "tinyman:ALGO-USDC",
                "input_asset_id": 0,
                "output_asset_id": 31566704,
                "input_amount": 5.0,
                "expected_output": 1.0,
            },
            {
                "venue": "pact",
                "pool_id": "pact:USDC-ALGO",
                "input_asset_id": 31566704,
                "output_asset_id": 0,
                "input_amount": 1.0,
                "expected_output": 5.2,
            },
        ],
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=5.2,
        expected_net_profit=0.18,
        expected_profit_bps=360.0,
        max_price_impact_bps=20.0,
        involved_pool_ids=["tinyman:ALGO-USDC", "pact:USDC-ALGO"],
        involved_asset_ids=[0, 31566704],
        status="rejected",
        skip_reason="profit_bps_ok",
        created_at=created_at,
    )


def _seed_contract_store(tmp_path, monkeypatch) -> None:
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    now = time.time() - 60
    opportunity = _opportunity(now)
    store.record_opportunities([opportunity])
    store.record_paper_trade(opportunity, would_execute=False, notes="contract report summary")
    store.record_service_health("market_scanner", "ok", detail="contract safety test", metrics={"opportunities": 1})
    monkeypatch.setattr(api_module, "store", store)


def test_redaction_contract_lists_required_record_types_and_classifications():
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    for record_type in REQUIRED_RECORD_TYPES:
        assert f"| {record_type} |" in contract
    for classification in REQUIRED_CLASSIFICATIONS:
        assert f"`{classification}`" in contract or f"| {classification} |" in contract
    assert "Any field not listed in this contract is `never_expose`" in contract


def test_current_public_report_outputs_follow_contract_basics(tmp_path, monkeypatch):
    _seed_contract_store(tmp_path, monkeypatch)
    client = _client()

    paper_report = client.get("/api/reports/paper/daily")
    market_report = client.get("/api/reports/market/daily")
    archive = client.get("/api/reports/market/archive?limit=3")
    markdown_export = client.get("/api/reports/market/daily/export?format=markdown")

    assert paper_report.status_code == 200
    assert market_report.status_code == 200
    assert archive.status_code == 200
    assert markdown_export.status_code == 200
    assert market_report.json()["data"]["publicSafe"] is True
    assert market_report.json()["data"]["liveExecutionTouched"] is False
    assert market_report.json()["data"]["signerCodeTouched"] is False
    assert archive.json()["data"]["publicSafe"] is True
    assert "market intelligence only" in markdown_export.text
    for payload in (paper_report.json(), market_report.json(), archive.json(), markdown_export.text):
        _assert_no_forbidden_public_fragments(payload)
    _assert_no_raw_route_payload(market_report.json()["data"])
    _assert_no_raw_route_payload(archive.json()["data"])


def test_central_redaction_helper_exists_for_all_record_types():
    from algopulse.public_record_redaction import PUBLIC_RECORD_REDACTION_CONTRACT
    from algopulse.public_record_redaction import redact_public_record

    for record_type in REQUIRED_RECORD_TYPES:
        assert record_type in PUBLIC_RECORD_REDACTION_CONTRACT
        assert redact_public_record({}, record_type) is not None


def test_redaction_helper_removes_report_execution_and_raw_route_artifacts():
    from algopulse.public_record_redaction import assert_public_safe
    from algopulse.public_record_redaction import redact_public_record

    report = {
        "reportDate": "2026-06-24",
        "publicSafe": True,
        "marketSummary": {"headline": "Stored aggregate market intelligence"},
        "marketContextRibbon": {
            "title": "External cached market context",
            "symbol": "ALGO",
            "change24hPct": -1.2,
            "contextLabel": "neutral",
            "snapshotAgeSeconds": 900,
            "snapshotAgeLabel": "15m old",
            "sourceLabel": "CoinMarketCap cached context",
            "availability": "available",
            "cached": True,
            "external": True,
            "scope": "internal/dev/research delayed report context only",
            "notice": "External cached market context only. Informational only; not investment or trading advice.",
            "BTC": "never public",
            "CMC_API_KEY": "never public",
        },
        "pnetLiquidityWatchlist": {
            "assetId": 3169177585,
            "symbol": "PNET",
            "poolCount": 1,
            "totalPnetReserve": 4200000,
            "source": "pool_snapshots",
            "listedWithoutOpportunity": True,
            "publicSafe": True,
            "notice": "PNET pool visibility is informational only; it is not investment advice, ROI guidance, or a request to trade.",
            "lpRiskNotice": "Adding liquidity can lose value through price movement, fees, and impermanent loss.",
            "pools": [
                {
                    "poolId": "pact:ALGO-PNET",
                    "venue": "pact",
                    "appId": 42,
                    "pairLabel": "ALGO/PNET",
                    "pnetAssetId": 3169177585,
                    "otherAssetId": 0,
                    "otherSymbol": "ALGO",
                    "pnetReserve": 4200000,
                    "otherReserve": 1200,
                    "liquidityEstimate": 70992,
                    "liquidityChangePct": 0,
                    "feeBps": 30,
                    "snapshotCount": 1,
                    "firstSeenAt": 1,
                    "lastSeenAt": 1,
                    "opportunityRequired": False,
                    "lpVisibilityNote": "Observed PNET liquidity surface; LP participation has risk and needs independent review.",
                    "route_json": [{"venue": "tinyman"}],
                }
            ],
        },
        "scannerHealth": {"latestDetail": "operator note private_key=never-public"},
        "surpriseInternalField": "unknown fields default to never_expose",
        "topSpreads": [
            {
                "pairLabel": "ALGO/USDC",
                "expectedProfitBps": 12.5,
                "adminPolicy": "never public",
                "route_hash": "fresh-route-hash",
                "route_json": [{"venue": "tinyman"}],
                "signed_transaction": "never-public",
                "submission_payload": {"tx": "never-public"},
            }
        ],
        "markdown": "# internal export body",
    }

    redacted = redact_public_record(report, "market_daily_report")

    assert redacted["reportDate"] == "2026-06-24"
    assert redacted["marketContextRibbon"]["symbol"] == "ALGO"
    assert redacted["marketContextRibbon"]["sourceLabel"] == "CoinMarketCap cached context"
    assert "BTC" not in redacted["marketContextRibbon"]
    assert "CMC_API_KEY" not in redacted["marketContextRibbon"]
    assert redacted["pnetLiquidityWatchlist"]["symbol"] == "PNET"
    assert redacted["pnetLiquidityWatchlist"]["listedWithoutOpportunity"] is True
    assert redacted["pnetLiquidityWatchlist"]["pools"][0]["pairLabel"] == "ALGO/PNET"
    assert "route_json" not in redacted["pnetLiquidityWatchlist"]["pools"][0]
    assert redacted["topSpreads"][0]["pairLabel"] == "ALGO/USDC"
    assert redacted["scannerHealth"]["latestDetail"] == "[redacted]"
    _assert_no_raw_route_payload(redacted)
    _assert_no_forbidden_public_fragments(redacted)
    assert "markdown" not in redacted
    assert "surpriseInternalField" not in redacted
    assert "adminPolicy" not in redacted["topSpreads"][0]
    assert_public_safe(redacted, "market_daily_report")


def test_assert_public_safe_rejects_unknown_public_report_fields():
    from algopulse.public_record_redaction import assert_public_safe

    unsafe_report = {
        "reportDate": "2026-06-24",
        "publicSafe": True,
        "marketSummary": {"headline": "Stored aggregate market intelligence"},
        "raw_route_json": [{"venue": "tinyman"}],
    }

    with pytest.raises(AssertionError, match="contains non-public fields"):
        assert_public_safe(unsafe_report, "market_daily_report")


def test_sensitive_record_redaction_helper_blocks_records_pending_human_review():
    from algopulse.public_record_redaction import redact_public_record

    redacted = redact_public_record(
        {
            "txid": "payment-txid",
            "sender": "USER",
            "receiver": "FEE_RECEIVER",
            "private_key": "never-public",
        },
        "pnet_fee_payment",
    )

    assert redacted == {
        "recordType": "pnet_fee_payment",
        "publicSafe": False,
        "redactionStatus": "blocked_pending_human_review",
    }
    _assert_no_forbidden_public_fragments(redacted)


@pytest.mark.xfail(
    reason="Sensitive record routes are awaiting human-approved public/admin/user-owned exposure policy.",
    strict=False,
)
@pytest.mark.parametrize(
    "path",
    [
        "/api/live-trades",
        "/api/reconciliations",
        "/api/payment-verifications",
        "/api/refund-cases",
    ],
)
def test_future_sensitive_record_routes_are_not_globally_public(path: str):
    response = _client().get(path)

    assert response.status_code in {401, 403}
