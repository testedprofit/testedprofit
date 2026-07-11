import json

from algopulse.market_report import build_daily_market_intelligence_report
from algopulse.market_report import render_market_intelligence_markdown


def _opportunity(route_hash: str, created_at: float, expected_profit_bps: float = 120.0) -> dict:
    return {
        "route_hash": route_hash,
        "route": [
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
                "pool_id": "pact:ALGO-USDC",
                "input_asset_id": 31566704,
                "output_asset_id": 0,
                "input_amount": 1.1,
                "expected_output": 5.12,
                "price_impact_bps": 10.0,
            },
        ],
        "input_asset_id": 0,
        "input_amount": 5.0,
        "expected_final_amount": 5.12,
        "gross_profit": 0.12,
        "estimated_network_fee": 0.006,
        "total_dex_fees": 0.018,
        "total_price_impact_bps": 22.0,
        "slippage_buffer": 0.02,
        "expected_net_profit": 0.094,
        "expected_profit_bps": expected_profit_bps,
        "max_price_impact_bps": 12.0,
        "involved_pool_ids": ["tinyman:ALGO-USDC", "pact:ALGO-USDC"],
        "involved_asset_ids": [0, 31566704],
        "status": "rejected",
        "skip_reason": "profit_bps_ok",
        "confidence_score": 80.0,
        "risk_rules": {"profit_bps_ok": False},
        "created_at": created_at,
    }


def _empty_report(**overrides):
    params = {
        "report_date": "2023-11-14",
        "window_start": 1_700_000_000.0,
        "window_end": 1_700_086_400.0,
        "generated_at": 1_700_086_400.0,
        "opportunities": [],
        "pool_snapshots": [],
        "paper_trades": [],
        "risk_decisions": [],
        "service_health": [],
        "assets": [],
    }
    params.update(overrides)
    return build_daily_market_intelligence_report(**params)


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def test_daily_market_report_explains_all_required_sections():
    window_start = 1_700_000_000.0
    window_end = window_start + 86_400
    opportunities = [
        _opportunity("route-a", window_start + 120, 180.0),
        _opportunity("route-b", window_start + 3_600, 90.0),
    ]
    pool_snapshots = [
        {
            "pool_id": "tinyman:ALGO-USDC",
            "venue_id": "tinyman",
            "app_id": 1,
            "asset_a_id": 0,
            "asset_b_id": 31566704,
            "liquidity_estimate": 10_000.0,
            "captured_at": window_start + 60,
        },
        {
            "pool_id": "tinyman:ALGO-USDC",
            "venue_id": "tinyman",
            "app_id": 1,
            "asset_a_id": 0,
            "asset_b_id": 31566704,
            "liquidity_estimate": 12_000.0,
            "captured_at": window_start + 720,
        },
    ]
    paper_trades = [
        {
            "route_hash": "route-a",
            "expected_net_profit": 0.1,
            "simulated_profit_5s": 0.08,
            "simulated_profit_30s": 0.05,
            "quote_decay_30s": 0.01,
            "expected_vs_simulated_profit_30s": -0.05,
            "checked_5s_at": window_start + 125,
            "checked_30s_at": window_start + 150,
            "would_execute": 1,
            "created_at": window_start + 121,
        }
    ]
    risk_decisions = [
        {"route_hash": "route-a", "approved": 0, "reason": "profit_bps_ok", "created_at": window_start + 122}
    ]
    service_health = [
        {
            "service_name": "market_scanner",
            "status": "ok",
            "detail": "scanner completed",
            "checked_at": window_start + 180,
        }
    ]

    report = build_daily_market_intelligence_report(
        report_date="2023-11-14",
        window_start=window_start,
        window_end=window_end,
        generated_at=window_end,
        opportunities=opportunities,
        pool_snapshots=pool_snapshots,
        paper_trades=paper_trades,
        risk_decisions=risk_decisions,
        service_health=service_health,
        assets=[],
    )

    assert report["source"] == "stored"
    assert report["publicSafe"] is True
    assert report["liveExecutionTouched"] is False
    assert report["signerCodeTouched"] is False
    assert report["marketSummary"]["opportunityCount"] == 2
    assert report["topPairs"][0]["pairLabel"] == "ALGO/USDC"
    assert report["topSpreads"][0]["expectedProfitBps"] == 180.0
    assert report["liquidityChanges"][0]["changePct"] == 20.0
    assert report["opportunityCounts"]["total"] == 2
    assert report["routePerformance"]["averageRouteLength"] == 2.0
    assert report["paperTradePerformance"]["winRate30s"] == 1.0
    assert report["scannerHealth"]["status"] == "ok"
    assert report["riskEvents"][0]["reason"] == "profit_bps_ok"


