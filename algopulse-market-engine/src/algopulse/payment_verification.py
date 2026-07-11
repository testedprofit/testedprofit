from __future__ import annotations

import base64
from dataclasses import asdict, dataclass, field

from algosdk import encoding

from algopulse.algorand import display_to_raw, raw_to_display


@dataclass(frozen=True)
class PaymentVerificationRequest:
    txid: str
    expected_receiver: str
    expected_amount: float
    asset_id: int = 0
    asset_decimals: int = 6
    amount_unit: str = "display"
    expected_sender: str | None = None
    note_text: str | None = None
    note_prefix: str | None = None
    min_confirmations: int = 1
    reject_rekey: bool = True
    reject_close_to: bool = True

    @property
    def expected_amount_raw(self) -> int:
        if self.amount_unit == "raw":
            return int(self.expected_amount)
        return display_to_raw(self.expected_amount, self.asset_decimals)


@dataclass(frozen=True)
class PaymentVerificationResult:
    ok: bool
    status: str
    reason: str | None
    txid: str
    asset_id: int
    expected: dict
    observed: dict
    checks: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class AlgorandPaymentVerifier:
    def __init__(self, indexer) -> None:
        self.indexer = indexer

    def verify(self, request: PaymentVerificationRequest) -> PaymentVerificationResult:
        validation_error = _validate_request(request)
        if validation_error:
            return _result(request=request, ok=False, status="invalid_request", reason=validation_error)

        try:
            response = self.indexer.transaction(request.txid)
        except Exception as exc:
            return _result(
                request=request,
                ok=False,
                status="lookup_failed",
                reason=f"indexer lookup failed: {exc}",
            )

        transaction = response.get("transaction") if isinstance(response, dict) else None
        if not transaction:
            return _result(request=request, ok=False, status="not_found", reason="transaction not found")

        current_round = int(response.get("current-round") or response.get("current_round") or 0)
        observed = _observed_transaction(transaction, current_round, request.asset_decimals)
        checks = _checks(request, transaction, observed)
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            return PaymentVerificationResult(
                ok=False,
                status="mismatch",
                reason=failed[0],
                txid=request.txid,
                asset_id=request.asset_id,
                expected=_expected_payload(request),
                observed=observed,
                checks=checks,
            )

        return PaymentVerificationResult(
            ok=True,
            status="verified",
            reason=None,
            txid=request.txid,
            asset_id=request.asset_id,
            expected=_expected_payload(request),
            observed=observed,
            checks=checks,
        )


def _validate_request(request: PaymentVerificationRequest) -> str | None:
    if not request.txid.strip():
        return "txid is required"
    if request.asset_id < 0:
        return "asset_id must be 0 for ALGO or a positive ASA id"
    if request.asset_decimals < 0:
        return "asset_decimals cannot be negative"
    if request.amount_unit not in {"display", "raw"}:
        return "amount_unit must be display or raw"
    if request.expected_amount_raw <= 0:
        return "expected amount must be positive"
    if request.min_confirmations < 1:
        return "min_confirmations must be at least 1"
    if not encoding.is_valid_address(request.expected_receiver):
        return "expected_receiver is not a valid Algorand address"
    if request.expected_sender and not encoding.is_valid_address(request.expected_sender):
        return "expected_sender is not a valid Algorand address"
    return None


def _checks(request: PaymentVerificationRequest, transaction: dict, observed: dict) -> dict[str, bool]:
    expected_type = "pay" if request.asset_id == 0 else "axfer"
    checks = {
        "confirmed": bool(observed["confirmed_round"]),
        "min_confirmations": observed["confirmations"] >= request.min_confirmations,
        "tx_type": observed["tx_type"] == expected_type,
        "asset_id": observed["asset_id"] == request.asset_id,
        "receiver": observed["receiver"] == request.expected_receiver,
        "amount": observed["amount_raw"] == request.expected_amount_raw,
    }
    if request.expected_sender:
        checks["sender"] = observed["sender"] == request.expected_sender
    if request.note_text is not None:
        checks["note_text"] = observed["note_text"] == request.note_text
    if request.note_prefix is not None:
        checks["note_prefix"] = (observed["note_text"] or "").startswith(request.note_prefix)
    if request.reject_rekey:
        checks["no_rekey"] = not bool(transaction.get("rekey-to"))
    if request.reject_close_to:
        checks["no_close_to"] = not bool(observed["close_to"])
    return checks


def _observed_transaction(transaction: dict, current_round: int, decimals: int) -> dict:
    tx_type = transaction.get("tx-type")
    confirmed_round = int(transaction.get("confirmed-round") or 0)
    confirmations = max(0, current_round - confirmed_round + 1) if current_round and confirmed_round else 0
    sender = transaction.get("sender")
    note_text = _decode_note(transaction.get("note"))

    observed = {
        "tx_type": tx_type,
        "sender": sender,
        "receiver": None,
        "amount_raw": None,
        "amount_display": None,
        "asset_id": 0,
        "confirmed_round": confirmed_round,
        "current_round": current_round,
        "confirmations": confirmations,
        "note_text": note_text,
        "close_to": None,
        "rekey_to": transaction.get("rekey-to"),
    }

    if tx_type == "pay":
        payment = transaction.get("payment-transaction") or {}
        amount_raw = int(payment.get("amount") or 0)
        observed.update(
            {
                "receiver": payment.get("receiver"),
                "amount_raw": amount_raw,
                "amount_display": raw_to_display(amount_raw, 6),
                "asset_id": 0,
                "close_to": payment.get("close-remainder-to"),
            }
        )
    elif tx_type == "axfer":
        transfer = transaction.get("asset-transfer-transaction") or {}
        amount_raw = int(transfer.get("amount") or 0)
        observed.update(
            {
                "receiver": transfer.get("receiver"),
                "amount_raw": amount_raw,
                "amount_display": raw_to_display(amount_raw, decimals),
                "asset_id": int(transfer.get("asset-id") or 0),
                "close_to": transfer.get("close-to"),
            }
        )

    return observed


def _decode_note(note: str | None) -> str | None:
    if not note:
        return None
    try:
        padding = "=" * (-len(note) % 4)
        return base64.b64decode(note + padding).decode("utf-8")
    except Exception:
        return None


def _expected_payload(request: PaymentVerificationRequest) -> dict:
    return {
        "receiver": request.expected_receiver,
        "sender": request.expected_sender,
        "amount_raw": request.expected_amount_raw,
        "amount_display": raw_to_display(request.expected_amount_raw, request.asset_decimals),
        "asset_id": request.asset_id,
        "asset_decimals": request.asset_decimals,
        "note_text": request.note_text,
        "note_prefix": request.note_prefix,
        "min_confirmations": request.min_confirmations,
        "reject_rekey": request.reject_rekey,
        "reject_close_to": request.reject_close_to,
    }


def _result(
    *,
    request: PaymentVerificationRequest,
    ok: bool,
    status: str,
    reason: str | None,
    observed: dict | None = None,
) -> PaymentVerificationResult:
    return PaymentVerificationResult(
        ok=ok,
        status=status,
        reason=reason,
        txid=request.txid,
        asset_id=request.asset_id,
        expected=_expected_payload(request),
        observed=observed or {},
        checks={},
    )
