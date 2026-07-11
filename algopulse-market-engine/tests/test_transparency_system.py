import json
import os
import tempfile
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["ALGO_PULSE_DATABASE"] = str(Path(tempfile.gettempdir()) / f"algopulse-transparency-{uuid.uuid4().hex}.db")

from algopulse.api import app
from algopulse.api import store


ROOT = Path(__file__).resolve().parents[1]
APP_JS = (ROOT / "src/algopulse/static/app.js").read_text(encoding="utf-8")
INDEX_HTML = (ROOT / "src/algopulse/static/index.html").read_text(encoding="utf-8")
SNAPSHOT_SCRIPT = (ROOT / "scripts/generate_transparency_snapshot.py").read_text(encoding="utf-8")


def _client() -> TestClient:
    return TestClient(app)


def test_transparency_public_ledger_redacts_payment_and_review_references():
    txid = "TXIDFULLSHOULDNOTAPPEAR1234567890"
    sender = "SENDERFULLSHOULDNOTAPPEARABCDEFG"
    receiver = "RECEIVERFULLSHOULDNOTAPPEARHIJKLMN"
    store.record_payment_verification(
        {
            "txid": txid,
            "ok": True,
            "status": "confirmed",
            "reason": None,
            "asset_id": 3169177585,
            "expected": {"receiver": receiver, "amount_raw": 1000000},
            "observed": {
                "sender": sender,
                "receiver": receiver,
                "amount_raw": 1000000,
                "confirmed_round": 123,
                "confirmations": 3,
            },
        }
    )
    contribution = _client().post(
        "/api/contribution-protocol/submit",
        json={
            "wallet": "USERTRANSPARENCYREVIEW0001",
            "contribution_type": "verification_report",
            "title": "Verify proof redaction",
            "summary": "Review transparency system output for redaction boundaries.",
        },
    )
    assert contribution.status_code == 200

    response = _client().get("/api/transparency/public-ledger")

    assert response.status_code == 200
    data = response.json()["data"]
    encoded = json.dumps(data, sort_keys=True)
    assert data["summary"]["paymentVerificationCount"] >= 1
    assert data["summary"]["reviewEventCount"] >= 1
    assert data["summary"]["rawTxidsExposed"] is False
    assert data["summary"]["rawWalletsExposed"] is False
    assert data["summary"]["paymentPayloadsExposed"] is False
    assert data["summary"]["secretsExposed"] is False
    assert txid not in encoded
    assert sender not in encoded
    assert receiver not in encoded
    assert "tx_" in encoded
    assert "payer_" in encoded
    assert "wallet_" in encoded
    assert data["liveExecutionTouched"] is False
    assert data["signerCodeTouched"] is False


def test_transparency_system_exposes_proofs_snapshot_and_audit_boundaries():
    response = _client().get("/api/transparency/system")

    assert response.status_code == 200
    data = response.json()["data"]
    proof_codes = {item["code"]: item for item in data["proofMatrix"]}
    assert proof_codes["x402_gate_3"]["status"] == "complete"
    assert proof_codes["x402_gate_3_5"]["status"] == "blocked"
    assert proof_codes["x402_settlement_failure_harness"]["status"] == "documented_limitation"
    assert data["githubSnapshot"]["scope"] == "public-safe GitHub dossier snapshot"
    assert "docs/TRANSPARENCY_SYSTEM.md" in data["githubSnapshot"]["docs"]
    assert data["auditReadiness"]["blockedClaims"]
    assert "audited" in data["auditReadiness"]["blockedClaims"]
    assert any("No secrets" in item for item in data["safetyBoundaries"])
    assert data["publicSafe"] is True
    assert data["liveExecutionTouched"] is False
    assert data["signerCodeTouched"] is False


def test_transparency_dashboard_and_snapshot_script_are_present():
    assert 'data-dashboard-view="transparency"' in INDEX_HTML
    assert 'transparency: { label: "Transparency", adminOnly: false' in APP_JS
    assert "function TransparencyDashboard()" in APP_JS
    assert "/api/transparency/system" in APP_JS
    assert "Public Proof System" in APP_JS
    assert "No Mainnet, deployment, signing, live trading, or public eligibility claim is implied." in SNAPSHOT_SCRIPT
    assert "/api/transparency/github-snapshot" in SNAPSHOT_SCRIPT