def test_daily_market_report_lists_pnet_pools_without_opportunities():
    window_start = 1_700_000_000.0
    window_end = window_start + 86_400
    report = build_daily_market_intelligence_report(
        report_date="2023-11-14",
        window_start=window_start,
        window_end=window_end,
        generated_at=window_end,
        opportunities=[],
        pool_snapshots=[
            {
                "pool_id": "pact:ALGO-PNET",
                "venue_id": "pact",
                "app_id": 42,
                "asset_a_id": 0,
                "asset_b_id": 3169177585,
                "reserve_a": 1200.0,
                "reserve_b": 4_200_000.0,
                "fee_bps": 30,
                "liquidity_estimate": 70_992.0,
                "captured_at": window_start + 60,
            }
        ],
        paper_trades=[],
        risk_decisions=[],
        service_health=[],
        assets=[],
    )

    watchlist = report["pnetLiquidityWatchlist"]
    assert report["marketSummary"]["opportunityCount"] == 0
    assert watchlist["poolCount"] == 1
    assert watchlist["listedWithoutOpportunity"] is True
    assert watchlist["pools"][0]["pairLabel"] == "ALGO/PNET"
    assert watchlist["pools"][0]["pnetReserve"] == 4_200_000.0
    assert "not investment advice" in watchlist["notice"]
    assert "impermanent loss" in watchlist["lpRiskNotice"]


def test_daily_market_report_markdown_export_contains_sections():
    report = _empty_report()

    markdown = render_market_intelligence_markdown(report)

    assert "# AlgoPulse Market Intelligence Report - 2023-11-14" in markdown
    assert "## Market Summary" in markdown
    assert "## Market Context Ribbon" in markdown
    assert "## PNET Liquidity Watchlist" in markdown
    assert "External cached market context" in markdown
    assert "## Top Pairs" in markdown
    assert "## Scanner Health" in markdown
    assert "Live execution touched: false" in markdown


def test_daily_market_report_gracefully_handles_missing_cmc_context():
    report = _empty_report(cached_market_context=None)

    ribbon = report["marketContextRibbon"]
    assert ribbon["title"] == "External cached market context"
    assert ribbon["symbol"] == "ALGO"
    assert ribbon["availability"] == "unavailable"
    assert ribbon["change24hPct"] is None
    assert ribbon["contextLabel"] == "unavailable"
    assert ribbon["sourceLabel"] == "CoinMarketCap cached context"
    assert ribbon["external"] is True
    assert "not investment or trading advice" in ribbon["notice"]


def test_daily_market_report_uses_algo_only_cached_market_context():
    report = _empty_report(
        cached_market_context={
            "assets": {
                "BTC": {"percent_change_24h": 4.5},
                "ETH": {"percent_change_24h": 2.1},
                "ALGO": {"percent_change_24h": -2.4},
            },
            "snapshot_at": 1_700_086_100.0,
            "CMC_API_KEY": "never-output",
        }
    )

    ribbon = report["marketContextRibbon"]
    serialized = json.dumps(report, sort_keys=True)

    assert ribbon["symbol"] == "ALGO"
    assert ribbon["change24hPct"] == -2.4
    assert ribbon["contextLabel"] == "risk-off"
    assert ribbon["snapshotAgeSeconds"] == 300.0
    assert ribbon["snapshotAgeLabel"] == "5m old"
    assert ribbon["availability"] == "available"
    assert ribbon["sourceLabel"] == "CoinMarketCap cached context"
    assert "BTC" not in serialized
    assert "ETH" not in serialized
    assert "CMC_API_KEY" not in serialized
    assert "never-output" not in serialized


def test_market_context_ribbon_adds_no_route_or_execution_fields():
    report = _empty_report(cached_market_context={"algo24hChangePct": 1.8, "snapshotAgeSeconds": 600})
    ribbon = report["marketContextRibbon"]

    forbidden_key_fragments = ("route", "exec", "signal", "wallet", "signer", "secret", "api")
    for key in _walk_keys(ribbon):
        normalized = key.replace("_", "").lower()
        assert not any(fragment in normalized for fragment in forbidden_key_fragments), key
