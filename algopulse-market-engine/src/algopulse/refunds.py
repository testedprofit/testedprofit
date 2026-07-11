from __future__ import annotations

from dataclasses import asdict, dataclass, field

from algopulse.algorand import raw_to_display


REFUNDABLE_STATUSES = {"refund_ready", "needs_review"}


@dataclass(frozen=True)
class RefundCaseInput:
    failure_type: str
    reason: str
    payment_verification: dict | None = None
    operator_note: str | None = None


@dataclass(frozen=True)
class RefundCaseDecision:
    status: str
    failure_type: str
    reason: str
    payment_verification_id: int | None
    source_txid: str | None
    refund_address: str | None
    asset_id: int
    asset_decimals: int
    amount_raw: int
    amount_display: float
    operator_action: str
    operator_note: str | None = None
    guardrails: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def build_refund_case(data: RefundCaseInput) -> RefundCaseDecision:
    receipt = data.payment_verification
    if not receipt:
        return _decision(
            data=data,
            status="not_refundable",
            operator_action="record_failure_only",
            reason="no payment verification receipt attached",
        )

    result = receipt.get("result") or {}
    observed = result.get("observed") or {}
    expected = result.get("expected") or {}
    source_txid = result.get("txid") or receipt.get("txid")
    asset_id = int(result.get("asset_id") or receipt.get("asset_id") or observed.get("asset_id") or 0)
    decimals = int(expected.get("asset_decimals") or 6)
    amount_raw = int(observed.get("amount_raw") or receipt.get("observed_amount_raw") or 0)
    sender = observed.get("sender") or receipt.get("observed_sender")
    receiver = observed.get("receiver") or receipt.get("observed_receiver")
    expected_receiver = expected.get("receiver") or receipt.get("expected_receiver")
    confirmed_round = int(observed.get("confirmed_round") or receipt.get("confirmed_round") or 0)

    if not sender or amount_raw <= 0 or not confirmed_round:
        return _decision(
            data=data,
            receipt=receipt,
            status="not_refundable",
            operator_action="manual_investigation_required",
            reason="no confirmed inbound payment with sender and amount",
            source_txid=source_txid,
            asset_id=asset_id,
            asset_decimals=decimals,
        )

    incoming_to_expected_receiver = bool(receiver and expected_receiver and receiver == expected_receiver)
    if result.get("ok") is True and result.get("status") == "verified":
        status = "refund_ready"
        action = "manual_refund_ready"
        reason = data.reason
    elif incoming_to_expected_receiver:
        status = "needs_review"
        action = "review_inbound_payment_before_refund"
        reason = f"inbound payment did not fully verify: {result.get('reason') or result.get('status') or data.reason}"
    else:
        return _decision(
            data=data,
            receipt=receipt,
            status="not_refundable",
            operator_action="do_not_refund_from_this_receipt",
            reason="transaction was not verified as an inbound payment to the expected receiver",
            source_txid=source_txid,
            asset_id=asset_id,
            asset_decimals=decimals,
        )

    return RefundCaseDecision(
        status=status,
        failure_type=data.failure_type,
        reason=reason,
        payment_verification_id=receipt.get("id"),
        source_txid=source_txid,
        refund_address=sender,
        asset_id=asset_id,
        asset_decimals=decimals,
        amount_raw=amount_raw,
        amount_display=raw_to_display(amount_raw, decimals),
        operator_action=action,
        operator_note=data.operator_note,
        guardrails=[
            "manual refund only; no automatic send",
            "verify the product/service was not delivered before refunding",
            "check for duplicate refund cases before sending",
            "record refund txid when resolved",
        ],
    )


def _decision(
    *,
    data: RefundCaseInput,
    status: str,
    operator_action: str,
    reason: str,
    receipt: dict | None = None,
    source_txid: str | None = None,
    asset_id: int = 0,
    asset_decimals: int = 6,
) -> RefundCaseDecision:
    return RefundCaseDecision(
        status=status,
        failure_type=data.failure_type,
        reason=reason,
        payment_verification_id=receipt.get("id") if receipt else None,
        source_txid=source_txid,
        refund_address=None,
        asset_id=asset_id,
        asset_decimals=asset_decimals,
        amount_raw=0,
        amount_display=0.0,
        operator_action=operator_action,
        operator_note=data.operator_note,
        guardrails=[
            "do not issue a refund without confirmed sender and amount",
            "attach or re-run payment verification before refunding",
        ],
    )
