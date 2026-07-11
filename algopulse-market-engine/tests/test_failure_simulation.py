from algopulse.failure_simulation import build_failure_lab_report


def test_failure_lab_report_contains_required_scenarios_and_safe_boundaries():
    report = build_failure_lab_report()

    assert report["source"] == "mock"
    assert report["mode"] == "simulation"
    assert report["liveExecutionTouched"] is False
    assert report["signerCodeTouched"] is False
    assert {scenario["key"] for scenario in report["scenarios"]} == {
        "tinyman_offline",
        "pact_offline",
        "stale_quotes",
        "database_unavailable",
        "route_engine_crash",
        "signer_unavailable",
        "unknown_asset",
        "unknown_app_id",
        "daily_loss_breach",
    }
    assert report["summary"]["scenarioCount"] == 9
    assert report["summary"]["gracefulCount"] == 9
    assert report["summary"]["gracefulPercent"] == 100


def test_failure_lab_each_scenario_explains_response_alerts_and_services():
    report = build_failure_lab_report()

    for scenario in report["scenarios"]:
        assert scenario["expectedResponse"]["message"]
        assert scenario["actualResponse"]["message"]
        assert scenario["expectedResponse"]["blocksLiveExecution"] is True
        assert scenario["actualResponse"]["blocksLiveExecution"] is True
        assert scenario["alertsGenerated"], scenario["key"]
        assert scenario["servicesAffected"], scenario["key"]
        assert scenario["operatorAction"]
        assert scenario["gracefulDegradation"] is True
        assert scenario["source"] == "mock"


def test_failure_lab_specific_hard_stops_are_rejected_or_locked():
    scenarios = {scenario["key"]: scenario for scenario in build_failure_lab_report()["scenarios"]}

    assert scenarios["unknown_asset"]["actualResponse"]["status"] == "rejected"
    assert scenarios["unknown_app_id"]["actualResponse"]["status"] == "rejected"
    assert scenarios["daily_loss_breach"]["actualResponse"]["status"] == "locked"
    assert scenarios["signer_unavailable"]["actualResponse"]["status"] == "locked"
    assert "unknown_asset_detected" in scenarios["unknown_asset"]["alertsGenerated"]
    assert "unknown_app_id_detected" in scenarios["unknown_app_id"]["alertsGenerated"]
    assert "daily_loss_limit_near_breach" in scenarios["daily_loss_breach"]["alertsGenerated"]
    assert "signer_offline" in scenarios["signer_unavailable"]["alertsGenerated"]
