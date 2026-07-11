from __future__ import annotations

from contextlib import asynccontextmanager
import hashlib
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Literal

from fastapi import Depends
from fastapi import FastAPI
from fastapi import Header
from fastapi import HTTPException
from fastapi import Request
from pydantic import BaseModel
from pydantic import Field
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from algopulse.algorand import build_indexer_client
from algopulse.config import Settings, get_settings
from algopulse.demo import run_five_to_ten_demo
from algopulse.failure_simulation import build_failure_lab_report
from algopulse.payment_verification import AlgorandPaymentVerifier
from algopulse.payment_verification import PaymentVerificationRequest
from algopulse.product_validation import ACTION_TAXONOMY
from algopulse.production_readiness import build_production_readiness_report
from algopulse.public_record_redaction import redact_public_record
from algopulse.readiness import build_live_readiness_report
from algopulse.recent_swaps import fetch_recent_pnet_swaps
from algopulse.refunds import RefundCaseInput
from algopulse.refunds import build_refund_case
from algopulse.scanner import MarketScanner
from algopulse.store import MarketStore
from algopulse.testnet_access import (
    TestnetAccessError,
    assert_testnet_access_profile_safe,
    build_network_health,
    build_public_wallet_access_config,
    is_valid_algo_address,
    read_account_state,
    validate_wallet_network,
)
from algopulse.testnet_readiness import build_testnet_readiness
from algopulse.testnet_soak import build_testnet_soak_summary
from algopulse.testnet_soak import public_safe_observation
from algopulse import x402_testnet


settings: Settings = get_settings()
store = MarketStore(settings.database_path)
scanner = MarketScanner(settings=settings, store=store)
payment_verifier = AlgorandPaymentVerifier(build_indexer_client(settings))


def _run_initial_scan_safely() -> None:
    try:
        scanner.run_once()
    except Exception as exc:
        store.record_service_health(
            "market_scanner",
            "error",
            detail="initial_scan_failed",
            metrics={"errorType": type(exc).__name__},
        )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    network = (settings.network or "").strip().lower()
    environment = (settings.env or "").strip().lower()
    if network == "testnet" or environment == "testnet":
        assert_testnet_access_profile_safe(settings)
    store.initialize(run_backfills=False)
    if settings.enable_scanner and not store.has_market_data():
        threading.Thread(
            target=_run_initial_scan_safely,
            name="algopulse-initial-scan",
            daemon=True,
        ).start()
    yield


app = FastAPI(title="AlgoPulse Market Engine", version="0.1.0", lifespan=lifespan)

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

LOCAL_REVIEW_ADMIN_WALLET = "ADMIN6H2ZREVIEWWALLET9KX4CONTROL"
MOCK_X402_REPORT_PROOF = "mock_x402_report_access"
X402_MARKET_PULSE_RESOURCE = "algopulse.market_pulse.daily.v0"

# Gate 3 — attach the official x402 TestNet payment middleware for the single
# protected report route, only when TestNet mode is fully enabled + confirmed.
# Fail-closed: defaults to mock mode when disabled/unconfirmed. If TestNet x402
# was enabled+confirmed but could not attach, the route returns a hard safe error.
X402_TESTNET_STATE = x402_testnet.attach_payment_middleware(app)
X402_TESTNET_ACTIVE = X402_TESTNET_STATE.active
X402_TESTNET_FAIL_CLOSED = X402_TESTNET_STATE.fail_closed

CONTRIBUTION_ACTIONS = {
    "docs_fix": {
        "label": "Docs improvement",
        "credits": 1,
        "reviewSla": "manual_review",
        "evidenceRequired": "GitHub issue, pull request, screenshot, or concise written note.",
    },
    "pool_observation": {
        "label": "PNET pool observation",
        "credits": 1,
        "reviewSla": "manual_review",
        "evidenceRequired": "Pool URL, venue, observed pair, and source timestamp.",
    },
    "bug_report": {
        "label": "Bug or safety report",
        "credits": 2,
        "reviewSla": "manual_review",
        "evidenceRequired": "Reproduction steps, expected behavior, observed behavior, and screenshots if safe.",
    },
    "demo_feedback": {
        "label": "Beta demo feedback",
        "credits": 1,
        "reviewSla": "manual_review",
        "evidenceRequired": "What was tested, what confused the user, and what should improve.",
    },
    "data_source_suggestion": {
        "label": "Data-source suggestion",
        "credits": 1,
        "reviewSla": "manual_review",
        "evidenceRequired": "Source URL, terms notes if known, and why it helps delayed market intelligence.",
    },
    "mining_evidence": {
        "label": "Mining evidence receipt",
        "credits": 1,
        "reviewSla": "manual_review",
        "evidenceRequired": "Redacted mining receipt, date, source, and methodology note. No earnings projection.",
    },
    "bandwidth_evidence": {
        "label": "Bandwidth evidence receipt",
        "credits": 1,
        "reviewSla": "manual_review",
        "evidenceRequired": "Redacted bandwidth-sharing receipt, date, source, and methodology note. No earnings projection.",
    },
    "verification_report": {
        "label": "Verification report",
        "credits": 2,
        "reviewSla": "manual_review",
        "evidenceRequired": "Reproducible verification steps, source links, screenshots if safe, and risk notes.",
    },
}

CONTRIBUTION_CREDIT_UNLOCKS = {
    "premium_market_report": {
        "label": "Premium delayed market report",
        "creditsCost": 2,
        "category": "tool_access",
        "unlocks": "Access to a distinct delayed intelligence payload or report export.",
    },
    "pair_scan_credit": {
        "label": "Pair scan credit",
        "creditsCost": 1,
        "category": "tool_access",
        "unlocks": "One delayed pair scan request queued for public-safe review output.",
    },
    "route_simulation_credit": {
        "label": "Route simulation credit",
        "creditsCost": 3,
        "category": "premium_feature",
        "unlocks": "One paper-only route simulation or replay view. No live execution.",
    },
    "governance_signal_comment": {
        "label": "Governance signal comment",
        "creditsCost": 1,
        "category": "governance_signal",
        "unlocks": "A non-binding proposal comment or priority signal for human review.",
    },
    "algoflow_tool_preview": {
        "label": "AlgoFlow tool preview",
        "creditsCost": 2,
        "category": "integration",
        "unlocks": "A beta preview path for approved AlgoFlow-compatible utility tooling.",
    },
}

_CONTRIBUTION_LEDGER: dict[str, list[dict]] = {}
_CREDIT_SPEND_LEDGER: dict[str, list[dict]] = {}
_CREDIT_BALANCE_ADJUSTMENTS: dict[str, int] = {}
_REFERRAL_LEDGER: dict[str, list[dict]] = {}

COMMUNITY_ONBOARDING_STEPS = [
    {
        "code": "read_boundaries",
        "label": "Read safety boundaries",
        "detail": "Start with no-custody, no-signing, no-live-trading, and no-yield boundaries.",
    },
    {
        "code": "inspect_utility",
        "label": "Inspect utility",
        "detail": "Review delayed reports, PNET pool visibility, and contribution-credit unlocks.",
    },
    {
        "code": "submit_contribution",
        "label": "Submit contribution",
        "detail": "Send docs, pool, bug, demo, mining, bandwidth, or verification evidence for manual review.",
    },
    {
        "code": "earn_reputation",
        "label": "Earn reputation",
        "detail": "Reputation grows from approved evidence and useful review activity, not token spend.",
    },
]

SEEDED_COMMUNITY_LEADERBOARD = [
    {
        "wallet": "reviewer_docs_001",
        "displayName": "Docs Reviewer",
        "category": "verification",
        "reputationScore": 72,
        "verifiedEvidence": 9,
        "badges": ["Verifier", "Docs Steward"],
        "source": "sample_local_review",
    },
    {
        "wallet": "pool_watch_002",
        "displayName": "Pool Watch",
        "category": "bandwidth",
        "reputationScore": 58,
        "verifiedEvidence": 6,
        "badges": ["Pool Observer"],
        "source": "sample_local_review",
    },
    {
        "wallet": "ops_receipts_003",
        "displayName": "Ops Receipts",
        "category": "mining",
        "reputationScore": 43,
        "verifiedEvidence": 4,
        "badges": ["Receipt Submitter"],
        "source": "sample_local_review",
    },
]

TRANSPARENCY_AUDIT_CHECKLIST = [
    {
        "code": "proof_redaction",
        "label": "Proof redaction",
        "status": "active",
        "evidence": "Public ledger uses hashes/suffixes only; no raw payment payloads or secrets.",
    },
    {
        "code": "manual_review",
        "label": "Manual review queue",
        "status": "active",
        "evidence": "Contribution, referral, and credit-spend records stay pending or receipt-only until human review.",
    },
    {
        "code": "x402_boundary",
        "label": "x402 report boundary",
        "status": "active",
        "evidence": "Paid x402 unlocks delayed/redacted intelligence only; no live trading or fresh executable routes.",
    },
    {
        "code": "gate_3_5",
        "label": "External TestNet payer proof",
        "status": "blocked",
        "evidence": "Requires payer != receiver, sanitized tx/reference, and no-secret/no-payload evidence.",
    },
    {
        "code": "gate_4a",
        "label": "Mainnet readiness docs",
        "status": "blocked",
        "evidence": "Requires legal/public wording, abuse controls, monitoring, rollback, and Mainnet receiver approval.",
    },
]

TRANSPARENCY_THREAT_MODEL = [
    {
        "threat": "Secret or payment-payload leakage",
        "control": "Public transparency APIs omit headers, payment groups, mnemonics, private keys, and raw .env values.",
        "residualRisk": "Future integrations must keep logging policies and redaction tests current.",
    },
    {
        "threat": "False production or challenge-readiness claim",
        "control": "Gate state explicitly separates Gate 3 mechanics proof from Gate 3.5/Gate 4A/Gate 4 approval.",
        "residualRisk": "Public copy still needs human review before external publication.",
    },
    {
        "threat": "Fake contribution or referral demand",
        "control": "Community growth records remain manual-review, non-financial, and non-binding.",
        "residualRisk": "Production needs anti-sybil and abuse controls before public incentives.",
    },
    {
        "threat": "Fresh route or signer exposure",
        "control": "Transparency payloads publish aggregate/redacted proof status only and keep live execution touched false.",
        "residualRisk": "Any future public analytics surface needs a route-data redaction review.",
    },
]


PHASE_GATES = [
    {
        "gate": 1,
        "title": "Scanner 24h",
        "status": "evidence_needed",
        "exitCriteria": "Scanner runs for 24 hours with no signer operational secrets and no submitted transactions.",
    },
    {
        "gate": 2,
        "title": "Comparable Quotes",
        "status": "built",
        "exitCriteria": "Quote engine records comparable Tinyman and Pact quote rows with block round, fee, impact, capture, and expiry metadata.",
    },
    {
        "gate": 3,
        "title": "Explained Rejections",
        "status": "built",
        "exitCriteria": "Route engine stores a skip reason and risk-rule map for every rejected opportunity.",
    },
    {
        "gate": 4,
        "title": "7-Day Paper Trading",
        "status": "evidence_needed",
        "exitCriteria": "Paper trading runs for 7 days with 5s/30s rechecks, quote decay, and expected-vs-simulated profit history.",
    },
    {
        "gate": 5,
        "title": "Risk Blocks Bad Routes",
        "status": "built",
        "exitCriteria": "Risk rules reject stale, unprofitable, high-impact, over-limit, or unallowlisted routes.",
    },
    {
        "gate": 6,
        "title": "Unsigned Dry Run",
        "status": "built",
        "exitCriteria": "Dry-run executor builds unsigned atomic groups only and enforces transaction group limits.",
    },
    {
        "gate": 7,
        "title": "Signer Policy Rejection",
        "status": "built_locked",
        "exitCriteria": "Signer rejects out-of-policy route hashes, app IDs, asset IDs, amounts, fees, transaction types, and kill-switch states.",
    },
    {
        "gate": 8,
        "title": "Manual First Live Trade",
        "status": "future",
        "exitCriteria": "First live trade is manual, tiny, ALGO/USDC scoped, verified in Lora, and reconciled against expected output.",
    },
    {
        "gate": 9,
        "title": "Delayed Public Dashboard",
        "status": "built",
        "exitCriteria": "Dashboard shows delayed, public-safe market data without exposing live raw route intelligence or execution control.",
    },
    {
        "gate": 10,
        "title": "Phase 1 Decision",
        "status": "future",
        "exitCriteria": "Phase 1 decision uses real user demand, market data, paper-trading history, and tiny-live receipts.",
    },
]


DEPLOYMENT_MODES = [
    {
        "mode": "local",
        "label": "Local",
        "summary": "Review and UI work with mock market data by default.",
        "scanner": "optional",
        "data": "mock data",
        "signer": "disabled",
        "submission": "disabled",
        "dashboard": "local operator dashboard",
        "capabilities": [
            "mock data",
            "scanner optional",
            "no signer",
            "no real submission",
        ],
        "requiredControls": [
            "ENABLE_SIGNER=false",
            "ENABLE_EXECUTION=false",
            "KILL_SWITCH=true",
        ],
    },
    {
        "mode": "staging",
        "label": "Staging",
        "summary": "Live market sensing and paper trading without live signing.",
        "scanner": "live",
        "data": "live quotes",
        "signer": "disabled",
        "submission": "disabled",
        "dashboard": "delayed dashboard",
        "capabilities": [
            "live scanner",
            "live quotes",
            "paper trading",
            "no live signing",
            "delayed dashboard",
        ],
        "requiredControls": [
            "ENABLE_SCANNER=true",
            "ENABLE_SIGNER=false",
            "ENABLE_EXECUTION=false",
            "PUBLIC_DATA_DELAY_SECONDS>0",
        ],
    },
    {
        "mode": "production_phase0",
        "label": "Production Phase 0",
        "summary": "Public-safe market intelligence with live signing still gated.",
        "scanner": "live",
        "data": "live scanner, route engine, paper trading, and risk engine",
        "signer": "isolated only after gates",
        "submission": "tiny own-funds hot wallet only after gates",
        "dashboard": "admin dashboard plus public delayed dashboard",
        "capabilities": [
            "live scanner",
            "route engine",
            "paper trading",
            "risk engine",
            "admin dashboard",
            "public delayed dashboard",
            "isolated signer only after gates",
            "tiny own-funds hot wallet only",
        ],
        "requiredControls": [
            "Gate 1-6 evidence complete",
            "Gate 7 signer rejection evidence complete",
            "manual first trade before automation",
            "own funds only",
        ],
    },
]


