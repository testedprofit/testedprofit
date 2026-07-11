from __future__ import annotations

from dataclasses import asdict, dataclass
import time

from algopulse.models import Opportunity, Pool


ALGORAND_TX_GROUP_LIMIT = 16


@dataclass(frozen=True)
class RiskPolicy:
    min_profit_absolute: float = 0.25
    min_profit_bps: float = 35.0
    max_price_impact_bps: float = 50.0
    min_pool_reserve: float = 1_000.0
    estimated_network_fee: float = 0.006
    safety_buffer_bps: float = 15.0
    max_route_age_seconds: float = 5.0
    max_trade_size: float = 100.0
    max_route_legs: int = 3
    own_funds_only: bool = True
    min_fee_buffer_multiplier: float = 2.0
    allowed_asset_ids: tuple[int, ...] = (0, 31566704, 388592191, 793124631)
    allowed_app_ids: tuple[int, ...] = ()
    require_app_id_allowlist: bool = False
    # Paper-only verified registry app IDs. Never used by signer/executor paths.
    paper_verified_app_ids: tuple[int, ...] = ()

    def to_public_dict(self) -> dict:
        data = asdict(self)
        data["allowed_asset_ids"] = list(self.allowed_asset_ids)
        data["allowed_app_ids"] = list(self.allowed_app_ids)
        data["paper_verified_app_ids"] = list(self.paper_verified_app_ids)
        data["min_net_profit_algos"] = self.min_profit_absolute
        data["min_net_profit_input_units"] = self.min_profit_absolute
        data["estimated_network_fee_algos"] = self.estimated_network_fee
        data["max_route_age_seconds"] = self.max_route_age_seconds
        data["max_route_legs"] = self.max_route_legs
        data["min_fee_buffer_multiplier"] = self.min_fee_buffer_multiplier
        data["app_id_allowlist_required"] = self.require_app_id_allowlist
        data["own_funds_only"] = self.own_funds_only
        data["volume_only_trading_allowed"] = False
        data["requires_positive_net_after_fees"] = True
        return data


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str | None
    rules: dict


@dataclass(frozen=True)
class RiskEvaluationInput:
    input_amount: float
    expected_net_profit: float
    expected_profit_bps: float
    max_price_impact_bps: float
    expected_total_fees: float
    quote_age_seconds: float
    route_leg_count: int
    trade_size_limit: float
    max_route_legs: int
    min_profit_absolute: float
    min_profit_bps: float
    max_price_impact_bps_limit: float
    min_fee_buffer_multiplier: float
    own_funds_only: bool
    assets_allowlisted: bool
    app_ids_allowlisted: bool
    pool_reserves_ok: bool
    quote_max_age_seconds: float
    daily_loss: float = 0.0
    max_daily_loss: float = 20.0
    daily_trades: int = 0
    max_daily_trades: int = 20
    concurrent_executions: int = 0
    max_concurrent_execution: int = 1
    connector_readiness_ok: bool = True
    tx_group_size: int = 0
    max_tx_group_size: int = ALGORAND_TX_GROUP_LIMIT
    transaction_types_allowlisted: bool = True
    kill_switch_active: bool = False


def evaluate_risk_rules(input_data: RiskEvaluationInput) -> RiskDecision:
    rules = {
        "kill_switch_inactive": not input_data.kill_switch_active,
        "own_funds_only": input_data.own_funds_only,
        "assets_allowlisted": input_data.assets_allowlisted,
        "app_ids_allowlisted": input_data.app_ids_allowlisted,
        "connector_readiness_ok": input_data.connector_readiness_ok,
        "quote_freshness_ok": 0 <= input_data.quote_age_seconds <= input_data.quote_max_age_seconds,
        "trade_size_ok": input_data.input_amount <= input_data.trade_size_limit,
        "route_leg_count_ok": input_data.route_leg_count <= input_data.max_route_legs,
        "tx_group_size_ok": input_data.tx_group_size <= min(input_data.max_tx_group_size, ALGORAND_TX_GROUP_LIMIT),
        "transaction_types_allowlisted": input_data.transaction_types_allowlisted,
        "net_profit_after_fees_ok": input_data.expected_net_profit >= input_data.min_profit_absolute,
        "profit_bps_ok": input_data.expected_profit_bps >= input_data.min_profit_bps,
        "fee_buffer_ok": _pure_fee_buffer_ok(
            input_data.expected_net_profit,
            input_data.expected_total_fees,
            input_data.min_fee_buffer_multiplier,
        ),
        "price_impact_ok": input_data.max_price_impact_bps <= input_data.max_price_impact_bps_limit,
        "pool_reserves_ok": input_data.pool_reserves_ok,
        "daily_loss_ok": input_data.daily_loss > -abs(input_data.max_daily_loss),
        "daily_trade_count_ok": input_data.daily_trades < input_data.max_daily_trades,
        "concurrent_execution_ok": input_data.concurrent_executions < input_data.max_concurrent_execution,
    }
    for name, passed in rules.items():
        if not passed:
            return RiskDecision(approved=False, reason=name, rules=rules)
    return RiskDecision(approved=True, reason=None, rules=rules)


def _pure_fee_buffer_ok(net_profit: float, expected_total_fees: float, multiplier: float) -> bool:
    if multiplier <= 0 or expected_total_fees <= 0:
        return True
    return net_profit >= expected_total_fees * multiplier


