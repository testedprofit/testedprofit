from __future__ import annotations

import json
import time
from collections.abc import Iterator
from datetime import datetime
from datetime import timezone

from fastapi.testclient import TestClient

import algopulse.api as api_module
from algopulse.api import app
from algopulse.models import Asset
from algopulse.models import Opportunity
from algopulse.models import Pool
from algopulse.store import MarketStore


FRESH_MARKET_ROUTE_HASH = "fresh-report-executable-route"
PAPER_ROUTE_HASH = "paper-report-summary-route"
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


def _assert_no_execution_artifacts(payload: object | str) -> None:
    serialized = payload.lower() if isinstance(payload, str) else json.dumps(payload, sort_keys=True).lower()
    for fragment in EXECUTION_ARTIFACT_FRAGMENTS:
        assert fragment not in serialized


def _assert_no_fresh_route_identity(payload: object | str) -> None:
    serialized = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True)
    assert FRESH_MARKET_ROUTE_HASH not in serialized


def _assert_no_raw_route_payload(payload: object) -> None:
    for path, _value in _walk_json(payload):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0]
        normalized = key.replace("-", "_").lower()
        assert normalized not in RAW_ROUTE_KEYS, path


def _opportunity(route_hash: str, created_at: float, expected_net_profit: float) -> Opportunity:
    return Opportunity(
        route_hash=route_hash,
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
        expected_net_profit=expected_net_profit,
        expected_profit_bps=expected_net_profit / 5.0 * 10_000,
        max_price_impact_bps=12.0,
        involved_pool_ids=["tinyman:ALGO-USDC", "pact:USDC-ALGO"],
        involved_asset_ids=[0, 31566704],
        status="rejected",
        skip_reason="profit_bps_ok",
        confidence_score=80.0,
        risk_rules={"profit_bps_ok": False},
        created_at=created_at,
    )


def _seed_report_store(tmp_path, monkeypatch) -> str:
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    now = time.time() - 60
    report_date = datetime.fromtimestamp(now, tz=timezone.utc).date().isoformat()
    opportunity = _opportunity(FRESH_MARKET_ROUTE_HASH, now, expected_net_profit=0.18)
    paper_opportunity = _opportunity(PAPER_ROUTE_HASH, now - 30, expected_net_profit=0.08)

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
            ),
            Pool(
                pool_id="tinyman:ALGO-USDC",
                venue_id="tinyman",
                app_id=1,
                asset_a_id=0,
                asset_b_id=31566704,
                reserve_a=110_000.0,
                reserve_b=21_000.0,
                fee_bps=30,
                block_round=101,
                captured_at=now - 5,
            ),
        ]
    )
    store.record_opportunities([opportunity, paper_opportunity])
    store.record_paper_trade(paper_opportunity, would_execute=False, notes="report safety summary")
    store.record_service_health("market_scanner", "ok", detail="report safety test", metrics={"opportunities": 2})
    monkeypatch.setattr(api_module, "store", store)
    return report_date


def test_public_paper_daily_report_is_aggregate_and_has_no_execution_artifacts(tmp_path, monkeypatch):
    _seed_report_store(tmp_path, monkeypatch)

    response = _client().get("/api/reports/paper/daily")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    report = payload["data"]
    assert {
        "candidates",
        "wouldExecute",
        "checked30s",
        "completionRate30s",
        "skipReasons",
        "bestRoute",
    }.issubset(report)
    assert "route" not in (report["bestRoute"] or {})
    assert "legs" not in (report["bestRoute"] or {})
    _assert_no_execution_artifacts(payload)


def test_public_market_report_json_and_archive_are_research_safe(tmp_path, monkeypatch):
    report_date = _seed_report_store(tmp_path, monkeypatch)
    client = _client()

    daily = client.get(f"/api/reports/market/daily?date={report_date}")
    archive = client.get("/api/reports/market/archive?limit=3")

    assert daily.status_code == 200
    assert archive.status_code == 200
    daily_payload = daily.json()
    archive_payload = archive.json()
    assert daily_payload["ok"] is True
    assert archive_payload["ok"] is True
    assert daily_payload["data"]["publicSafe"] is True
    assert archive_payload["data"]["publicSafe"] is True
    assert daily_payload["data"]["liveExecutionTouched"] is False
    assert daily_payload["data"]["signerCodeTouched"] is False
    assert daily_payload["data"]["reportTier"] == "public-preview"
    assert daily_payload["data"]["preview"] is True
    assert daily_payload["data"]["paymentUpgradeAvailable"] is True
    assert archive_payload["data"]["liveExecutionTouched"] is False
    assert archive_payload["data"]["signerCodeTouched"] is False
    assert daily_payload["data"]["marketContextRibbon"]["title"] == "External cached market context"
    assert daily_payload["data"]["marketContextRibbon"]["symbol"] == "ALGO"
    assert daily_payload["data"]["marketContextRibbon"]["availability"] == "unavailable"
    assert daily_payload["data"]["marketContextRibbon"]["sourceLabel"] == "CoinMarketCap cached context"
    assert {"marketSummary", "topPairs", "opportunityCounts", "scannerHealth"}.issubset(daily_payload["data"])
    assert "topSpreads" not in daily_payload["data"]
    assert "routePerformance" not in daily_payload["data"]
    assert {"topSpreads", "routePerformance"}.issubset(daily_payload["data"]["excludedDetailSections"])
    _assert_no_raw_route_payload(daily_payload["data"])
    _assert_no_raw_route_payload(archive_payload["data"])
    _assert_no_fresh_route_identity(daily_payload)
    _assert_no_fresh_route_identity(archive_payload)
    _assert_no_execution_artifacts(daily_payload)
    _assert_no_execution_artifacts(archive_payload)
    assert "CMC_API_KEY" not in json.dumps({"daily": daily_payload, "archive": archive_payload}, sort_keys=True)


def test_public_market_report_exports_are_research_safe(tmp_path, monkeypatch):
    report_date = _seed_report_store(tmp_path, monkeypatch)
    client = _client()

    json_export = client.get(f"/api/reports/market/daily/export?date={report_date}&format=json")
    markdown_export = client.get(f"/api/reports/market/daily/export?date={report_date}&format=markdown")

    assert json_export.status_code == 200
    assert markdown_export.status_code == 200
    assert markdown_export.headers["content-type"].startswith("text/markdown")
    json_payload = json_export.json()
    assert json_payload["publicSafe"] is True
    assert json_payload["liveExecutionTouched"] is False
    assert json_payload["signerCodeTouched"] is False
    assert "## Market Summary" in markdown_export.text
    assert "market intelligence only" in markdown_export.text
    _assert_no_raw_route_payload(json_payload)
    _assert_no_fresh_route_identity(json_payload)
    _assert_no_fresh_route_identity(markdown_export.text)
    _assert_no_execution_artifacts(json_payload)
    _assert_no_execution_artifacts(markdown_export.text)