PRODUCT_CAPABILITIES = [
    {
        "code": "market_intelligence",
        "label": "Market Intelligence",
        "audience": "public, PNET users, admins",
        "status": "active_phase0",
        "dataPolicy": "delayed for public users; richer summaries for PNET access",
        "executionBoundary": "read-only market data",
        "detail": "Turns pool state, quote history, freshness, and paper results into a daily Algorand market view.",
    },
    {
        "code": "scanner",
        "label": "Scanner",
        "audience": "admins now; delayed public and PNET users later",
        "status": "active_phase0",
        "dataPolicy": "pool snapshots, freshness, venue labels, and source badges",
        "executionBoundary": "read-only collection with no private key required",
        "detail": "Collects Tinyman, Pact, and later Vestige/Folks market state without signing or submitting transactions.",
    },
    {
        "code": "route_engine",
        "label": "Route Engine",
        "audience": "PNET users, admins",
        "status": "active_phase0",
        "dataPolicy": "candidate routes, fee math, impact, confidence, and skip reasons",
        "executionBoundary": "generates and explains routes; does not execute them",
        "detail": "Builds two-leg and three-leg route candidates and explains why each route is accepted, rejected, or watched.",
    },
    {
        "code": "paper_trading",
        "label": "Paper Trading",
        "audience": "admins, PNET report users",
        "status": "active_phase0",
        "dataPolicy": "simulation history, 5s/30s rechecks, quote decay, and daily reports",
        "executionBoundary": "no real funds and no submitted transactions",
        "detail": "Replays candidate routes before capital touches the system and records expected-vs-simulated results.",
    },
    {
        "code": "risk_engine",
        "label": "Risk Engine",
        "audience": "admins",
        "status": "active_phase0",
        "dataPolicy": "reject reasons, allowlist decisions, fee buffers, and policy evidence",
        "executionBoundary": "rejects most routes and cannot sign or submit",
        "detail": "Applies freshness, allowlist, size, impact, profit, loss-limit, and route-length gates before any dry-run handoff.",
    },
    {
        "code": "execution_controls",
        "label": "Execution Controls",
        "audience": "admins only",
        "status": "gated_future",
        "dataPolicy": "lock state, dry-run receipts, signer boundary evidence, and reconciliation proof",
        "executionBoundary": "unsigned dry runs only until all gates pass; never user deposits",
        "detail": "Shows arm/disarm, kill switch, unsigned-builder, signer-lock, and future tiny own-funds controls without exposing keys.",
    },
    {
        "code": "public_dashboard",
        "label": "Public Dashboard",
        "audience": "public",
        "status": "active_phase0",
        "dataPolicy": "delayed, aggregated, and public-safe market intelligence",
        "executionBoundary": "view-only dashboard",
        "detail": "Builds trust with delayed route intelligence, market health, source labels, receipts, and no fresh executable strategy.",
    },
    {
        "code": "pnet_access_layer",
        "label": "PNET Access Layer",
        "audience": "PNET users, admins",
        "status": "active_phase0",
        "dataPolicy": "wallet checks, fee quotes, tx verification, credits, receipts, and delayed reports",
        "executionBoundary": "PNET buys scans, simulations, reports, and credits only; it is not a deposit or execution permission",
        "detail": "Connects Algorand wallet access and PNET payments to market-data products while keeping user funds out of the trading system.",
    },
]


ALERT_CATALOG = [
    {
        "code": "scanner_down",
        "title": "Scanner Down",
        "severity": "critical",
        "service": "pool_scanner",
        "trigger": "No scanner heartbeat or scan completion inside the configured freshness window.",
        "operatorAction": "Pause promotion, restart scanner, and confirm no signer secrets are required.",
        "phase0Behavior": "Block staging promotion and mark public data stale.",
    },
    {
        "code": "tinyman_connector_failing",
        "title": "Tinyman Connector Failing",
        "severity": "high",
        "service": "quote_engine",
        "trigger": "Tinyman pool fetch or quote normalization fails repeatedly.",
        "operatorAction": "Disable Tinyman routes for paper decisions until connector recovery is verified.",
        "phase0Behavior": "Keep scanner read-only and continue Pact-only monitoring if safe.",
    },
    {
        "code": "pact_connector_failing",
        "title": "Pact Connector Failing",
        "severity": "high",
        "service": "quote_engine",
        "trigger": "Pact pool fetch or quote normalization fails repeatedly.",
        "operatorAction": "Disable Pact routes for paper decisions until connector recovery is verified.",
        "phase0Behavior": "Keep scanner read-only and continue Tinyman-only monitoring if safe.",
    },
    {
        "code": "quote_age_above_threshold",
        "title": "Quote Age Above Threshold",
        "severity": "warning",
        "service": "quote_engine",
        "trigger": "Quote age exceeds the max freshness policy before route or risk evaluation.",
        "operatorAction": "Reject the route, refresh quotes, and preserve the stale quote rejection reason.",
        "phase0Behavior": "Risk engine blocks stale opportunities.",
    },
    {
        "code": "route_engine_crash",
        "title": "Route Engine Crash",
        "severity": "critical",
        "service": "route_engine",
        "trigger": "Route generation raises an exception or stops producing explained rejections.",
        "operatorAction": "Stop route jobs, inspect the failing pair, and require a regression test before restart.",
        "phase0Behavior": "No dry-run or paper approval is allowed until route explanations resume.",
    },
    {
        "code": "database_unavailable",
        "title": "Database Unavailable",
        "severity": "critical",
        "service": "storage",
        "trigger": "Market store cannot read or write scanner, quote, opportunity, or audit rows.",
        "operatorAction": "Stop jobs that depend on persistence and restore database health before resuming.",
        "phase0Behavior": "Block scanner promotion and paper-trading evidence collection.",
    },
    {
        "code": "redis_unavailable",
        "title": "Redis Unavailable",
        "severity": "warning",
        "service": "job_queue",
        "trigger": "Redis queue/cache is unreachable in staging or production Phase 0.",
        "operatorAction": "Pause queued control jobs and fall back to direct read-only checks only.",
        "phase0Behavior": "No live-signing impact; queued automation waits for Redis recovery.",
    },
    {
        "code": "unknown_asset_detected",
        "title": "Unknown Asset Detected",
        "severity": "high",
        "service": "risk_engine",
        "trigger": "A route, pool, or quote contains an asset outside the configured allowlist.",
        "operatorAction": "Reject route, record the asset id, and require manual allowlist review.",
        "phase0Behavior": "Risk engine blocks the opportunity.",
    },
    {
        "code": "unknown_app_id_detected",
        "title": "Unknown App ID Detected",
        "severity": "high",
        "service": "risk_engine",
        "trigger": "A route references an application id outside the reviewed venue allowlist.",
        "operatorAction": "Reject route, record the app id, and require connector review.",
        "phase0Behavior": "Risk engine blocks the opportunity before unsigned construction.",
    },
    {
        "code": "kill_switch_triggered",
        "title": "Kill Switch Triggered",
        "severity": "critical",
        "service": "operator_control",
        "trigger": "Kill switch is active or has been manually triggered.",
        "operatorAction": "Keep execution disarmed and require separate production policy review to clear.",
        "phase0Behavior": "Live arm requests stay rejected.",
    },
    {
        "code": "signer_offline",
        "title": "Signer Offline",
        "severity": "high",
        "service": "isolated_signer",
        "trigger": "Signer service heartbeat is missing when signer review mode is expected.",
        "operatorAction": "Do not retry with another wallet path; investigate the isolated signer host only.",
        "phase0Behavior": "Unsigned groups may be reviewed, but signing remains unavailable.",
    },
    {
        "code": "signer_rejection_spike",
        "title": "Signer Rejection Spike",
        "severity": "critical",
        "service": "isolated_signer",
        "trigger": "Signer policy rejects exceed the configured spike threshold.",
        "operatorAction": "Trigger kill switch, inspect route hashes, and review app/asset/fee mismatch causes.",
        "phase0Behavior": "No automation until signer rejections are explained.",
    },
    {
        "code": "hot_wallet_balance_changed",
        "title": "Hot Wallet Balance Changed",
        "severity": "high",
        "service": "reconciliation",
        "trigger": "Hot-wallet balance changes outside an expected dry-run or reconciled trade window.",
        "operatorAction": "Freeze execution review, reconcile balance deltas, and inspect wallet history.",
        "phase0Behavior": "Block live promotion and require manual reconciliation.",
    },
    {
        "code": "daily_loss_limit_near_breach",
        "title": "Daily Loss Limit Near Breach",
        "severity": "critical",
        "service": "risk_engine",
        "trigger": "Daily realized or simulated loss approaches the configured loss limit.",
        "operatorAction": "Stop execution attempts and lower route/trade limits before review resumes.",
        "phase0Behavior": "Risk engine blocks additional execution candidates.",
    },
    {
        "code": "live_trade_failed",
        "title": "Live Trade Failed",
        "severity": "critical",
        "service": "executor",
        "trigger": "A submitted tiny own-funds trade fails or times out after manual approval.",
        "operatorAction": "Disarm automation, inspect tx group result in Lora, and reconcile wallet deltas.",
        "phase0Behavior": "No further live trades until failure is explained.",
    },
    {
        "code": "reconciliation_mismatch",
        "title": "Reconciliation Mismatch",
        "severity": "critical",
        "service": "reconciliation",
        "trigger": "Expected deltas do not match simulated or actual post-trade balances.",
        "operatorAction": "Freeze live progression, preserve receipts, and fix accounting before restart.",
        "phase0Behavior": "Block Phase 0 automation and public receipt promotion.",
    },
]


def _policy_control_catalog() -> list[dict]:
    daily_spend_limit = settings.max_live_trade_size * settings.max_daily_trades
    allowed_asset_ids = settings.allowed_asset_ids or tuple(sorted({0, settings.target_asset_id, 31566704}))
    return [
        {
            "code": "max_input_amount",
            "label": "Max Input Amount",
            "status": "configured",
            "configuredValue": f"{settings.max_live_trade_size:.6f} ALGO",
            "enforcementLayer": "risk_engine + isolated_signer",
            "rejects": "Routes whose input amount exceeds the per-trade cap.",
        },
        {
            "code": "max_transaction_fee",
            "label": "Max Transaction Fee",
            "status": "configured",
            "configuredValue": f"{settings.max_group_fee_algos:.6f} ALGO group fee cap",
            "enforcementLayer": "unsigned_executor + isolated_signer",
            "rejects": "Unsigned groups whose estimated or actual fees exceed the cap.",
        },
        {
            "code": "asset_allowlist",
            "label": "Asset Allowlist",
            "status": "configured",
            "configuredValue": f"{len(allowed_asset_ids)} allowed asset IDs",
            "enforcementLayer": "risk_engine + isolated_signer",
            "rejects": "Routes containing an input, output, or intermediate asset outside the reviewed list.",
        },
        {
            "code": "app_id_allowlist",
            "label": "App ID Allowlist",
            "status": "required" if settings.require_app_id_allowlist else "review",
            "configuredValue": f"{len(settings.allowed_app_ids)} allowed app IDs",
            "enforcementLayer": "risk_engine + isolated_signer",
            "rejects": "Routes or transaction groups that call unreviewed applications.",
        },
        {
            "code": "transaction_type_allowlist",
            "label": "Transaction Type Allowlist",
            "status": "configured",
            "configuredValue": "pay, axfer, appl",
            "enforcementLayer": "isolated_signer",
            "rejects": "Any transaction type outside the narrow payment, asset-transfer, and app-call set.",
        },
        {
            "code": "route_hash_approval",
            "label": "Route Hash Approval",
            "status": "locked" if not settings.signer_allowed_route_hashes else "configured",
            "configuredValue": f"{len(settings.signer_allowed_route_hashes)} approved route hashes",
            "enforcementLayer": "isolated_signer",
            "rejects": "Unsigned groups whose route hash was not explicitly reviewed and allowlisted.",
        },
        {
            "code": "daily_spend_limit",
            "label": "Daily Spend Limit",
            "status": "configured",
            "configuredValue": f"{daily_spend_limit:.6f} ALGO gross input cap per day",
            "enforcementLayer": "risk_engine + operator_preflight",
            "rejects": "Additional routes once daily trade count or gross input exposure reaches policy limits.",
        },
        {
            "code": "wallet_reserve_minimum",
            "label": "Wallet Reserve Minimum",
            "status": "configured",
            "configuredValue": f"{settings.signer_min_wallet_reserve_algos:.6f} ALGO minimum reserve",
            "enforcementLayer": "isolated_signer + reconciliation",
            "rejects": "Groups that would take the hot wallet below reserve after fees and minimum balance.",
        },
        {
            "code": "kill_switch",
            "label": "Kill Switch",
            "status": "locked" if settings.signer_kill_switch else "review",
            "configuredValue": "active" if settings.signer_kill_switch else "open",
            "enforcementLayer": "admin_preflight + isolated_signer",
            "rejects": "All live arm and signing requests while the kill switch is active.",
        },
    ]


def _iso_timestamp(value: float | int | None) -> str | None:
    if not value:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(value)))


def _ops_snapshot() -> dict:
    pools = store.list_latest_pools(limit=100, required_asset_id=_required_asset_id())
    opportunities = store.list_opportunities(limit=100, public_delay_seconds=0, required_asset_id=_required_asset_id())
    paper_trades = store.list_paper_trades(limit=100)
    paper_report = store.paper_daily_report(lookback_seconds=7 * 86_400)
    live_trades = store.list_live_trades(limit=20)
    reconciliations = store.list_reconciliations(limit=20)
    readiness = build_live_readiness_report(
        settings=scanner.settings,
        store=store,
        scanner=scanner,
        run_scan=False,
        check_wallet=False,
        build_execution_plan=False,
    )
    production_readiness = build_production_readiness_report(store=store, settings=settings)
    return {
        "pools": pools,
        "opportunities": opportunities,
        "paper_trades": paper_trades,
        "paper_report": paper_report,
        "live_trades": live_trades,
        "reconciliations": reconciliations,
        "readiness": readiness,
        "production_readiness": production_readiness,
    }


def _source_for(has_data: bool, fallback: str = "unavailable") -> str:
    return "stored" if has_data else fallback


def _production_status(source: str = "stored") -> dict:
    network = (settings.network or "unknown").strip().lower()
    env = (settings.env or "").strip().lower()
    mainnet_readonly = network == "mainnet" and env in {"mainnet-readonly", "mainnet_readonly", "staging"}
    if mainnet_readonly:
        reason = (
            "MainNet Read-Only staging is active: live Tinyman/Pact market intelligence, quotes, routes, "
            "risk, and paper trading only. No keys, signing, or submission. Live execution remains locked."
        )
        safe_mode = "MainNet Read-Only: Scanner / Paper / Dry Run only."
    else:
        reason = (
            "Phase 3 TestNet readiness is the active control-room focus: read-only scanner, quotes, routes, "
            "risk, paper evidence, and soak coverage. Live execution remains locked until prior gates and "
            "human review complete."
        )
        safe_mode = "Phase 3 TestNet: Scanner / Paper / Dry Run only."
    return {
        "status": "not_live_ready",
        "headline": "NOT LIVE READY",
        "reason": reason,
        "safeMode": safe_mode,
        "restrictions": [
            "No user deposits.",
            "No guaranteed returns.",
            "No live execution unless explicitly armed by admin after gates pass.",
            f"Network context: {network}.",
            f"Profile: {env or 'unconfigured'}.",
        ],
        "source": source,
    }


def _production_readiness(snapshot: dict | None = None) -> dict:
    if snapshot and snapshot.get("production_readiness"):
        summary = dict(snapshot["production_readiness"]["summary"])
    else:
        summary = dict(build_production_readiness_report(store=store, settings=settings)["summary"])
    # Active product phase is Phase 3 TestNet or MainNet Read-Only; Phase 0 ladder is historical.
    historical_phase = summary.get("historicalPhase") or summary.get("currentPhase") or "Phase 0 evidence"
    historical_key = summary.get("historicalPhaseKey") or summary.get("currentPhaseKey") or "phase_0_history"
    env = (settings.env or "").strip().lower()
    network = (settings.network or "").strip().lower()
    if network == "mainnet" and env in {"mainnet-readonly", "mainnet_readonly", "staging"}:
        active_phase = "MainNet Read-Only Staging"
        active_key = "mainnet_readonly_staging"
        next_gate = "24h MainNet read-only paper collector evidence"
    else:
        active_phase = "Phase 3: TestNet Access"
        active_key = "phase_3_testnet_access"
        next_gate = "connect-only Pera/Defly on TestNet + sustained soak evidence"
    summary["activePhase"] = active_phase
    summary["activePhaseKey"] = active_key
    summary["currentPhase"] = active_phase
    summary["currentPhaseKey"] = active_key
    summary["historicalPhase"] = historical_phase
    summary["historicalPhaseKey"] = historical_key
    summary["nextGate"] = summary.get("nextGate") or next_gate
    if "source" not in summary or not summary["source"]:
        summary["source"] = "stored"
    # Mock evidence never inflates readiness percentage.
    if summary.get("source") == "mock":
        summary["overallPercent"] = 0
        summary["passedEvidenceCount"] = 0
        summary["blockingItems"] = list(
            dict.fromkeys([*(summary.get("blockingItems") or []), "mock_evidence_excluded_from_readiness"])
        )
    return summary


