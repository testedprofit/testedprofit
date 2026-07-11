from __future__ import annotations

import time
from dataclasses import replace
from typing import TYPE_CHECKING

from algosdk import account
from algosdk import mnemonic as algo_mnemonic

from algopulse.algorand import build_algod_client, raw_to_display
from algopulse.config import Settings
from algopulse.executor import ALGORAND_TX_GROUP_LIMIT, ArbitrageExecutor
from algopulse.store import MarketStore

if TYPE_CHECKING:
    from algopulse.scanner import MarketScanner


PROBE_TRADE_SIZE_ALGO = 5.0
LIVE_CONNECTOR_NAMES = {"tinyman", "pact"}


def build_live_readiness_report(
    *,
    settings: Settings,
    store: MarketStore,
    scanner: MarketScanner | None = None,
    run_scan: bool = False,
    check_wallet: bool = True,
    build_execution_plan: bool = True,
) -> dict:
    scan_result = None
    scan_started_at = None
    if run_scan:
        if scanner is None:
            raise ValueError("scanner is required when run_scan=True")
        scan_started_at = time.time()
        scan_result = scanner.run_once()

    now = time.time()
    required_asset_id = settings.target_asset_id if settings.use_vestige_discovery else None
    pulse = store.get_pulse(settings.public_delay_seconds, required_asset_id=required_asset_id)
    pools = store.list_latest_pools(limit=250, required_asset_id=required_asset_id)
    connector_names = _connector_names(settings)
    live_connectors = sorted(name for name in connector_names if name in LIVE_CONNECTOR_NAMES)
    observed_venues = sorted({pool["venue_id"] for pool in pools})
    last_scan_at = pulse.get("last_scan_at")
    last_scan_age_seconds = None if last_scan_at is None else max(0.0, now - float(last_scan_at))
    fresh_after_seconds = max(90, settings.scanner_interval_seconds * 3)
    fresh_opportunity_cutoff = scan_started_at - 1 if scan_started_at is not None else now - fresh_after_seconds
    opportunities = store.list_opportunities(
        limit=25,
        public_delay_seconds=0,
        min_created_at=fresh_opportunity_cutoff,
        required_asset_id=required_asset_id,
    )
    best_approved = store.get_best_approved_opportunity(
        max_input_amount=settings.max_live_trade_size,
        min_created_at=fresh_opportunity_cutoff,
        required_asset_id=required_asset_id,
    )
    best_observed = opportunities[0] if opportunities else None

    wallet = _wallet_status(settings=settings, check_wallet=check_wallet)
    signer = _signer_status(settings)
    tiny_live = _tiny_live_status(
        settings=settings,
        wallet=wallet,
        best_approved=best_approved,
        daily_profit=store.get_submitted_live_profit_24h(),
        daily_trade_count=store.get_submitted_live_trade_count_24h(),
    )
    execution = _execution_preflight(
        settings=settings,
        best_approved=best_approved,
        build_execution_plan=build_execution_plan,
    )

    daily_profit = tiny_live["daily_profit_24h"]
    daily_trade_count = tiny_live["daily_trade_count_24h"]
    daily_loss_room_ok = daily_profit > -abs(settings.max_daily_loss)
    daily_trade_room_ok = daily_trade_count < settings.max_daily_trades
    app_id_allowlist_ok = not settings.require_app_id_allowlist or bool(settings.allowed_app_ids)
    profit_guard_ok = (
        settings.min_net_profit_input_units > 0
        and settings.min_profit_bps > 0
        and settings.estimated_network_fee_algos >= 0
        and settings.safety_buffer_bps >= 0
        and settings.min_fee_buffer_multiplier >= 2.0
        and settings.max_route_age_seconds <= 5.0
    )
    checks = [
        _check(
            "live_connectors_configured",
            bool(live_connectors),
            f"configured: {', '.join(connector_names) or 'none'}",
        ),
        _check(
            "pool_data_available",
            len(pools) > 0,
            f"{len(pools)} latest pools observed",
        ),
        _check(
            "multi_venue_market_data",
            len(observed_venues) >= 2,
            f"venues: {', '.join(observed_venues) or 'none'}",
        ),
        _check(
            "fresh_scan",
            last_scan_age_seconds is not None and last_scan_age_seconds <= fresh_after_seconds,
            "not scanned yet" if last_scan_age_seconds is None else f"{int(last_scan_age_seconds)}s old",
        ),
        _check(
            "wallet_configured",
            bool(wallet.get("configured")),
            wallet.get("detail", "wallet address or signer secret present"),
        ),
        _check(
            "spendable_probe_funds",
            bool(wallet.get("spendable_for_probe")),
            wallet.get("balance_detail", f"requires at least {PROBE_TRADE_SIZE_ALGO:g} spendable ALGO"),
            skipped=wallet.get("account_lookup") == "skipped",
        ),
        _check(
            "asset_opt_ins",
            bool(wallet.get("asset_opt_ins_ok")),
            wallet.get("opt_in_detail", "required non-ALGO assets are opted in"),
            skipped=wallet.get("account_lookup") == "skipped",
        ),
        _check(
            "profit_guard_configured",
            profit_guard_ok,
            (
                f"min {settings.min_net_profit_input_units:.6f} starting-asset units and "
                f"{settings.min_profit_bps:g} bps; {settings.min_fee_buffer_multiplier:g}x fee buffer; "
                f"{settings.max_route_age_seconds:g}s quote"
            ),
        ),
        _check(
            "app_id_allowlist",
            app_id_allowlist_ok,
            (
                f"{len(settings.allowed_app_ids)} app ids configured"
                if settings.require_app_id_allowlist
                else "app id allowlist not required in this mode"
            ),
        ),
        _check(
            "daily_loss_room",
            daily_loss_room_ok,
            f"submitted 24h profit: {daily_profit:.6f} ALGO",
        ),
        _check(
            "daily_trade_room",
            daily_trade_room_ok,
            f"{daily_trade_count}/{settings.max_daily_trades} submitted trades today",
        ),
        _check(
            "execution_serialized",
            settings.max_concurrent_execution == 1,
            f"max concurrent execution: {settings.max_concurrent_execution}",
        ),
        _check(
            "unsigned_executor_only",
            settings.unsigned_executor_only,
            "unsigned group construction only" if settings.unsigned_executor_only else "signing path can be reached",
        ),
        _check(
            "isolated_signer_boundary",
            bool(signer["main_executor_can_sign"] is False),
            "main executor builds unsigned groups only; signer owns key policy",
        ),
        _check(
            "signer_policy_locked_or_reviewed",
            bool(signer["policy_locked_or_reviewed"]),
            signer["policy_detail"],
        ),
        _check(
            "tiny_live_scope",
            bool(tiny_live["scope_ok"]),
            tiny_live["scope_detail"],
            skipped=not settings.tiny_live_mode,
        ),
        _check(
            "tiny_live_limits",
            bool(tiny_live["limits_ok"]),
            tiny_live["limits_detail"],
            skipped=not settings.tiny_live_mode,
        ),
        _check(
            "tiny_live_wallet_funding",
            bool(tiny_live["funding_range"]["ok"]),
            tiny_live["funding_range"]["detail"],
            skipped=not settings.tiny_live_mode,
        ),
        _check(
            "tiny_live_manual_first_route",
            bool(tiny_live["manual_first_route_ok"]),
            tiny_live["manual_first_route_detail"],
            skipped=not settings.tiny_live_mode,
        ),
        _check(
            "tiny_live_post_first_trade_proof",
            bool(tiny_live["post_first_trade_proof_ok"]),
            tiny_live["post_first_trade_detail"],
            skipped=not settings.tiny_live_mode,
        ),
        _check(
            "tiny_live_automation_gate",
            bool(tiny_live["automation_gate_ok"]),
            tiny_live["automation_gate_detail"],
            skipped=not settings.tiny_live_mode,
        ),
        _check(
            "profitable_route_available",
            best_approved is not None,
            "market-dependent; bot can be ready while waiting for a spread",
            blocking=False,
        ),
        _check(
            "atomic_dry_run_build",
            bool(execution.get("group_build_ok")),
            execution.get("detail", "no route dry-run attempted"),
            skipped=execution.get("attempted") is False,
        ),
    ]

    verdict = _verdict(
        checks=checks,
        wallet=wallet,
        best_approved=best_approved,
        execution=execution,
        settings=settings,
    )

    return {
        "mode": "live-market-readiness",
        "created_at": now,
        "verdict": verdict["code"],
        "verdict_label": verdict["label"],
        "verdict_detail": verdict["detail"],
        "readiness_score": _score(checks),
        "network": settings.network,
        "target_asset": {
            "asset_id": settings.target_asset_id,
            "vestige_discovery_enabled": settings.use_vestige_discovery,
            "asset_pairs": [list(pair) for pair in settings.asset_pairs],
            "discovery": getattr(scanner, "discovery_report", None) if scanner is not None else None,
            "execution_note": (
                "Two-leg round trips can be built as atomic dry-runs. ALGO-starting routes can be submitted "
                "when live flags are armed; non-ALGO starts require explicit dry-run enablement and remain "
                "blocked from signing unless ALGO-equivalent profit reconciliation is reviewed."
            ),
        },
        "connectors": {
            "configured": connector_names,
            "live": live_connectors,
            "observed_venues": observed_venues,
            "mock_present": "mock" in connector_names,
        },
        "scan": {
            "ran_now": run_scan,
            "result": scan_result,
            "last_scan_at": last_scan_at,
            "last_scan_age_seconds": last_scan_age_seconds,
            "fresh_after_seconds": fresh_after_seconds,
            "pools_monitored": pulse.get("pools_monitored", 0),
            "opportunities_24h": pulse.get("opportunities_24h", 0),
            "approved_24h": pulse.get("approved_24h", 0),
        },
        "wallet": wallet,
        "signer": signer,
        "tiny_live": tiny_live,
        "risk": {
            "max_live_trade_size": settings.max_live_trade_size,
            "trade_sizes": list(settings.trade_sizes),
            "min_net_profit_algos": settings.min_net_profit_algos,
            "min_net_profit_input_units": settings.min_net_profit_input_units,
            "min_profit_bps": settings.min_profit_bps,
            "estimated_network_fee_algos": settings.estimated_network_fee_algos,
            "safety_buffer_bps": settings.safety_buffer_bps,
            "max_price_impact_bps": settings.max_price_impact_bps,
            "min_pool_reserve": settings.min_pool_reserve,
            "max_daily_loss": settings.max_daily_loss,
            "max_daily_trades": settings.max_daily_trades,
            "submitted_live_trades_24h": daily_trade_count,
            "max_concurrent_execution": settings.max_concurrent_execution,
            "submitted_profit_24h": daily_profit,
            "max_group_fee_algos": settings.max_group_fee_algos,
            "max_tx_group_size": ALGORAND_TX_GROUP_LIMIT,
            "max_route_age_seconds": settings.max_route_age_seconds,
            "max_route_legs": settings.max_route_legs,
            "min_fee_buffer_multiplier": settings.min_fee_buffer_multiplier,
            "own_funds_only": settings.own_funds_only,
            "app_id_allowlist_required": settings.require_app_id_allowlist,
            "allowed_app_ids_count": len(settings.allowed_app_ids),
            "allowed_asset_ids": list(settings.allowed_asset_ids),
            "slippage_bps": settings.slippage_bps,
            "volume_only_trading_allowed": False,
            "requires_positive_net_after_fees": True,
        },
        "route_gate": {
            "rejection_summary": _rejection_summary(opportunities),
            "best_observed_skip_reason": best_observed.get("skip_reason") if best_observed else None,
        },
        "execution_flags": {
            "enable_live_execution": settings.enable_live_execution,
            "execute_approved": settings.execute_approved,
            "allow_api_execution": settings.allow_api_execution,
            "allow_non_algo_starting_routes": settings.allow_non_algo_starting_routes,
            "allow_non_algo_live_submission": settings.allow_non_algo_live_submission,
            "unsigned_executor_only": settings.unsigned_executor_only,
            "readiness_never_submits": True,
        },
        "best_approved_route": _route_summary(best_approved),
        "best_observed_route": _route_summary(best_observed),
        "execution_preflight": execution,
        "checks": checks,
    }


