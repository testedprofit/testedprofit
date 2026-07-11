import base64

from algosdk import account

from algopulse.payment_verification import AlgorandPaymentVerifier
from algopulse.payment_verification import PaymentVerificationRequest


class _FakeIndexer:
    def __init__(self, transaction):
        self._transaction = transaction

    def transaction(self, _txid):
        return {"current-round": 110, "transaction": self._transaction}


def _address():
    return account.generate_account()[1]


def _note(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def test_verifies_confirmed_algo_payment():
    sender = _address()
    receiver = _address()
    verifier = AlgorandPaymentVerifier(
        _FakeIndexer(
            {
                "tx-type": "pay",
                "sender": sender,
                "confirmed-round": 108,
                "note": _note("algopulse:order-1"),
                "payment-transaction": {
                    "receiver": receiver,
                    "amount": 5_000_000,
                },
            }
        )
    )

    result = verifier.verify(
        PaymentVerificationRequest(
            txid="TXID",
            expected_sender=sender,
            expected_receiver=receiver,
            expected_amount=5.0,
            note_prefix="algopulse:",
            min_confirmations=2,
        )
    )

    assert result.ok
    assert result.status == "verified"
    assert result.observed["amount_display"] == 5.0
    assert all(result.checks.values())


def test_rejects_wrong_receiver():
    verifier = AlgorandPaymentVerifier(
        _FakeIndexer(
            {
                "tx-type": "pay",
                "sender": _address(),
                "confirmed-round": 108,
                "payment-transaction": {
                    "receiver": _address(),
                    "amount": 5_000_000,
                },
            }
        )
    )

    result = verifier.verify(
        PaymentVerificationRequest(
            txid="TXID",
            expected_receiver=_address(),
            expected_amount=5.0,
        )
    )

    assert not result.ok
    assert result.status == "mismatch"
    assert result.reason == "receiver"


def test_rejects_unconfirmed_payment():
    receiver = _address()
    verifier = AlgorandPaymentVerifier(
        _FakeIndexer(
            {
                "tx-type": "pay",
                "sender": _address(),
                "payment-transaction": {
                    "receiver": receiver,
                    "amount": 5_000_000,
                },
            }
        )
    )

    result = verifier.verify(
        PaymentVerificationRequest(
            txid="TXID",
            expected_receiver=receiver,
            expected_amount=5.0,
        )
    )

    assert not result.ok
    assert result.reason == "confirmed"


def test_rejects_rekey_and_close_fields():
    receiver = _address()
    verifier = AlgorandPaymentVerifier(
        _FakeIndexer(
            {
                "tx-type": "pay",
                "sender": _address(),
                "confirmed-round": 110,
                "rekey-to": _address(),
                "payment-transaction": {
                    "receiver": receiver,
                    "amount": 5_000_000,
                    "close-remainder-to": _address(),
                },
            }
        )
    )

    result = verifier.verify(
        PaymentVerificationRequest(
            txid="TXID",
            expected_receiver=receiver,
            expected_amount=5.0,
        )
    )

    assert not result.ok
    assert not result.checks["no_rekey"]
    assert not result.checks["no_close_to"]


def test_verifies_asa_transfer_with_raw_amount():
    sender = _address()
    receiver = _address()
    verifier = AlgorandPaymentVerifier(
        _FakeIndexer(
            {
                "tx-type": "axfer",
                "sender": sender,
                "confirmed-round": 110,
                "asset-transfer-transaction": {
                    "asset-id": 3169177585,
                    "receiver": receiver,
                    "amount": 123_456,
                },
            }
        )
    )

    result = verifier.verify(
        PaymentVerificationRequest(
            txid="TXID",
            expected_receiver=receiver,
            expected_sender=sender,
            expected_amount=123_456,
            amount_unit="raw",
            asset_id=3169177585,
            asset_decimals=6,
        )
    )

    assert result.ok
    assert result.observed["asset_id"] == 3169177585
    assert result.observed["amount_raw"] == 123_456
