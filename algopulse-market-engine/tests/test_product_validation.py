from algopulse.product_validation import ACTION_TAXONOMY
from algopulse.product_validation import build_product_validation_report
from algopulse.product_validation import is_decision_action


def test_product_validation_counts_decisions_funnel_and_personas():
    now = 1_800_000_000.0
    actions = [
        {
            "id": 1,
            "action_type": "viewed_market_pulse",
            "timestamp": now - 100,
            "user_role": "guest",
            "wallet_connected": 0,
            "source_page": "pulse",
            "metadata_json": '{"session_id":"guest-1"}',
        },
        {
            "id": 2,
            "action_type": "opened_route",
            "timestamp": now - 90,
            "user_role": "user",
            "wallet_connected": 1,
            "source_page": "routes",
            "metadata_json": '{"session_id":"user-1","pnet_user":true}',
        },
        {
            "id": 3,
            "action_type": "opened_daily_report",
            "timestamp": now - 86_500,
            "user_role": "user",
            "wallet_connected": 1,
            "source_page": "research",
            "metadata_json": '{"session_id":"user-1","pnet_user":true}',
        },
        {
            "id": 4,
            "action_type": "exported_data",
            "timestamp": now - 30,
            "user_role": "admin",
            "wallet_connected": 1,
            "source_page": "api",
            "metadata_json": '{"session_id":"builder-1","persona":"Builder"}',
        },
    ]
    decisions = [
        {
            "decision_id": "d1",
            "action_type": "opened_route",
            "user_role": "user",
            "page": "routes",
            "evidence_source": "route_details",
            "created_at": now - 90,
        },
        {
            "decision_id": "d2",
            "action_type": "opened_daily_report",
            "user_role": "user",
            "page": "research",
            "evidence_source": "daily_report",
            "created_at": now - 86_500,
        },
        {
            "decision_id": "d3",
            "action_type": "exported_data",
            "user_role": "admin",
            "page": "api",
            "evidence_source": "export",
            "created_at": now - 30,
            "metadata_json": '{"persona":"Builder"}',
        },
    ]

    report = build_product_validation_report(actions, decisions, now=now, window_days=30)

    assert report["source"] == "stored"
    assert report["summary"]["totalActions"] == 4
    assert report["summary"]["activeUsers"] == 3
    assert report["summary"]["repeatUsers"] == 1
    assert report["summary"]["decisionCount"] == 3
    assert report["summary"]["decisionRate"] == 0.75
    funnel = {item["key"]: item for item in report["funnel"]}
    assert funnel["guest"]["users"] == 1
    assert funnel["connected_user"]["users"] == 2
    assert funnel["pnet_user"]["users"] == 1
    assert funnel["report_user"]["users"] == 2
    assert funnel["repeat_user"]["users"] == 1
    builder = next(item for item in report["personas"] if item["persona"] == "Builder")
    assert builder["activeUsers"] >= 1
    assert builder["evidenceBackedDecisions"] >= 1
    feature = next(item for item in report["featureUtility"] if item["feature"] == "Route Intelligence")
    assert feature["decisionCount"] == 1
    assert report["whyUsersReturn"]["decisionMetrics"]["dailyEvidenceBackedDecisions"]
    assert report["liveExecutionTouched"] is False
    assert report["signerCodeTouched"] is False


def test_product_validation_empty_report_is_unavailable_and_taxonomy_is_decision_scoped():
    report = build_product_validation_report([], [], now=1_000.0)

    assert report["source"] == "unavailable"
    assert report["summary"]["decisionCount"] == 0
    assert "page_load" in report["decisionRules"]["excludedExamples"]
    assert is_decision_action("opened_route") is True
    assert is_decision_action("viewed_market_pulse") is False
    assert {"requested_scan", "exported_data"}.issubset(ACTION_TAXONOMY)
