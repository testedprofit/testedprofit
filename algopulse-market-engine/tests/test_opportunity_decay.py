from algopulse.opportunity_decay import build_opportunity_decay_report


def test_opportunity_decay_calculates_half_life_and_group_summaries():
    report = build_opportunity_decay_report(
        [
            {
                "detected_at": 1_000.0,
                "route_hash": "fast",
                "expected_profit": 0.10,
                "expected_profit_5s": 0.04,
                "expected_profit_30s": -0.01,
                "expected_profit_60s": -0.02,
                "pair_label": "ALGO/USDC",
                "pair_key": "0-31566704",
                "venues_json": '["tinyman", "pact"]',
                "route_type": "venue_arbitrage",
                "source": "stored",
            },
            {
                "detected_at": 1_100.0,
                "route_hash": "slow",
                "expected_profit": 0.20,
                "expected_profit_5s": 0.18,
                "expected_profit_30s": 0.16,
                "expected_profit_60s": 0.11,
                "pair_label": "ALGO/PNET",
                "pair_key": "0-3169177585",
                "venues_json": '["tinyman"]',
                "route_type": "single_venue",
                "source": "stored",
            },
            {
                "detected_at": -3_000.0,
                "route_hash": "old",
                "expected_profit": 1.0,
                "expected_profit_5s": 0.0,
                "pair_label": "OLD",
                "pair_key": "old",
            },
        ],
        view="1h",
        now=1_200.0,
    )

    assert report["source"] == "stored"
    assert report["view"] == "1h"
    assert report["summary"]["opportunityCount"] == 2
    assert report["summary"]["totalOpportunities"] == 2
    assert report["summary"]["resolved60sCount"] == 2
    assert report["summary"]["survivedT5Count"] == 2
    assert report["summary"]["survivedT30Count"] == 1
    assert report["summary"]["fadedCount"] == 1
    assert report["summary"]["mostCommonFadeReason"] == {"reason": "faded_by_t30", "count": 1}
    assert report["summary"]["fastestDecay"]["routeHash"] == "fast"
    assert report["summary"]["slowestDecay"]["routeHash"] == "slow"
    assert report["summary"]["averageHalfLifeSeconds"] > 0
    assert report["summary"]["medianHalfLifeSeconds"] > 0
    fast = next(item for item in report["records"] if item["routeHash"] == "fast")
    slow = next(item for item in report["records"] if item["routeHash"] == "slow")
    assert fast["expectedProfitAtT0"] == 0.10
    assert fast["simulatedProfitAtT5"] == 0.04
    assert fast["simulatedProfitAtT30"] == -0.01
    assert fast["survivedT5"] is True
    assert fast["survivedT30"] is False
    assert fast["finalOutcome"] == "faded"
    assert fast["reason"] == "faded_by_t30"
    assert slow["survivedT30"] is True
    assert slow["finalOutcome"] == "survived"
    assert {item["label"] for item in report["byPair"]} == {"ALGO/USDC", "ALGO/PNET"}
    assert {item["label"] for item in report["byVenue"]} == {"tinyman", "pact"}
    assert {item["label"] for item in report["byRouteType"]} == {"venue_arbitrage", "single_venue"}
    assert len(report["timeline"]) == 12
    assert report["liveExecutionTouched"] is False
    assert report["signerCodeTouched"] is False


def test_opportunity_decay_handles_empty_source():
    report = build_opportunity_decay_report([], view="bad", now=1_000.0)

    assert report["view"] == "24h"
    assert report["source"] == "unavailable"
    assert report["summary"]["opportunityCount"] == 0


def test_opportunity_decay_survival_outcomes_and_aggregate_metrics():
    report = build_opportunity_decay_report(
        [
            {
                "detected_at": 1_000.0,
                "route_hash": "survives",
                "expected_profit": 0.10,
                "expected_profit_5s": 0.08,
                "expected_profit_30s": 0.05,
                "quote_decay_5s": 0.01,
                "quote_decay_30s": 0.03,
                "pair_label": "ALGO/USDC",
                "pair_key": "0-31566704",
                "venues_json": '["tinyman", "pact"]',
            },
            {
                "detected_at": 1_010.0,
                "route_hash": "fades",
                "expected_profit": 0.12,
                "expected_profit_5s": 0.02,
                "expected_profit_30s": -0.01,
                "quote_decay_5s": 0.02,
                "quote_decay_30s": 0.11,
                "pair_label": "ALGO/PNET",
                "pair_key": "0-3169177585",
                "venues_json": '["tinyman"]',
            },
            {
                "detected_at": 1_020.0,
                "route_hash": "negative",
                "expected_profit": -0.01,
                "expected_profit_5s": -0.02,
                "expected_profit_30s": -0.03,
                "quote_decay_5s": 0.00,
                "quote_decay_30s": 0.00,
                "pair_label": "ALGO/BSF",
                "pair_key": "0-123",
                "venues_json": '["pact"]',
            },
            {
                "detected_at": 1_030.0,
                "route_hash": "missing-t30",
                "expected_profit": 0.20,
                "expected_profit_5s": 0.18,
                "quote_decay_5s": 0.03,
                "pair_label": "ALGO/X",
                "pair_key": "0-456",
                "venues_json": '["tinyman"]',
            },
        ],
        view="1h",
        now=1_100.0,
    )

    by_hash = {item["routeHash"]: item for item in report["records"]}

    assert by_hash["survives"]["survivedT5"] is True
    assert by_hash["survives"]["survivedT30"] is True
    assert by_hash["survives"]["finalOutcome"] == "survived"
    assert by_hash["fades"]["survivedT5"] is True
    assert by_hash["fades"]["survivedT30"] is False
    assert by_hash["fades"]["finalOutcome"] == "faded"
    assert by_hash["fades"]["reason"] == "faded_by_t30"
    assert by_hash["negative"]["finalOutcome"] == "rejected"
    assert by_hash["negative"]["reason"] == "expected_profit_not_positive"
    assert by_hash["missing-t30"]["survivedT5"] is True
    assert by_hash["missing-t30"]["survivedT30"] is None
    assert by_hash["missing-t30"]["finalOutcome"] == "unknown"
    assert by_hash["missing-t30"]["reason"] == "missing_t30_evidence"

    summary = report["summary"]
    assert summary["totalOpportunities"] == 4
    assert summary["survivedT5Count"] == 3
    assert summary["survivedT30Count"] == 1
    assert summary["fadedCount"] == 1
    assert summary["rejectedCount"] == 1
    assert summary["unknownCount"] == 1
    assert summary["averageDecayT5"] == 0.015
    assert round(summary["averageDecayT30"], 6) == round((0.03 + 0.11 + 0.0) / 3, 6)
    assert summary["bestPairBySurvival"]["pair"] == "ALGO/USDC"
    assert summary["worstPairBySurvival"]["pair"] in {"ALGO/BSF", "ALGO/PNET"}
    assert summary["mostCommonFadeReason"]["reason"] in {
        "expected_profit_not_positive",
        "faded_by_t30",
        "missing_t30_evidence",
    }
