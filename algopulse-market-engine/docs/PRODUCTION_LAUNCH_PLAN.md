# Production Launch Plan

This plan defines how AlgoPulse / PNET Market Engine moves toward production using an enterprise release discipline similar to Microsoft SDL, threat modeling, staged rollout, operational readiness, incident response, and rollback.

Production in this document means **Production Phase 0** unless a later human-reviewed gate says otherwise. Production Phase 0 is live read-only market intelligence, delayed/public-safe dashboard data, admin observability, paper trading, risk evidence, and PNET access workflows. It is not live trading.

## Source Notes

- Microsoft SDL overview: <https://www.microsoft.com/en-us/securityengineering/sdl>
- Microsoft SDL practices: <https://www.microsoft.com/en-us/securityengineering/sdl/practices>
- Microsoft threat modeling: <https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling>
- Azure Well-Architected Framework: <https://learn.microsoft.com/en-us/azure/well-architected/>
- Azure Operational Excellence principles: <https://learn.microsoft.com/en-us/azure/well-architected/operational-excellence/principles>

## Production Definition

### Production Phase 0 Allows

- Live read-only scanner.
- Live Tinyman/Pact quote capture.
- Connector health and quote freshness evidence.
- Route detection and route rejection explanations.
- Risk decisions.
- Paper trading and opportunity decay analytics.
- Delayed or redacted public dashboard data.
- Admin Control Room observability.
- PNET access for reports, scans, credits, simulations, and research workflows after human review.

### Production Phase 0 Blocks

- Live trading.
- Signer changes.
- Mnemonics, private keys, seed phrases, or AI-held keys.
- Hot-wallet funding, custody, or reserve logic.
- Transaction signing or submission.
- Public fresh executable route data.
- User deposits.
- Profit, passive-income, copy-trading, managed-strategy, or guaranteed-return claims.
- Risk-limit loosening without explicit human review.

## Enterprise Release Principles

### 1. Security Requirements First

Every production candidate must preserve the repo's safe defaults:

- `ENABLE_EXECUTION=false`
- `ENABLE_SIGNER=false`
- `KILL_SWITCH=true`
- `ALGO_PULSE_ALLOW_API_EXECUTION=false`
- no signer secrets in source, docs, screenshots, logs, artifacts, or `.env` files

Any change involving wallet SDKs, payment activation, production deployment, risk policy, app/asset allowlists, signer behavior, public claims, or execution-adjacent behavior requires human review before implementation or merge.

### 2. Threat Modeling Before Production

Before deployment, maintain a reviewed threat model for:

- browser and public dashboard
- backend API
- scanner and quote workers
- database and evidence store
- admin ops surfaces
- PNET fee quote and verification flows
- refund and reconciliation records
- Pera/Defly wallet UX
- dry-run validator
- future isolated signer boundary
- logs, alerts, and evidence exports

Each threat must become one of:

- blocked item
- human-review item
- test-planning item
- safe implementation item
- completed item

### 3. Staged Rollout

Promotion must move through controlled environments:

| Stage | Data | Wallet | Signer | Submission | Public Surface |
| --- | --- | --- | --- | --- | --- |
| Local | mock/stored/live optional | review-mode only | disabled | disabled | local operator review |
| Read-only staging | live scanner and quotes | review-mode only | disabled | disabled | delayed/internal dashboard |
| Production Phase 0 | live scanner, quotes, routes, risk, paper evidence | reviewed access flows only | disabled unless later gates pass | disabled | delayed/redacted public data |
| Dry-run review | live route evidence plus unsigned group validation | own operator address only | disabled | disabled | admin-only receipts |
| Tiny own-funds pilot | one manual route after all prior gates | dedicated tiny hot wallet only | isolated and reviewed | manual only | delayed/redacted receipts |

## Phase Path

### Phase A - Release Train And Repo Hygiene

Goal: keep `main` deployable in safe read-only mode.

Required work:

- Protect `main` with required PR review, CI, CODEOWNERS, and status checks.
- Use release branches or tags for production candidates.
- Keep real environment values outside git.
- Require PR evidence: tests, repo guard, changed gates, rollback note, Whitepaper Delta, and xChain Delta.
- Build deployment artifacts from exact commit SHA.

Exit criteria:

- `python scripts/repo_guard.py` passes.
- `node --check src/algopulse/static/app.js` passes.
- `python -m pytest -q` passes.
- `git diff --check` passes.
- `main` can deploy with execution and signer disabled.

### Phase B - Security Requirements And Threat Model

Goal: make the attack surface reviewable before production.

Required work:

- Maintain a formal threat model.
- Define trust boundaries: public user, connected user, admin, worker, scanner, future isolated signer, database, Algorand nodes/indexer, DEX SDKs.
- Review abuse cases: fake wallet role, stale-route exposure, raw-route leaks, payment spoofing, refund abuse, signer bypass, leaked secrets, connector manipulation, quote decay, and unsafe public claims.
- Map every abuse case to a test, mitigation, blocked item, or human-review item.

