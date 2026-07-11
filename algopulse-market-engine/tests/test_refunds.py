from algopulse.refunds import RefundCaseInput
from algopulse.refunds import build_refund_case


def _receipt(*, ok: bool = True, reason: str | None = None) -> dict:
    return {
        "id": 7,
        "txid": "PAYTXID",
        "ok": ok,
        "status": "verified" if ok else "mismatch",
        "reason": reason,
        "asset_id": 0,
        "expected_receiver": "RECEIVER",
        "observed_sender": "SENDER",
        "observed_receiver": "RECEIVER",
        "observed_amount_raw": 5_000_000,
        "confirmed_round": 123,
        "result": {
            "ok": ok,
            "status": "verified" if ok else "mismatch",
            "reason": reason,
            "txid": "PAYTXID",
            "asset_id": 0,
            "expected": {
                "receiver": "RECEIVER",
                "amount_raw": 5_000_000,
                "asset_decimals": 6,
            },
            "observed": {
                "sender": "SENDER",
                "receiver": "RECEIVER",
                "amount_raw": 5_000_000,
                "asset_id": 0,
                "confirmed_round": 123,
            },
        },
    }


def test_refund_case_is_ready_for_verified_inbound_payment():
    decision = build_refund_case(
        RefundCaseInput(
            failure_type="service_failure",
            reason="service did not complete",
            payment_verification=_receipt(),
        )
    )

    assert decision.status == "refund_ready"
    assert decision.operator_action == "manual_refund_ready"
    assert decision.refund_address == "SENDER"
    assert decision.amount_raw == 5_000_000
    assert decision.amount_display == 5
    assert "manual refund only; no automatic send" in decision.guardrails


def test_refund_case_needs_review_when_inbound_payment_did_not_fully_verify():
    decision = build_refund_case(
        RefundCaseInput(
            failure_type="payment_mismatch",
            reason="wrong amount",
            payment_verification=_receipt(ok=False, reason="amount"),
        )
    )

    assert decision.status == "needs_review"
    assert decision.operator_action == "review_inbound_payment_before_refund"
    assert decision.refund_address == "SENDER"
    assert "amount" in decision.reason


def test_refund_case_without_payment_receipt_is_not_refundable():
    decision = build_refund_case(
        RefundCaseInput(
            failure_type="route_failure",
            reason="route failed before service",
            payment_verification=None,
        )
    )

    assert decision.status == "not_refundable"
    assert decision.operator_action == "record_failure_only"
    assert decision.refund_address is None
    assert decision.amount_raw == 0
