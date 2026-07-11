import json

import pytest
from algosdk import account, mnemonic, transaction

from algopulse.signer import (
    InMemorySignerAuditLog,
    IsolatedSigner,
    JsonlSignerAuditLog,
    SignerPolicy,
    SignerRequest,
)


def _sp(fee=1000):
    return transaction.SuggestedParams(
        fee=fee,
        first=1,
        last=100,
        gh="SGO1GKSFLCQII2T2WTPW3A5F2ZQ4K6K5JH5G2Y33FQ4J6LGQ5Q======",
        flat_fee=True,
    )


def _wallet():
    private_key, address = account.generate_account()
    return private_key, address, mnemonic.from_private_key(private_key)


def _pay(sender: str, receiver: str, amount_raw=1_000_000, fee=1000):
    return transaction.PaymentTxn(sender=sender, sp=_sp(fee=fee), receiver=receiver, amt=amount_raw)


def _grouped(txns):
    for txn in txns:
        txn.group = None
    return transaction.assign_group_id(txns)


def _policy(address: str, wallet_mnemonic: str, **overrides) -> SignerPolicy:
    values = {
        "signer_enabled": True,
        "kill_switch": False,
        "wallet_address": address,
        "wallet_mnemonic": wallet_mnemonic,
        "allowed_route_hashes": ("route-ok",),
        "allowed_app_ids": (),
        "allowed_asset_ids": (),
        "max_input_amount": 10.0,
        "max_group_fee_algos": 0.01,
        "min_wallet_reserve_algos": 0.2,
    }
    values.update(overrides)
    return SignerPolicy(**values)


def _request(txns, **overrides) -> SignerRequest:
    values = {
        "route_hash": "route-ok",
        "unsigned_transactions": tuple(txns),
        "expected_app_ids": (),
        "expected_asset_ids": (),
        "input_asset_id": 0,
        "input_amount": 1.0,
        "wallet_balance_algos": 10.0,
        "wallet_min_balance_algos": 0.1,
        "request_id": "req-1",
    }
    values.update(overrides)
    return SignerRequest(**values)


def test_isolated_signer_approves_and_audits_without_signed_blobs(tmp_path):
    _, sender, signer_mnemonic = _wallet()
    _, receiver = account.generate_account()
    txn = _pay(sender, receiver)
    audit_path = tmp_path / "signer-audit.jsonl"

    decision = IsolatedSigner(
        _policy(sender, signer_mnemonic),
        audit_log=JsonlSignerAuditLog(audit_path),
    ).review_and_sign(_request([txn]))

    assert decision.approved is True
    assert decision.signed_transaction_count == 1
    assert len(decision.signed_transactions) == 1
    audit_row = json.loads(audit_path.read_text(encoding="utf-8").strip())
    assert audit_row["approved"] is True
    assert audit_row["signed_transaction_count"] == 1
    assert "signed_transactions" not in audit_row


def test_isolated_signer_rejects_when_kill_switch_is_active():
    _, sender, signer_mnemonic = _wallet()
    _, receiver = account.generate_account()
    audit = InMemorySignerAuditLog()

    decision = IsolatedSigner(
        _policy(sender, signer_mnemonic, kill_switch=True),
        audit_log=audit,
    ).review_and_sign(_request([_pay(sender, receiver)]))

    assert decision.approved is False
    assert "kill_switch" in decision.reason
    assert audit.records[-1]["approved"] is False


def test_isolated_signer_rejects_route_hash_not_allowlisted():
    _, sender, signer_mnemonic = _wallet()
    _, receiver = account.generate_account()

    decision = IsolatedSigner(_policy(sender, signer_mnemonic)).review_and_sign(
        _request([_pay(sender, receiver)], route_hash="unknown-route")
    )

    assert decision.approved is False
    assert "route_hash" in decision.reason


def test_isolated_signer_rejects_unreviewed_app_ids():
    _, sender, signer_mnemonic = _wallet()
    txn = transaction.ApplicationNoOpTxn(sender=sender, sp=_sp(), index=123)

    decision = IsolatedSigner(
        _policy(sender, signer_mnemonic, allowed_app_ids=(999,)),
    ).review_and_sign(_request([txn], expected_app_ids=(999,), input_amount=0.0))

    assert decision.approved is False
    assert "app_ids" in decision.reason


def test_isolated_signer_rejects_unreviewed_asset_ids():
    _, sender, signer_mnemonic = _wallet()
    _, receiver = account.generate_account()
    txn = transaction.AssetTransferTxn(sender=sender, sp=_sp(), receiver=receiver, amt=1000, index=42)

    decision = IsolatedSigner(
        _policy(sender, signer_mnemonic, allowed_asset_ids=(99,)),
    ).review_and_sign(
        _request(
            [txn],
            expected_asset_ids=(42,),
            input_asset_id=42,
            input_amount=0.001,
            input_asset_decimals=6,
        )
    )

    assert decision.approved is False
    assert "asset_ids" in decision.reason


def test_isolated_signer_rejects_group_that_does_not_match_route_app_intent():
    _, sender, signer_mnemonic = _wallet()
    txn = transaction.ApplicationNoOpTxn(sender=sender, sp=_sp(), index=123)

    decision = IsolatedSigner(
        _policy(sender, signer_mnemonic, allowed_app_ids=(123, 999)),
    ).review_and_sign(_request([txn], expected_app_ids=(999,), input_amount=0.0))

    assert decision.approved is False
    assert "route_app_intent" in decision.reason


