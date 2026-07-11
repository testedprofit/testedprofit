from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from algopulse.config import Settings


MIN_PUBLIC_DELAY_SECONDS = 900
MAINNET_ONLY_ASSET_IDS = {
    31_566_704: "MainNet USDC",
    3_169_177_585: "MainNet PNET",
}


def build_testnet_readiness(
    settings: Settings,
    *,
    network_health: dict[str, Any] | None = None,
    health_probe: Callable[[Settings], dict[str, Any]] | None = None,
) -> dict:
    """Build TestNet readiness / access evidence.

    Optional live health: pass ``network_health`` or ``health_probe`` to include
    real algod/Indexer probes. Pure unit tests can omit both (URL-label checks only).
    """
    live_health = network_health
    if live_health is None and health_probe is not None:
        try:
            live_health = health_probe(settings)
        except Exception as exc:
            live_health = {
                "overall": "down",
                "ok": False,
                "mismatches": [],
                "algod": {"healthy": False, "detail": f"probe_error:{type(exc).__name__}"},
                "indexer": {"healthy": False, "detail": f"probe_error:{type(exc).__name__}"},
            }

    checks = [
        _network_check(settings),
        _environment_check(settings),
        _execution_boundary_check(settings),
        _secret_boundary_check(settings),
        _public_delay_check(settings),
        _endpoint_check("algod_endpoint", "algod", settings.algod_url),
        _endpoint_check("indexer_endpoint", "Indexer", settings.indexer_url),
        _asset_configuration_check(settings),
        _connector_check(settings.connector_mode),
        _wallet_boundary_check(settings),
    ]
    if live_health is not None:
        checks.extend(_live_health_checks(live_health))

    read_only_checks = [item for item in checks if item["gate"] == "read_only"]
    read_only_status = _rollup_status(read_only_checks)
    wallet_checks = [item for item in checks if item["gate"] in {"read_only", "wallet", "access"}]
    # Wallet connect-only does not require PNET ASA to be configured.
    wallet_gate_keys = {
        "network",
        "execution_boundary",
        "secret_boundary",
        "algod_endpoint",
        "indexer_endpoint",
        "wallet_boundary",
        "algod_live",
        "indexer_live",
    }
    wallet_gate_checks = [item for item in checks if item["key"] in wallet_gate_keys]
    wallet_access_status = _rollup_status(wallet_gate_checks)
    wallet_connection_ready = (
        settings.network == "testnet"
        and wallet_access_status == "ready"
        and _boundary_flags(settings)["readOnly"]
    )
    if wallet_connection_ready:
        wallet_status = "ready"
    elif read_only_status == "blocked" or wallet_access_status == "blocked":
        wallet_status = "blocked"
    else:
        wallet_status = "wait"

    blocked_reasons = [item["reason"] for item in checks if item["status"] == "blocked"]
    wait_reasons = [item["reason"] for item in checks if item["status"] == "wait"]
    passed_count = sum(1 for item in checks if item["status"] == "pass")

    if wallet_connection_ready:
        status = "testnet_access_ready"
        next_action = (
            "Connect Pera or Defly on TestNet (read account state only). "
            "Signing and submission remain out of scope."
        )
    elif read_only_status == "ready":
        status = "ready_for_wallet_review"
        next_action = (
            "Pera/Defly connect-only adapters are available; complete remaining live health checks."
        )
    else:
        status = read_only_status
        next_action = _next_action(checks)

    pnet_id = int(settings.target_asset_id or 0)
    return {
        "phase": "Phase 3 - TestNet Access",
        "status": status,
        "readOnlyStatus": read_only_status,
        "walletStatus": wallet_status,
        "walletAccessStatus": wallet_access_status,
        "testnetReadOnlyReady": read_only_status == "ready",
        "walletConnectionReady": wallet_connection_ready,
        "walletAccessMode": "connect_only",
        "pnetAsaConfigured": pnet_id > 0,
        "pnetAsaId": pnet_id if pnet_id > 0 else None,
        "pnetMessage": None if pnet_id > 0 else "PNET TestNet asset not configured",
        "productionReady": False,
        "network": settings.network,
        "environment": settings.env,
        "chainId": 416002 if settings.network == "testnet" else (416001 if settings.network == "mainnet" else None),
        "evidenceSource": "runtime_config_redacted",
        "networkHealth": _public_safe_health(live_health) if live_health is not None else None,
        "checks": checks,
        "passedCount": passed_count,
        "totalCount": len(checks),
        "blockedReasons": blocked_reasons,
        "waitReasons": wait_reasons,
        "nextAction": next_action,
        "boundaries": _boundary_flags(settings),
        "supportedWallets": ["pera", "defly"],
    }


def _check(*, key: str, label: str, status: str, reason: str, gate: str = "read_only") -> dict:
    return {
        "key": key,
        "label": label,
        "status": status,
        "reason": reason,
        "gate": gate,
    }


