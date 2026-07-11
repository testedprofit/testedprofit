from algopulse.confidence_calibration import build_confidence_calibration_report


def test_confidence_calibration_buckets_resolved_paper_trades():
    report = build_confidence_calibration_report(
        [
            {
                "id": 1,
                "route_hash": "high-win",
                "confidence_score": 95.0,
                "expected_net_profit": 0.12,
                "checked_30s_at": 100.0,
                "simulated_profit_30s": 0.08,
                "quote_decay_30s": 0.02,
                "success": 1,
                "created_at": 1.0,
            },
            {
                "id": 2,
                "route_hash": "high-loss",
                "confidence_score": 84.0,
                "expected_net_profit": 0.10,
                "checked_30s_at": 101.0,
                "simulated_profit_30s": -0.03,
                "quote_decay_30s": 0.08,
                "success": 0,
                "created_at": 2.0,
            },
            {
                "id": 3,
                "route_hash": "mid-win",
                "confidence_score": 0.74,
                "expected_profit": 0.06,
                "checked_5s_at": 102.0,
                "simulated_profit_5s": 0.02,
                "quote_decay_5s": 0.01,
                "success": None,
                "created_at": 3.0,
            },
            {
                "id": 4,
                "route_hash": "pending",
                "confidence_score": 91.0,
                "expected_profit": 0.06,
                "checked_5s_at": None,
                "checked_30s_at": None,
                "created_at": 4.0,
            },
        ]
    )

    by_label = {bucket["label"]: bucket for bucket in report["buckets"]}
    assert report["summary"]["paperTradeCount"] == 4
    assert report["summary"]["resolvedCount"] == 3
    assert report["summary"]["successCount"] == 2
    assert report["summary"]["verdict"] == "under_sampled"
    assert by_label["0.90-1.00"]["count"] == 1
    assert by_label["0.90-1.00"]["successRate"] == 1.0
    assert by_label["0.80-0.89"]["count"] == 1
    assert by_label["0.80-0.89"]["successRate"] == 0.0
    assert by_label["0.70-0.79"]["count"] == 1
    assert by_label["0.70-0.79"]["averageSimulatedProfit"] == 0.02
    assert report["liveExecutionTouched"] is False
    assert report["signerCodeTouched"] is False