def _connector_names(settings: Settings) -> list[str]:
    names = []
    for part in settings.connector_mode.split(","):
        name = part.strip().lower()
        if name:
            names.append(name)
    return names


def _wallet_status(*, settings: Settings, check_wallet: bool) -> dict:
    resolved = _resolve_address(settings)
    wallet = {
        "configured": bool(resolved.get("address")),
        "address_masked": _mask_address(resolved.get("address", "")),
        "address_source": resolved.get("source"),
        "detail": resolved.get("detail"),
        "non_algo_assets_required": sorted({asset_id for pair in settings.asset_pairs for asset_id in pair if asset_id != 0}),
        "account_lookup": "skipped",
        "asset_opt_ins_ok": False,
        "spendable_for_probe": False,
    }

    if not resolved.get("address") or not check_wallet:
        if wallet["non_algo_assets_required"]:
            wallet["opt_in_detail"] = "wallet lookup skipped"
        else:
            wallet["asset_opt_ins_ok"] = True
            wallet["opt_in_detail"] = "no non-ALGO opt-ins required"
        return wallet

    try:
        account_info = build_algod_client(settings).account_info(resolved["address"])
        balance_algo = raw_to_display(account_info.get("amount", 0), 6)
        min_balance_algo = raw_to_display(account_info.get("min-balance", 0), 6)
        spendable_algo = max(0.0, balance_algo - min_balance_algo)
        held_assets = {int(asset["asset-id"]) for asset in account_info.get("assets", [])}
        missing_assets = [asset_id for asset_id in wallet["non_algo_assets_required"] if asset_id not in held_assets]
        wallet.update(
            {
                "account_lookup": "ok",
                "balance_algo": balance_algo,
                "minimum_balance_algo": min_balance_algo,
                "spendable_algo": spendable_algo,
                "spendable_for_probe": spendable_algo >= PROBE_TRADE_SIZE_ALGO,
                "balance_detail": f"{spendable_algo:.6f} spendable ALGO",
                "missing_asset_opt_ins": missing_assets,
                "asset_opt_ins_ok": not missing_assets,
                "opt_in_detail": "all required assets opted in"
                if not missing_assets
                else f"missing opt-ins: {missing_assets}",
            }
        )
    except Exception as exc:
        wallet.update(
            {
                "account_lookup": "error",
                "balance_detail": f"account lookup failed: {exc}",
                "opt_in_detail": f"account lookup failed: {exc}",
            }
        )
    return wallet


