"""Gate 3 — x402 TestNet payment wiring (managed GoPlausible + Algorand TestNet USDC).

Isolated, fail-closed configuration and middleware builder for protecting exactly
one resource — ``GET /api/x402/reports/market-pulse/daily`` — with the official
``x402-avm`` FastAPI path.

Safety invariants (enforced here):
  - Disabled by default. Activates only when BOTH
    ``ALGOPULSE_X402_TESTNET_ENABLED=true`` and
    ``ALGOPULSE_X402_TESTNET_CONFIG_CONFIRMED=true`` and all required values are
    present and non-placeholder. Otherwise it fails closed (stays disabled).
  - Never prints or logs configured env *values* — only variable names / reasons.
  - Imports no signer, wallet-custody, trading, or transaction-submission code.
  - Does not construct, parse, log, or rewrite the payment payload / paymentGroup;
    that is owned entirely by the official package and facilitator.

This module is TestNet-only. It contains no Mainnet config and performs no deploy.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Mapping

logger = logging.getLogger("algopulse.x402")

# The single protected resource. No other route is exposed or protected.
PROTECTED_ROUTE = "GET /api/x402/reports/market-pulse/daily"
RESOURCE_ID = "algopulse.market_pulse.daily.v0"

ENABLE_VAR = "ALGOPULSE_X402_TESTNET_ENABLED"
CONFIRM_VAR = "ALGOPULSE_X402_TESTNET_CONFIG_CONFIRMED"

# Required to build a real TestNet payment requirement.
REQUIRED_VARS = (
    "ALGOPULSE_X402_FACILITATOR_URL",
    "ALGOPULSE_X402_NETWORK",
    "ALGOPULSE_X402_ASSET_ID",
    "ALGOPULSE_X402_ASSET_SYMBOL",
    "ALGOPULSE_X402_ASSET_DECIMALS",
    "ALGOPULSE_X402_AMOUNT",
    "ALGOPULSE_X402_RECEIVER",
    "ALGOPULSE_X402_RESOURCE",
)

ALLOWED_FACILITATOR_URL = "https://facilitator.goplausible.xyz"
ALLOWED_NETWORK = "algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
ALLOWED_ASSET_ID = 10458941
ALLOWED_ASSET_SYMBOL = "USDC"
ALLOWED_ASSET_DECIMALS = 6

# Substrings that mark a value as not-yet-real. Fail closed if any appears.
PLACEHOLDER_MARKERS = (
    "placeholder", "replace", "todo", "changeme", "example",
    "dummy", "mock", "fake", "do_not_commit", "<", ">",
)


@dataclass(frozen=True)
class X402TestnetConfig:
    facilitator_url: str
    network: str
    asset_id: int
    asset_decimals: int
    asset_symbol: str
    amount_base_units: str
    receiver: str
    resource: str


@dataclass(frozen=True)
class X402ConfigEvaluation:
    config: X402TestnetConfig | None
    enabled: bool
    confirmed: bool
    fail_closed: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class X402AttachState:
    active: bool
    enabled: bool
    confirmed: bool
    fail_closed: bool
    reason: str
    errors: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.active


def _norm(value: str | None) -> str:
    return (value or "").strip()


def _is_placeholder(value: str) -> bool:
    low = _norm(value).lower()
    return (not low) or any(marker in low for marker in PLACEHOLDER_MARKERS)


def _to_base_units(amount: str, decimals: int) -> str | None:
    """Convert a price to integer base units as a string.

    Accepts a dollar amount (e.g. ``$0.01`` -> ``10000`` at 6 decimals) or an
    already-base-unit integer (e.g. ``10000``). Returns None if unparseable.
    """
    raw = _norm(amount).lstrip("$").strip()
    if not raw:
        return None
    if raw.isdigit():
        return raw
    try:
        scaled = Decimal(raw) * (Decimal(10) ** decimals)
    except (InvalidOperation, ValueError):
        return None
    if scaled != scaled.to_integral_value():
        return None
    return str(int(scaled))


def evaluate_testnet_config(env: Mapping[str, str] | None = None) -> X402ConfigEvaluation:
    """Evaluate TestNet config without logging configured values."""
    env = os.environ if env is None else env
    enabled = _norm(env.get(ENABLE_VAR)).lower() == "true"
    confirmed = _norm(env.get(CONFIRM_VAR)).lower() == "true"

    if not enabled:
        return X402ConfigEvaluation(config=None, enabled=False, confirmed=confirmed, fail_closed=False)

    if not confirmed:
        return X402ConfigEvaluation(config=None, enabled=True, confirmed=False, fail_closed=False)

    reasons: list[str] = []
    missing = [name for name in REQUIRED_VARS if not _norm(env.get(name))]
    placeholders = [
        name for name in REQUIRED_VARS
        if _norm(env.get(name)) and _is_placeholder(env.get(name, ""))
    ]
    if missing:
        reasons.append("missing:" + ",".join(missing))
    if placeholders:
        reasons.append("placeholder:" + ",".join(placeholders))

    try:
        asset_id = int(_norm(env.get("ALGOPULSE_X402_ASSET_ID")) or "0")
    except ValueError:
        asset_id = 0
        reasons.append("ALGOPULSE_X402_ASSET_ID:not-int")

    try:
        decimals = int(_norm(env.get("ALGOPULSE_X402_ASSET_DECIMALS")) or "6")
    except ValueError:
        decimals = 6
        reasons.append("ALGOPULSE_X402_ASSET_DECIMALS:not-int")

    amount_base = _to_base_units(env.get("ALGOPULSE_X402_AMOUNT", ""), decimals)
    if amount_base is None and not missing:
        reasons.append("ALGOPULSE_X402_AMOUNT:unparseable")
    else:
        try:
            if int(amount_base or "0") <= 0:
                reasons.append("ALGOPULSE_X402_AMOUNT:not-positive")
        except ValueError:
            reasons.append("ALGOPULSE_X402_AMOUNT:unparseable")

    facilitator_url = _norm(env.get("ALGOPULSE_X402_FACILITATOR_URL"))
    network = _norm(env.get("ALGOPULSE_X402_NETWORK"))
    asset_symbol = _norm(env.get("ALGOPULSE_X402_ASSET_SYMBOL"))
    resource = _norm(env.get("ALGOPULSE_X402_RESOURCE"))

    if facilitator_url and facilitator_url != ALLOWED_FACILITATOR_URL:
        reasons.append("ALGOPULSE_X402_FACILITATOR_URL:not-allowed")
    if network and network != ALLOWED_NETWORK:
        reasons.append("ALGOPULSE_X402_NETWORK:not-allowed")
    if asset_id and asset_id != ALLOWED_ASSET_ID:
        reasons.append("ALGOPULSE_X402_ASSET_ID:not-allowed")
    if asset_symbol and asset_symbol.upper() != ALLOWED_ASSET_SYMBOL:
        reasons.append("ALGOPULSE_X402_ASSET_SYMBOL:not-allowed")
    if decimals != ALLOWED_ASSET_DECIMALS:
        reasons.append("ALGOPULSE_X402_ASSET_DECIMALS:not-allowed")
    if resource and resource != RESOURCE_ID:
        reasons.append("ALGOPULSE_X402_RESOURCE:not-allowed")

    if reasons:
        return X402ConfigEvaluation(
            config=None,
            enabled=True,
            confirmed=True,
            fail_closed=True,
            errors=tuple(reasons),
        )

    return X402ConfigEvaluation(
        config=X402TestnetConfig(
            facilitator_url=facilitator_url,
            network=network,
            asset_id=asset_id,
            asset_decimals=decimals,
            asset_symbol=asset_symbol,
            amount_base_units=amount_base or "",
            receiver=_norm(env.get("ALGOPULSE_X402_RECEIVER")),
            resource=resource,
        ),
        enabled=True,
        confirmed=True,
        fail_closed=False,
    )


def load_testnet_config(env: Mapping[str, str] | None = None) -> X402TestnetConfig | None:
    """Return a validated config, or None if inactive/invalid.

    Never logs configured values — only variable names and failure reasons.
    """
    evaluation = evaluate_testnet_config(env)
    if evaluation.fail_closed:
        logger.warning("x402 TestNet disabled (fail-closed): %s", "; ".join(evaluation.errors))
    return evaluation.config


def build_routes_and_server(config: X402TestnetConfig):
    """Build the official x402 routes mapping and resource server for one route.

    Imports the official package lazily so the package is only required when
    TestNet mode is actually enabled.
    """
    from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
    from x402.http.types import RouteConfig
    from x402.mechanisms.avm.exact import ExactAvmServerScheme
    from x402.schemas import AssetAmount
    from x402.server import x402ResourceServer

    facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=config.facilitator_url))
    server = x402ResourceServer(facilitator)
    server.register(config.network, ExactAvmServerScheme())

    routes = {
        PROTECTED_ROUTE: RouteConfig(
            accepts=PaymentOption(
                scheme="exact",
                pay_to=config.receiver,
                price=AssetAmount(
                    amount=config.amount_base_units,
                    asset=str(config.asset_id),
                    extra={"name": config.asset_symbol, "decimals": config.asset_decimals},
                ),
                network=config.network,
            ),
            resource=config.resource,
            description="AlgoPulse delayed market-pulse daily report (TestNet x402).",
        ),
    }
    return routes, server


def attach_payment_middleware(app, env: Mapping[str, str] | None = None) -> X402AttachState:
    """Attach x402 payment middleware for the one protected route if fully enabled.

    Returns an attach state. Logs no configured values.
    """
    evaluation = evaluate_testnet_config(env)
    config = evaluation.config
    if config is None:
        if evaluation.fail_closed:
            logger.warning("x402 TestNet middleware fail-closed: %s", "; ".join(evaluation.errors))
            return X402AttachState(
                active=False,
                enabled=evaluation.enabled,
                confirmed=evaluation.confirmed,
                fail_closed=True,
                reason="invalid_config",
                errors=evaluation.errors,
            )
        logger.info("x402 TestNet middleware NOT attached (mock mode).")
        return X402AttachState(
            active=False,
            enabled=evaluation.enabled,
            confirmed=evaluation.confirmed,
            fail_closed=False,
            reason="mock_mode",
        )

    try:
        from x402.http.middleware.fastapi import PaymentMiddlewareASGI

        routes, server = build_routes_and_server(config)
        app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)
    except Exception as exc:  # noqa: BLE001 — fail closed on any wiring/import error
        exc_name = type(exc).__name__
        logger.error(
            "x402 TestNet middleware attach failed; fail-closed: %s",
            "exception_class=" + exc_name,
        )
        return X402AttachState(
            active=False,
            enabled=True,
            confirmed=True,
            fail_closed=True,
            reason="attach_failed",
            errors=("attach_failed:" + exc_name,),
        )

    logger.info("x402 TestNet middleware active for %s (config loaded).", PROTECTED_ROUTE)
    return X402AttachState(
        active=True,
        enabled=True,
        confirmed=True,
        fail_closed=False,
        reason="active",
    )


def status_summary(active: bool) -> dict:
    """Non-sensitive status for health/debug. Contains no configured env values."""
    return {
        "x402TestnetActive": active,
        "protectedRoute": PROTECTED_ROUTE,
        "resource": RESOURCE_ID,
        "facilitator": "goplausible" if active else None,
        "valuesPrinted": False,
    }
