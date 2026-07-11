from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

from algosdk import account, constants, mnemonic, transaction

from algopulse.algorand import build_algod_client, display_to_raw, raw_to_display
from algopulse.config import Settings
from algopulse.models import Opportunity


ALGORAND_TX_GROUP_LIMIT = int(constants.TX_GROUP_LIMIT)


class LiveExecutionDisabled(RuntimeError):
    pass


@dataclass(frozen=True)
class DryRunExecutionPlan:
    route_hash: str
    route: list[dict]
    expected_net_profit: float
    policy_note: str


class DryRunExecutor:
    def build_plan(self, opportunity: Opportunity) -> DryRunExecutionPlan:
        return DryRunExecutionPlan(
            route_hash=opportunity.route_hash,
            route=opportunity.route,
            expected_net_profit=opportunity.expected_net_profit,
            policy_note="Dry run only. Live signing is intentionally disabled in Phase 0 starter.",
        )


class ArbitrageExecutor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.algod = build_algod_client(settings)
        self._tinyman_client = None
        self._pact_client = None

    def execute(self, opportunity: Opportunity | dict[str, Any]) -> dict:
        data = opportunity.to_dict() if isinstance(opportunity, Opportunity) else opportunity
        route = data.get("route") or []
        approval_check = self._risk_approval_check(data)
        if not approval_check["ok"]:
            return self._not_submitted(approval_check["reason"], data, extra=approval_check)

        if len(route) != 2:
            return self._not_submitted("only two-leg routes are supported for atomic execution", data)

        route_age_seconds = self._route_age_seconds(data)
        if route_age_seconds > self.settings.max_route_age_seconds:
            return self._not_submitted(
                f"route is stale: {route_age_seconds:.2f}s old exceeds {self.settings.max_route_age_seconds:.2f}s cutoff",
                data,
                extra={"route_age_seconds": route_age_seconds},
            )

        input_asset_id = int(data["input_asset_id"])
        input_amount = float(data["input_amount"])
        input_is_algo = input_asset_id == 0
        if int(route[0]["input_asset_id"]) != input_asset_id:
            return self._not_submitted("route first leg does not match opportunity input asset", data)
        if int(route[-1]["output_asset_id"]) != input_asset_id:
            return self._not_submitted("route is not a round trip back to the starting asset", data)
        if not input_is_algo and not self.settings.allow_non_algo_starting_routes:
            return self._not_submitted(
                "non-ALGO starting routes are disabled; set ALGO_PULSE_ALLOW_NON_ALGO_STARTING_ROUTES=true "
                "after reviewing starting-asset profit math",
                data,
            )
        if input_amount > self.settings.max_live_trade_size:
            return self._not_submitted("route exceeds max live trade size", data)

        address = self._resolve_address()
        if not address:
            return self._not_submitted("missing trader address or signer secret", data)

        opt_in_check = self._check_opted_in(address, self._non_algo_assets(route))
        if not opt_in_check["ok"]:
            return self._not_submitted(opt_in_check["reason"], data)

        inventory_check = self._check_trade_inventory(address, input_asset_id, input_amount)
        if not inventory_check["ok"]:
            return self._not_submitted(inventory_check["reason"], data, extra=inventory_check)

        balance_asset_ids = self._route_asset_ids(route) | {0}
        before_balances = self._balance_snapshot(address, balance_asset_ids)
        if not before_balances["ok"]:
            return self._not_submitted(before_balances["reason"], data, extra={"balance_reconciliation": before_balances})

        built = self._build_atomic_group(route=route, address=address)
        if not built["ok"]:
            return self._not_submitted(built["reason"], data, extra=built)

        txns = built["transactions"]
        group_check = self._validate_transaction_group(
            txns=txns,
            address=address,
            expected_app_ids=built["expected_app_ids"],
            expected_asset_ids=built["expected_asset_ids"],
        )
        if not group_check["ok"]:
            return self._not_submitted(group_check["reason"], data, extra=group_check)

        fee_algos = sum(int(getattr(txn, "fee", 0) or 0) for txn in txns) / 1_000_000
        if fee_algos > self.settings.max_group_fee_algos:
            return self._not_submitted(
                f"group fee {fee_algos:.6f} exceeds max {self.settings.max_group_fee_algos:.6f} ALGO",
                data,
                extra={"fee_algos": fee_algos},
            )

        expected_deltas = self._expected_balance_deltas(
            input_asset_id=input_asset_id,
            input_amount=input_amount,
            minimum_final_output=built["final_min_output_display"],
            fee_algos=fee_algos,
        )

        conservative_profit_input_units = built["final_min_output_display"] - input_amount
        if input_is_algo:
            conservative_profit_algos = conservative_profit_input_units - fee_algos
            min_conservative_profit = self.settings.min_net_profit_algos
            profit_floor_detail = (
                f"{conservative_profit_algos:.6f} ALGO < {min_conservative_profit:.6f} ALGO"
            )
        else:
            conservative_profit_algos = None
            min_conservative_profit = self.settings.min_net_profit_input_units
            profit_floor_detail = (
                f"{conservative_profit_input_units:.6f} input units < {min_conservative_profit:.6f} input units"
            )

        conservative_profit_for_floor = (
            conservative_profit_algos if input_is_algo else conservative_profit_input_units
        )
        if conservative_profit_for_floor < min_conservative_profit:
            return self._not_submitted(
                "conservative profit below configured net-profit floor after slippage: "
                f"{profit_floor_detail}",
                data,
                extra={
                    "fee_algos": fee_algos,
                    "profit_asset_id": input_asset_id,
                    "conservative_profit": conservative_profit_algos,
                    "conservative_profit_algos": conservative_profit_algos,
                    "conservative_profit_input_units": conservative_profit_input_units,
                    "min_net_profit_algos": min_conservative_profit,
                    "min_net_profit_input_units": self.settings.min_net_profit_input_units,
                },
            )

        for txn in txns:
            txn.group = None
        grouped_txns = transaction.assign_group_id(txns)
        group_id = grouped_txns[0].group.hex() if grouped_txns and grouped_txns[0].group else None

        dry_run_result = {
            "submitted": False,
            "dry_run": True,
            "unsigned_group": True,
            "signed": False,
            "atomic_group": True,
            "route_hash": data["route_hash"],
            "tx_count": len(grouped_txns),
            "max_tx_group_size": ALGORAND_TX_GROUP_LIMIT,
            "group_size_ok": len(grouped_txns) <= ALGORAND_TX_GROUP_LIMIT,
            "group_id_hex": group_id,
            "fee_algos": fee_algos,
            "expected_final_output": built["final_expected_output_display"],
            "minimum_final_output": built["final_min_output_display"],
            "profit_asset_id": input_asset_id,
            "conservative_profit": conservative_profit_algos,
            "conservative_profit_algos": conservative_profit_algos,
            "conservative_profit_input_units": conservative_profit_input_units,
            "min_net_profit_algos": self.settings.min_net_profit_algos,
            "min_net_profit_input_units": self.settings.min_net_profit_input_units,
            "non_algo_starting_route": not input_is_algo,
            "address": address,
            "wallet_inventory": inventory_check.get("inventory"),
            "route_age_seconds": route_age_seconds,
            "quote_refreshed_at": time.time(),
            "balance_reconciliation": self._planned_reconciliation(
                before_balances=before_balances,
                expected_deltas=expected_deltas,
            ),
        }

        if getattr(self.settings, "unsigned_executor_only", True):
            dry_run_result["reason"] = "unsigned executor only; signing disabled before isolated signer review"
            dry_run_result["signing_blocked"] = True
            return dry_run_result
        if not self.settings.enable_live_execution or not self.settings.execute_approved:
            dry_run_result["reason"] = "execution flags are disabled; built atomic group only"
            return dry_run_result
        if not input_is_algo and not self.settings.allow_non_algo_live_submission:
            dry_run_result["reason"] = (
                "non-ALGO live submission is disabled; atomic dry-run group built, but signing is blocked "
                "until ALGO-equivalent profit reconciliation is reviewed"
            )
            return dry_run_result

        algo_balance = before_balances.get("balances", {}).get("0", {})
        dry_run_result["reason"] = "isolated signer handoff required; main executor never signs or submits"
        dry_run_result["signing_blocked"] = True
        dry_run_result["signer_handoff"] = {
            "route_hash": data["route_hash"],
            "expected_app_ids": built["expected_app_ids"],
            "expected_asset_ids": built["expected_asset_ids"],
            "expected_tx_count": len(grouped_txns),
            "expected_group_id_hex": group_id,
            "input_asset_id": input_asset_id,
            "input_amount": input_amount,
            "input_asset_decimals": inventory_check.get("inventory", {}).get("input_asset_decimals", 6),
            "fee_algos": fee_algos,
            "wallet_balance_algos": algo_balance.get("amount"),
            "wallet_min_balance_algos": algo_balance.get("minimum_balance"),
            "tx_count": len(grouped_txns),
            "max_tx_group_size": ALGORAND_TX_GROUP_LIMIT,
            "note": "send the grouped unsigned transactions only to the isolated signer service after route review",
        }
        return dry_run_result

    def _risk_approval_check(self, opportunity: dict) -> dict:
        status = str(opportunity.get("status", "")).strip().lower()
        risk_rules = opportunity.get("risk_rules")
        failed_rules = []
        if isinstance(risk_rules, dict):
            failed_rules = sorted(str(name) for name, passed in risk_rules.items() if not bool(passed))
        if status != "approved":
            return {
                "ok": False,
                "reason": "execution requires a risk-approved opportunity",
                "approval_status": status or "missing",
            }
        if not isinstance(risk_rules, dict) or not risk_rules:
            return {
                "ok": False,
                "reason": "execution requires a risk approval rule receipt",
                "approval_status": status,
            }
        if failed_rules:
            return {
                "ok": False,
                "reason": f"risk approval receipt contains failed rules: {failed_rules}",
                "approval_status": status,
                "failed_risk_rules": failed_rules,
            }
        if opportunity.get("skip_reason"):
            return {
                "ok": False,
                "reason": f"risk-approved opportunity cannot carry skip_reason: {opportunity.get('skip_reason')}",
                "approval_status": status,
            }
        return {"ok": True, "approval_status": status}

    def _build_atomic_group(self, route: list[dict], address: str) -> dict:
        first = self._build_leg(route[0], address=address)
        if not first["ok"]:
            return first
        second_input_raw = first["minimum_output_raw"]
        second = self._build_leg(route[1], address=address, input_raw=second_input_raw)
        if not second["ok"]:
            return second
        txns = first["transactions"] + second["transactions"]
        if len(txns) > ALGORAND_TX_GROUP_LIMIT:
            return {
                "ok": False,
                "reason": (
                    f"transaction group too large: {len(txns)} exceeds "
                    f"TX_GROUP_LIMIT {ALGORAND_TX_GROUP_LIMIT}"
                ),
                "tx_count": len(txns),
                "max_tx_group_size": ALGORAND_TX_GROUP_LIMIT,
            }
        return {
            "ok": True,
            "transactions": txns,
            "tx_count": len(txns),
            "max_tx_group_size": ALGORAND_TX_GROUP_LIMIT,
            "final_expected_output_display": second["expected_output_display"],
            "final_min_output_display": second["minimum_output_display"],
            "expected_app_ids": sorted(set(first["expected_app_ids"] + second["expected_app_ids"])),
            "expected_asset_ids": sorted(set(first["expected_asset_ids"] + second["expected_asset_ids"])),
        }

    def _build_leg(self, leg: dict, address: str, input_raw: int | None = None) -> dict:
        venue = leg["venue"]
        if venue == "tinyman":
            return self._build_tinyman_leg(leg, address, input_raw)
        if venue == "pact":
            return self._build_pact_leg(leg, address, input_raw)
        return {"ok": False, "reason": f"unsupported venue for execution: {venue}"}

    def _build_tinyman_leg(self, leg: dict, address: str, input_raw: int | None) -> dict:
        from tinyman.assets import AssetAmount

        pool = self.tinyman_client.fetch_pool(int(leg["input_asset_id"]), int(leg["output_asset_id"]), fetch=True)
        asset_in = pool.asset_1 if int(pool.asset_1.id) == int(leg["input_asset_id"]) else pool.asset_2
        amount_raw = input_raw if input_raw is not None else display_to_raw(float(leg["input_amount"]), asset_in.decimals)
        quote = pool.fetch_fixed_input_swap_quote(
            AssetAmount(asset_in, amount_raw),
            slippage=self.settings.slippage_bps / 10_000,
            refresh=True,
        )
        group = pool.prepare_swap_transactions_from_quote(quote, user_address=address)
        output_decimals = quote.amount_out.asset.decimals
        return {
            "ok": True,
            "transactions": group.transactions,
            "expected_output_raw": quote.amount_out.amount,
            "minimum_output_raw": quote.amount_out_with_slippage.amount,
            "expected_output_display": raw_to_display(quote.amount_out.amount, output_decimals),
            "minimum_output_display": raw_to_display(quote.amount_out_with_slippage.amount, output_decimals),
            "expected_app_ids": [int(pool.validator_app_id)],
            "expected_asset_ids": sorted({int(leg["input_asset_id"]), int(leg["output_asset_id"])} - {0}),
        }

    def _build_pact_leg(self, leg: dict, address: str, input_raw: int | None) -> dict:
        app_id = self._pact_app_id_from_pool_id(leg["pool_id"])
        pool = self.pact_client.fetch_pool_by_id(app_id) if app_id else self.pact_client.fetch_pools_by_assets(
            int(leg["input_asset_id"]),
            int(leg["output_asset_id"]),
        )[0]
        asset_in = pool.primary_asset if int(pool.primary_asset.index) == int(leg["input_asset_id"]) else pool.secondary_asset
        amount_raw = input_raw if input_raw is not None else display_to_raw(float(leg["input_amount"]), asset_in.decimals)
        swap = pool.prepare_swap(asset_in, amount_raw, self.settings.slippage_bps / 100)
        group = pool.prepare_swap_tx_group(swap, address)
        output_asset = pool.get_other_asset(asset_in)
        return {
            "ok": True,
            "transactions": group.transactions,
            "expected_output_raw": swap.effect.amount_received,
            "minimum_output_raw": swap.effect.minimum_amount_received,
            "expected_output_display": raw_to_display(swap.effect.amount_received, output_asset.decimals),
            "minimum_output_display": raw_to_display(swap.effect.minimum_amount_received, output_asset.decimals),
            "expected_app_ids": [int(pool.app_id)],
            "expected_asset_ids": sorted({int(leg["input_asset_id"]), int(leg["output_asset_id"])} - {0}),
        }

    def _validate_transaction_group(
        self,
        txns: list,
        address: str,
        expected_app_ids: list[int],
        expected_asset_ids: list[int],
    ) -> dict:
        allowed_types = {"pay", "axfer", "appl"}
        app_ids = set(int(app_id) for app_id in expected_app_ids)
        asset_ids = set(int(asset_id) for asset_id in expected_asset_ids)
        if len(txns) == 0:
            return {"ok": False, "reason": "transaction group is empty"}
        if len(txns) > ALGORAND_TX_GROUP_LIMIT:
            return {
                "ok": False,
                "reason": (
                    f"transaction group too large: {len(txns)} exceeds "
                    f"TX_GROUP_LIMIT {ALGORAND_TX_GROUP_LIMIT}"
                ),
                "validated_tx_count": len(txns),
                "max_tx_group_size": ALGORAND_TX_GROUP_LIMIT,
            }

        for index, txn in enumerate(txns):
            txn_dict = txn.dictify()
            txn_type = txn_dict.get("type")
            if txn_type not in allowed_types:
                return {"ok": False, "reason": f"txn {index} unsupported type: {txn_type}"}

            sender = getattr(txn, "sender", None) or txn_dict.get("snd")
            if sender != address:
                return {"ok": False, "reason": f"txn {index} unexpected sender: {sender}"}

            if self._has_rekey_or_close(txn, txn_dict):
                return {"ok": False, "reason": f"txn {index} has rekey or close-out field set"}

            if txn_type == "appl":
                app_id = int(txn_dict.get("apid") or getattr(txn, "index", 0) or 0)
                if app_id not in app_ids:
                    return {"ok": False, "reason": f"txn {index} unexpected app id: {app_id}"}

            if txn_type == "axfer":
                asset_id = int(txn_dict.get("xaid") or getattr(txn, "index", 0) or 0)
                if asset_id not in asset_ids:
                    return {"ok": False, "reason": f"txn {index} unexpected asset id: {asset_id}"}

            fee = int(txn_dict.get("fee") or getattr(txn, "fee", 0) or 0)
            if fee <= 0:
                return {"ok": False, "reason": f"txn {index} has invalid fee: {fee}"}

        return {
            "ok": True,
            "validated_tx_count": len(txns),
            "max_tx_group_size": ALGORAND_TX_GROUP_LIMIT,
            "group_size_ok": True,
        }

    def _has_rekey_or_close(self, txn, txn_dict: dict) -> bool:
        risky_dict_keys = ("rekey", "close", "aclose")
        if any(txn_dict.get(key) for key in risky_dict_keys):
            return True

        risky_attrs = (
            "rekey_to",
            "close_remainder_to",
            "asset_close_to",
            "close_assets_to",
        )
        return any(bool(getattr(txn, attr, None)) for attr in risky_attrs)

    @property
    def tinyman_client(self):
        if self._tinyman_client is None:
            from tinyman.v2.client import TinymanV2MainnetClient, TinymanV2TestnetClient

            client_cls = TinymanV2TestnetClient if self.settings.network == "testnet" else TinymanV2MainnetClient
            self._tinyman_client = client_cls(self.algod, user_address=self._resolve_address(), client_name="algopulse-phase0")
        return self._tinyman_client

    @property
    def pact_client(self):
        if self._pact_client is None:
            from pactsdk import PactClient

            network = "testnet" if self.settings.network == "testnet" else "mainnet"
            self._pact_client = PactClient(self.algod, network=network)
        return self._pact_client

    def _check_opted_in(self, address: str, asset_ids: set[int]) -> dict:
        if not asset_ids:
            return {"ok": True}
        try:
            account_info = self.algod.account_info(address)
            held = {int(asset["asset-id"]) for asset in account_info.get("assets", [])}
            missing = sorted(asset_id for asset_id in asset_ids if asset_id not in held)
            if missing:
                return {"ok": False, "reason": f"trader account is not opted into assets: {missing}"}
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "reason": f"could not verify trader opt-ins: {exc}"}

    def _check_trade_inventory(self, address: str, input_asset_id: int, input_amount: float) -> dict:
        try:
            account_info = self.algod.account_info(address)
            balance_algo = raw_to_display(account_info.get("amount", 0), 6)
            min_balance_algo = raw_to_display(account_info.get("min-balance", 0), 6)
            spendable_algo = max(0.0, balance_algo - min_balance_algo)
            min_fee_budget = max(0.001, self.settings.max_group_fee_algos)
            if spendable_algo < min_fee_budget:
                return {
                    "ok": False,
                    "reason": (
                        f"insufficient spendable ALGO for transaction fees: "
                        f"{spendable_algo:.6f} < {min_fee_budget:.6f}"
                    ),
                    "inventory": {
                        "balance_algo": balance_algo,
                        "minimum_balance_algo": min_balance_algo,
                        "spendable_algo": spendable_algo,
                    },
                }

            inventory = {
                "balance_algo": balance_algo,
                "minimum_balance_algo": min_balance_algo,
                "spendable_algo": spendable_algo,
                "input_asset_id": input_asset_id,
                "required_input_amount": input_amount,
            }
            if input_asset_id == 0:
                required_algo = input_amount + min_fee_budget
                inventory["required_spendable_algo"] = required_algo
                if spendable_algo < required_algo:
                    return {
                        "ok": False,
                        "reason": (
                            f"insufficient spendable ALGO for trade plus fees: "
                            f"{spendable_algo:.6f} < {required_algo:.6f}"
                        ),
                        "inventory": inventory,
                    }
                return {"ok": True, "inventory": inventory}

            held_asset = next(
                (
                    asset
                    for asset in account_info.get("assets", [])
                    if int(asset.get("asset-id", -1)) == input_asset_id
                ),
                None,
            )
            if held_asset is None:
                return {
                    "ok": False,
                    "reason": f"trader account does not hold input asset {input_asset_id}",
                    "inventory": inventory,
                }

            decimals = self._asset_decimals(input_asset_id)
            input_balance = raw_to_display(held_asset.get("amount", 0), decimals)
            inventory.update(
                {
                    "input_asset_decimals": decimals,
                    "input_asset_balance": input_balance,
                }
            )
            if input_balance < input_amount:
                return {
                    "ok": False,
                    "reason": (
                        f"insufficient input asset balance for trade: "
                        f"{input_balance:.6f} < {input_amount:.6f}"
                    ),
                    "inventory": inventory,
                }
            return {"ok": True, "inventory": inventory}
        except Exception as exc:
            return {"ok": False, "reason": f"could not verify trader inventory: {exc}"}

    def _asset_decimals(self, asset_id: int) -> int:
        if asset_id == 0:
            return 6
        asset_info = self.algod.asset_info(asset_id)
        return int(asset_info.get("params", {}).get("decimals", 0))

    def _route_age_seconds(self, opportunity: dict) -> float:
        created_at = opportunity.get("created_at")
        if created_at is None:
            return 0.0
        try:
            return max(0.0, time.time() - float(created_at))
        except (TypeError, ValueError):
            return 0.0

    def _route_asset_ids(self, route: list[dict]) -> set[int]:
        asset_ids: set[int] = set()
        for leg in route:
            asset_ids.add(int(leg["input_asset_id"]))
            asset_ids.add(int(leg["output_asset_id"]))
        return asset_ids

    def _balance_snapshot(self, address: str, asset_ids: set[int]) -> dict:
        try:
            account_info = self.algod.account_info(address)
            held_assets = {int(asset["asset-id"]): asset for asset in account_info.get("assets", [])}
            balances: dict[str, dict] = {}
            algo_amount = raw_to_display(account_info.get("amount", 0), 6)
            min_balance_algo = raw_to_display(account_info.get("min-balance", 0), 6)
            balances["0"] = {
                "asset_id": 0,
                "decimals": 6,
                "raw_amount": int(account_info.get("amount", 0) or 0),
                "amount": algo_amount,
                "minimum_balance": min_balance_algo,
                "spendable": max(0.0, algo_amount - min_balance_algo),
            }
            for asset_id in sorted(asset_id for asset_id in asset_ids if asset_id != 0):
                held = held_assets.get(asset_id)
                decimals = self._asset_decimals(asset_id)
                raw_amount = int(held.get("amount", 0) if held else 0)
                balances[str(asset_id)] = {
                    "asset_id": asset_id,
                    "decimals": decimals,
                    "raw_amount": raw_amount,
                    "amount": raw_to_display(raw_amount, decimals),
                }
            return {
                "ok": True,
                "status": "snapshot",
                "address": address,
                "captured_at": time.time(),
                "balances": balances,
            }
        except Exception as exc:
            return {"ok": False, "status": "snapshot_failed", "reason": f"could not capture balance snapshot: {exc}"}

    def _expected_balance_deltas(
        self,
        *,
        input_asset_id: int,
        input_amount: float,
        minimum_final_output: float,
        fee_algos: float,
    ) -> dict[str, float]:
        expected = {"0": -float(fee_algos)}
        starting_delta = float(minimum_final_output) - float(input_amount)
        if input_asset_id == 0:
            expected["0"] = starting_delta - float(fee_algos)
        else:
            expected[str(input_asset_id)] = starting_delta
        return expected

    def _planned_reconciliation(self, *, before_balances: dict, expected_deltas: dict[str, float]) -> dict:
        return {
            "ok": None,
            "status": "planned",
            "detail": "pre-trade balances captured; after-balances require submitted confirmation",
            "before": before_balances,
            "after": None,
            "expected_deltas": expected_deltas,
            "actual_deltas": None,
            "variance": None,
        }

    def _reconcile_balances(self, *, before_balances: dict, after_balances: dict, expected_deltas: dict[str, float]) -> dict:
        if not before_balances.get("ok"):
            return {
                "ok": False,
                "status": "failed",
                "detail": before_balances.get("reason", "pre-trade balance snapshot failed"),
                "before": before_balances,
                "after": after_balances,
                "expected_deltas": expected_deltas,
            }
        if not after_balances.get("ok"):
            return {
                "ok": False,
                "status": "failed",
                "detail": after_balances.get("reason", "post-trade balance snapshot failed"),
                "before": before_balances,
                "after": after_balances,
                "expected_deltas": expected_deltas,
            }

        actual_deltas: dict[str, float] = {}
        variance: dict[str, float] = {}
        before = before_balances.get("balances", {})
        after = after_balances.get("balances", {})
        asset_ids = set(before) | set(after) | set(expected_deltas)
        for asset_id in sorted(asset_ids, key=lambda value: int(value)):
            before_amount = float(before.get(asset_id, {}).get("amount", 0.0))
            after_amount = float(after.get(asset_id, {}).get("amount", 0.0))
            actual = after_amount - before_amount
            expected = float(expected_deltas.get(asset_id, 0.0))
            actual_deltas[asset_id] = actual
            variance[asset_id] = actual - expected

        tolerance = 0.000001
        failed_assets = [
            asset_id
            for asset_id, expected in expected_deltas.items()
            if actual_deltas.get(asset_id, 0.0) + tolerance < float(expected)
        ]
        ok = not failed_assets
        return {
            "ok": ok,
            "status": "reconciled" if ok else "variance",
            "detail": "actual balances met minimum expected deltas"
            if ok
            else f"actual delta below minimum for assets: {failed_assets}",
            "before": before_balances,
            "after": after_balances,
            "expected_deltas": expected_deltas,
            "actual_deltas": actual_deltas,
            "variance": variance,
        }

    def _resolve_address(self) -> str:
        if self.settings.trader_address:
            return self.settings.trader_address
        private_key = self._private_key()
        if private_key:
            return account.address_from_private_key(private_key)
        return ""

    def _private_key(self) -> str:
        if not self.settings.trader_mnemonic:
            return ""
        return mnemonic.to_private_key(self.settings.trader_mnemonic)

    def _non_algo_assets(self, route: list[dict]) -> set[int]:
        asset_ids: set[int] = set()
        for leg in route:
            for key in ("input_asset_id", "output_asset_id"):
                asset_id = int(leg[key])
                if asset_id != 0:
                    asset_ids.add(asset_id)
        return asset_ids

    def _pact_app_id_from_pool_id(self, pool_id: str) -> int | None:
        parts = pool_id.split(":")
        if len(parts) >= 2 and parts[0] == "pact":
            try:
                return int(parts[1])
            except ValueError:
                return None
        return None

    def _not_submitted(self, reason: str, opportunity: dict, extra: dict | None = None) -> dict:
        return {
            "submitted": False,
            "dry_run": True,
            "route_hash": opportunity.get("route_hash"),
            "reason": reason,
            **(extra or {}),
        }