def _boundary_flags(settings: Settings) -> dict:
    """Report live runtime flags; never hardcode disarmed when settings are armed."""
    signing_enabled = bool(settings.signer_enabled)
    live_trading_enabled = bool(settings.enable_live_execution)
    submission_enabled = bool(
        settings.enable_live_execution
        or settings.allow_api_execution
        or settings.execute_approved
        or not settings.unsigned_executor_only
    )
    disarmed = (
        not live_trading_enabled
        and not settings.execute_approved
        and not settings.allow_api_execution
        and settings.unsigned_executor_only
        and not signing_enabled
        and settings.signer_kill_switch
    )
    return {
        "readOnly": disarmed,
        "walletConnectOnly": True,
        "signingEnabled": signing_enabled,
        "submissionEnabled": submission_enabled,
        "liveTradingEnabled": live_trading_enabled,
        "killSwitchActive": bool(settings.signer_kill_switch),
    }


def _network_check(settings: Settings) -> dict:
    if settings.network == "testnet":
        return _check(
            key="network",
            label="Algorand network",
            status="pass",
            reason="network_testnet",
        )
    return _check(
        key="network",
        label="Algorand network",
        status="blocked",
        reason=f"network_{settings.network or 'unconfigured'}_not_testnet",
    )


def _environment_check(settings: Settings) -> dict:
    normalized = settings.env.strip().lower()
    if normalized in {"testnet", "staging"}:
        status = "pass"
        reason = f"environment_{normalized}"
    else:
        status = "wait"
        reason = f"environment_{normalized or 'unconfigured'}_not_staging"
    return _check(key="environment", label="Runtime environment", status=status, reason=reason)


def _execution_boundary_check(settings: Settings) -> dict:
    safe = (
        not settings.enable_live_execution
        and not settings.execute_approved
        and not settings.allow_api_execution
        and settings.unsigned_executor_only
        and not settings.signer_enabled
        and settings.signer_kill_switch
    )
    return _check(
        key="execution_boundary",
        label="Execution boundary",
        status="pass" if safe else "blocked",
        reason="execution_and_signer_disarmed" if safe else "execution_or_signer_boundary_open",
    )


def _secret_boundary_check(settings: Settings) -> dict:
    secret_absent = not bool(settings.trader_mnemonic.strip())
    return _check(
        key="secret_boundary",
        label="Signer secret boundary",
        status="pass" if secret_absent else "blocked",
        reason="no_signer_secret_loaded" if secret_absent else "signer_secret_loaded_in_api_process",
    )


def _public_delay_check(settings: Settings) -> dict:
    safe = settings.public_delay_seconds >= MIN_PUBLIC_DELAY_SECONDS
    return _check(
        key="public_delay",
        label="Public route delay",
        status="pass" if safe else "blocked",
        reason=(
            f"public_delay_{settings.public_delay_seconds}_seconds"
            if safe
            else f"public_delay_below_{MIN_PUBLIC_DELAY_SECONDS}_seconds"
        ),
    )


def _endpoint_check(key: str, label: str, url: str) -> dict:
    normalized = (url or "").strip().lower()
    if not normalized:
        status, reason = "blocked", f"{key}_missing"
    elif "mainnet" in normalized:
        status, reason = "blocked", f"{key}_points_to_mainnet"
    elif "testnet" in normalized:
        status, reason = "pass", f"{key}_testnet_labeled"
    else:
        status, reason = "wait", f"{key}_custom_network_requires_review"
    return _check(key=key, label=f"{label} endpoint", status=status, reason=reason)


def _asset_configuration_check(settings: Settings) -> dict:
    configured_ids = {asset_id for pair in settings.asset_pairs for asset_id in pair if asset_id > 0}
    mainnet_ids = sorted(configured_ids.intersection(MAINNET_ONLY_ASSET_IDS))
    target_id = int(settings.target_asset_id)

    if target_id in MAINNET_ONLY_ASSET_IDS:
        return _check(
            key="asset_configuration",
            label="TestNet asset configuration",
            status="blocked",
            reason=f"target_asset_{target_id}_is_mainnet_only",
        )
    if mainnet_ids:
        return _check(
            key="asset_configuration",
            label="TestNet asset configuration",
            status="blocked",
            reason=f"mainnet_asset_ids_in_testnet_pairs_{'_'.join(str(item) for item in mainnet_ids)}",
        )
    if target_id <= 0:
        return _check(
            key="asset_configuration",
            label="TestNet asset configuration",
            status="blocked",
            reason="testnet_pnet_asset_id_not_configured",
        )
    if target_id not in configured_ids:
        return _check(
            key="asset_configuration",
            label="TestNet asset configuration",
            status="wait",
            reason="testnet_pnet_asset_missing_from_scan_pairs",
        )
    return _check(
        key="asset_configuration",
        label="TestNet asset configuration",
        status="pass",
        reason="testnet_asset_ids_are_network_scoped",
    )


