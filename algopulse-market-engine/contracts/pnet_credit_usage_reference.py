"""Reference blueprint for a future PNET credit-usage Algorand app.

This file is intentionally not wired into deployment, signing, or Mainnet code.
It documents the minimal on-chain functions a reviewed credit app would need so
AlgoPulse and AlgoFlow can share the same vocabulary before any contract build.
"""

from __future__ import annotations

from dataclasses import dataclass


APP_NAME = "pnet_credit_usage_reference"
APP_STATUS = "blueprint_only_not_deployed"


@dataclass(frozen=True)
class CreditMethod:
    name: str
    args: tuple[str, ...]
    purpose: str
    blocked_effects: tuple[str, ...]


CREDIT_METHODS: tuple[CreditMethod, ...] = (
    CreditMethod(
        name="grant_credit",
        args=("account", "amount", "reason_hash"),
        purpose="Record reviewed off-chain contribution credit for an account.",
        blocked_effects=("no token payout", "no treasury movement", "no trading authority"),
    ),
    CreditMethod(
        name="spend_credit",
        args=("account", "unlock_code", "amount", "receipt_hash"),
        purpose="Consume credits for bounded tool/report access.",
        blocked_effects=("no signer access", "no transaction submission", "no live route exposure"),
    ),
    CreditMethod(
        name="record_nonbinding_signal",
        args=("account", "proposal_id", "signal_hash"),
        purpose="Record a non-binding governance/community signal.",
        blocked_effects=("no vote buying", "no treasury control", "no deployment authority"),
    ),
    CreditMethod(
        name="record_referral",
        args=("account", "referral_hash", "channel_hash"),
        purpose="Record a reviewed referral receipt without automatic rewards.",
        blocked_effects=("no automatic payout", "no token emission", "no leaderboard manipulation"),
    ),
    CreditMethod(
        name="record_reputation_event",
        args=("account", "event_type", "evidence_hash", "score_delta"),
        purpose="Record non-financial reputation evidence for community ranking.",
        blocked_effects=("no yield", "no binding vote power", "no investment claim"),
    ),
    CreditMethod(
        name="freeze_credit_account",
        args=("account", "reason_hash"),
        purpose="Freeze a credit account after abuse review.",
        blocked_effects=("no fund custody", "no asset seizure", "no wallet control"),
    ),
)


def method_names() -> tuple[str, ...]:
    """Return supported reference method names for tests and docs."""
    return tuple(method.name for method in CREDIT_METHODS)


def app_spec() -> dict:
    """Return a small app-spec-like contract summary without external deps."""
    return {
        "name": APP_NAME,
        "status": APP_STATUS,
        "network": "not_configured",
        "deployed": False,
        "stateModel": {
            "local": ["credit_balance", "account_frozen", "last_receipt_hash", "reputation_score", "referral_count"],
            "global": ["admin", "pnet_asset_id", "schema_version"],
        },
        "methods": [
            {
                "name": method.name,
                "args": list(method.args),
                "purpose": method.purpose,
                "blockedEffects": list(method.blocked_effects),
            }
            for method in CREDIT_METHODS
        ],
        "safetyBoundaries": [
            "Credits are utility access receipts, not token rewards.",
            "Governance signals are non-binding.",
            "Reputation and referral records are non-financial and do not create payout rights.",
            "The app must never sign, custody, submit trades, move treasury, or expose fresh executable routes.",
            "Deployment requires separate TestNet review, audit scope, receiver/admin approval, and Mainnet approval gate.",
        ],
    }


def reference_approval_program_notes() -> str:
    """Human-readable approval-program notes for future TEAL/PyTeal work."""
    return """
    Future approval program requirements:
    - create: set admin, PNET ASA id, schema version
    - opt_in: initialize credit_balance=0, account_frozen=0
    - grant_credit: admin-only, positive amount, reason_hash required
    - spend_credit: account-only or delegated app-call proof, positive amount, sufficient balance
    - record_nonbinding_signal: account-only, proposal_id and signal_hash required
    - record_referral: account-only, referral_hash required, manual-review source
    - record_reputation_event: admin/reviewer-only, evidence_hash required, bounded score_delta
    - freeze_credit_account: admin-only abuse-control path
    - reject: any request for treasury movement, token emission, trading, signing, payout, yield, or deployment control
    """.strip()