def _service_node(
    *,
    key: str,
    label: str,
    status: str,
    source: str,
    last_run_at: float | None,
    input_count: int,
    output_count: int,
    error_count: int,
    freshness_seconds: float | None,
    summary: str,
    blocker: str | None = None,
    motion_label: str | None = None,
    motion_state: str | None = None,
    approved_count: int | None = None,
    rejected_count: int | None = None,
    evidence: list[dict] | None = None,
) -> dict:
    return {
        "key": key,
        "label": label,
        "status": status,
        "source": source,
        "lastRunAt": _iso_timestamp(last_run_at),
        "lastSuccessAt": _iso_timestamp(last_run_at) if status == "ok" else None,
        "inputCount24h": input_count,
        "outputCount24h": output_count,
        "errorCount24h": error_count,
        "freshnessSeconds": freshness_seconds,
        "summary": summary,
        "blocker": blocker,
        "motionLabel": motion_label or summary,
        "motionState": motion_state or ("blocked" if blocker else status),
        "approvedCount24h": approved_count,
        "rejectedCount24h": rejected_count,
        "evidence": evidence or [],
        "endpoint": f"/api/ops/pipeline#{key}",
        "lastLogs": [
            f"{label}: {summary}",
            f"source={source}",
            f"status={status}",
        ],
        "nextAction": blocker or "Continue evidence collection.",
    }


def _ops_pipeline(snapshot: dict | None = None) -> dict:
    data = snapshot or _ops_snapshot()
    pools = data["pools"]
    opportunities = data["opportunities"]
    paper = data["paper_report"]
    live_trades = data["live_trades"]
    reconciliations = data["reconciliations"]
    readiness = data["readiness"]
    now = time.time()
    latest_pool_at = max((float(pool.get("captured_at") or 0.0) for pool in pools), default=0.0)
    latest_opp_at = max((float(item.get("created_at") or 0.0) for item in opportunities), default=0.0)
    scanner_age = readiness.get("scan", {}).get("last_scan_age_seconds")
    quote_leg_count = sum(len(item.get("route") or []) for item in opportunities)
    approved_count = sum(1 for item in opportunities if item.get("status") == "approved")
    rejected_count = sum(1 for item in opportunities if item.get("status") != "approved")
    dry_run_count = sum(1 for item in live_trades if item.get("dry_run"))
    submitted_count = sum(1 for item in live_trades if item.get("submitted"))
    paper_skip_reasons = paper.get("skipReasons") or []
    top_skip = max(paper_skip_reasons, key=lambda item: int(item.get("count") or 0), default=None)
    scanner_source = _source_for(bool(pools))
    route_source = _source_for(bool(opportunities))
    paper_source = _source_for(bool(paper["candidates"]))
    services = [
        _service_node(
            key="pool_scanner",
            label="Pool Scanner",
            status="ok" if pools else "wait",
            source=scanner_source,
            last_run_at=latest_pool_at,
            input_count=0,
            output_count=len(pools),
            error_count=0,
            freshness_seconds=scanner_age,
            summary=f"{len(pools)} latest pool snapshots available.",
            blocker=None if pools else "Run read-only scanner for current pool snapshots.",
            motion_label=f"{len(pools)} snapshots stored",
            motion_state="active" if pools else "waiting",
            evidence=[
                {
                    "label": "Pools scanned",
                    "value": str(len(pools)),
                    "detail": "Latest stored pool snapshots from the read-only scanner.",
                    "source": scanner_source,
                },
                {
                    "label": "Freshness",
                    "value": f"{int(scanner_age)}s" if scanner_age is not None else "unknown",
                    "detail": "Age of the latest scanner snapshot.",
                    "source": scanner_source,
                },
            ],
        ),
        _service_node(
            key="quote_engine",
            label="Quote Engine",
            status="ok" if opportunities else "wait",
            source=route_source,
            last_run_at=latest_opp_at,
            input_count=len(pools),
            output_count=quote_leg_count,
            error_count=0,
            freshness_seconds=max(0.0, now - latest_opp_at) if latest_opp_at else None,
            summary=f"{quote_leg_count} comparable quote legs are stored with fees and impact." if opportunities else "No stored route quotes yet.",
            blocker=None if opportunities else "Run route scan after scanner has fresh pools.",
            motion_label=f"{quote_leg_count} quote legs captured",
            motion_state="active" if opportunities else "waiting",
            evidence=[
                {
                    "label": "Quote count",
                    "value": str(quote_leg_count),
                    "detail": "Comparable quote legs captured across stored route candidates.",
                    "source": route_source,
                },
                {
                    "label": "Input pools",
                    "value": str(len(pools)),
                    "detail": "Pool snapshots available to quote against.",
                    "source": scanner_source,
                },
            ],
        ),
        _service_node(
            key="route_engine",
            label="Route Engine",
            status="ok" if opportunities else "wait",
            source=route_source,
            last_run_at=latest_opp_at,
            input_count=len(pools),
            output_count=len(opportunities),
            error_count=0,
            freshness_seconds=max(0.0, now - latest_opp_at) if latest_opp_at else None,
            summary=f"{len(opportunities)} route candidates stored.",
            blocker=None if opportunities else "Need comparable quotes before route evidence exists.",
            motion_label=f"{len(opportunities)} candidates created",
            motion_state="active" if opportunities else "waiting",
            evidence=[
                {
                    "label": "Candidate count",
                    "value": str(len(opportunities)),
                    "detail": "Stored route candidates generated from comparable quotes.",
                    "source": route_source,
                },
                {
                    "label": "Approved / rejected",
                    "value": f"{approved_count} / {rejected_count}",
                    "detail": "Route decisions before any live execution handoff.",
                    "source": route_source,
                },
            ],
        ),
        _service_node(
            key="paper_trader",
            label="Simulator / Paper Trader",
            status="ok" if paper["candidates"] else "wait",
            source=paper_source,
            last_run_at=max((float(item.get("created_at") or 0.0) for item in data["paper_trades"]), default=0.0),
            input_count=len(opportunities),
            output_count=int(paper["candidates"]),
            error_count=0,
            freshness_seconds=None,
            summary=f"{paper['candidates']} paper candidates in the 7-day window.",
            blocker=None if paper["candidates"] else "Collect paper-trading evidence before dry-run promotion.",
            motion_label=f"expected {paper['expectedNetProfit']:.6f} vs simulated {paper['simulatedProfit30s']:.6f}",
            motion_state="active" if paper["candidates"] else "waiting",
            evidence=[
                {
                    "label": "Simulated trades",
                    "value": str(int(paper["candidates"])),
                    "detail": "Paper-trade candidates with 5s/30s replay data where available.",
                    "source": paper_source,
                },
                {
                    "label": "Expected / simulated",
                    "value": f"{paper['expectedNetProfit']:.6f} / {paper['simulatedProfit30s']:.6f}",
                    "detail": "Expected net vs 30s simulated net from the paper window.",
                    "source": paper_source,
                },
            ],
        ),
        _service_node(
            key="risk_engine",
            label="Risk Engine",
            status="ok" if opportunities else "wait",
            source=route_source,
            last_run_at=latest_opp_at,
            input_count=len(opportunities),
            output_count=rejected_count,
            error_count=0,
            freshness_seconds=max(0.0, now - latest_opp_at) if latest_opp_at else None,
            summary=f"Reject-first policy reviewed {len(opportunities)} routes: {rejected_count} rejected, {approved_count} approved.",
            blocker=None if opportunities else "Need route candidates to inspect risk decisions.",
            motion_label=f"{rejected_count} rejected / {approved_count} approved",
            motion_state="active" if opportunities else "waiting",
            approved_count=approved_count,
            rejected_count=rejected_count,
            evidence=[
                {
                    "label": "Rejection reasons",
                    "value": f"{rejected_count} rejected",
                    "detail": f"Top skip reason: {top_skip['reason']} ({top_skip['count']})" if top_skip else "Waiting for runtime rejection buckets.",
                    "source": "stored" if top_skip else route_source,
                },
                {
                    "label": "Approved for review",
                    "value": str(approved_count),
                    "detail": "Approved here still means review-only; it does not arm execution.",
                    "source": route_source,
                },
            ],
        ),
        _service_node(
            key="dry_run_builder",
            label="Dry-Run Builder",
            status="blocked" if settings.unsigned_executor_only else "wait",
            source="stored" if live_trades else "unavailable",
            last_run_at=max((float(item.get("created_at") or 0.0) for item in live_trades), default=0.0),
            input_count=sum(1 for item in opportunities if item.get("status") == "approved"),
            output_count=sum(1 for item in live_trades if item.get("dry_run")),
            error_count=sum(1 for item in live_trades if not item.get("submitted") and item.get("reason")),
            freshness_seconds=None,
            summary="Unsigned-only mode remains the safe default.",
            blocker="Live signing is outside this control-room view.",
            motion_label="unsigned groups only",
            motion_state="blocked",
            evidence=[
                {
                    "label": "Unsigned receipts",
                    "value": str(dry_run_count),
                    "detail": "Dry-run rows are unsigned-only evidence, not submissions.",
                    "source": "stored" if dry_run_count else "unavailable",
                },
                {
                    "label": "Submission authority",
                    "value": "not exposed",
                    "detail": "Control Room cannot sign or submit transaction groups.",
                    "source": "unavailable",
                },
            ],
        ),
        _service_node(
            key="signer_gate",
            label="Signer Gate",
            status="disabled" if not settings.signer_enabled else "blocked",
            source="unavailable",
            last_run_at=None,
            input_count=0,
            output_count=0,
            error_count=0,
            freshness_seconds=None,
            summary="Signer is disabled/not configured in Phase 3 TestNet control-room mode.",
            blocker="Signer stays isolated and locked until gate evidence is complete.",
            motion_label="signer disabled",
            motion_state="locked",
            evidence=[
                {
                    "label": "Signer state",
                    "value": "disabled" if not settings.signer_enabled else "blocked",
                    "detail": "No signer service is configured for this Phase 3 Control Room.",
                    "source": "unavailable",
                },
                {
                    "label": "Key exposure",
                    "value": "none",
                    "detail": "No mnemonic, hot-wallet key, or signing authority is exposed here.",
                    "source": "unavailable",
                },
                {
                    "label": "Kill switch",
                    "value": "active" if settings.signer_kill_switch else "inactive",
                    "detail": "Signer boundary remains locked unless all gates and policy checks pass.",
                    "source": "stored",
                },
            ],
        ),
        _service_node(
            key="live_micro_execution",
            label="Live Micro-Execution",
            status="disabled" if not settings.enable_live_execution else "blocked",
            source="unavailable",
            last_run_at=None,
            input_count=0,
            output_count=sum(1 for item in live_trades if item.get("submitted")),
            error_count=0,
            freshness_seconds=None,
            summary="Live execution remains disarmed.",
            blocker="Live micro-execution requires manual gate approval and own funds only.",
            motion_label="locked: kill switch / disabled signer / gate evidence",
            motion_state="locked",
            evidence=[
                {
                    "label": "Live submissions",
                    "value": str(submitted_count),
                    "detail": "No automated live submission path is exposed in this view.",
                    "source": "unavailable" if not submitted_count else "stored",
                },
                {
                    "label": "Execution lock",
                    "value": "locked",
                    "detail": "Live Micro remains disarmed until scanner, paper, risk, signer, and manual gates pass.",
                    "source": "stored",
                },
            ],
        ),
        _service_node(
            key="receipts_reconciliation",
            label="Receipts / Reconciliation",
            status="ok" if reconciliations else "wait",
            source=_source_for(bool(reconciliations)),
            last_run_at=max((float(item.get("created_at") or 0.0) for item in reconciliations), default=0.0),
            input_count=len(live_trades),
            output_count=len(reconciliations),
            error_count=sum(1 for item in reconciliations if not item.get("ok")),
            freshness_seconds=None,
            summary=f"{len(reconciliations)} reconciliation receipts stored.",
            blocker=None if reconciliations else "No live/dry-run reconciliation receipts stored yet.",
            motion_label=f"{len(reconciliations)} receipts reconciled",
            motion_state="active" if reconciliations else "waiting",
            evidence=[
                {
                    "label": "Receipts",
                    "value": str(len(reconciliations)),
                    "detail": "Reconciliation rows proving expected-vs-actual outcomes.",
                    "source": _source_for(bool(reconciliations)),
                },
                {
                    "label": "Mismatches",
                    "value": str(sum(1 for item in reconciliations if not item.get("ok"))),
                    "detail": "Any mismatch keeps production promotion blocked.",
                    "source": _source_for(bool(reconciliations)),
                },
            ],
        ),
    ]
    return {
        "services": services,
        "generatedAt": _iso_timestamp(now),
        "liveExecutionLocked": not (settings.enable_live_execution and settings.execute_approved) or settings.signer_kill_switch,
        "productionStatus": _production_status("stored"),
        "productionReadiness": _production_readiness(data),
        "source": "stored" if any(node["source"] == "stored" for node in services) else "unavailable",
    }


def _ops_phase_gates(snapshot: dict | None = None) -> dict:
    data = snapshot or _ops_snapshot()
    report = data["production_readiness"]
    readiness = _production_readiness(data)
    historical_phases = [
        {
            **phase,
            "lane": "historical",
            "label": phase.get("label") or phase.get("key"),
        }
        for phase in report["phases"]
    ]
    return {
        "activePhase": {
            "key": "phase_3_testnet_access",
            "label": "Phase 3: TestNet Access",
            "status": "in_progress",
            "percent": min(99, int(readiness.get("overallPercent") or 0)),
            "requiredEvidence": [
                "TestNet config gate",
                "algod/Indexer health",
                "connect-only Pera/Defly",
                "account state read",
                "network mismatch rejection",
                "connector health",
            ],
            "completedEvidence": [],
            "blockers": list(readiness.get("blockingItems") or [])[:6],
            "source": readiness.get("source") or report["source"],
            "lane": "active",
        },
        "phases": historical_phases,
        "gates": report["gates"],
        "productionReadiness": readiness,
        "generatedAt": report["generatedAt"],
        "source": report["source"],
        "phaseNote": "Phase 3 TestNet Access is active (connect-only wallets). Phase 0A–0G remain historical gate evidence.",
    }