def _signer_status(settings: Settings) -> dict:
    enabled = bool(getattr(settings, "signer_enabled", False))
    kill_switch = bool(getattr(settings, "signer_kill_switch", True))
    allowed_route_hashes = tuple(getattr(settings, "signer_allowed_route_hashes", ()) or ())
    audit_log_path = getattr(settings, "signer_audit_log_path", None)
    policy_locked_or_reviewed = (not enabled) or kill_switch or bool(allowed_route_hashes)
    if not enabled:
        policy_detail = "signer disabled by default"
    elif kill_switch:
        policy_detail = "signer enabled but kill switch is active"
    elif allowed_route_hashes:
        policy_detail = f"{len(allowed_route_hashes)} reviewed route hashes allowlisted"
    else:
        policy_detail = "signer enabled with kill switch off but no route hashes allowlisted"
    return {
        "enabled": enabled,
        "kill_switch": kill_switch,
        "route_hash_allowlist_count": len(allowed_route_hashes),
        "audit_log_path": str(audit_log_path) if audit_log_path else "",
        "min_wallet_reserve_algos": float(getattr(settings, "signer_min_wallet_reserve_algos", 0.2)),
        "key_material_configured": bool(getattr(settings, "trader_mnemonic", "")),
        "main_executor_can_sign": False,
        "policy_locked_or_reviewed": policy_locked_or_reviewed,
        "policy_detail": policy_detail,
    }