Exit criteria:

- Threat model has human review.
- No unresolved critical or high-risk threat blocks Production Phase 0.
- Any unresolved wallet, payment, execution, or public-claim risk is explicitly blocked.

### Phase C - Architecture Hardening

Goal: separate public intelligence, operator control, and future execution boundaries.

Required work:

- Run API/dashboard as public-safe read surfaces.
- Run scanner/worker separately from web serving.
- Use Postgres for production evidence rather than local SQLite.
- Treat Redis as optional infrastructure that can degrade safely.
- Validate config at startup and fail closed for unsafe environment combinations.
- Keep signer disabled and unconfigured for Production Phase 0.

Exit criteria:

- Public endpoints return delayed, aggregate, redacted, or source-labeled data only.
- Admin ops endpoints are backend-protected or not publicly exposed.
- Scanner runs without private keys.
- Production config cannot accidentally enable execution.

### Phase D - QA And Test Certification

Goal: prove the system behaves safely before staging.

Required work:

- Preserve current unit, integration, security, redaction, and dashboard tests.
- Add or keep tests for production config fail-closed behavior, admin/session spoofing, public delay/redaction, wallet UX review-mode boundaries, payment/refund/reconciliation exposure policy, connector health, paper evidence, and unsigned dry-run non-submission.
- Add browser smoke coverage for Pulse, Routes, Access, Control Room, Reports, and public-safe dashboards.
- Review dependency posture for FastAPI, py-algorand-sdk, Tinyman SDK, Pact SDK, and x402 packages.

Exit criteria:

- Full test suite passes in CI.
- No skipped or xfailed test hides a Production Phase 0 safety issue.
- Browser QA confirms public users cannot access admin controls.
- Mock data is visibly labeled as mock.

### Phase E - Read-Only Staging

Goal: run against live market data without signing, submitting, or holding funds.

Required configuration:

```text
ALGO_PULSE_CONNECTORS=tinyman,pact
ALGO_PULSE_TARGET_ASSET_ID=3169177585
ALGO_PULSE_USE_VESTIGE_DISCOVERY=true
ALGO_PULSE_ENABLE_LIVE_EXECUTION=false
ALGO_PULSE_EXECUTE_APPROVED=false
ALGO_PULSE_ALLOW_API_EXECUTION=false
ENABLE_SIGNER=false
KILL_SWITCH=true
```

Required evidence:

- 24h scanner uptime.
- Tinyman/Pact connector health.
- Quote freshness counts.
- Route candidates and rejection reasons.
- Risk decisions.
- Paper-trading records with T+5s and T+30s rechecks.
- Alerts for connector failure, stale quotes, database unavailability, and route engine errors.

Exit criteria:

- Scanner runs 24 hours with no keys and no submitted transactions.
- Seven-day paper trading begins.
- Admin Control Room clearly shows what is live, mock, delayed, blocked, and unavailable.

### Phase F - TestNet Wallet And PNET Access Layer

Goal: make Pera/Defly useful for access flows without turning AlgoPulse into a trading wallet.

Required work:

- Write and approve wallet connector design before SDK integration.
- Add Pera and Defly TestNet connect-only integration behind feature flags.
- Backend verifies address/session independently; frontend role state is never authorization.
- PNET access stays limited to scans, delayed reports, simulations, research exports, and credits.
- No frontend keys, AI-held keys, custody, or transaction submission by AlgoPulse.

Exit criteria:

- TestNet wallet connection works for Pera and Defly.
- Backend role/session behavior is tested.
- PNET access flow is proven with mock or TestNet receipts.
- User-owned history is not globally public.
- Human review approves any MainNet payment receiver activation.

### Phase G - Production Phase 0 Launch

Goal: launch the safe product.

Allowed:

- Live scanner.
- Live quotes.
- Route and risk analysis.
- Paper trading.
- Public delayed dashboard.
- Admin Control Room.
- PNET access layer for reports, scans, simulations, and credits after review.

Blocked:

- live trading
- signer changes
- hot-wallet funding
- transaction submission
- public fresh executable route data
- user deposits
- guaranteed-return language

Exit criteria:

- Go/no-go checklist passes.
- Rollback plan is tested.
- Alerts route to a real human.
- Public copy is market-intelligence, simulation, research, or delayed-report language only.
- Production deployment URL and commit SHA are recorded.
- Incident runbook exists.

### Phase H - Unsigned Dry-Run And Signer Review

Goal: prepare future execution safely without executing.

Required work:

- Dry-run builder validates route hash, group size, app IDs, asset IDs, fees, transaction types, validity window, rekey absence, and close-out absence.
- Dry-run emits unsigned, unsubmitted receipts only.
- Signer review remains separate and includes policy, threat model, audit logs, kill switch, route-hash approval, wallet reserve, and fee caps.
- Signer secrets are never placed in repo files, browser state, AI tools, docs, screenshots, or logs.

