# Senior Review Guide

Use this as the first-pass map for a senior engineer reviewing AlgoPulse Phase 0.

## Review Stance

This repo is a private Phase 0 market-intelligence and arb-research system. Treat it as safety-critical even when code paths are mock, paper-only, or dry-run. The current acceptable mode is scanner, quotes, routes, risk analysis, paper trading, delayed dashboard data, admin observability, and unsigned validation only.

Do not treat this repo as live-trading ready until the gate evidence says so.

## First Files To Read

| Purpose | File |
|---|---|
| Product and safety boundary | `README.md` |
| Current gate status | `docs/GATED_PROGRESS_TRACKER.md` |
| AI/code-change protocol | `docs/AI_DEVELOPMENT_PROTOCOL.md` |
| AI workflow modes and verification | `docs/AI_WORKFLOW_GOVERNOR.md` |
| Human review gates | `docs/HUMAN_REVIEW_GATES.md` |
| Pre-merge checklist | `docs/SAFETY_CHECKLIST.md` |
| Working whitepaper | `docs/WHITEPAPER_WORKING_DRAFT.md` |
| API exposure inventory | `docs/API_EXPOSURE_INVENTORY.md` |
| Test coverage map | `docs/TEST_MATRIX.md` |
| Release checks | `docs/RELEASE_CHECKLIST.md` |
| xChain learning track | `docs/XCHAIN_ACCOUNTS_LEARNING_TRACK.md` |

## Sensitive Paths

Changes in these areas require human review before merge:

- `src/algopulse/signer.py`
- `src/algopulse/executor.py`
- `src/algopulse/dry_run.py`
- `src/algopulse/dry_run_validator.py`
- `src/algopulse/config.py`
- `src/algopulse/api.py`
- `src/algopulse/payment_verification.py`
- `src/algopulse/refunds.py`
- `src/algopulse/public_record_redaction.py`
- `src/algopulse/static/`
- `.env*.example`
- `.github/`

## What Should Be True Before Merge

- The change is small enough to review in one sitting.
- Public data is delayed, aggregate, redacted, or clearly source-labeled.
- Mock data remains visibly marked as mock.
- No signer secret, mnemonic, private key, API token, `.env`, database, or log file is committed.
- No live trading, transaction signing, transaction submission, hot-wallet funding, or custody behavior is added.
- Risk limits are not loosened without explicit human approval.
- Dashboard JS passes `node --check src/algopulse/static/app.js` when touched.
- `python scripts/repo_guard.py` passes.
- `python -m pytest -q` passes, or any failure is documented before handoff.

## Review Questions

1. Does the change preserve the current safe mode?
2. Does it make evidence more traceable or easier to verify?
3. Could a public user see fresh executable route data?
4. Could a frontend-only role or local mock session be mistaken for backend authorization?
5. Could any new field leak signer, wallet, transaction, payment, refund, or route internals?
6. Did the change introduce a second system where an existing module already had the pattern?
7. Are tests proving behavior rather than just snapshotting mock output?
8. Did the AI work mode match the risk level of the task?

## Local Validation

Run:

```powershell
python scripts/repo_guard.py
node --check src/algopulse/static/app.js
python -m pytest -q
git diff --check
```

## Gate Handoff

Every meaningful change should end with the current gate status from `docs/GATED_PROGRESS_TRACKER.md`. If a risk is found, convert it into one of:

- blocked item
- human-review item
- test-planning item
- safe implementation item
- completed item

Also include a `Whitepaper Delta` for any confirmed architecture, safety, evidence, phase, risk, PNET utility, or product-positioning change. The whitepaper must remain evidence-backed and Phase 0 honest.

Also include an `xChain Learning Delta`. xChain Accounts are learning/product-access research only unless a human separately approves implementation.