def _connector_check(connector_mode: str) -> dict:
    modes = {part.strip().lower() for part in connector_mode.split(",") if part.strip()}
    required = {"tinyman", "pact"}
    if required.issubset(modes) and "mock" not in modes:
        status, reason = "pass", "tinyman_and_pact_read_only_connectors_configured"
    elif modes.intersection(required):
        status, reason = "wait", "cross_venue_connector_coverage_incomplete"
    else:
        status, reason = "wait", "mock_connectors_not_testnet_evidence"
    return _check(key="connectors", label="DEX connector coverage", status=status, reason=reason)


def _wallet_boundary_check(settings: Settings) -> dict:
    """Connect-only Pera/Defly adapters are available; signing remains forbidden."""
    disarmed = (
        not settings.enable_live_execution
        and not settings.execute_approved
        and not settings.allow_api_execution
        and settings.unsigned_executor_only
        and not settings.signer_enabled
        and settings.signer_kill_switch
        and not bool(settings.trader_mnemonic.strip())
    )
    if settings.network != "testnet":
        return _check(
            key="wallet_boundary",
            label="Pera / Defly wallet boundary",
            status="blocked",
            reason="wallet_access_requires_testnet_backend",
            gate="wallet",
        )
    if not disarmed:
        return _check(
            key="wallet_boundary",
            label="Pera / Defly wallet boundary",
            status="blocked",
            reason="execution_or_signer_boundary_open",
            gate="wallet",
        )
    return _check(
        key="wallet_boundary",
        label="Pera / Defly wallet boundary",
        status="pass",
        reason="connect_only_pera_defly_adapters_available",
        gate="wallet",
    )


def _live_health_checks(health: dict[str, Any]) -> list[dict]:
    algod = health.get("algod") or {}
    indexer = health.get("indexer") or {}
    mismatches = list(health.get("mismatches") or [])
    checks = [
        _check(
            key="algod_live",
            label="algod live health",
            status="pass" if algod.get("healthy") else "blocked",
            reason=str(algod.get("detail") or ("algod_healthy" if algod.get("healthy") else "algod_unreachable")),
            gate="access",
        ),
        _check(
            key="indexer_live",
            label="Indexer live health",
            status="pass" if indexer.get("healthy") else "blocked",
            reason=str(
                indexer.get("detail")
                or ("indexer_healthy" if indexer.get("healthy") else "indexer_unreachable")
            ),
            gate="access",
        ),
    ]
    if mismatches:
        checks.append(
            _check(
                key="network_mismatch",
                label="Endpoint network match",
                status="blocked",
                reason=",".join(mismatches),
                gate="access",
            )
        )
    return checks


def _public_safe_health(health: dict[str, Any]) -> dict[str, Any]:
    """Strip anything that could look like an endpoint URL or token."""
    def _probe(item: dict[str, Any] | None) -> dict[str, Any]:
        item = item or {}
        return {
            "connector": item.get("connector"),
            "status": item.get("status"),
            "healthy": bool(item.get("healthy")),
            "lastRound": item.get("lastRound"),
            "networkHint": item.get("networkHint"),
            "latencyMs": item.get("latencyMs"),
            "detail": item.get("detail"),
        }

    return {
        "overall": health.get("overall"),
        "ok": bool(health.get("ok")),
        "mismatches": list(health.get("mismatches") or []),
        "algod": _probe(health.get("algod")),
        "indexer": _probe(health.get("indexer")),
    }


def _rollup_status(checks: Iterable[dict]) -> str:
    statuses = {item["status"] for item in checks}
    if "blocked" in statuses:
        return "blocked"
    if "wait" in statuses:
        return "in_progress"
    return "ready"


def _next_action(checks: Iterable[dict]) -> str:
    priority = (
        "network",
        "execution_boundary",
        "secret_boundary",
        "public_delay",
        "algod_endpoint",
        "indexer_endpoint",
        "asset_configuration",
        "connectors",
        "environment",
    )
    by_key = {item["key"]: item for item in checks}
    actions = {
        "network": "Load the safe TestNet environment profile.",
        "execution_boundary": "Disarm execution and signer flags and keep the kill switch active.",
        "secret_boundary": "Remove signer material from the API process before TestNet staging.",
        "public_delay": f"Set PUBLIC_ROUTE_DELAY_SECONDS to at least {MIN_PUBLIC_DELAY_SECONDS}.",
        "algod_endpoint": "Configure and verify a TestNet algod endpoint.",
        "indexer_endpoint": "Configure and verify a TestNet Indexer endpoint.",
        "asset_configuration": "Create or select a TestNet-only PNET test ASA and add it to the scan pairs.",
        "connectors": "Enable both Tinyman and Pact read-only TestNet connectors.",
        "environment": "Run the profile with APP_ENV=testnet or APP_ENV=staging.",
    }
    for key in priority:
        item = by_key.get(key)
        if item and item["status"] != "pass":
            return actions[key]
    return "Review remaining TestNet evidence."