class RiskEngine:
    def __init__(self, policy: RiskPolicy | None = None) -> None:
        self.policy = policy or RiskPolicy()

    def assess(self, opportunity: Opportunity, pools: list[Pool]) -> RiskDecision:
        rules: dict[str, bool] = {}

        rules["own_funds_only"] = self.policy.own_funds_only
        rules["route_leg_count_ok"] = len(opportunity.route) <= self.policy.max_route_legs
        rules["quote_freshness_ok"] = self._quote_freshness_ok(opportunity)
        rules["trade_size_ok"] = opportunity.input_amount <= self.policy.max_trade_size
        rules["assets_allowlisted"] = all(
            asset_id in self.policy.allowed_asset_ids for asset_id in opportunity.involved_asset_ids
        )
        rules["app_ids_allowlisted"] = self._app_ids_allowlisted(pools)
        rules["net_profit_after_fees_ok"] = opportunity.expected_net_profit >= self.policy.min_profit_absolute
        rules["fee_buffer_ok"] = self._fee_buffer_ok(opportunity)
        rules["profit_bps_ok"] = opportunity.expected_profit_bps >= self.policy.min_profit_bps
        rules["price_impact_ok"] = opportunity.max_price_impact_bps <= self.policy.max_price_impact_bps
        rules["pool_reserves_ok"] = all(
            min(pool.reserve_a, pool.reserve_b) >= self.policy.min_pool_reserve for pool in pools
        )

        for name, passed in rules.items():
            if not passed:
                return RiskDecision(approved=False, reason=name, rules=rules)
        return RiskDecision(approved=True, reason=None, rules=rules)

    def _quote_freshness_ok(self, opportunity: Opportunity) -> bool:
        if not opportunity.route:
            return True

        now = time.time()
        for leg in opportunity.route:
            raw_capture = leg.get("captured_at")
            if raw_capture is None:
                # Fail closed: missing source capture is never treated as fresh.
                return False
            try:
                captured_at = float(raw_capture)
            except (TypeError, ValueError):
                return False
            if captured_at <= 0:
                return False
            raw_exp = leg.get("expires_at")
            expires_at = (
                float(raw_exp)
                if raw_exp is not None
                else captured_at + self.policy.max_route_age_seconds
            )
            if captured_at > now + 1:
                return False
            if now - captured_at > self.policy.max_route_age_seconds:
                return False
            if expires_at < now:
                return False
        return True

    def _app_ids_allowlisted(self, pools: list[Pool]) -> bool:
        # Paper-only path: verified on-chain registry. Execution/signer never set this field.
        if self.policy.paper_verified_app_ids:
            return all(int(pool.app_id) in self.policy.paper_verified_app_ids for pool in pools)
        # Execution / ambient allowlist path (unchanged semantics).
        if not self.policy.require_app_id_allowlist and not self.policy.allowed_app_ids:
            return True
        if not self.policy.allowed_app_ids:
            return False
        return all(pool.app_id in self.policy.allowed_app_ids for pool in pools)

    def _fee_buffer_ok(self, opportunity: Opportunity) -> bool:
        """Require net profit (input-asset units) to cover fee buffer in the same unit.

        ``estimated_network_fee`` and ``total_dex_fees`` must already be normalized to
        the route input asset. DEX fees are embedded in AMM outputs; they are included
        here as buffer magnitude evidence, not re-subtracted from gross.
        """
        if self.policy.min_fee_buffer_multiplier <= 0:
            return True
        # Consistent unit: both components expressed in route input asset.
        expected_total_fees = max(0.0, opportunity.estimated_network_fee) + max(0.0, opportunity.total_dex_fees)
        if expected_total_fees <= 0:
            return True
        return opportunity.expected_net_profit >= expected_total_fees * self.policy.min_fee_buffer_multiplier


def policy_from_settings(settings, *, paper_verified_app_ids: tuple[int, ...] | None = None) -> RiskPolicy:
    configured_asset_ids = tuple(getattr(settings, "allowed_asset_ids", ()))
    asset_ids = sorted(configured_asset_ids or {asset_id for pair in settings.asset_pairs for asset_id in pair})
    if 0 not in asset_ids:
        asset_ids.insert(0, 0)
    # Execution/signer allowlist stays settings.allowed_app_ids only.
    # paper_verified_app_ids is optional and paper-path exclusive.
    paper_ids = paper_verified_app_ids
    if paper_ids is None:
        paper_ids = tuple(getattr(settings, "paper_verified_app_ids", ()) or ())
    return RiskPolicy(
        min_profit_absolute=getattr(settings, "min_net_profit_input_units", settings.min_net_profit_algos),
        min_profit_bps=settings.min_profit_bps,
        max_price_impact_bps=settings.max_price_impact_bps,
        min_pool_reserve=settings.min_pool_reserve,
        estimated_network_fee=settings.estimated_network_fee_algos,
        safety_buffer_bps=settings.safety_buffer_bps,
        max_route_age_seconds=settings.max_route_age_seconds,
        max_route_legs=getattr(settings, "max_route_legs", 3),
        max_trade_size=settings.max_live_trade_size,
        own_funds_only=getattr(settings, "own_funds_only", True),
        min_fee_buffer_multiplier=getattr(settings, "min_fee_buffer_multiplier", 2.0),
        allowed_asset_ids=tuple(asset_ids),
        allowed_app_ids=tuple(getattr(settings, "allowed_app_ids", ())),
        require_app_id_allowlist=getattr(settings, "require_app_id_allowlist", False),
        paper_verified_app_ids=tuple(int(app_id) for app_id in paper_ids if int(app_id) > 0),
    )