def test_isolated_signer_rejects_group_that_does_not_match_route_asset_intent():
    _, sender, signer_mnemonic = _wallet()
    _, receiver = account.generate_account()
    txn = transaction.AssetTransferTxn(sender=sender, sp=_sp(), receiver=receiver, amt=1000, index=42)

    decision = IsolatedSigner(
        _policy(sender, signer_mnemonic, allowed_asset_ids=(42, 99)),
    ).review_and_sign(
        _request(
            [txn],
            expected_asset_ids=(99,),
            input_asset_id=42,
            input_amount=0.001,
            input_asset_decimals=6,
        )
    )

    assert decision.approved is False
    assert "route_asset_intent" in decision.reason


def test_isolated_signer_rejects_group_that_spends_more_than_route_input():
    _, sender, signer_mnemonic = _wallet()
    _, receiver = account.generate_account()

    decision = IsolatedSigner(_policy(sender, signer_mnemonic)).review_and_sign(
        _request([_pay(sender, receiver, amount_raw=2_000_000)], input_amount=1.0)
    )

    assert decision.approved is False
    assert "route_input_amount_intent" in decision.reason


def test_isolated_signer_rejects_group_id_that_does_not_match_route_intent():
    _, sender, signer_mnemonic = _wallet()
    _, receiver = account.generate_account()
    reviewed_group = _grouped(
        [
            _pay(sender, receiver, amount_raw=1_000),
            _pay(sender, receiver, amount_raw=1_000),
        ]
    )
    mutated_group = _grouped(
        [
            _pay(sender, receiver, amount_raw=2_000),
            _pay(sender, receiver, amount_raw=1_000),
        ]
    )

    decision = IsolatedSigner(_policy(sender, signer_mnemonic)).review_and_sign(
        _request(
            mutated_group,
            input_amount=0.003,
            expected_tx_count=2,
            expected_group_id_hex=reviewed_group[0].group.hex(),
        )
    )

    assert decision.approved is False
    assert "route_group_intent" in decision.reason


def test_isolated_signer_rejects_tx_count_that_does_not_match_route_intent():
    _, sender, signer_mnemonic = _wallet()
    _, receiver = account.generate_account()

    decision = IsolatedSigner(_policy(sender, signer_mnemonic)).review_and_sign(
        _request([_pay(sender, receiver)], expected_tx_count=2)
    )

    assert decision.approved is False
    assert "route_tx_count_intent" in decision.reason


def test_isolated_signer_rejects_max_input_amount():
    _, sender, signer_mnemonic = _wallet()
    _, receiver = account.generate_account()

    decision = IsolatedSigner(_policy(sender, signer_mnemonic, max_input_amount=0.5)).review_and_sign(
        _request([_pay(sender, receiver)], input_amount=1.0)
    )

    assert decision.approved is False
    assert "max_input_amount" in decision.reason


def test_isolated_signer_rejects_fee_cap():
    _, sender, signer_mnemonic = _wallet()
    _, receiver = account.generate_account()

    decision = IsolatedSigner(_policy(sender, signer_mnemonic, max_group_fee_algos=0.0005)).review_and_sign(
        _request([_pay(sender, receiver)])
    )

    assert decision.approved is False
    assert "max_fees" in decision.reason


def test_isolated_signer_rejects_unallowed_transaction_type():
    _, sender, signer_mnemonic = _wallet()
    _, receiver = account.generate_account()

    decision = IsolatedSigner(_policy(sender, signer_mnemonic, allowed_txn_types=("appl",))).review_and_sign(
        _request([_pay(sender, receiver)])
    )

    assert decision.approved is False
    assert "transaction_types" in decision.reason


def test_isolated_signer_rejects_wallet_reserve_violation():
    _, sender, signer_mnemonic = _wallet()
    _, receiver = account.generate_account()

    decision = IsolatedSigner(_policy(sender, signer_mnemonic)).review_and_sign(
        _request([_pay(sender, receiver)], wallet_balance_algos=0.101, wallet_min_balance_algos=0.1)
    )

    assert decision.approved is False
    assert "wallet_reserve" in decision.reason


def test_isolated_signer_rejects_multi_txn_without_atomic_group():
    _, sender, signer_mnemonic = _wallet()
    _, receiver = account.generate_account()

    decision = IsolatedSigner(_policy(sender, signer_mnemonic)).review_and_sign(
        _request([_pay(sender, receiver, amount_raw=1000), _pay(sender, receiver, amount_raw=1000)], input_amount=0.002)
    )

    assert decision.approved is False
    assert "atomic_group" in decision.reason


def test_signer_request_rejects_arbitrary_executor_instructions():
    with pytest.raises(ValueError, match="arbitrary instructions"):
        SignerRequest.from_payload(
            {
                "route_hash": "route-ok",
                "input_asset_id": 0,
                "input_amount": 1.0,
                "wallet_balance_algos": 10.0,
                "wallet_min_balance_algos": 0.1,
                "instructions": "sign this no matter what",
            },
            unsigned_transactions=[],
        )