Exit criteria:

- Unsigned group validator tests pass.
- Signer rejection tests are reviewed.
- Main API/scanner cannot directly sign or submit.
- Human approval is recorded before signer enablement.

### Phase I - Tiny Own-Funds Micro-Execution Pilot

Goal: only after all prior gates, run one manual, tiny, reconciled trade.

Required constraints:

- Fresh dedicated hot wallet only.
- 100-250 ALGO max wallet funding.
- Start with ALGO/USDC only.
- Max trade size 10 ALGO or less.
- Daily loss cap active.
- Daily trade cap active.
- Max concurrent execution equals 1.
- Manual route-hash approval.
- Lora verification.
- Expected versus actual reconciliation.
- Public receipt delayed or redacted.

Exit criteria:

- First trade is manually approved.
- Trade is verified in Lora.
- Actual balance deltas reconcile.
- Any mismatch blocks additional live attempts.
- Automation remains off until multiple reviewed receipts support it.

## Go / No-Go Board

### Go For Production Phase 0 Only If

- CI and repo guard pass on the exact deploy commit.
- No secrets, keys, mnemonics, `.env`, database dumps, or logs are staged.
- Admin auth is backend-enforced.
- Public dashboard is delayed or redacted.
- Scanner and quote health are fresh.
- Paper trading evidence exists.
- Risk rejects unsafe routes with reasons.
- Alerts and runbooks exist.
- Rollback is tested.
- Public copy does not imply profit, passive income, copy trading, managed strategies, user deposits, or guaranteed returns.

### No-Go If

- Live execution is enabled.
- Signer is enabled.
- API execution is enabled.
- Public fresh routes are visible.
- Wallet role is frontend-only.
- Payment or refund data is globally public.
- Any claim implies guaranteed profit, passive income, copy trading, managed strategy, or user deposits.

## Required Tests And Checks

Run before each release candidate:

```powershell
python scripts\repo_guard.py
node --check src\algopulse\static\app.js
python -m pytest -q
git diff --check
```

Additional release checks:

- Docker build smoke test.
- Local dashboard browser smoke test.
- Public user access test.
- Connected user access test.
- Admin access test.
- Public route/report redaction test.
- Read-only staging scanner report.
- Paper-trading evidence report.

## Production Monitoring

Required production signals:

- scanner uptime
- connector health
- quote age
- stale quote count
- route rejection reasons
- paper-trade survival at T+5s and T+30s
- database health
- Redis health if used
- public dashboard delay
- admin auth failures
- payment verification failures
- refund backlog
- kill switch state

Required alerts:

- scanner down
- Tinyman connector failing
- Pact connector failing
- quote age above threshold
- route engine crash
- database unavailable
- Redis unavailable
- unknown asset detected
- unknown app ID detected
- kill switch triggered
- signer offline if signer is later approved
- signer rejection spike if signer is later approved
- daily loss limit near breach if live pilot is later approved
- reconciliation mismatch
- PNET fee verification failed
- refund queue backlog

## Rollback And Incident Response

Rollback steps:

1. Keep or trigger kill switch.
2. Disable execution flags.
3. Preserve logs, evidence rows, receipts, and database snapshots.
4. Revert to last known-good deployment revision.
5. Confirm public dashboard shows degraded, delayed, or unavailable states safely.
6. Reconcile PNET fee receipts and pending credits/reports.
7. Record incident note before re-enabling staging or production.

Incident response priorities:

- protect secrets
- stop unsafe exposure
- preserve evidence
- notify owner/reviewer
- avoid public claims until facts are confirmed

## Human Review Requirements

Human approval is required before:

- real Pera/Defly SDK integration
- production payment receiver activation
- live Tinyman/Pact staging config promotion
- public dashboard freshness or redaction policy changes
- risk-limit changes
- app ID or asset allowlist changes
- deployment config changes
- dry-run behavior that moves closer to signing
- signer code or signer policy changes
- hot-wallet funding
- any live transaction
- public launch copy

Approval record must include:

- reviewer
- date
- change summary
- evidence reviewed
- approved scope
- explicit exclusions
- rollback path

## Current Status

Current safe production target: **Production Phase 0 market intelligence**.

Current blocked areas:

- live trading
- signer changes
- hot-wallet logic
- transaction submission
- unreviewed wallet SDK integration
- public fresh executable routes
- guaranteed-return or passive-income claims

Next safest production action:

- keep building staging evidence for scanner uptime, quote freshness, connector reliability, paper-trade survival, route/risk explainability, public redaction, and admin observability.

## Whitepaper Delta

Whitepaper update recommended: `Evaluation Plan` should summarize Production Phase 0 readiness requirements, including 24h scanner evidence, 7-day paper trading, public delay/redaction, and Microsoft-style threat-model/release gates.

## xChain Learning Delta

No xChain implementation belongs in this production path yet. Keep xChain as a future product-access learning track until the Phase 0 wallet boundary and market-intelligence product are proven.
