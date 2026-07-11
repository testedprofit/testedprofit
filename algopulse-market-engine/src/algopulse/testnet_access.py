"""TestNet Access Phase helpers (connect + read only).

Probes algod/Indexer health and reads public account state for connected wallets.
Never constructs, signs, or submits transactions. Never loads mnemonics or keys.
"""

from __future__ import annotations

import time
from typing import Any

from algosdk.encoding import is_valid_address

from algopulse.algorand import build_algod_client, build_indexer_client, raw_to_display
from algopulse.config import Settings
from algopulse.readonly_safety import assert_execution_disarmed
from algopulse.testnet_readiness import MAINNET_ONLY_ASSET_IDS

# Algorand genesis / WalletConnect chain ids used by Pera and Defly.
ALGORAND_CHAIN_IDS = {
    "mainnet": 416001,
    "testnet": 416002,
    "betanet": 416003,
}

class TestnetAccessError(RuntimeError):  # noqa: N818 - project-local error name
    """Raised for invalid wallet/network access requests."""


# Prevent pytest from collecting this exception class as a test.
TestnetAccessError.__test__ = False  # type: ignore[attr-defined]


def assert_testnet_access_profile_safe(settings: Settings) -> None:
    """Fail-closed gate for the TestNet Access runtime profile."""
    network = (settings.network or "").strip().lower()
    env = (settings.env or "").strip().lower()
    if network != "testnet":
        raise TestnetAccessError(f"refused_non_testnet_network:{network or 'unconfigured'}")
    if env not in {"testnet", "staging"}:
        raise TestnetAccessError(f"refused_env_not_testnet_access:{env or 'unconfigured'}")
    assert_execution_disarmed(settings)
    if "mainnet" in (settings.algod_url or "").lower():
        raise TestnetAccessError("refused_algod_points_to_mainnet")
    if "mainnet" in (settings.indexer_url or "").lower():
        raise TestnetAccessError("refused_indexer_points_to_mainnet")


def chain_id_for_network(network: str) -> int | None:
    return ALGORAND_CHAIN_IDS.get((network or "").strip().lower())


def is_valid_algo_address(address: str) -> bool:
    return is_valid_address((address or "").strip().upper())


def _testnet_pnet_configuration(settings: Settings) -> tuple[int, bool]:
    pnet_id = int(settings.target_asset_id or 0)
    configured = pnet_id > 0
    if (settings.network or "").strip().lower() == "testnet":
        configured = configured and pnet_id not in MAINNET_ONLY_ASSET_IDS
    return pnet_id, configured


def validate_wallet_network(
    settings: Settings,
    *,
    claimed_network: str | None,
    claimed_chain_id: int | None = None,
) -> dict[str, Any]:
    """Backend is authority: wallet/session network must match settings.network."""
    expected = (settings.network or "").strip().lower()
    claimed = (claimed_network or "").strip().lower()
    expected_chain = chain_id_for_network(expected)
    ok = True
    reasons: list[str] = []
    if not claimed:
        ok = False
        reasons.append("wallet_network_missing")
    elif claimed != expected:
        ok = False
        reasons.append(f"wallet_network_mismatch:claimed_{claimed}_expected_{expected}")
    if claimed_chain_id is not None and expected_chain is not None:
        if int(claimed_chain_id) != int(expected_chain):
            ok = False
            reasons.append(
                f"wallet_chain_id_mismatch:claimed_{claimed_chain_id}_expected_{expected_chain}"
            )
    return {
        "ok": ok,
        "expectedNetwork": expected,
        "claimedNetwork": claimed or None,
        "expectedChainId": expected_chain,
        "claimedChainId": claimed_chain_id,
        "reasons": reasons,
        "rejected": not ok,
        "rejectionCode": reasons[0] if reasons else None,
        "message": (
            None
            if ok
            else (
                f"Wallet/network mismatch: backend is {expected}; "
                f"wallet claimed {claimed or 'unknown'}."
            )
        ),
    }