def _tiny_live_status(
    *,
    settings: Settings,
    wallet: dict,
    best_approved: dict | None,
    daily_profit: float,
    daily_trade_count: int,
) -> dict:
    usdc_asset_id = 31566704
    algo_usdc_pair = tuple(sorted((0, usdc_asset_id)))
    configured_pairs = {tuple(sorted(pair)) for pair in settings.asset_pairs}
    allowed_asset_ids = set(settings.allowed_asset_ids or ())
    pair_scope_ok = configured_pairs == {algo_usdc_pair}
    allowed_asset_scope_ok = not allowed_asset_ids or allowed_asset_ids.issubset({0, usdc_asset_id})
    target_scope_ok = not settings.use_vestige_discovery or settings.target_asset_id == usdc_asset_id
    scope_ok = pair_scope_ok and allowed_asset_scope_ok and target_scope_ok

    trade_size_ok = settings.max_live_trade_size <= 10.0
    daily_loss_limit_ok = abs(settings.max_daily_loss) <= 20.0
    daily_trade_limit_ok = settings.max_daily_trades <= 20
    route_length_ok = settings.max_route_legs <= 3
    concurrency_ok = settings.max_concurrent_execution == 1
    own_funds_ok = settings.own_funds_only
    limits_ok = all(
        (
            trade_size_ok,
            daily_loss_limit_ok,
            daily_trade_limit_ok,
            route_length_ok,
            concurrency_ok,
            own_funds_ok,
        )
    )

    manual_route_hash = settings.tiny_live_manual_route_hash.strip()
    best_route_hash = str(best_approved.get("route_hash")) if best_approved else ""
    manual_first_route_ok = bool(manual_route_hash and best_route_hash and manual_route_hash == best_route_hash)
    lora_txid = settings.tiny_live_lora_txid.strip()
    reconciliation_confirmed = bool(settings.tiny_live_reconciliation_confirmed)
    post_first_trade_proof_ok = bool(lora_txid and reconciliation_confirmed)
    automation_gate_ok = not settings.tiny_live_allow_automation or (
        manual_first_route_ok and post_first_trade_proof_ok and limits_ok and scope_ok
    )

    funding_range = _tiny_live_funding_range(settings=settings, wallet=wallet)
    return {
        "enabled": bool(settings.tiny_live_mode),
        "allow_automation": bool(settings.tiny_live_allow_automation),
        "allowed_pair": "ALGO/USDC only",
        "usdc_asset_id": usdc_asset_id,
        "configured_pairs": [list(pair) for pair in sorted(configured_pairs)],
        "scope_ok": scope_ok,
        "scope_detail": (
            "ALGO/USDC only"
            if scope_ok
            else "tiny live requires only ALGO/USDC, no Vestige PNET target, and no extra allowed assets"
        ),
        "trade_size_ok": trade_size_ok,
        "daily_loss_limit_ok": daily_loss_limit_ok,
        "daily_trade_limit_ok": daily_trade_limit_ok,
        "route_length_ok": route_length_ok,
        "concurrency_ok": concurrency_ok,
        "own_funds_ok": own_funds_ok,
        "limits_ok": limits_ok,
        "limits_detail": (
            f"{settings.max_live_trade_size:g} ALGO max trade, "
            f"{settings.max_daily_loss:g} ALGO daily loss, "
            f"{settings.max_daily_trades} daily trades, "
            f"{settings.max_route_legs} swaps, "
            f"{settings.max_concurrent_execution} concurrent"
        ),
        "funding_range": funding_range,
        "manual_route_hash": manual_route_hash,
        "best_route_hash": best_route_hash,
        "manual_first_route_ok": manual_first_route_ok,
        "manual_first_route_detail": (
            "manual route hash matches current approved route"
            if manual_first_route_ok
            else "set ALGO_PULSE_TINY_LIVE_MANUAL_ROUTE_HASH to the reviewed approved route hash"
        ),
        "lora_txid": lora_txid,
        "reconciliation_confirmed": reconciliation_confirmed,
        "post_first_trade_proof_ok": post_first_trade_proof_ok,
        "post_first_trade_detail": (
            "Lora txid recorded and reconciliation confirmed"
            if post_first_trade_proof_ok
            else "record Lora txid and confirm expected-vs-actual reconciliation before automation"
        ),
        "automation_gate_ok": automation_gate_ok,
        "automation_gate_detail": (
            "automation disabled"
            if not settings.tiny_live_allow_automation
            else "automation allowed only after manual route, Lora, reconciliation, scope, and limit gates pass"
        ),
        "daily_profit_24h": daily_profit,
        "daily_trade_count_24h": daily_trade_count,
    }