def _ops_activity(snapshot: dict | None = None) -> dict:
    data = snapshot or _ops_snapshot()
    now = time.time()
    pools = data["pools"]
    opportunities = data["opportunities"]
    paper = data["paper_report"]
    quote_leg_count = sum(len(item.get("route") or []) for item in opportunities)
    approved_count = sum(1 for item in opportunities if item.get("status") == "approved")
    rejected_count = sum(1 for item in opportunities if item.get("status") != "approved")
    events = [
        {
            "id": "scan-state",
            "timestamp": _iso_timestamp(now),
            "service": "Pool Scanner",
            "severity": "info" if pools else "warn",
            "message": f"{len(pools)} stored pool snapshots available." if pools else "No stored scanner snapshots available.",
            "source": _source_for(bool(pools)),
        },
        {
            "id": "quote-state",
            "timestamp": _iso_timestamp(now),
            "service": "Quote Engine",
            "severity": "info" if quote_leg_count else "warn",
            "message": f"{quote_leg_count} comparable quote legs captured." if quote_leg_count else "No comparable quote evidence yet.",
            "source": _source_for(bool(quote_leg_count)),
        },
        {
            "id": "route-state",
            "timestamp": _iso_timestamp(now),
            "service": "Route Engine",
            "severity": "info" if opportunities else "warn",
            "message": f"{len(opportunities)} stored route candidates available." if opportunities else "Route engine needs quote evidence.",
            "source": _source_for(bool(opportunities)),
        },
        {
            "id": "risk-state",
            "timestamp": _iso_timestamp(now),
            "service": "Risk Engine",
            "severity": "info" if opportunities else "warn",
            "message": f"Reject-first policy blocked {rejected_count} routes and approved {approved_count} for review." if opportunities else "Risk engine is waiting for route candidates.",
            "source": _source_for(bool(opportunities)),
        },
        {
            "id": "paper-state",
            "timestamp": _iso_timestamp(now),
            "service": "Paper Trader",
            "severity": "info" if paper["candidates"] else "warn",
            "message": (
                f"{paper['candidates']} paper candidates; expected {paper['expectedNetProfit']:.6f} vs "
                f"simulated {paper['simulatedProfit30s']:.6f}; rechecks 5s={paper.get('checked5s', 0)} "
                f"30s={paper.get('checked30s', 0)}."
            ),
            "source": _source_for(bool(paper["candidates"])),
        },
        {
            "id": "phase-state",
            "timestamp": _iso_timestamp(now),
            "service": "Phase Ladder",
            "severity": "info",
            "message": (
                "Active phase is Phase 3 TestNet Readiness; Phase 0 ladder remains historical evidence. "
                f"Paper days {min(7, int(paper.get('daysCollected') or 0))}/7."
            ),
            "source": "stored",
        },
        {
            "id": "live-lock",
            "timestamp": _iso_timestamp(now),
            "service": "Live Micro-Execution",
            "severity": "blocked",
            "message": "Live execution remains disarmed and locked.",
            "source": "stored",
        },
    ]

    # Connector degradation from stored service health (Tinyman/Pact/algod/indexer).
    try:
        connector_evidence = store.connector_reliability_evidence(
            lookback_seconds=24 * 60 * 60,
            max_quote_age_seconds=settings.max_route_age_seconds,
        )
        for item in connector_evidence.get("connectors") or []:
            name = str(item.get("connectorName") or item.get("connector") or "connector")
            status = str(item.get("status") or "unavailable")
            if status in {"ok", "mock"}:
                continue
            events.append(
                {
                    "id": f"connector-{name}",
                    "timestamp": _iso_timestamp(now),
                    "service": f"Connector:{name}",
                    "severity": "blocked" if status in {"down", "error"} else "warn",
                    "message": (
                        f"{name} is {status}"
                        + (f" ({item.get('degradationReason')})" if item.get("degradationReason") else "")
                        + "."
                    ),
                    "source": str(item.get("source") or connector_evidence.get("source") or "stored"),
                }
            )
    except Exception:
        events.append(
            {
                "id": "connector-unavailable",
                "timestamp": _iso_timestamp(now),
                "service": "Connectors",
                "severity": "warn",
                "message": "Connector reliability evidence is unavailable.",
                "source": "unavailable",
            }
        )

    # TestNet soak observation evidence when present.
    try:
        from algopulse.testnet_soak import summarize_testnet_soak_readiness

        soak = summarize_testnet_soak_readiness(store)
        completed = int(soak.get("completedObservationCount") or 0)
        gate = soak.get("gateStatus") or soak.get("currentGateStatus") or "not_started"
        severity = "info" if completed else "warn"
        if gate == "blocked":
            severity = "blocked"
        events.append(
            {
                "id": "testnet-soak",
                "timestamp": _iso_timestamp(now),
                "service": "TestNet Soak",
                "severity": severity,
                "message": (
                    f"{completed} live soak observations; coverage "
                    f"{float(soak.get('coveragePercent') or 0.0):.1f}%; gate={gate}."
                ),
                "source": str(soak.get("source") or "stored"),
            }
        )
        for blocker in list(soak.get("blockers") or [])[:2]:
            events.append(
                {
                    "id": f"soak-blocker-{blocker}",
                    "timestamp": _iso_timestamp(now),
                    "service": "TestNet Soak",
                    "severity": "warn",
                    "message": f"Soak blocker: {blocker}.",
                    "source": str(soak.get("source") or "stored"),
                }
            )
    except Exception:
        pass

    return {"events": events, "source": "stored", "count": len(events)}


def _ops_rejections(snapshot: dict | None = None) -> dict:
    data = snapshot or _ops_snapshot()
    paper = data["paper_report"]
    total = sum(item["count"] for item in paper.get("skipReasons", []))
    if total <= 0:
        buckets = [{"reason": "waiting_for_paper_data", "count": 0, "percent": 0.0}]
        return {"buckets": buckets, "source": "unavailable", "summary": "Rejected routes are expected once paper data exists."}
    buckets = [
        {"reason": item["reason"], "count": item["count"], "percent": (item["count"] / total) * 100}
        for item in paper["skipReasons"]
    ]
    return {"buckets": buckets, "source": "stored", "summary": "Rejections are useful evidence, not a failure state."}


def _ops_paper_summary(snapshot: dict | None = None) -> dict:
    data = snapshot or _ops_snapshot()
    paper = data["paper_report"]
    trades = data["paper_trades"]
    evidence = store.paper_trading_evidence_summary(limit=10, lookback_seconds=7 * 86_400)
    checked_5s_wins = sum(1 for item in trades if (item.get("simulated_profit_5s") or 0) > 0)
    checked_30s_wins = sum(1 for item in trades if (item.get("simulated_profit_30s") or 0) > 0)
    candidates = int(paper["candidates"])
    verdict = "not_ready"
    if candidates > 0:
        verdict = "watching"
    if paper["simulatedProfit30s"] > 0:
        verdict = "paper_positive"
    if candidates >= 70 and paper["completionRate30s"] >= 0.8 and paper["simulatedProfit30s"] > 0:
        verdict = "ready_for_dry_run"
    return {
        "daysCollected": min(7, int(paper.get("daysCollected") or 0)),
        "targetDays": 7,
        "candidatesObserved": candidates,
        "wouldExecuteCount": int(paper["wouldExecute"]),
        "simulatedWins5s": checked_5s_wins,
        "simulatedWins30s": checked_30s_wins,
        "expectedNetAlgo": f"{paper['expectedNetProfit']:.6f}",
        "simulatedNetAlgo5s": f"{sum(float(item.get('simulated_profit_5s') or 0.0) for item in trades):.6f}",
        "simulatedNetAlgo30s": f"{paper['simulatedProfit30s']:.6f}",
        "averageQuoteDecayAlgo": f"{paper['averageQuoteDecay30s']:.6f}",
        "evidence": evidence,
        "verdict": verdict,
        "source": _source_for(bool(candidates)),
    }


def _ops_risk_gates(snapshot: dict | None = None) -> dict:
    data = snapshot or _ops_snapshot()
    readiness = data["readiness"]
    risk = readiness.get("risk", {})
    live_locked = not (settings.enable_live_execution and settings.execute_approved) or settings.signer_kill_switch
    lock_reasons = []
    if not settings.enable_live_execution:
        lock_reasons.append("ENABLE_EXECUTION=false")
    if not settings.execute_approved:
        lock_reasons.append("execute approved flag is false")
    if settings.signer_kill_switch:
        lock_reasons.append("kill switch active")
    if not settings.signer_enabled:
        lock_reasons.append("signer disabled")
    checks = [
        ("live_execution", "Live execution disarmed", "blocked" if live_locked else "ok", "Live execution must stay locked until gates complete."),
        ("kill_switch", "Kill switch", "blocked" if settings.signer_kill_switch else "wait", "Kill switch is active by default."),
        ("signer", "Signer state", "disabled" if not settings.signer_enabled else "blocked", "Signer is isolated and outside this UI task."),
        ("profit", "Positive net after fees", "ok" if risk.get("requires_positive_net_after_fees", True) else "error", "Risk requires net-positive routes."),
        ("app_allowlist", "App ID allowlist", "ok" if risk.get("app_id_allowlist_required", True) else "wait", "Reviewed app IDs required for execution progression."),
        ("asset_allowlist", "Asset allowlist", "ok", "Reviewed asset universe only."),
        ("max_trade", "Max trade size", "ok", f"Max live trade size {settings.max_live_trade_size:.6f} ALGO."),
    ]
    return {
        "liveExecutionLocked": live_locked,
        "lockReasons": lock_reasons or ["manual production review required"],
        "checks": [{"key": key, "label": label, "status": status, "evidence": evidence} for key, label, status, evidence in checks],
        "productionStatus": _production_status("stored"),
        "productionReadiness": _production_readiness(data),
        "source": "stored",
    }


def _ops_environment(snapshot: dict | None = None) -> dict:
    data = snapshot or _ops_snapshot()
    pools = data["pools"]
    opportunities = data["opportunities"]
    paper = data["paper_report"]
    live_locked = not (settings.enable_live_execution and settings.execute_approved) or settings.signer_kill_switch
    return {
        "environment": settings.env,
        "network": settings.network,
        "items": [
            {"label": "Pool data", "source": _source_for(bool(pools)), "status": "ok" if pools else "wait", "detail": f"{len(pools)} pool snapshots"},
            {"label": "Route data", "source": _source_for(bool(opportunities)), "status": "ok" if opportunities else "wait", "detail": f"{len(opportunities)} route candidates"},
            {"label": "Paper data", "source": _source_for(bool(paper["candidates"])), "status": "ok" if paper["candidates"] else "wait", "detail": f"{paper['candidates']} paper rows"},
            {"label": "Public dashboard", "source": "delayed", "status": "ok", "detail": f"{settings.public_delay_seconds}s delay"},
            {"label": "Signer", "source": "unavailable", "status": "disabled" if not settings.signer_enabled else "blocked", "detail": "isolated signer not used by this UI"},
            {
                "label": "Live execution",
                "source": "unavailable",
                "status": "blocked" if live_locked else "wait",
                "detail": "disarmed in Phase 3 TestNet control room",
            },
            {
                "label": "Active phase",
                "source": "stored",
                "status": "wait",
                "detail": "Phase 3: TestNet Readiness (Phase 0 ladder is historical)",
            },
        ],
    }


def _required_asset_id() -> int | None:
    return settings.target_asset_id if settings.use_vestige_discovery else None


class PaymentVerificationBody(BaseModel):
    txid: str = Field(min_length=1)
    expected_receiver: str = Field(min_length=1)
    expected_amount: float = Field(gt=0)
    asset_id: int = Field(default=0, ge=0)
    asset_decimals: int = Field(default=6, ge=0)
    amount_unit: Literal["display", "raw"] = "display"
    expected_sender: str | None = None
    note_text: str | None = None
    note_prefix: str | None = None
    min_confirmations: int = Field(default=1, ge=1)
    reject_rekey: bool = True
    reject_close_to: bool = True


class RefundCaseBody(BaseModel):
    payment_verification_id: int | None = Field(default=None, ge=1)
    failure_type: Literal["service_failure", "payment_mismatch", "route_failure", "operator_cancelled", "other"] = "service_failure"
    reason: str = Field(min_length=1)
    operator_note: str | None = None


class RefundCaseStatusBody(BaseModel):
    status: Literal["needs_review", "refund_ready", "not_refundable", "resolved", "failed", "cancelled"]
    resolution_txid: str | None = None
    resolution_note: str | None = None


class PnetFeeQuoteBody(BaseModel):
    wallet: str = Field(min_length=1)
    action: Literal["public_scan", "pair_scan", "route_unlock", "run_simulation", "pool_monitor_request"]
    pair: str | None = None
    network: str | None = None


class PnetFeeConfirmBody(BaseModel):
    wallet: str = Field(min_length=1)
    fee_quote_id: str = Field(min_length=1)
    txid: str | None = None
    action: Literal["public_scan", "pair_scan", "route_unlock", "run_simulation", "pool_monitor_request"]
    pair: str | None = None


class PnetAccessCheckBody(BaseModel):
    wallet: str = Field(min_length=1)
    network: str | None = None
    action: Literal["public_scan", "pair_scan", "route_unlock", "run_simulation", "pool_monitor_request"] | None = None


class ContributionSubmitBody(BaseModel):
    wallet: str = Field(min_length=1)
    contribution_type: Literal[
        "docs_fix",
        "pool_observation",
        "bug_report",
        "demo_feedback",
        "data_source_suggestion",
        "mining_evidence",
        "bandwidth_evidence",
        "verification_report",
    ]
    title: str = Field(min_length=3, max_length=120)
    summary: str = Field(min_length=10, max_length=800)
    evidence_url: str | None = Field(default=None, max_length=300)


class ReferralRecordBody(BaseModel):
    wallet: str = Field(min_length=1)
    referred_wallet: str | None = Field(default=None, max_length=80)
    channel: Literal["direct", "x", "discord", "github", "forum", "in_person", "other"] = "direct"
    note: str | None = Field(default=None, max_length=240)


class CreditSpendBody(BaseModel):
    wallet: str = Field(min_length=1)
    unlock_code: Literal[
        "premium_market_report",
        "pair_scan_credit",
        "route_simulation_credit",
        "governance_signal_comment",
        "algoflow_tool_preview",
    ]
    quantity: int = Field(default=1, ge=1, le=10)
    note: str | None = Field(default=None, max_length=300)


class ProductActionBody(BaseModel):
    action_type: str = Field(min_length=1)
    user_role: Literal["guest", "user", "admin"] = "guest"
    wallet_connected: bool = False
    source_page: str = Field(default="unknown", min_length=1)
    metadata: dict = Field(default_factory=dict)
    timestamp: float | None = None


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: dict | None = None) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


@app.exception_handler(ApiError)
def api_error_handler(_request: Request, error: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=_api_response(
            ok=False,
            data=None,
            error={
                "code": error.code,
                "message": error.message,
                "details": error.details,
            },
        ),
    )


def _request_id() -> str:
    return f"req_{uuid.uuid4().hex[:12]}"


def _api_response(*, ok: bool, data: dict | list | None, error: dict | None = None) -> dict:
    return {"ok": ok, "requestId": _request_id(), "data": data, "error": error}


def _api_ok(data: dict | list | None) -> dict:
    return _api_response(ok=True, data=data, error=None)


def _admin_wallet_allowlist() -> tuple[str, ...]:
    return settings.admin_wallet_allowlist or (LOCAL_REVIEW_ADMIN_WALLET,)


def _wallet_session(address: str) -> dict:
    normalized = address.strip()
    is_guest = not normalized or normalized.lower() == "guest"
    is_admin = normalized in _admin_wallet_allowlist()
    role = "guest" if is_guest else "admin" if is_admin else "user"
    pnet_balance = "0.000000" if is_guest else "50000.000000" if is_admin else "1234.560000"
    credits = 0 if is_guest else 99 if is_admin else 3
    return {
        "address": normalized,
        "role": role,
        "network": settings.network,
        "isAdmin": is_admin,
        "pnetBalance": pnet_balance,
        "pnetOptedIn": not is_guest,
        "credits": credits,
        "accessTier": "public" if is_guest else role,
        "lastPaidRunAt": None,
        "authMode": "local-review-mock",
        "warning": "Mock wallet session only; production admin auth requires signed wallet proof.",
    }


def _pnet_fee_by_action() -> dict[str, str]:
    return {
        "public_scan": "4.000000",
        "pair_scan": "12.000000",
        "route_unlock": "18.000000",
        "run_simulation": "24.000000",
        "pool_monitor_request": "30.000000",
    }


def _pnet_fee_amount(action: str | None) -> str:
    fees = _pnet_fee_by_action()
    return fees.get(action or "pair_scan", fees["pair_scan"])


def _pnet_access_check(wallet: str, *, network: str | None = None, action: str | None = None) -> dict:
    session = _wallet_session(wallet)
    requested_network = (network or session["network"] or "").strip().lower()
    expected_network = settings.network.lower()
    required_fee = _pnet_fee_amount(action)
    balance = float(session["pnetBalance"])
    checks = [
        {
            "label": "Algorand wallet connected",
            "ok": session["role"] != "guest",
            "detail": "A connected wallet address is required before quoting PNET fees.",
        },
        {
            "label": "Correct network",
            "ok": requested_network == expected_network,
            "detail": f"Wallet network is {requested_network or 'unknown'}; expected {settings.network}.",
        },
        {
            "label": "PNET opt-in",
            "ok": bool(session["pnetOptedIn"]),
            "detail": f"Wallet must opt in to ASA {settings.target_asset_id}.",
        },
        {
            "label": "PNET balance",
            "ok": balance >= float(required_fee),
            "detail": f"Wallet has {session['pnetBalance']} PNET; {required_fee} PNET required.",
        },
    ]
    return {
        "wallet": session["address"],
        "role": session["role"],
        "network": requested_network or session["network"],
        "expectedNetwork": settings.network,
        "pnetAsaId": settings.target_asset_id,
        "pnetOptedIn": session["pnetOptedIn"],
        "pnetBalance": session["pnetBalance"],
        "requiredFeeAmount": required_fee,
        "action": action,
        "checks": checks,
        "ok": all(check["ok"] for check in checks),
        "liveExecutionTouched": False,
    }