def probe_algod_health(settings: Settings, *, timeout_note: str | None = None) -> dict[str, Any]:
    """Live algod status probe (no secrets returned)."""
    started = time.perf_counter()
    url_label = _endpoint_network_label(settings.algod_url)
    try:
        client = build_algod_client(settings)
        status = client.status()
        last_round = int(status.get("last-round") or status.get("last_round") or 0)
        genesis = str(status.get("genesis-id") or status.get("genesis_id") or "")
        network_hint = _network_from_genesis(genesis) or url_label
        latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
        healthy = last_round > 0
        return {
            "connector": "algod",
            "status": "ok" if healthy else "degraded",
            "healthy": healthy,
            "lastRound": last_round,
            "genesisId": genesis or None,
            "networkHint": network_hint,
            "endpointNetworkLabel": url_label,
            "latencyMs": latency_ms,
            "detail": "algod_status_ok" if healthy else "algod_round_missing",
            "note": timeout_note,
        }
    except Exception as exc:
        return {
            "connector": "algod",
            "status": "down",
            "healthy": False,
            "lastRound": 0,
            "genesisId": None,
            "networkHint": url_label,
            "endpointNetworkLabel": url_label,
            "latencyMs": round((time.perf_counter() - started) * 1000.0, 2),
            "detail": f"algod_error:{type(exc).__name__}",
            "note": timeout_note,
        }


def probe_indexer_health(settings: Settings) -> dict[str, Any]:
    """Live Indexer health probe (no secrets returned)."""
    started = time.perf_counter()
    url_label = _endpoint_network_label(settings.indexer_url)
    try:
        client = build_indexer_client(settings)
        # Prefer health if present; fall back to a minimal search.
        health = None
        if hasattr(client, "health"):
            try:
                health = client.health()
            except Exception:
                health = None
        round_hint = 0
        if isinstance(health, dict):
            round_hint = int(health.get("round") or health.get("data", {}).get("round") or 0)
        if round_hint <= 0:
            # search_transactions with limit=1 is a cheap reachability probe.
            result = client.search_transactions(limit=1)
            if isinstance(result, dict):
                # current-round is commonly present on indexer responses
                round_hint = int(result.get("current-round") or result.get("current_round") or 0)
        latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
        healthy = True  # response returned without exception
        return {
            "connector": "indexer",
            "status": "ok" if healthy else "degraded",
            "healthy": healthy,
            "lastRound": round_hint,
            "networkHint": url_label,
            "endpointNetworkLabel": url_label,
            "latencyMs": latency_ms,
            "detail": "indexer_reachable",
        }
    except Exception as exc:
        return {
            "connector": "indexer",
            "status": "down",
            "healthy": False,
            "lastRound": 0,
            "networkHint": url_label,
            "endpointNetworkLabel": url_label,
            "latencyMs": round((time.perf_counter() - started) * 1000.0, 2),
            "detail": f"indexer_error:{type(exc).__name__}",
        }


def build_network_health(settings: Settings) -> dict[str, Any]:
    algod = probe_algod_health(settings)
    indexer = probe_indexer_health(settings)
    expected = (settings.network or "").strip().lower()
    mismatches: list[str] = []
    for probe in (algod, indexer):
        hint = str(probe.get("networkHint") or "")
        if hint and hint not in {expected, "custom", "unknown"} and hint != expected:
            if expected == "testnet" and hint == "mainnet":
                mismatches.append(f"{probe['connector']}_mainnet_mismatch")
            elif expected == "mainnet" and hint == "testnet":
                mismatches.append(f"{probe['connector']}_testnet_mismatch")
    overall = "ok"
    if not algod.get("healthy") or not indexer.get("healthy"):
        overall = "degraded" if algod.get("healthy") or indexer.get("healthy") else "down"
    if mismatches:
        overall = "blocked"
    return {
        "network": expected,
        "environment": settings.env,
        "overall": overall,
        "ok": overall == "ok",
        "mismatches": mismatches,
        "algod": algod,
        "indexer": indexer,
        "productionReady": False,
        "signingEnabled": False,
        "submissionEnabled": False,
        "walletAccessMode": "connect_only",
    }