def _tiny_live_funding_range(*, settings: Settings, wallet: dict) -> dict:
    min_algos = float(settings.tiny_live_min_wallet_algos)
    max_algos = float(settings.tiny_live_max_wallet_algos)
    if wallet.get("account_lookup") != "ok":
        return {
            "ok": False,
            "skipped": wallet.get("account_lookup") == "skipped",
            "detail": f"wallet lookup required; expected {min_algos:g}-{max_algos:g} ALGO hot wallet",
            "min_algos": min_algos,
            "max_algos": max_algos,
        }
    balance = float(wallet.get("balance_algo", 0.0))
    ok = min_algos <= balance <= max_algos
    return {
        "ok": ok,
        "skipped": False,
        "balance_algo": balance,
        "min_algos": min_algos,
        "max_algos": max_algos,
        "detail": (
            f"{balance:.6f} ALGO in hot wallet"
            if ok
            else f"{balance:.6f} ALGO outside {min_algos:g}-{max_algos:g} ALGO tiny-live range"
        ),
    }


def _resolve_address(settings: Settings) -> dict:
    if settings.trader_address:
        return {
            "address": settings.trader_address,
            "source": "ALGO_PULSE_TRADER_ADDRESS",
            "detail": "trader address configured",
        }
    if not settings.trader_mnemonic:
        return {
            "address": "",
            "source": None,
            "detail": "missing trader address or signer secret",
        }
    try:
        private_key = algo_mnemonic.to_private_key(settings.trader_mnemonic)
        return {
            "address": account.address_from_private_key(private_key),
            "source": "signer secret source",
            "detail": "signer secret resolves to an address",
        }
    except Exception as exc:
        return {
            "address": "",
            "source": "signer secret source",
            "detail": f"invalid signer secret: {exc}",
        }