def _contribution_wallet_key(wallet: str) -> str:
    return (wallet or "guest").strip() or "guest"


def _base_credit_balance(wallet: str) -> int:
    session = _wallet_session(wallet)
    return int(session["credits"]) if session["role"] != "guest" else 0


def _credit_balance(wallet: str) -> int:
    key = _contribution_wallet_key(wallet)
    return max(0, _base_credit_balance(wallet) + _CREDIT_BALANCE_ADJUSTMENTS.get(key, 0))


def _contribution_activity(wallet: str) -> list[dict]:
    key = _contribution_wallet_key(wallet)
    activity = [*_CONTRIBUTION_LEDGER.get(key, []), *_CREDIT_SPEND_LEDGER.get(key, [])]
    return sorted(activity, key=lambda item: item["createdAtEpoch"], reverse=True)


def _contribution_protocol_catalog() -> dict:
    return {
        "contributionActions": [
            {"code": code, **details} for code, details in CONTRIBUTION_ACTIONS.items()
        ],
        "creditUnlocks": [
            {"code": code, **details} for code, details in CONTRIBUTION_CREDIT_UNLOCKS.items()
        ],
        "safetyBoundaries": [
            "Credits unlock tool access, delayed reports, non-binding proposal signals, or beta previews only.",
            "Credits do not represent token rewards, investment returns, revenue share, staking yield, treasury control, or execution authority.",
            "Governance signals are non-binding until a separate legal, security, and human-review gate approves any real governance system.",
            "AlgoFlow integration should consume signed receipts or API envelopes; it must not receive signer secrets or custody user funds.",
        ],
        "smartContractStatus": "reference_blueprint_only_not_deployed",
        "liveExecutionTouched": False,
    }


def _contribution_protocol_session(wallet: str) -> dict:
    session = _wallet_session(wallet)
    activity = _contribution_activity(wallet)
    pending = [
        item
        for item in _CONTRIBUTION_LEDGER.get(_contribution_wallet_key(wallet), [])
        if item["status"] == "pending_review"
    ]
    return {
        "wallet": session["address"],
        "role": session["role"],
        "network": session["network"],
        "creditBalance": _credit_balance(wallet),
        "pendingContributions": len(pending),
        "activityHistory": activity[:20],
        "catalog": _contribution_protocol_catalog(),
        "integrationBoundary": "AlgoFlow may request contribution receipts or credit-spend receipts through API integration only; no signer, wallet custody, or live trading authority is granted.",
        "authMode": "local-review-mock",
        "liveExecutionTouched": False,
    }


def _referral_code(wallet: str) -> str:
    normalized = _contribution_wallet_key(wallet).upper().replace(" ", "")
    return f"PNET-{normalized[:6] or 'GUEST'}"


def _community_activity(wallet: str) -> list[dict]:
    key = _contribution_wallet_key(wallet)
    return sorted(
        [
            *_CONTRIBUTION_LEDGER.get(key, []),
            *_CREDIT_SPEND_LEDGER.get(key, []),
            *_REFERRAL_LEDGER.get(key, []),
        ],
        key=lambda item: item["createdAtEpoch"],
        reverse=True,
    )


def _reputation_profile(wallet: str) -> dict:
    activity = _community_activity(wallet)
    contribution_count = sum(1 for item in activity if item.get("kind") == "contribution_submission")
    spend_count = sum(1 for item in activity if item.get("kind") == "credit_spend")
    referral_count = sum(1 for item in activity if item.get("kind") == "referral")
    evidence_count = sum(
        1
        for item in activity
        if item.get("contributionType") in {"mining_evidence", "bandwidth_evidence", "verification_report"}
    )
    score = contribution_count * 10 + evidence_count * 8 + referral_count * 5 + spend_count * 2 + _credit_balance(wallet)
    badges = []
    if contribution_count:
        badges.append("Contributor")
    if evidence_count:
        badges.append("Evidence Builder")
    if referral_count:
        badges.append("Community Connector")
    if spend_count:
        badges.append("Utility User")
    tier = "observer"
    if score >= 80:
        tier = "steward"
    elif score >= 40:
        tier = "builder"
    elif score >= 15:
        tier = "contributor"
    return {
        "wallet": _contribution_wallet_key(wallet),
        "reputationScore": score,
        "tier": tier,
        "badges": badges or ["Observer"],
        "contributionCount": contribution_count,
        "verifiedEvidenceCount": evidence_count,
        "referralCount": referral_count,
        "creditSpendCount": spend_count,
        "scoringModel": "local_review_non_financial",
        "notYield": True,
        "notGovernancePower": True,
    }


def _community_leaderboard(wallet: str | None = None) -> list[dict]:
    rows = [dict(item) for item in SEEDED_COMMUNITY_LEADERBOARD]
    wallets = set(_CONTRIBUTION_LEDGER) | set(_CREDIT_SPEND_LEDGER) | set(_REFERRAL_LEDGER)
    if wallet:
        wallets.add(_contribution_wallet_key(wallet))
    for key in sorted(wallets):
        profile = _reputation_profile(key)
        rows.append(
            {
                "wallet": key,
                "displayName": "Local contributor",
                "category": "verification" if profile["verifiedEvidenceCount"] else "community",
                "reputationScore": profile["reputationScore"],
                "verifiedEvidence": profile["verifiedEvidenceCount"],
                "badges": profile["badges"],
                "source": "local_review_session",
            }
        )
    rows.sort(key=lambda item: (-int(item["reputationScore"]), item["displayName"], item["wallet"]))
    return rows[:10]


def _community_growth_overview(wallet: str) -> dict:
    session = _wallet_session(wallet)
    profile = _reputation_profile(wallet)
    return {
        "wallet": session["address"],
        "role": session["role"],
        "referral": {
            "code": _referral_code(wallet),
            "status": "local_review_only",
            "rewardPolicy": "manual review; no token payout, yield, or automatic credit grant",
        },
        "leaderboard": _community_leaderboard(wallet),
        "reputation": profile,
        "onboardingSteps": COMMUNITY_ONBOARDING_STEPS,
        "activityHistory": _community_activity(wallet)[:20],
        "allowedEvidenceCategories": ["mining_evidence", "bandwidth_evidence", "verification_report"],
        "safetyBoundaries": [
            "Mining and bandwidth rows are evidence submissions, not income claims.",
            "Leaderboard ranks contribution/reputation activity, not token holdings or earnings amount.",
            "Referrals do not create automatic payouts, token rewards, or binding governance rights.",
            "No Mainnet, deployment, signer, wallet custody, or live trading behavior is triggered.",
        ],
        "liveExecutionTouched": False,
    }


def _hashed_reference(value: str | None, *, prefix: str = "ref") -> dict:
    normalized = (value or "").strip()
    if not normalized:
        return {"hash": None, "suffix": None, "available": False}
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return {
        "hash": f"{prefix}_{digest[:16]}",
        "suffix": normalized[-6:],
        "available": True,
    }


def _epoch_to_iso(value: float | int | None) -> str | None:
    if value is None:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(value)))


def _transparency_payment_row(row: dict) -> dict:
    result = row.get("result") or {}
    expected = result.get("expected") or {}
    observed = result.get("observed") or {}
    return {
        "id": f"pay_{row.get('id')}",
        "kind": "payment_verification",
        "status": row.get("status"),
        "ok": bool(row.get("ok")),
        "txReference": _hashed_reference(row.get("txid"), prefix="tx"),
        "senderReference": _hashed_reference(observed.get("sender"), prefix="payer"),
        "receiverReference": _hashed_reference(observed.get("receiver") or expected.get("receiver"), prefix="receiver"),
        "assetId": row.get("asset_id"),
        "amountRaw": row.get("observed_amount_raw") or row.get("expected_amount_raw"),
        "confirmedRound": row.get("confirmed_round"),
        "confirmations": row.get("confirmations"),
        "createdAt": _epoch_to_iso(row.get("created_at")),
        "source": "stored_payment_verification",
        "publicSafe": True,
        "secretsPrinted": False,
        "paymentPayloadLogged": False,
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
    }


def _transparency_review_row(item: dict) -> dict:
    return {
        "id": item.get("id") or f"review_{uuid.uuid4().hex[:8]}",
        "kind": item.get("kind") or "review_event",
        "status": item.get("status") or "recorded",
        "walletReference": _hashed_reference(item.get("wallet"), prefix="wallet"),
        "label": item.get("label") or item.get("title") or item.get("unlockCode") or item.get("contributionType") or "Review event",
        "category": item.get("contributionType") or item.get("unlockCode") or item.get("category") or item.get("channel") or "review",
        "createdAt": _epoch_to_iso(item.get("createdAtEpoch")),
        "source": "local_review_ledger",
        "reviewMode": item.get("reviewMode") or "manual_review",
        "creditsGranted": int(item.get("creditsGranted") or 0),
        "publicSafe": True,
        "rewardPolicy": item.get("rewardPolicy") or "manual_review_no_token_payout",
        "liveExecutionTouched": bool(item.get("liveExecutionTouched", False)),
        "signerCodeTouched": False,
    }


def _transparency_review_events(limit: int = 50) -> list[dict]:
    events: list[dict] = []
    for ledger in (_CONTRIBUTION_LEDGER, _CREDIT_SPEND_LEDGER, _REFERRAL_LEDGER):
        for rows in ledger.values():
            events.extend(_transparency_review_row(item) for item in rows)
    events.sort(key=lambda item: item.get("createdAt") or "", reverse=True)
    return events[: max(1, min(limit, 100))]


def _transparency_proof_matrix() -> list[dict]:
    payment_count = len(store.list_payment_verifications(limit=100))
    refund_count = len(store.list_refund_cases(limit=100))
    review_count = len(_transparency_review_events(limit=100))
    return [
        {
            "code": "on_chain_payment_receipts",
            "label": "On-chain payment receipts",
            "status": "active" if payment_count else "waiting",
            "evidenceCount": payment_count,
            "detail": "Stored payment verifications are converted into redacted public references.",
        },
        {
            "code": "manual_review_receipts",
            "label": "Manual review receipts",
            "status": "active" if review_count else "waiting",
            "evidenceCount": review_count,
            "detail": "Contribution, referral, and credit-spend receipts remain manual-review only.",
        },
        {
            "code": "refund_case_tracking",
            "label": "Refund/failure case tracking",
            "status": "active" if refund_count else "waiting",
            "evidenceCount": refund_count,
            "detail": "Refund/failure cases are tracked for operator review; public summaries must stay redacted.",
        },
        {
            "code": "x402_gate_3",
            "label": "x402 Gate 3 mechanics proof",
            "status": "complete",
            "evidenceCount": 1,
            "detail": "Local/TestNet paid 200 proof exists with payer==receiver caveat; no Mainnet or eligibility claim.",
        },
        {
            "code": "x402_gate_3_5",
            "label": "External TestNet payer proof",
            "status": "blocked",
            "evidenceCount": 0,
            "detail": "Requires independent payer != receiver evidence before external-user or Mainnet readiness claims.",
        },
        {
            "code": "x402_settlement_failure_harness",
            "label": "Settlement-failure harness",
            "status": "documented_limitation",
            "evidenceCount": 0,
            "detail": "No officially documented secrets-safe TestNet failure harness for x402-avm/GoPlausible is available.",
        },
    ]


def _transparency_public_ledger(limit: int = 50) -> dict:
    payments = [_transparency_payment_row(row) for row in store.list_payment_verifications(limit=limit)]
    reviews = _transparency_review_events(limit=limit)
    entries = [*payments, *reviews]
    entries.sort(key=lambda item: item.get("createdAt") or "", reverse=True)
    return {
        "entries": entries[: max(1, min(limit, 100))],
        "summary": {
            "paymentVerificationCount": len(payments),
            "reviewEventCount": len(reviews),
            "publicSafe": True,
            "rawTxidsExposed": False,
            "rawWalletsExposed": False,
            "paymentPayloadsExposed": False,
            "secretsExposed": False,
        },
        "redactionPolicy": {
            "txids": "sha256 prefix plus suffix only",
            "wallets": "sha256 prefix plus suffix only",
            "paymentPayloads": "omitted",
            "headers": "omitted",
            "privateNotes": "omitted",
        },
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
    }


def _transparency_audit_readiness() -> dict:
    return {
        "checklist": TRANSPARENCY_AUDIT_CHECKLIST,
        "threatModel": TRANSPARENCY_THREAT_MODEL,
        "blockedClaims": [
            "audited",
            "production-ready",
            "Mainnet-approved",
            "challenge-eligible",
            "guaranteed returns",
            "yield",
            "staking rewards",
            "token price appreciation",
        ],
        "requiredBeforePublication": [
            "human wording review",
            "secret-scan result",
            "proof redaction review",
            "public dashboard screenshot redaction review",
            "Gate 3.5 payer != receiver evidence before external-user claims",
            "Gate 4A before any Mainnet readiness wording",
        ],
        "publicSafe": True,
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
    }


def _transparency_github_snapshot() -> dict:
    ledger = _transparency_public_ledger(limit=25)
    proofs = _transparency_proof_matrix()
    audit = _transparency_audit_readiness()
    return {
        "title": "AlgoPulse Transparency Snapshot",
        "generatedAt": _epoch_to_iso(time.time()),
        "scope": "public-safe GitHub dossier snapshot",
        "proofSummary": {
            "checks": len(proofs),
            "activeOrComplete": sum(1 for item in proofs if item["status"] in {"active", "complete"}),
            "blockedOrLimited": sum(1 for item in proofs if item["status"] in {"blocked", "documented_limitation"}),
        },
        "ledgerSummary": ledger["summary"],
        "auditSummary": {
            "checklistItems": len(audit["checklist"]),
            "threatsTracked": len(audit["threatModel"]),
            "blockedClaims": audit["blockedClaims"],
        },
        "recommendedSnapshotCadence": "Before external demos, after proof evidence changes, and before public claims.",
        "validationCommands": [
            "git diff --check",
            "python scripts/repo_guard.py",
            "node --check src/algopulse/static/app.js",
            "python -m pytest -q",
            "changed-diff secret scan",
        ],
        "docs": [
            "docs/TRANSPARENCY_SYSTEM.md",
            "docs/PNET_DOCUMENTATION_AND_AUDIT_READINESS.md",
            "docs/PUBLIC_RECORD_REDACTION_CONTRACT.md",
            "docs/X402_GATE_LOG.md",
        ],
        "publicSafe": True,
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
    }


def _transparency_system() -> dict:
    return {
        "proofMatrix": _transparency_proof_matrix(),
        "publicLedger": _transparency_public_ledger(limit=25),
        "githubSnapshot": _transparency_github_snapshot(),
        "auditReadiness": _transparency_audit_readiness(),
        "safetyBoundaries": [
            "Public transparency exposes redacted proof references only.",
            "No secrets, mnemonics, private keys, payment headers, full payment payloads, or .env contents are returned.",
            "No Mainnet, deploy, signing, transaction submission, live trading, or fresh executable route approval is implied.",
            "PNET and x402 evidence is operational transparency, not financial advice or a production-readiness claim.",
        ],
        "publicSafe": True,
        "liveExecutionTouched": False,
        "signerCodeTouched": False,
    }


