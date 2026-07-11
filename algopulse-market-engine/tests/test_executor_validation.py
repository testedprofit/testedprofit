from types import SimpleNamespace
import time

from algosdk import account, transaction

from algopulse.executor import ALGORAND_TX_GROUP_LIMIT, ArbitrageExecutor


def _sp():
    return transaction.SuggestedParams(
        fee=1000,
        first=1,
        last=100,
        gh="SGO1GKSFLCQII2T2WTPW3A5F2ZQ4K6K5JH5G2Y33FQ4J6LGQ5Q======",
        flat_fee=True,
    )


def _route(input_asset_id=0):
    middle_asset_id = 31566704 if input_asset_id == 0 else 31566704
    return [
        {
            "venue": "tinyman",
            "pool_id": "tinyman:test",
            "input_asset_id": input_asset_id,
            "output_asset_id": middle_asset_id,
            "input_amount": 5.0,
            "expected_output": 6.0,
        },
        {
            "venue": "pact",
            "pool_id": "pact:1",
            "input_asset_id": middle_asset_id,
            "output_asset_id": input_asset_id,
            "input_amount": 6.0,
            "expected_output": 5.5,
        },
    ]


def _approved_opportunity(**overrides):
    values = {
        "route_hash": "route",
        "input_asset_id": 0,
        "input_amount": 5.0,
        "route": _route(0),
        "status": "approved",
        "risk_rules": {
            "net_profit_after_fees_ok": True,
            "profit_bps_ok": True,
            "fee_buffer_ok": True,
            "app_ids_allowlisted": True,
            "assets_allowlisted": True,
        },
    }
    values.update(overrides)
    return values