def _execution_preflight(
    *,
    settings: Settings,
    best_approved: dict | None,
    build_execution_plan: bool,
) -> dict:
    if best_approved is None:
        return {"attempted": False, "group_build_ok": False, "detail": "no approved route available"}
    if not build_execution_plan:
        return {"attempted": False, "group_build_ok": False, "detail": "execution preflight skipped"}

    safe_settings = replace(
        settings,
        enable_live_execution=False,
        execute_approved=False,
        allow_api_execution=False,
        unsigned_executor_only=True,
    )
    try:
        result = ArbitrageExecutor(settings=safe_settings).execute(best_approved)
        group_build_ok = bool(result.get("dry_run")) and not result.get("submitted") and bool(result.get("tx_count"))
        detail = "atomic group built without submitting" if group_build_ok else result.get("reason", "group not built")
        return {
            "attempted": True,
            "group_build_ok": group_build_ok,
            "detail": detail,
            "result": result,
        }
    except Exception as exc:
        return {
            "attempted": True,
            "group_build_ok": False,
            "detail": f"execution preflight failed: {exc}",
            "error": str(exc),
        }


def _route_summary(route: dict | None) -> dict | None:
    if not route:
        return None
    return {
        "route_hash": route.get("route_hash"),
        "status": route.get("status"),
        "skip_reason": route.get("skip_reason"),
        "input_asset_id": route.get("input_asset_id"),
        "input_amount": route.get("input_amount"),
        "expected_final_amount": route.get("expected_final_amount"),
        "expected_net_profit": route.get("expected_net_profit"),
        "profit_asset_id": route.get("input_asset_id"),
        "expected_profit_bps": route.get("expected_profit_bps"),
        "max_price_impact_bps": route.get("max_price_impact_bps"),
        "venues": [leg.get("venue") for leg in route.get("route", [])],
        "route": route.get("route", []),
    }


