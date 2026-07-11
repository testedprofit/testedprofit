import importlib.util
import os
import sys
import tempfile
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["ALGO_PULSE_DATABASE"] = str(Path(tempfile.gettempdir()) / f"algopulse-contribution-{uuid.uuid4().hex}.db")

from algopulse.api import app


ROOT = Path(__file__).resolve().parents[1]


def _client() -> TestClient:
    return TestClient(app)


def test_contribution_catalog_defines_bounded_credit_unlocks():
    response = _client().get("/api/contribution-protocol/catalog")

    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]
    unlocks = {item["code"]: item for item in data["creditUnlocks"]}
    actions = {item["code"]: item for item in data["contributionActions"]}

    assert "docs_fix" in actions
    assert "pool_observation" in actions
    assert actions["mining_evidence"]["label"] == "Mining evidence receipt"
    assert actions["bandwidth_evidence"]["label"] == "Bandwidth evidence receipt"
    assert "No earnings projection" in actions["mining_evidence"]["evidenceRequired"]
    assert unlocks["premium_market_report"]["category"] == "tool_access"
    assert unlocks["governance_signal_comment"]["category"] == "governance_signal"
    assert data["smartContractStatus"] == "reference_blueprint_only_not_deployed"
    assert data["liveExecutionTouched"] is False
    assert any("not represent token rewards" in item for item in data["safetyBoundaries"])
    assert any("Governance signals are non-binding" in item for item in data["safetyBoundaries"])


def test_contribution_submit_records_pending_manual_review_only():
    wallet = "USERCONTRIBREVIEWWALLET0001"
    response = _client().post(
        "/api/contribution-protocol/submit",
        json={
            "wallet": wallet,
            "contribution_type": "docs_fix",
            "title": "Improve install instructions",
            "summary": "Clarify local beta setup without making production or investment claims.",
            "evidence_url": "https://example.invalid/review-note",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    submission = payload["data"]["submission"]
    assert submission["status"] == "pending_review"
    assert submission["requestedCredits"] == 1
    assert submission["creditsGranted"] == 0
    assert payload["data"]["creditBalance"] == 3
    assert payload["data"]["liveExecutionTouched"] is False
    assert "No token reward" in payload["data"]["message"]


def test_credit_spend_creates_bounded_access_receipt_without_governance_authority():
    wallet = "USERCONTRIBSPENDWALLET0002"
    response = _client().post(
        "/api/contribution-protocol/spend",
        json={
            "wallet": wallet,
            "unlock_code": "governance_signal_comment",
            "quantity": 1,
            "note": "Prioritize docs cleanup",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    receipt = payload["data"]["spendReceipt"]
    assert receipt["unlockCode"] == "governance_signal_comment"
    assert receipt["nonBindingGovernance"] is True
    assert receipt["smartContractFunction"] == "spend_credit"
    assert receipt["smartContractStatus"] == "reference_blueprint_only_not_deployed"
    assert payload["data"]["creditBalance"] == 2
    assert payload["data"]["liveExecutionTouched"] is False
    assert "No treasury" in payload["data"]["message"]


def test_credit_spend_fails_closed_when_balance_is_too_low():
    wallet = "USERCONTRIBLOWBALANCE0003"
    response = _client().post(
        "/api/contribution-protocol/spend",
        json={
            "wallet": wallet,
            "unlock_code": "premium_market_report",
            "quantity": 10,
        },
    )

    assert response.status_code == 402
    payload = response.json()
    assert payload["error"]["code"] == "CREDIT_BALANCE_TOO_LOW"
    assert payload["error"]["details"]["requiredCredits"] == 20
    assert payload["error"]["details"]["liveExecutionTouched"] is False


def test_contribution_protocol_requires_connected_wallet():
    response = _client().post(
        "/api/contribution-protocol/submit",
        json={
            "wallet": "guest",
            "contribution_type": "demo_feedback",
            "title": "Guest cannot submit",
            "summary": "Guest sessions should not submit contribution protocol records.",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_community_growth_overview_exposes_referral_leaderboard_and_reputation():
    wallet = "USERCOMMUNITYWALLET0004"
    response = _client().get(f"/api/community-growth/overview/{wallet}")

    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]
    assert data["referral"]["code"].startswith("PNET-")
    assert data["referral"]["rewardPolicy"] == "manual review; no token payout, yield, or automatic credit grant"
    assert len(data["leaderboard"]) >= 3
    assert data["reputation"]["notYield"] is True
    assert data["reputation"]["notGovernancePower"] is True
    assert "mining_evidence" in data["allowedEvidenceCategories"]
    assert any("not income claims" in item for item in data["safetyBoundaries"])
    assert data["liveExecutionTouched"] is False


def test_referral_receipt_is_manual_review_only_and_updates_reputation():
    wallet = "USERREFERRALWALLET0005"
    response = _client().post(
        "/api/community-growth/referral",
        json={
            "wallet": wallet,
            "referred_wallet": "USERREFERREDWALLET0006",
            "channel": "github",
            "note": "Invited a reviewer to inspect docs.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    receipt = payload["data"]["referralReceipt"]
    assert receipt["status"] == "pending_review"
    assert receipt["creditsGranted"] == 0
    assert receipt["rewardPolicy"] == "manual_review_no_token_payout"
    assert payload["data"]["overview"]["reputation"]["referralCount"] == 1
    assert payload["data"]["overview"]["reputation"]["notYield"] is True
    assert "No token payout" in payload["data"]["message"]
    assert payload["data"]["liveExecutionTouched"] is False


def test_referral_requires_connected_wallet():
    response = _client().post(
        "/api/community-growth/referral",
        json={"wallet": "guest", "channel": "direct"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_credit_usage_contract_blueprint_is_reference_only():
    path = ROOT / "contracts/pnet_credit_usage_reference.py"
    spec = importlib.util.spec_from_file_location("pnet_credit_usage_reference", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    app_spec = module.app_spec()
    assert app_spec["status"] == "blueprint_only_not_deployed"
    assert app_spec["deployed"] is False
    assert "spend_credit" in module.method_names()
    assert "record_nonbinding_signal" in module.method_names()
    assert "record_referral" in module.method_names()
    assert "record_reputation_event" in module.method_names()
    boundaries = " ".join(app_spec["safetyBoundaries"])
    assert "not token rewards" in boundaries
    assert "Governance signals are non-binding" in boundaries
    assert "Reputation and referral records are non-financial" in boundaries
    assert "must never sign, custody, submit trades" in boundaries
