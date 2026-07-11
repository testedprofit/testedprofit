import time

from algopulse.market_heatmap import build_market_pulse_heatmap
from algopulse.models import Opportunity
from algopulse.store import MarketStore


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
                "fee_amount": 0.015,
                "price_impact_bps": 12.0,
                "captured_at": created_at,
                "expires_at": created_at + 5,
            },
            {
                "venue": "pact",
                "pool_id": "pact:ALGO-USDC",
                "input_asset_id": 31566704,
                "output_asset_id": 0,
                "input_amount": 1.1,
                "expected_output": 5.12,
                "fee_amount": 0.003,
                "price_impact_bps": 10.0,
                "captured_at": created_at,
                "expires_at": created_at + 5,
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
        "skip_reason": "app_ids_allowlisted",
        "confidence_score": 80.0,
        "risk_rules": {"app_ids_allowlisted": False},
        "created_at": created_at,
    }


def test_market_heatmap_aggregates_pair_venue_time_and_paper_performance():
    now = 1_000_000.0
    opportunities = [
        _opportunity("route-a", now - 600, 120.0),
        _opportunity("route-b", now - 600, 80.0),
        _opportunity("route-old", now - 90_000, 400.0),
    ]
    paper_trades = [
        {
            "route_hash": "route-a",
            "expected_net_profit": 0.1,
            "simulated_profit_5s": 0.08,
            "simulated_profit_30s": 0.06,
            "quote_decay_30s": 0.04,
            "created_at": now - 590,
        }
    ]

    heatmap = build_market_pulse_heatmap(opportunities, paper_trades, view="1h", now=now)

    assert heatmap["view"] == "1h"
    assert heatmap["bucketSeconds"] == 300
    assert len(heatmap["timeBuckets"]) == 12
    assert heatmap["source"] == "stored"
    assert heatmap["totals"]["opportunityCount"] == 4
    assert heatmap["totals"]["pairCount"] == 1
    assert heatmap["totals"]["venueCount"] == 2
    assert heatmap["cells"]
    hot_cell = heatmap["cells"][0]
    assert hot_cell["pairLabel"] == "0/31566704"
    assert hot_cell["venue"] in {"tinyman", "pact"}
    assert hot_cell["opportunityCount"] == 2
    assert hot_cell["spreadFrequency"] > 0
    assert hot_cell["averageSpreadBps"] == 100.0
    assert hot_cell["averageRouteCount"] == 2.0
    assert hot_cell["opportunityHalfLifeSeconds"] >= 5.0
    assert hot_cell["paperTradePerformance"]["count"] == 1
    assert hot_cell["paperTradePerformance"]["winRate"] == 1.0
    assert hot_cell["intensity"] == 1.0
    assert hot_cell["densityLabel"] == "hot"


def test_market_heatmap_unknown_view_defaults_to_24h():
    heatmap = build_market_pulse_heatmap([], [], view="bad-view", now=1_000_000.0)

    assert heatmap["view"] == "24h"
    assert heatmap["source"] == "unavailable"
    assert heatmap["totals"]["opportunityCount"] == 0


def test_store_market_pulse_heatmap_uses_stored_opportunities(tmp_path):
    now = time.time()
    store = MarketStore(tmp_path / "market.db")
    store.initialize()
    opportunity = Opportunity(
        route_hash="stored-heatmap-route",
        route=_opportunity("stored-heatmap-route", now)["route"],
        input_asset_id=0,
        input_amount=5.0,
        expected_final_amount=5.12,
        gross_profit=0.12,
        estimated_network_fee=0.006,
        total_dex_fees=0.018,
        total_price_impact_bps=22.0,
        slippage_buffer=0.02,
        expected_net_profit=0.094,
        expected_profit_bps=188.0,
        max_price_impact_bps=12.0,
        involved_pool_ids=["tinyman:ALGO-USDC", "pact:ALGO-USDC"],
        involved_asset_ids=[0, 31566704],
        status="rejected",
        skip_reason="app_ids_allowlisted",
        risk_rules={"app_ids_allowlisted": False},
        created_at=now,
    )
    store.record_opportunities([opportunity])
    store.record_paper_trade(opportunity, would_execute=False, notes="heatmap test")

    heatmap = store.market_pulse_heatmap(view="24h", now=now + 1)

    assert heatmap["source"] == "stored"
    assert heatmap["totals"]["opportunityCount"] == 2
    assert heatmap["totals"]["activeCells"] == 2
    assert {cell["venue"] for cell in heatmap["cells"]} == {"tinyman", "pact"}