def _rejection_summary(opportunities: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for route in opportunities:
        if route.get("status") == "approved":
            continue
        reason = route.get("skip_reason") or "unknown"
        counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))


def _check(name: str, ok: bool, detail: str, *, skipped: bool = False, blocking: bool = True) -> dict:
    return {
        "name": name,
        "ok": bool(ok) if not skipped else False,
        "skipped": skipped,
        "blocking": blocking,
        "detail": detail,
    }


def _score(checks: list[dict]) -> int:
    scored = [check for check in checks if check.get("blocking", True) and not check.get("skipped")]
    if not scored:
        return 0
    passed = sum(1 for check in scored if check["ok"])
    return int(round((passed / len(scored)) * 100))


def _verdict(
    *,
    checks: list[dict],
    wallet: dict,
    best_approved: dict | None,
    execution: dict,
    settings: Settings,
) -> dict:
    by_name = {check["name"]: check for check in checks}
    scanner_ready = all(
        by_name[name]["ok"]
        for name in (
            "live_connectors_configured",
            "pool_data_available",
            "multi_venue_market_data",
            "fresh_scan",
            "profit_guard_configured",
            "app_id_allowlist",
            "daily_loss_room",
            "daily_trade_room",
            "execution_serialized",
            "unsigned_executor_only",
            "isolated_signer_boundary",
            "signer_policy_locked_or_reviewed",
        )
    )
    if settings.tiny_live_mode:
        scanner_ready = scanner_ready and all(
            by_name[name]["ok"]
            for name in (
                "tiny_live_scope",
                "tiny_live_limits",
                "tiny_live_wallet_funding",
                "tiny_live_manual_first_route",
                "tiny_live_post_first_trade_proof",
                "tiny_live_automation_gate",
            )
        )
    wallet_ready = bool(wallet.get("configured")) and bool(wallet.get("spendable_for_probe")) and bool(
        wallet.get("asset_opt_ins_ok")
    )
    if not scanner_ready:
        return {
            "code": "not_live_ready",
            "label": "Not live-market ready",
            "detail": "Needs live connectors, current pool data, fresh scan, and reviewed risk allowlists.",
        }
    if not wallet_ready:
        return {
            "code": "watch_ready_wallet_needed",
            "label": "Watch-ready, wallet needed",
            "detail": "Live market scanning works, but funding or opt-ins are not ready.",
        }
    if best_approved is None:
        return {
            "code": "funded_waiting_for_route",
            "label": "Funded, waiting for spread",
            "detail": "The bot is prepared to dry-run, but no approved route is available right now.",
        }
    if not execution.get("group_build_ok"):
        return {
            "code": "route_seen_execution_fix_needed",
            "label": "Route seen, execution fix needed",
            "detail": execution.get("detail", "Could not build the atomic dry-run group."),
        }
    if settings.enable_live_execution and settings.execute_approved:
        return {
            "code": "submission_armed",
            "label": "Submission armed",
            "detail": "Live execution flags are enabled. Readiness checks still do not submit.",
        }
    return {
        "code": "dry_run_ready_disarmed",
        "label": "Dry-run ready, disarmed",
        "detail": "Live route can be built as an atomic dry run. Submission flags are off.",
    }


def _mask_address(address: str) -> str:
    if not address:
        return ""
    if len(address) <= 12:
        return address
    return f"{address[:6]}...{address[-6:]}"