def _require_admin_session(
    x_algopulse_role: str | None = Header(default=None, alias="X-Algopulse-Role"),
    x_algopulse_wallet: str | None = Header(default=None, alias="X-Algopulse-Wallet"),
) -> dict:
    wallet = (x_algopulse_wallet or "").strip()
    role = (x_algopulse_role or "").strip().lower()
    session = _wallet_session(wallet)
    if role != "admin" or not session["isAdmin"]:
        raise ApiError(
            403,
            "NOT_AUTHORIZED",
            "Admin wallet session required.",
            {
                "requiredRole": "admin",
                "authMode": "local-review-mock",
                "walletAllowlisted": session["isAdmin"],
            },
        )
    return session


def _job_response(action: str, session: dict, message: str) -> dict:
    return _api_ok(
        {
            "jobId": f"job_{uuid.uuid4().hex[:10]}",
            "action": action,
            "status": "queued",
            "message": message,
            "wallet": session["address"],
            "liveExecutionTouched": False,
        }
    )


def _preflight_checklist(report: dict, session: dict) -> list[dict]:
    scan_age = report.get("scan", {}).get("last_scan_age_seconds")
    observed_venues = set(report.get("connectors", {}).get("observed_venues") or [])
    pool_count = int(report.get("scan", {}).get("pools_monitored") or 0)
    has_fresh_pool_data = scan_age is not None and scan_age <= max(settings.max_route_age_seconds * 12, 60)
    signer_locked = not settings.signer_enabled and settings.signer_kill_switch
    return [
        {
            "label": "Admin wallet connected",
            "status": "ok" if session["role"] == "admin" else "blocked",
            "detail": "Wallet session resolved through the backend role gate.",
        },
        {
            "label": "Admin wallet verified",
            "status": "ok" if session["isAdmin"] else "blocked",
            "detail": "Address is present in the configured admin allowlist.",
        },
        {
            "label": "Correct network",
            "status": "ok" if settings.network == "mainnet" else "wait",
            "detail": f"Configured network is {settings.network}.",
        },
        {
            "label": "Scanner online",
            "status": "ok",
            "detail": "Read-only scanner service is reachable from the API process.",
        },
        {
            "label": "Pool data fresh",
            "status": "ok" if has_fresh_pool_data else "wait",
            "detail": "Latest scan age is unavailable." if scan_age is None else f"Latest scan is {round(scan_age, 1)} seconds old.",
        },
        {
            "label": "Pool coverage",
            "status": "ok" if pool_count else "wait",
            "detail": f"{pool_count} pools are present in the local market store.",
        },
        {
            "label": "Tinyman connector",
            "status": "ok" if "tinyman" in observed_venues or settings.connector_mode == "mock" else "wait",
            "detail": "Executable venue connector is observed or mocked for local review.",
        },
        {
            "label": "Pact connector",
            "status": "ok" if "pact" in observed_venues or settings.connector_mode == "mock" else "wait",
            "detail": "Executable venue connector is observed or mocked for local review.",
        },
        {
            "label": "Route engine",
            "status": "ok",
            "detail": "Two-leg and triangle route search are available for scanner and paper review.",
        },
        {
            "label": "Risk engine",
            "status": "ok" if report.get("risk", {}).get("requires_positive_net_after_fees", True) else "blocked",
            "detail": "Profit, fee buffer, quote freshness, app ID, asset, and route-length gates are active.",
        },
        {
            "label": "Public data delay",
            "status": "ok" if settings.public_delay_seconds > 0 else "wait",
            "detail": f"Public route delay is {settings.public_delay_seconds} seconds.",
        },
        {
            "label": "PNET fee receiver",
            "status": "ok" if settings.pnet_fee_receiver_address else "wait",
            "detail": "Market-data fee receiver is configured for review-mode quotes.",
        },
        {
            "label": "Signer locked",
            "status": "ok" if signer_locked else "blocked",
            "detail": "Signer is disabled and kill switch is active by default.",
        },
        {
            "label": "Live execution disabled",
            "status": "ok" if not settings.enable_live_execution else "blocked",
            "detail": "Control-plane review must not enable live execution.",
        },
        {
            "label": "Hot wallet skipped",
            "status": "wait",
            "detail": "Wallet reserve lookup is intentionally skipped in this safe mock control plane.",
        },
    ]


@app.get("/")
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def health() -> dict:
    return {"ok": True, "mode": settings.connector_mode, "execution_enabled": settings.enable_live_execution}


@app.get("/api/health")
def api_health() -> dict:
    return _api_ok(
        {
            "service": "algopulse-api",
            "status": "ok",
            "version": app.version,
            "network": settings.network,
            "executionEnabled": settings.enable_live_execution,
            "signerEnabled": settings.signer_enabled,
        }
    )


@app.get("/api/config/public")
def public_config() -> dict:
    wallet_access = build_public_wallet_access_config(settings)
    return _api_ok(
        {
            "appName": settings.app_name,
            "developmentPhase": wallet_access["developmentPhase"],
            "developmentPhaseStatus": wallet_access["developmentPhaseStatus"],
            "environment": settings.env,
            "network": settings.network,
            "backendNetworkAuthority": True,
            "chainId": wallet_access.get("chainId"),
            "walletAccessMode": wallet_access["walletAccessMode"],
            "walletConnectOnly": True,
            "supportedWallets": wallet_access["supportedWallets"],
            "supportedNetworks": wallet_access["supportedNetworks"],
            "pnetAsaId": wallet_access["pnetAsaId"],
            "pnetAsaConfigured": wallet_access["pnetAsaConfigured"],
            "pnetMessage": wallet_access.get("pnetMessage"),
            "pnetFeeReceiverAddress": settings.pnet_fee_receiver_address,
            "pnetFeeAppId": settings.pnet_fee_app_id,
            "publicRouteDelaySeconds": settings.public_delay_seconds,
            "supportedVenues": ["tinyman", "pact"],
            "supportedPaidActions": [
                "public_scan",
                "pair_scan",
                "route_unlock",
                "run_simulation",
                "pool_monitor_request",
            ],
            "adminAuthMode": "local-review-mock",
            "adminWalletsConfigured": len(_admin_wallet_allowlist()),
            "liveExecutionEnabled": settings.enable_live_execution,
            "signerEnabled": settings.signer_enabled,
            "signingEnabled": False,
            "submissionEnabled": False,
            "productionReady": False,
            "capabilities": wallet_access["capabilities"],
            "boundaries": wallet_access["boundaries"],
            "productCapabilities": PRODUCT_CAPABILITIES,
            "phaseGates": PHASE_GATES,
            "deploymentModes": DEPLOYMENT_MODES,
        }
    )


@app.get("/api/testnet/readiness")
def testnet_readiness() -> dict:
    # Live probes for Control Room; never expose URLs/tokens in the payload.
    try:
        health = build_network_health(settings)
    except Exception as exc:
        health = {
            "overall": "down",
            "ok": False,
            "mismatches": [],
            "algod": {"healthy": False, "detail": f"probe_error:{type(exc).__name__}", "connector": "algod"},
            "indexer": {
                "healthy": False,
                "detail": f"probe_error:{type(exc).__name__}",
                "connector": "indexer",
            },
        }
    return _api_ok(build_testnet_readiness(settings, network_health=health))


@app.get("/api/network/health")
def network_health() -> dict:
    return _api_ok(build_network_health(settings))


@app.get("/api/wallet/account/{address}")
def wallet_account_state(
    address: str,
    network: str | None = None,
    chain_id: int | None = None,
    provider: str | None = None,
) -> dict:
    """Connect-only account read. Rejects MainNet wallet/network mismatches."""
    try:
        assert_testnet_access_profile_safe(settings)
    except Exception as exc:
        raise ApiError(
            status_code=503,
            code="TESTNET_ACCESS_PROFILE_BLOCKED",
            message="Wallet account reads require the disarmed TestNet Access profile.",
            details={"reason": str(exc)},
        ) from exc
    if not is_valid_algo_address(address):
        raise ApiError(
            status_code=422,
            code="INVALID_WALLET_ADDRESS",
            message="Wallet address is not a valid Algorand public address.",
            details={"address": address},
        )
    match = validate_wallet_network(
        settings,
        claimed_network=network or settings.network,
        claimed_chain_id=chain_id,
    )
    if match["rejected"]:
        raise ApiError(
            status_code=409,
            code="WALLET_NETWORK_MISMATCH",
            message=match["message"] or "Wallet network does not match backend network.",
            details=match,
        )
    try:
        account = read_account_state(settings, address)
    except TestnetAccessError as exc:
        raise ApiError(
            status_code=422,
            code="WALLET_ACCOUNT_READ_FAILED",
            message=str(exc),
            details={"address": address},
        ) from exc
    except Exception as exc:
        raise ApiError(
            status_code=502,
            code="WALLET_ACCOUNT_UPSTREAM_ERROR",
            message="Could not read account state from the configured Algorand node.",
            details={"errorType": type(exc).__name__},
        ) from exc
    provider_key = (provider or "").strip().lower() or None
    if provider_key and provider_key not in {"pera", "defly"}:
        raise ApiError(
            status_code=422,
            code="UNSUPPORTED_WALLET_PROVIDER",
            message="Only Pera and Defly are supported in the TestNet Access Phase.",
            details={"provider": provider_key, "supportedWallets": ["pera", "defly"]},
        )
    return _api_ok(
        {
            **account,
            "provider": provider_key,
            "networkMatch": match,
            "walletAccessMode": "connect_only",
            "capabilities": {
                "connectWallet": True,
                "readAccountState": True,
                "signTransactions": False,
                "submitTransactions": False,
                "assetOptIn": False,
                "liveTrading": False,
            },
        }
    )


@app.get("/api/session/wallet/{address}")
def wallet_session(address: str) -> dict:
    return _api_ok(_wallet_session(address))


@app.post("/api/user/pnet/access-check")
def pnet_access_check(body: PnetAccessCheckBody) -> dict:
    return _api_ok(_pnet_access_check(body.wallet, network=body.network, action=body.action))


@app.post("/api/events/user-action")
def record_product_user_action(body: ProductActionBody) -> dict:
    if body.action_type not in ACTION_TAXONOMY:
        raise ApiError(
            status_code=422,
            code="UNKNOWN_PRODUCT_ACTION",
            message="Product validation action_type is not in the approved taxonomy.",
            details={"knownActions": sorted(ACTION_TAXONOMY)},
        )
    receipt = store.record_user_action(
        action_type=body.action_type,
        user_role=body.user_role,
        wallet_connected=body.wallet_connected,
        source_page=body.source_page,
        metadata=body.metadata,
        timestamp=body.timestamp,
    )
    return _api_ok(receipt)


@app.get("/api/pulse")
def pulse() -> dict:
    return store.get_pulse(settings.public_delay_seconds, required_asset_id=_required_asset_id())


@app.get("/api/pools")
def pools(limit: int = 50) -> list[dict]:
    return store.list_latest_pools(limit=limit, required_asset_id=_required_asset_id())


@app.get("/api/opportunities")
def opportunities(limit: int = 50) -> list[dict]:
    return store.list_opportunities(
        limit=limit,
        public_delay_seconds=settings.public_delay_seconds,
        required_asset_id=_required_asset_id(),
    )


@app.get("/api/market/pnet/recent-swaps")
def pnet_recent_swaps(limit: int = 5) -> dict:
    safe_limit = max(1, min(25, int(limit)))
    try:
        data = fetch_recent_pnet_swaps(
            vestige_api_url=settings.vestige_api_url,
            asset_id=settings.target_asset_id,
            limit=safe_limit,
        )
    except Exception:
        data = {
            "assetId": settings.target_asset_id,
            "source": "unavailable",
            "sourceLabel": "Vestige swaps API",
            "dataPolicy": "public_read_only_historical_swaps",
            "publicSafe": True,
            "freshExecutableRoutes": False,
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
            "count": 0,
            "swaps": [],
            "error": "vestige_recent_swaps_unavailable",
        }
    return _api_ok(data)


@app.get("/api/paper-trades")
def paper_trades(limit: int = 50) -> list[dict]:
    return store.list_paper_trades(limit=limit)


@app.get("/api/live-trades")
def live_trades(limit: int = 50) -> list[dict]:
    return store.list_live_trades(limit=limit)


@app.get("/api/reconciliations")
def reconciliations(limit: int = 50) -> list[dict]:
    return store.list_reconciliations(limit=limit)


@app.get("/api/payment-verifications")
def payment_verifications(limit: int = 50) -> list[dict]:
    return store.list_payment_verifications(limit=limit)


@app.get("/api/refund-cases")
def refund_cases(limit: int = 50) -> list[dict]:
    return store.list_refund_cases(limit=limit)


@app.post("/api/verify-payment")
def verify_payment(body: PaymentVerificationBody) -> dict:
    payload = body.model_dump() if hasattr(body, "model_dump") else body.dict()
    result = payment_verifier.verify(PaymentVerificationRequest(**payload)).to_dict()
    store.record_payment_verification(result)
    return result


@app.post("/api/refund-cases")
def create_refund_case(body: RefundCaseBody) -> dict:
    payload = body.model_dump() if hasattr(body, "model_dump") else body.dict()
    receipt = None
    verification_id = payload.get("payment_verification_id")
    if verification_id:
        receipt = store.get_payment_verification(verification_id)
        if not receipt:
            raise HTTPException(status_code=404, detail="payment verification not found")

    decision = build_refund_case(
        RefundCaseInput(
            failure_type=payload["failure_type"],
            reason=payload["reason"].strip(),
            payment_verification=receipt,
            operator_note=payload.get("operator_note"),
        )
    )
    return store.record_refund_case(decision.to_dict())


@app.post("/api/refund-cases/{case_id}/status")
def update_refund_case(case_id: int, body: RefundCaseStatusBody) -> dict:
    payload = body.model_dump() if hasattr(body, "model_dump") else body.dict()
    updated = store.update_refund_case_status(
        case_id,
        status=payload["status"],
        resolution_txid=payload.get("resolution_txid"),
        resolution_note=payload.get("resolution_note"),
    )
    if not updated:
        raise HTTPException(status_code=404, detail="refund case not found")
    return updated


@app.get("/api/risk-policy")
def risk_policy() -> dict:
    return scanner.risk_engine.policy.to_public_dict()


@app.get("/api/demo-run")
def demo_run() -> dict:
    return run_five_to_ten_demo()


@app.get("/api/live-readiness")
def live_readiness(run_scan: bool = False, build_execution_plan: bool = True) -> dict:
    return build_live_readiness_report(
        settings=scanner.settings,
        store=store,
        scanner=scanner,
        run_scan=run_scan,
        build_execution_plan=build_execution_plan,
    )


@app.get("/api/admin/preflight")
def admin_preflight(session: dict = Depends(_require_admin_session)) -> dict:
    report = build_live_readiness_report(
        settings=scanner.settings,
        store=store,
        scanner=scanner,
        run_scan=False,
        check_wallet=False,
        build_execution_plan=False,
    )
    checklist = _preflight_checklist(report, session)
    return _api_ok(
        {
            "mode": "scanner" if not settings.tiny_live_mode else "live_micro",
            "liveArmed": bool(settings.enable_live_execution and settings.execute_approved),
            "killSwitch": bool(settings.signer_kill_switch),
            "signerStatus": "online" if settings.signer_enabled else "locked",
            "riskGate": "passing" if report.get("best_approved_route") else "blocked",
            "hotWalletReserve": "lookup_skipped",
            "dailyPnL": "0.000000",
            "dailyLossRemaining": f"{settings.max_daily_loss:.6f}",
            "lastConfirmedTradeAt": None,
            "lastScanAgeSeconds": report.get("scan", {}).get("last_scan_age_seconds"),
            "quoteFreshnessSeconds": settings.max_route_age_seconds,
            "checklist": checklist,
            "checks": report.get("checks", []),
            "adminSession": {"wallet": session["address"], "authMode": session["authMode"]},
        }
    )


@app.get("/api/admin/alerts/catalog")
def admin_alert_catalog(session: dict = Depends(_require_admin_session)) -> dict:
    return _api_ok(
        {
            "alerts": ALERT_CATALOG,
            "count": len(ALERT_CATALOG),
            "adminSession": {"wallet": session["address"], "authMode": session["authMode"]},
            "liveExecutionTouched": False,
        }
    )