def read_account_state(settings: Settings, address: str) -> dict[str, Any]:
    """Read public account balances from TestNet/MainNet node configured by backend."""
    normalized = (address or "").strip().upper()
    if not is_valid_algo_address(normalized):
        raise TestnetAccessError("invalid_algo_address")
    client = build_algod_client(settings)
    info = client.account_info(normalized)
    micro = int(info.get("amount") or 0)
    algo_balance = raw_to_display(micro, 6)
    assets = info.get("assets") or []
    holding_map = {
        int(item.get("asset-id") or item.get("asset_id") or 0): int(item.get("amount") or 0)
        for item in assets
        if isinstance(item, dict)
    }
    pnet_id, pnet_configured = _testnet_pnet_configuration(settings)
    pnet_opted_in = False
    pnet_balance = None
    pnet_message = None
    if not pnet_configured:
        pnet_message = "PNET TestNet asset not configured"
    else:
        decimals = None
        try:
            asset_info = client.asset_info(pnet_id)
            params = asset_info.get("params") or {}
            if "decimals" in params:
                decimals = int(params["decimals"])
        except Exception:
            decimals = None
        if pnet_id in holding_map:
            pnet_opted_in = True
            if decimals is None:
                pnet_message = f"ASA {pnet_id} metadata unavailable; balance not displayed"
            else:
                pnet_balance = raw_to_display(holding_map[pnet_id], decimals)
        else:
            pnet_opted_in = False
            pnet_balance = 0.0
            pnet_message = f"Wallet not opted into ASA {pnet_id}"

    return {
        "address": normalized,
        "network": settings.network,
        "chainId": chain_id_for_network(settings.network),
        "algoBalance": algo_balance,
        "algoBalanceMicro": micro,
        "pnetAsaId": pnet_id if pnet_configured else None,
        "pnetAsaConfigured": pnet_configured,
        "pnetOptedIn": pnet_opted_in if pnet_configured else None,
        "pnetBalance": pnet_balance,
        "pnetMessage": pnet_message,
        "source": "algod_account_info",
        "readOnly": True,
        "signingEnabled": False,
        "submissionEnabled": False,
        "optInTransactionOffered": False,
    }


def build_public_wallet_access_config(settings: Settings) -> dict[str, Any]:
    """Public-safe wallet/network identity for the frontend."""
    network = (settings.network or "").strip().lower()
    pnet_id, pnet_configured = _testnet_pnet_configuration(settings)
    return {
        "developmentPhase": "AlgoPulse Phase 3: TestNet Access",
        "developmentPhaseStatus": "in_progress" if network == "testnet" else "blocked",
        "environment": settings.env,
        "network": network,
        "backendNetworkAuthority": True,
        "chainId": chain_id_for_network(network),
        "walletAccessMode": "connect_only",
        "walletConnectOnly": True,
        "supportedWallets": ["pera", "defly"],
        "supportedNetworks": ["testnet", "mainnet"],
        "pnetAsaId": pnet_id if pnet_configured else 0,
        "pnetAsaConfigured": pnet_configured,
        "pnetMessage": None if pnet_configured else "PNET TestNet asset not configured",
        "liveExecutionEnabled": bool(settings.enable_live_execution),
        "signerEnabled": bool(settings.signer_enabled),
        "signingEnabled": False,
        "submissionEnabled": False,
        "productionReady": False,
        "capabilities": {
            "connectWallet": True,
            "readAccountState": True,
            "signTransactions": False,
            "submitTransactions": False,
            "assetOptIn": False,
            "liveTrading": False,
        },
        "boundaries": {
            "transactionConstructionDisabled": True,
            "signingRequestsDisabled": True,
            "submissionDisabled": True,
            "accountCredentialHandlingDisabled": True,
            "recoveryPhraseHandlingDisabled": True,
        },
    }


def _endpoint_network_label(url: str) -> str:
    normalized = (url or "").strip().lower()
    if not normalized:
        return "unknown"
    if "mainnet" in normalized:
        return "mainnet"
    if "testnet" in normalized:
        return "testnet"
    if "betanet" in normalized:
        return "betanet"
    return "custom"


def _network_from_genesis(genesis_id: str) -> str | None:
    value = (genesis_id or "").strip().lower()
    if not value:
        return None
    if "mainnet" in value or value.startswith("mainnet"):
        return "mainnet"
    if "testnet" in value or value.startswith("testnet"):
        return "testnet"
    if "betanet" in value:
        return "betanet"
    return None