def _settings(**overrides):
    values = {
        "allow_non_algo_starting_routes": False,
        "allow_non_algo_live_submission": False,
        "max_live_trade_size": 25.0,
        "max_route_age_seconds": 5.0,
        "max_group_fee_algos": 0.05,
        "min_net_profit_algos": 0.25,
        "min_net_profit_input_units": 0.25,
        "enable_live_execution": False,
        "execute_approved": False,
        "unsigned_executor_only": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class _FakeAlgod:
    def account_info(self, _address):
        return {
            "amount": 2_000_000,
            "min-balance": 100_000,
            "assets": [
                {
                    "asset-id": 3169177585,
                    "amount": 12_500_000,
                }
            ],
        }

    def asset_info(self, _asset_id):
        return {"params": {"decimals": 6}}


def test_transaction_validator_rejects_close_remainder():
    _, sender = account.generate_account()
    _, receiver = account.generate_account()
    _, attacker = account.generate_account()
    txn = transaction.PaymentTxn(
        sender=sender,
        sp=_sp(),
        receiver=receiver,
        amt=1000,
        close_remainder_to=attacker,
    )
    executor = object.__new__(ArbitrageExecutor)

    result = executor._validate_transaction_group(
        txns=[txn],
        address=sender,
        expected_app_ids=[],
        expected_asset_ids=[],
    )

    assert not result["ok"]
    assert "rekey or close-out" in result["reason"]


def test_transaction_validator_rejects_unexpected_app_id():
    _, sender = account.generate_account()
    txn = transaction.ApplicationNoOpTxn(sender=sender, sp=_sp(), index=12345)
    executor = object.__new__(ArbitrageExecutor)

    result = executor._validate_transaction_group(
        txns=[txn],
        address=sender,
        expected_app_ids=[999],
        expected_asset_ids=[],
    )

    assert not result["ok"]
    assert "unexpected app id" in result["reason"]


def test_executor_requires_explicit_non_algo_start_enablement():
    executor = object.__new__(ArbitrageExecutor)
    executor.settings = _settings(allow_non_algo_starting_routes=False)
    opportunity = _approved_opportunity(input_asset_id=3169177585, route=_route(3169177585))

    result = executor.execute(opportunity)

    assert not result["submitted"]
    assert "non-ALGO starting routes are disabled" in result["reason"]


def test_executor_rejects_three_leg_routes_before_wallet_checks():
    executor = object.__new__(ArbitrageExecutor)
    executor.settings = _settings()
    route = [
        {
            "venue": "tinyman",
            "pool_id": "tinyman:ALGO-ASA",
            "input_asset_id": 0,
            "output_asset_id": 3169177585,
            "input_amount": 1.0,
            "expected_output": 1000.0,
        },
        {
            "venue": "pact",
            "pool_id": "pact:ASA-USDC",
            "input_asset_id": 3169177585,
            "output_asset_id": 31566704,
            "input_amount": 1000.0,
            "expected_output": 0.2,
        },
        {
            "venue": "tinyman",
            "pool_id": "tinyman:ALGO-USDC",
            "input_asset_id": 31566704,
            "output_asset_id": 0,
            "input_amount": 0.2,
            "expected_output": 1.01,
        },
    ]
    opportunity = _approved_opportunity(
        route_hash="triangle",
        input_amount=1.0,
        route=route,
    )

    result = executor.execute(opportunity)

    assert not result["submitted"]
    assert "only two-leg routes are supported" in result["reason"]


def test_transaction_validator_rejects_group_above_algorand_limit():
    _, sender = account.generate_account()
    _, receiver = account.generate_account()
    txns = [
        transaction.PaymentTxn(sender=sender, sp=_sp(), receiver=receiver, amt=1000)
        for _ in range(ALGORAND_TX_GROUP_LIMIT + 1)
    ]
    executor = object.__new__(ArbitrageExecutor)

    result = executor._validate_transaction_group(
        txns=txns,
        address=sender,
        expected_app_ids=[],
        expected_asset_ids=[],
    )

    assert not result["ok"]
    assert result["max_tx_group_size"] == ALGORAND_TX_GROUP_LIMIT
    assert "TX_GROUP_LIMIT" in result["reason"]


def test_atomic_group_builder_rejects_group_above_algorand_limit():
    executor = object.__new__(ArbitrageExecutor)

    def fake_build_leg(leg, address, input_raw=None):
        tx_count = 9 if leg["venue"] == "tinyman" else ALGORAND_TX_GROUP_LIMIT - 8
        return {
            "ok": True,
            "transactions": [object() for _ in range(tx_count)],
            "minimum_output_raw": input_raw or 1,
            "minimum_output_display": 1.0,
            "expected_output_display": 1.0,
            "expected_app_ids": [1],
            "expected_asset_ids": [31566704],
        }

    executor._build_leg = fake_build_leg

    result = executor._build_atomic_group(route=_route(), address="ADDR")

    assert not result["ok"]
    assert result["tx_count"] == ALGORAND_TX_GROUP_LIMIT + 1
    assert result["max_tx_group_size"] == ALGORAND_TX_GROUP_LIMIT


def test_executor_rejects_stale_routes_before_wallet_checks():
    executor = object.__new__(ArbitrageExecutor)
    executor.settings = _settings(max_route_age_seconds=2.0)
    opportunity = _approved_opportunity(created_at=time.time() - 30)

    result = executor.execute(opportunity)

    assert not result["submitted"]
    assert "route is stale" in result["reason"]
    assert result["route_age_seconds"] >= 2.0


def test_executor_requires_risk_approved_opportunity_before_wallet_checks(monkeypatch):
    executor = object.__new__(ArbitrageExecutor)
    executor.settings = _settings()
    monkeypatch.setattr(
        executor,
        "_resolve_address",
        lambda: (_ for _ in ()).throw(AssertionError("wallet lookup should not run without approval")),
    )

    result = executor.execute(
        _approved_opportunity(
            status="rejected",
            skip_reason="profit_bps_ok",
            risk_rules={"profit_bps_ok": False},
        )
    )

    assert result["submitted"] is False
    assert "risk-approved opportunity" in result["reason"]
    assert result["approval_status"] == "rejected"


def test_executor_rejects_approved_status_with_failed_risk_receipt(monkeypatch):
    executor = object.__new__(ArbitrageExecutor)
    executor.settings = _settings()
    monkeypatch.setattr(
        executor,
        "_resolve_address",
        lambda: (_ for _ in ()).throw(AssertionError("wallet lookup should not run when risk receipt failed")),
    )

    result = executor.execute(
        _approved_opportunity(
            risk_rules={
                "net_profit_after_fees_ok": True,
                "profit_bps_ok": False,
            }
        )
    )

    assert result["submitted"] is False
    assert "failed rules" in result["reason"]
    assert result["failed_risk_rules"] == ["profit_bps_ok"]


def test_executor_unsigned_only_blocks_signing_even_when_live_flags_are_enabled(monkeypatch):
    _, sender = account.generate_account()
    _, receiver = account.generate_account()
    executor = object.__new__(ArbitrageExecutor)
    executor.settings = _settings(
        enable_live_execution=True,
        execute_approved=True,
        unsigned_executor_only=True,
        min_net_profit_algos=0.0,
        min_net_profit_input_units=0.0,
    )
    executor.algod = _FakeAlgod()
    monkeypatch.setattr(executor, "_resolve_address", lambda: sender)
    monkeypatch.setattr(executor, "_check_opted_in", lambda _address, _asset_ids: {"ok": True})
    monkeypatch.setattr(
        executor,
        "_check_trade_inventory",
        lambda _address, _asset_id, _amount: {"ok": True, "inventory": {"spendable_algo": 10.0}},
    )
    monkeypatch.setattr(
        executor,
        "_balance_snapshot",
        lambda _address, _asset_ids: {"ok": True, "balances": {"0": {"amount": 10.0}}},
    )
    monkeypatch.setattr(
        executor,
        "_build_atomic_group",
        lambda route, address: {
            "ok": True,
            "transactions": [transaction.PaymentTxn(sender=sender, sp=_sp(), receiver=receiver, amt=1000)],
            "final_expected_output_display": 5.5,
            "final_min_output_display": 5.5,
            "expected_app_ids": [],
            "expected_asset_ids": [],
        },
    )
    monkeypatch.setattr(
        executor,
        "_private_key",
        lambda: (_ for _ in ()).throw(AssertionError("signing path should not be reached")),
    )

    result = executor.execute(
        _approved_opportunity(created_at=time.time())
    )

    assert result["dry_run"] is True
    assert result["submitted"] is False
    assert result["unsigned_group"] is True
    assert result["signed"] is False
    assert result["signing_blocked"] is True
    assert result["tx_count"] == 1
    assert result["max_tx_group_size"] == ALGORAND_TX_GROUP_LIMIT


def test_executor_requires_isolated_signer_handoff_instead_of_direct_signing(monkeypatch):
    _, sender = account.generate_account()
    _, receiver = account.generate_account()
    executor = object.__new__(ArbitrageExecutor)
    executor.settings = _settings(
        enable_live_execution=True,
        execute_approved=True,
        unsigned_executor_only=False,
        min_net_profit_algos=0.0,
        min_net_profit_input_units=0.0,
    )
    executor.algod = _FakeAlgod()
    monkeypatch.setattr(executor, "_resolve_address", lambda: sender)
    monkeypatch.setattr(executor, "_check_opted_in", lambda _address, _asset_ids: {"ok": True})
    monkeypatch.setattr(
        executor,
        "_check_trade_inventory",
        lambda _address, _asset_id, _amount: {"ok": True, "inventory": {"spendable_algo": 10.0}},
    )
    monkeypatch.setattr(
        executor,
        "_balance_snapshot",
        lambda _address, _asset_ids: {
            "ok": True,
            "balances": {"0": {"amount": 10.0, "minimum_balance": 0.1}},
        },
    )
    monkeypatch.setattr(
        executor,
        "_build_atomic_group",
        lambda route, address: {
            "ok": True,
            "transactions": [transaction.PaymentTxn(sender=sender, sp=_sp(), receiver=receiver, amt=1000)],
            "final_expected_output_display": 5.5,
            "final_min_output_display": 5.5,
            "expected_app_ids": [],
            "expected_asset_ids": [],
        },
    )
    monkeypatch.setattr(
        executor,
        "_private_key",
        lambda: (_ for _ in ()).throw(AssertionError("main executor must not sign directly")),
    )
    monkeypatch.setattr(
        executor.algod,
        "send_transactions",
        lambda _signed: (_ for _ in ()).throw(AssertionError("main executor must not submit directly")),
        raising=False,
    )

    result = executor.execute(
        _approved_opportunity(created_at=time.time())
    )

    assert result["submitted"] is False
    assert result["signed"] is False
    assert result["signing_blocked"] is True
    assert "isolated signer handoff required" in result["reason"]
    assert result["signer_handoff"]["route_hash"] == "route"
    assert result["signer_handoff"]["wallet_balance_algos"] == 10.0


def test_trade_inventory_checks_non_algo_balance_and_algo_fee_budget():
    executor = object.__new__(ArbitrageExecutor)
    executor.settings = _settings()
    executor.algod = _FakeAlgod()

    result = executor._check_trade_inventory("ADDR", 3169177585, 5.0)

    assert result["ok"]
    assert result["inventory"]["input_asset_balance"] == 12.5
    assert result["inventory"]["spendable_algo"] == 1.9