@app.get("/api/admin/policy/catalog")
def admin_policy_catalog(session: dict = Depends(_require_admin_session)) -> dict:
    controls = _policy_control_catalog()
    return _api_ok(
        {
            "controls": controls,
            "count": len(controls),
            "adminSession": {"wallet": session["address"], "authMode": session["authMode"]},
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
        }
    )


@app.get("/api/ops/pipeline")
def ops_pipeline(session: dict = Depends(_require_admin_session)) -> dict:
    return _api_ok({**_ops_pipeline(), "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/phase-gates")
def ops_phase_gates(session: dict = Depends(_require_admin_session)) -> dict:
    return _api_ok({**_ops_phase_gates(), "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/production-readiness")
def ops_production_readiness(session: dict = Depends(_require_admin_session)) -> dict:
    report = build_production_readiness_report(store=store, settings=settings)
    return _api_ok({**report, "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/readiness-report")
def ops_readiness_report(session: dict = Depends(_require_admin_session)) -> dict:
    report = store.read_only_staging_report(max_quote_age_seconds=settings.max_route_age_seconds)
    return _api_ok({**report, "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/activity")
def ops_activity(session: dict = Depends(_require_admin_session)) -> dict:
    return _api_ok({**_ops_activity(), "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/rejections")
def ops_rejections(session: dict = Depends(_require_admin_session)) -> dict:
    return _api_ok({**_ops_rejections(), "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/paper-summary")
def ops_paper_summary(session: dict = Depends(_require_admin_session)) -> dict:
    return _api_ok(
        {**_ops_paper_summary(), "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}}
    )


@app.get("/api/ops/pipeline-evidence")
def ops_pipeline_evidence(session: dict = Depends(_require_admin_session)) -> dict:
    evidence = store.scanner_to_paper_pipeline_evidence(
        limit=10,
        lookback_seconds=7 * 86_400,
        max_quote_age_seconds=settings.max_route_age_seconds,
    )
    return _api_ok({**evidence, "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/quote-freshness")
def ops_quote_freshness(session: dict = Depends(_require_admin_session)) -> dict:
    evidence = store.quote_freshness_evidence(max_age_seconds=settings.max_route_age_seconds, limit=50)
    return _api_ok({**evidence, "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/connectors")
def ops_connectors(session: dict = Depends(_require_admin_session)) -> dict:
    evidence = store.connector_reliability_evidence(
        lookback_seconds=24 * 60 * 60,
        max_quote_age_seconds=settings.max_route_age_seconds,
    )
    return _api_ok({**evidence, "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/testnet-soak")
def ops_testnet_soak(session: dict = Depends(_require_admin_session)) -> dict:
    """Admin-only rollup of stored TestNet soak observations. No remote start/stop."""
    rollup = build_testnet_soak_summary(store, settings)
    return _api_ok(
        {
            **rollup,
            "blockers": list(rollup.get("blockers") or []),
            "warnings": list(rollup.get("warnings") or []),
            "gateStatus": rollup.get("gateStatus") or rollup.get("currentGateStatus") or "not_started",
            "productionReady": False,
            "liveExecutionLocked": True,
            "adminSession": {"wallet": session["address"], "authMode": session["authMode"]},
        }
    )


@app.get("/api/ops/testnet-soak/observations")
def ops_testnet_soak_observations(
    limit: int = 50,
    session: dict = Depends(_require_admin_session),
) -> dict:
    """Admin-only recent soak observations, newest first. Cap at 50 rows."""
    safe_limit = max(1, min(50, int(limit)))
    rows = store.list_testnet_soak_observations(limit=safe_limit, newest_first=True)
    observations = [public_safe_observation(item) for item in rows]
    return _api_ok(
        {
            "observations": observations,
            "count": len(observations),
            "limit": safe_limit,
            "requestedLimit": int(limit),
            "source": "stored" if observations else "unavailable",
            "productionReady": False,
            "liveExecutionLocked": True,
            "adminSession": {"wallet": session["address"], "authMode": session["authMode"]},
        }
    )


@app.get("/api/ops/risk-gates")
def ops_risk_gates(session: dict = Depends(_require_admin_session)) -> dict:
    return _api_ok({**_ops_risk_gates(), "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/environment")
def ops_environment(session: dict = Depends(_require_admin_session)) -> dict:
    return _api_ok({**_ops_environment(), "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/replay-lab")
def ops_replay_lab(limit: int = 30, session: dict = Depends(_require_admin_session)) -> dict:
    safe_limit = max(1, min(100, int(limit)))
    replays = store.list_opportunity_replays(limit=safe_limit)
    verdict_counts: dict[str, int] = {}
    for replay in replays:
        verdict = str(replay.get("verdict") or "unknown")
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
    return _api_ok(
        {
            "replays": replays,
            "count": len(replays),
            "compareDefaults": [item["id"] for item in replays[:3]],
            "verdictCounts": verdict_counts,
            "source": "stored" if replays else "unavailable",
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
            "adminSession": {"wallet": session["address"], "authMode": session["authMode"]},
        }
    )


@app.get("/api/ops/route-forensics")
def ops_route_forensics(limit: int = 50, session: dict = Depends(_require_admin_session)) -> dict:
    safe_limit = max(1, min(100, int(limit)))
    routes = store.list_route_decision_forensics(limit=safe_limit)
    summary = store.route_forensics_summary()
    decision_counts = {decision: 0 for decision in ("approved", "rejected", "wait", "paper_only")}
    for route in routes:
        decision = str(route.get("finalDecision") or "rejected")
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
    decision_counts["complete"] = int(summary["completeCount"])
    decision_counts["total"] = int(summary["routeCount"])
    return _api_ok(
        {
            "routes": routes,
            "count": len(routes),
            "summary": summary,
            "decisionCounts": decision_counts,
            "compareDefaults": [item["id"] for item in routes[:3]],
            "source": "stored" if routes else "unavailable",
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
            "adminSession": {"wallet": session["address"], "authMode": session["authMode"]},
        }
    )


@app.get("/api/ops/market-heatmap")
def ops_market_heatmap(view: str = "24h", session: dict = Depends(_require_admin_session)) -> dict:
    heatmap = store.market_pulse_heatmap(view=view)
    return _api_ok({**heatmap, "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/failure-lab")
def ops_failure_lab(session: dict = Depends(_require_admin_session)) -> dict:
    report = build_failure_lab_report()
    return _api_ok({**report, "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/provenance")
def ops_data_provenance(
    metric: str = "route.expected_net_profit",
    route_hash: str | None = None,
    session: dict = Depends(_require_admin_session),
) -> dict:
    report = store.data_provenance_report(metric_key=metric, route_hash=route_hash)
    return _api_ok({**report, "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/evidence")
def ops_evidence_records(
    category: str | None = None,
    service: str | None = None,
    status: str | None = None,
    session: dict = Depends(_require_admin_session),
) -> dict:
    report = store.evidence_records_report(
        settings=settings,
        category=category,
        service=service,
        status=status,
    )
    return _api_ok({**report, "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/confidence-calibration")
def ops_confidence_calibration(session: dict = Depends(_require_admin_session)) -> dict:
    report = store.confidence_calibration_report()
    return _api_ok({**report, "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/opportunity-decay")
def ops_opportunity_decay(view: str = "24h", session: dict = Depends(_require_admin_session)) -> dict:
    report = store.opportunity_decay_dashboard(view=view)
    return _api_ok({**report, "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.get("/api/ops/product-validation")
def ops_product_validation(window_days: int = 30, session: dict = Depends(_require_admin_session)) -> dict:
    report = store.product_validation_report(window_days=max(1, min(window_days, 90)))
    return _api_ok({**report, "adminSession": {"wallet": session["address"], "authMode": session["authMode"]}})


@app.post("/api/admin/scan-now")
def admin_scan_now(session: dict = Depends(_require_admin_session)) -> dict:
    return _job_response("scan_now", session, "Scan job queued for the read-only scanner.")


@app.post("/api/admin/scanner/start")
def admin_scanner_start(session: dict = Depends(_require_admin_session)) -> dict:
    return _job_response("scanner_start", session, "Scanner start request queued.")


@app.post("/api/admin/scanner/pause")
def admin_scanner_pause(session: dict = Depends(_require_admin_session)) -> dict:
    return _job_response("scanner_pause", session, "Scanner pause request queued.")


@app.post("/api/admin/routes/run")
def admin_routes_run(session: dict = Depends(_require_admin_session)) -> dict:
    return _job_response("routes_run", session, "Route engine job queued.")


@app.post("/api/admin/paper/start")
def admin_paper_start(session: dict = Depends(_require_admin_session)) -> dict:
    return _job_response("paper_start", session, "Paper-trading job queued.")


@app.post("/api/admin/dry-run/build")
def admin_dry_run_build(session: dict = Depends(_require_admin_session)) -> dict:
    return _job_response("dry_run_build", session, "Unsigned dry-run build request queued.")


@app.post("/api/admin/live/arm")
def admin_live_arm(session: dict = Depends(_require_admin_session)) -> dict:
    if not settings.enable_live_execution:
        raise ApiError(
            403,
            "LIVE_EXECUTION_DISABLED",
            "Live execution is disabled by configuration.",
            {
                "wallet": session["address"],
                "killSwitch": settings.signer_kill_switch,
                "signerEnabled": settings.signer_enabled,
            },
        )
    if settings.signer_kill_switch:
        raise ApiError(403, "KILL_SWITCH_ACTIVE", "Kill switch is active.", {"wallet": session["address"]})
    return _job_response("live_arm", session, "Live micro-execution arm request queued for policy review.")


@app.post("/api/admin/live/disarm")
def admin_live_disarm(session: dict = Depends(_require_admin_session)) -> dict:
    return _job_response("live_disarm", session, "Live execution disarm request queued.")


@app.post("/api/admin/kill-switch/trigger")
def admin_kill_switch_trigger(session: dict = Depends(_require_admin_session)) -> dict:
    return _job_response("kill_switch_trigger", session, "Kill switch trigger request queued.")


@app.post("/api/admin/kill-switch/clear")
def admin_kill_switch_clear(session: dict = Depends(_require_admin_session)) -> dict:
    raise ApiError(
        403,
        "KILL_SWITCH_ACTIVE",
        "Clearing the kill switch requires a separate production policy review.",
        {"wallet": session["address"], "queued": False},
    )


@app.post("/api/user/pnet/fee-quote")
def pnet_fee_quote(body: PnetFeeQuoteBody) -> dict:
    access = _pnet_access_check(body.wallet, network=body.network, action=body.action)
    session = _wallet_session(body.wallet)
    if not access["checks"][0]["ok"]:
        raise ApiError(401, "NOT_AUTHENTICATED", "Connected wallet required.", {"action": body.action})
    if not access["ok"]:
        raise ApiError(
            402,
            "PNET_ACCESS_CHECK_FAILED",
            "Wallet must pass network, PNET opt-in, and PNET balance checks before a fee quote.",
            {"checks": access["checks"], "liveExecutionTouched": False},
        )
    fee = _pnet_fee_amount(body.action)
    quote_id = f"fq_{uuid.uuid4().hex[:10]}"
    fee_amount_atomic = str(int(float(fee) * 1_000_000))
    note = f"pnet_fee:{quote_id}:{body.action}:{body.wallet}"
    return _api_ok(
        {
            "feeQuoteId": quote_id,
            "wallet": body.wallet,
            "action": body.action,
            "pair": body.pair,
            "pnetAsaId": settings.target_asset_id,
            "feeAmount": fee,
            "feeAmountAtomic": fee_amount_atomic,
            "receiver": settings.pnet_fee_receiver_address,
            "network": settings.network,
            "feeAppId": settings.pnet_fee_app_id,
            "note": note,
            "paymentIntent": {
                "kind": "pnet_market_data_fee",
                "transactionType": "asset_transfer",
                "sender": body.wallet,
                "receiver": settings.pnet_fee_receiver_address,
                "assetId": settings.target_asset_id,
                "assetDecimals": 6,
                "amount": fee,
                "amountAtomic": fee_amount_atomic,
                "note": note,
                "notePrefix": f"pnet_fee:{quote_id}:{body.action}:",
                "buildInFrontend": True,
                "signer": "user_connected_wallet",
                "submitter": "frontend_user_wallet",
            },
            "expiresAtEpoch": round(time.time() + 300, 3),
            "verificationMode": "mock_or_on_chain_txid",
            "accessCheck": access,
            "nextStep": "Frontend builds the PNET ASA transfer, the user reviews it in their selected wallet, and backend verification grants access only after a reviewed txid path exists.",
            "disclaimer": "This is a market-data or route-intelligence fee. It does not guarantee profit, deposit funds into the bot, or grant control over platform execution.",
        }
    )


@app.post("/api/user/pnet/fee-confirm")
def pnet_fee_confirm(body: PnetFeeConfirmBody) -> dict:
    session = _wallet_session(body.wallet)
    if session["role"] == "guest":
        raise ApiError(401, "NOT_AUTHENTICATED", "Connected wallet required.", {"action": body.action})
    fee = _pnet_fee_amount(body.action)
    txid = body.txid or f"mock_pnet_fee_{uuid.uuid4().hex[:10]}"
    note_prefix = f"pnet_fee:{body.fee_quote_id}:{body.action}:"
    if txid.startswith("mock_") or txid.startswith("mock-"):
        receipt = {
            "ok": True,
            "status": "mock_confirmed",
            "reason": None,
            "txid": txid,
            "asset_id": settings.target_asset_id,
            "expected": {
                "receiver": settings.pnet_fee_receiver_address,
                "sender": body.wallet,
                "amount_raw": int(float(fee) * 1_000_000),
                "amount_display": float(fee),
                "asset_id": settings.target_asset_id,
                "asset_decimals": 6,
                "note_prefix": note_prefix,
            },
            "observed": {
                "sender": body.wallet,
                "receiver": settings.pnet_fee_receiver_address,
                "amount_raw": int(float(fee) * 1_000_000),
                "amount_display": float(fee),
                "asset_id": settings.target_asset_id,
                "confirmations": 0,
                "note_text": f"{note_prefix}{body.wallet}",
            },
            "checks": {"mock_control_plane": True},
        }
        store.record_payment_verification(receipt)
        verification_status = "mock_confirmed"
        verification_mode = "mock-control-plane"
    else:
        verification = payment_verifier.verify(
            PaymentVerificationRequest(
                txid=txid,
                expected_sender=body.wallet,
                expected_receiver=settings.pnet_fee_receiver_address,
                expected_amount=float(fee),
                asset_id=settings.target_asset_id,
                asset_decimals=6,
                note_prefix=note_prefix,
                min_confirmations=1,
            )
        )
        receipt = verification.to_dict()
        store.record_payment_verification(receipt)
        verification_status = receipt["status"]
        verification_mode = "on-chain-indexer"
        if not verification.ok:
            raise ApiError(
                402,
                "PNET_PAYMENT_NOT_VERIFIED",
                "PNET payment transaction did not verify on-chain.",
                {"verification": receipt, "liveExecutionTouched": False},
            )
    return _api_ok(
        {
            "feeQuoteId": body.fee_quote_id,
            "wallet": body.wallet,
            "action": body.action,
            "pair": body.pair,
            "txid": txid,
            "status": verification_status,
            "verificationMode": verification_mode,
            "paymentVerification": receipt,
            "creditsGranted": 1,
            "liveExecutionTouched": False,
            "message": "PNET market-data credit recorded. Access unlocks delayed scans, reports, route intelligence, or credits only.",
        }
    )


@app.get("/api/contribution-protocol/catalog")
def contribution_protocol_catalog() -> dict:
    return _api_ok(_contribution_protocol_catalog())


@app.get("/api/contribution-protocol/session/{wallet}")
def contribution_protocol_session(wallet: str) -> dict:
    return _api_ok(_contribution_protocol_session(wallet))


@app.post("/api/contribution-protocol/submit")
def contribution_protocol_submit(body: ContributionSubmitBody) -> dict:
    session = _wallet_session(body.wallet)
    if session["role"] == "guest":
        raise ApiError(
            401,
            "NOT_AUTHENTICATED",
            "Connected wallet required before submitting a contribution.",
            {"authMode": "local-review-mock"},
        )
    action = CONTRIBUTION_ACTIONS[body.contribution_type]
    contribution_id = f"cp_{uuid.uuid4().hex[:12]}"
    event = {
        "id": contribution_id,
        "kind": "contribution_submission",
        "wallet": session["address"],
        "contributionType": body.contribution_type,
        "label": action["label"],
        "title": body.title.strip(),
        "summary": body.summary.strip(),
        "evidenceUrl": body.evidence_url,
        "status": "pending_review",
        "requestedCredits": action["credits"],
        "creditsGranted": 0,
        "reviewMode": action["reviewSla"],
        "createdAtEpoch": round(time.time(), 3),
        "liveExecutionTouched": False,
    }
    _CONTRIBUTION_LEDGER.setdefault(_contribution_wallet_key(body.wallet), []).append(event)
    return _api_ok(
        {
            "submission": event,
            "creditBalance": _credit_balance(body.wallet),
            "message": "Contribution recorded for manual review. No token reward, payout, or governance authority was granted.",
            "activityHistory": _contribution_activity(body.wallet)[:20],
            "liveExecutionTouched": False,
        }
    )


@app.post("/api/contribution-protocol/spend")
def contribution_protocol_spend(body: CreditSpendBody) -> dict:
    session = _wallet_session(body.wallet)
    if session["role"] == "guest":
        raise ApiError(
            401,
            "NOT_AUTHENTICATED",
            "Connected wallet required before spending credits.",
            {"authMode": "local-review-mock"},
        )
    unlock = CONTRIBUTION_CREDIT_UNLOCKS[body.unlock_code]
    total_cost = int(unlock["creditsCost"]) * body.quantity
    current_balance = _credit_balance(body.wallet)
    if current_balance < total_cost:
        raise ApiError(
            402,
            "CREDIT_BALANCE_TOO_LOW",
            "Not enough local-review contribution credits for this unlock.",
            {
                "creditBalance": current_balance,
                "requiredCredits": total_cost,
                "unlockCode": body.unlock_code,
                "liveExecutionTouched": False,
            },
        )
    key = _contribution_wallet_key(body.wallet)
    _CREDIT_BALANCE_ADJUSTMENTS[key] = _CREDIT_BALANCE_ADJUSTMENTS.get(key, 0) - total_cost
    spend_id = f"cs_{uuid.uuid4().hex[:12]}"
    event = {
        "id": spend_id,
        "kind": "credit_spend",
        "wallet": session["address"],
        "unlockCode": body.unlock_code,
        "label": unlock["label"],
        "category": unlock["category"],
        "quantity": body.quantity,
        "creditsSpent": total_cost,
        "status": "access_receipt_created",
        "note": body.note,
        "nonBindingGovernance": unlock["category"] == "governance_signal",
        "smartContractFunction": "spend_credit",
        "smartContractStatus": "reference_blueprint_only_not_deployed",
        "createdAtEpoch": round(time.time(), 3),
        "liveExecutionTouched": False,
    }
    _CREDIT_SPEND_LEDGER.setdefault(key, []).append(event)
    return _api_ok(
        {
            "spendReceipt": event,
            "creditBalance": _credit_balance(body.wallet),
            "message": "Credits spent for a bounded access unlock. No treasury, deployment, signer, trading, or binding governance action occurred.",
            "activityHistory": _contribution_activity(body.wallet)[:20],
            "liveExecutionTouched": False,
        }
    )


@app.get("/api/community-growth/overview/{wallet}")
def community_growth_overview(wallet: str) -> dict:
    return _api_ok(_community_growth_overview(wallet))


@app.post("/api/community-growth/referral")
def community_growth_referral(body: ReferralRecordBody) -> dict:
    session = _wallet_session(body.wallet)
    if session["role"] == "guest":
        raise ApiError(
            401,
            "NOT_AUTHENTICATED",
            "Connected wallet required before recording a referral receipt.",
            {"authMode": "local-review-mock"},
        )
    key = _contribution_wallet_key(body.wallet)
    event = {
        "id": f"ref_{uuid.uuid4().hex[:12]}",
        "kind": "referral",
        "wallet": session["address"],
        "referralCode": _referral_code(body.wallet),
        "referredWallet": body.referred_wallet,
        "channel": body.channel,
        "note": body.note,
        "status": "pending_review",
        "creditsGranted": 0,
        "rewardPolicy": "manual_review_no_token_payout",
        "createdAtEpoch": round(time.time(), 3),
        "liveExecutionTouched": False,
    }
    _REFERRAL_LEDGER.setdefault(key, []).append(event)
    return _api_ok(
        {
            "referralReceipt": event,
            "overview": _community_growth_overview(body.wallet),
            "message": "Referral receipt recorded for manual review. No token payout, yield, or governance power was granted.",
            "liveExecutionTouched": False,
        }
    )


@app.get("/api/transparency/proofs")
def transparency_proofs() -> dict:
    return _api_ok(
        {
            "proofMatrix": _transparency_proof_matrix(),
            "safetyBoundaries": _transparency_system()["safetyBoundaries"],
            "publicSafe": True,
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
        }
    )


@app.get("/api/transparency/public-ledger")
def transparency_public_ledger(limit: int = 50) -> dict:
    return _api_ok(_transparency_public_ledger(limit=limit))


@app.get("/api/transparency/github-snapshot")
def transparency_github_snapshot() -> dict:
    return _api_ok(_transparency_github_snapshot())


@app.get("/api/transparency/audit-readiness")
def transparency_audit_readiness() -> dict:
    return _api_ok(_transparency_audit_readiness())


@app.get("/api/transparency/system")
def transparency_system() -> dict:
    return _api_ok(_transparency_system())


@app.get("/api/reports/paper/daily")
def paper_daily_report() -> dict:
    return _api_ok(redact_public_record(store.paper_daily_report(), "paper_trade_report"))


def _strip_report_markdown(report: dict) -> dict:
    return redact_public_record(report, "market_daily_report")


PUBLIC_MARKET_PREVIEW_FIELDS = (
    "reportDate",
    "windowStart",
    "windowEnd",
    "generatedAt",
    "source",
    "publicSafe",
    "liveExecutionTouched",
    "signerCodeTouched",
    "marketSummary",
    "marketContextRibbon",
    "summary",
    "topPairs",
    "pnetLiquidityWatchlist",
    "opportunityCounts",
    "scannerHealth",
)
PREMIUM_MARKET_DETAIL_FIELDS = (
    "topSpreads",
    "liquidityChanges",
    "routePerformance",
    "paperTradePerformance",
    "riskEvents",
    "exports",
)
PAID_PAYLOAD_ALLOWED_SAFETY_KEYS = {"signerCodeTouched", "paymentPayloadLogged", "secretsPrinted"}
PAID_PAYLOAD_FORBIDDEN_KEY_FRAGMENTS = (
    "mnemonic",
    "private",
    "secret",
    "signature",
    "paymentpayload",
    "paymentgroup",
    "authorization",
    "header",
    "env",
    "avmprivatekey",
    "algopulsex402payermnemonic",
    "seed",
    "signer",
    "walletsecret",
)


def _market_daily_preview(report: dict) -> dict:
    redacted = _strip_report_markdown(report)
    preview = {field: redacted[field] for field in PUBLIC_MARKET_PREVIEW_FIELDS if field in redacted}
    preview.update(
        {
            "reportTier": "public-preview",
            "preview": True,
            "paymentUpgradeAvailable": True,
            "upgradeResource": X402_MARKET_PULSE_RESOURCE,
            "paymentUnlocks": "premium delayed intelligence sections only",
            "excludedDetailSections": [field for field in PREMIUM_MARKET_DETAIL_FIELDS if field in redacted],
            "publicSafe": True,
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
        }
    )
    return preview


def _premium_market_daily_report(report: dict) -> dict:
    redacted = _strip_report_markdown(report)
    premium_sections = [field for field in PREMIUM_MARKET_DETAIL_FIELDS if field in redacted]
    premium_report = _strip_paid_sensitive_metadata_names(redacted)
    premium_report.update(
        {
            "reportTier": "premium-delayed-intelligence",
            "premium": True,
            "access": "x402-paid",
            "delayed": True,
            "premiumSections": premium_sections,
            "exportMetadata": {
                "resource": X402_MARKET_PULSE_RESOURCE,
                "format": "json",
                "redacted": True,
                "paymentGated": True,
                "reportDate": redacted.get("reportDate"),
                "generatedAt": redacted.get("generatedAt"),
            },
            "redactionPolicy": {
                "rawRoutes": "excluded",
                "custodyFields": "excluded",
                "paymentMaterial": "excluded",
                "freshExecutableRoutes": False,
            },
            "publicSafe": True,
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
        }
    )
    return premium_report


def _strip_paid_sensitive_metadata_names(value):
    if isinstance(value, dict):
        return {
            key: _strip_paid_sensitive_metadata_names(child)
            for key, child in value.items()
            if not _paid_metadata_key_looks_sensitive(key)
        }
    if isinstance(value, list):
        return [_strip_paid_sensitive_metadata_names(child) for child in value]
    return value


def _paid_metadata_key_looks_sensitive(key: str) -> bool:
    if key in PAID_PAYLOAD_ALLOWED_SAFETY_KEYS:
        return False
    normalized = "".join(character for character in str(key).lower() if character.isalnum())
    return normalized == "key" or normalized.endswith("key") or any(
        fragment in normalized for fragment in PAID_PAYLOAD_FORBIDDEN_KEY_FRAGMENTS
    )


@app.get("/api/reports/market/daily")
def market_daily_report(date: str | None = None) -> dict:
    try:
        report = store.generate_market_intelligence_report(report_date=date)
    except ValueError as exc:
        raise ApiError(400, "INVALID_REPORT_DATE", "Report date must use YYYY-MM-DD.", {"detail": str(exc)}) from exc
    return _api_ok(_market_daily_preview(report))


@app.get("/api/x402/reports/market-pulse/daily")
def x402_market_pulse_daily_report(
    date: str | None = None,
    x_algopulse_mock_x402_proof: str | None = Header(default=None, alias="X-Algopulse-Mock-X402-Proof"),
):
    if X402_TESTNET_ACTIVE:
        # The x402 payment middleware has already verified + settled payment via
        # the GoPlausible facilitator before this handler runs. Serve only the
        # delayed/redacted report; no payment payload is inspected or logged here.
        try:
            report = store.generate_market_intelligence_report(report_date=date)
        except ValueError as exc:
            raise ApiError(400, "INVALID_REPORT_DATE", "Report date must use YYYY-MM-DD.", {"detail": str(exc)}) from exc
        return _api_ok(
            {
                "resource": X402_MARKET_PULSE_RESOURCE,
                "mode": "testnet-x402",
                "facilitator": "goplausible",
                "source": "premium-delayed-intelligence",
                "accessTier": "premium-delayed-intelligence",
                "paymentUnlocks": "premium delayed market intelligence report",
                "publicSafe": True,
                "liveExecutionTouched": False,
                "signerCodeTouched": False,
                "report": _premium_market_daily_report(report),
            }
        )

    if X402_TESTNET_FAIL_CLOSED:
        return JSONResponse(
            status_code=503,
            content=_api_response(
                ok=False,
                data=None,
                error={
                    "code": "X402_TESTNET_UNAVAILABLE",
                    "message": "x402 TestNet payment gate is enabled but unavailable; access is fail-closed.",
                    "details": {
                        "mode": "testnet-x402",
                        "resource": X402_MARKET_PULSE_RESOURCE,
                        "paymentUnlocks": "delayed market intelligence report only",
                        "mockUnlockAvailable": False,
                        "liveExecutionTouched": False,
                        "signerCodeTouched": False,
                    },
                },
            ),
        )

    # --- Mock readiness mode (default; fail-closed when TestNet not enabled) ---
    if x_algopulse_mock_x402_proof != MOCK_X402_REPORT_PROOF:
        return JSONResponse(
            status_code=402,
            content=_api_response(
                ok=False,
                data=None,
                error={
                    "code": "X402_PAYMENT_REQUIRED",
                    "message": "Mock/TestNet x402 readiness proof required for this delayed market intelligence report.",
                    "details": {
                        "mode": "mock-testnet-readiness",
                        "resource": X402_MARKET_PULSE_RESOURCE,
                        "acceptedProofHeader": "X-Algopulse-Mock-X402-Proof",
                        "acceptedProofValue": MOCK_X402_REPORT_PROOF,
                        "network": "algorand-testnet-readiness",
                        "assetId": settings.target_asset_id,
                        "assetLabel": "PNET",
                        "paymentRequirements": {
                            "mode": "mock-testnet-readiness",
                            "resource": X402_MARKET_PULSE_RESOURCE,
                            "scheme": "mock-x402-readiness",
                            "network": "algorand-testnet-readiness",
                            "assetId": settings.target_asset_id,
                            "assetLabel": "PNET",
                            "proofHeader": "X-Algopulse-Mock-X402-Proof",
                            "settlement": "not-performed",
                        },
                        "paymentUnlocks": "delayed market intelligence report only",
                        "noCustody": True,
                        "noSigning": True,
                        "noSubmission": True,
                        "liveExecutionTouched": False,
                        "signerCodeTouched": False,
                    },
                },
            ),
            headers={"X-Algopulse-Payment-Required": "mock-x402-readiness"},
        )
    try:
        report = store.generate_market_intelligence_report(report_date=date)
    except ValueError as exc:
        raise ApiError(400, "INVALID_REPORT_DATE", "Report date must use YYYY-MM-DD.", {"detail": str(exc)}) from exc
    return _api_ok(
        {
            "resource": X402_MARKET_PULSE_RESOURCE,
            "mode": "mock-testnet-readiness",
            "source": "premium-delayed-intelligence",
            "accessTier": "premium-delayed-intelligence",
            "paymentUnlocks": "premium delayed market intelligence report",
            "proofAccepted": True,
            "publicSafe": True,
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
            "report": _premium_market_daily_report(report),
        }
    )


@app.get("/api/reports/market/archive")
def market_report_archive(limit: int = 30) -> dict:
    reports = [
        _strip_report_markdown(report)
        for report in store.generate_recent_market_intelligence_reports(limit_days=max(1, min(limit, 90)))
    ]
    return _api_ok(
        redact_public_record(
            {
                "reports": reports,
                "count": len(reports),
                "source": "stored" if reports else "unavailable",
                "publicSafe": True,
                "liveExecutionTouched": False,
                "signerCodeTouched": False,
            },
            "market_archive_report",
        )
    )


@app.get("/api/reports/market/daily/export")
def market_daily_report_export(date: str | None = None, format: Literal["json", "markdown"] = "json"):
    try:
        report = store.generate_market_intelligence_report(report_date=date)
    except ValueError as exc:
        raise ApiError(400, "INVALID_REPORT_DATE", "Report date must use YYYY-MM-DD.", {"detail": str(exc)}) from exc
    if format == "markdown":
        filename = f"algopulse-market-report-{report['reportDate']}.md"
        return PlainTextResponse(
            report["markdown"],
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    return JSONResponse(
        content=_strip_report_markdown(report),
        headers={"Content-Disposition": f'attachment; filename="algopulse-market-report-{report["reportDate"]}.json"'},
    )


@app.post("/api/scan")
def scan_now() -> dict:
    return scanner.run_once()


@app.post("/api/execute-best")
def execute_best() -> dict:
    if not settings.allow_api_execution:
        raise HTTPException(status_code=403, detail="API execution is disabled. Use CLI worker or set ALGO_PULSE_ALLOW_API_EXECUTION=true.")
    return scanner.execute_best_once()
