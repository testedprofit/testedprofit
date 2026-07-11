# AlgoPulse Phase 0 Market Engine

AlgoPulse Phase 0 is a safe-by-default Algorand market-intelligence and arb-research engine.

It scans liquidity venues, detects two-leg and three-leg spread opportunities, records paper trades, validates risk and readiness evidence, and serves public-safe dashboard data. It runs with deterministic mock market data for smoke tests and supports live Tinyman/Pact mainnet scanning through official Python SDKs.

The initial live target is ProfitNet / PNET, asset `3169177585`. Vestige discovery can be enabled to pull the larger PNET pools first, then the bot fetches executable pool state from Tinyman/Pact.

## Reviewer Quick Path

Start here if you are reviewing this repo for handoff or production readiness:

1. Read `docs/SENIOR_REVIEW_GUIDE.md`.
2. Use `docs/AI_WORKFLOW_GOVERNOR.md` for complex AI-assisted work.
3. Confirm `docs/GATED_PROGRESS_TRACKER.md` still matches the current work.
4. Check `docs/WHITEPAPER_WORKING_DRAFT.md` when a change creates confirmed architecture, safety, evidence, phase, risk, PNET utility, or product-positioning facts.
5. Check `docs/XCHAIN_ACCOUNTS_LEARNING_TRACK.md` before any EVM-wallet, xChain, bridge, x402, or account-linking research.
6. Run:

```powershell
python scripts/repo_guard.py
node --check src/algopulse/static/app.js
python -m pytest -q
git diff --check
```

Expected safe posture: scanner, quotes, routes, risk, paper trading, delayed dashboard, admin observability, and unsigned validation only. Live execution remains locked until the required gate evidence is reviewed.

## AI-Assisted Development

This repository uses an AI-assisted development workflow. Planning, implementation support, review, and documentation have used a mix of ChatGPT agents, Codex, Claude Code, Copilot, and GitHub Copilot, with human review and explicit approval gates for safety-sensitive changes.

For the x402 workstream specifically, AI tools helped draft plans, implement tests and docs, inspect pull requests, and prepare gated handoffs. Human approval remained required for merges, payment exercises, Mainnet/deploy decisions, public claims, and any safety-sensitive action.

## What This Is

- market scanner
- quote normalizer
- route/spread detector
- risk policy engine
- paper-trading logger
- live Tinyman/Pact pair scanner
- Vestige target-asset pool discovery
- two-leg venue arb route generation
- three-leg ALGO/ASA/USDC triangle route generation for scanner and paper-trade review
- guarded two-leg atomic dry-run builder
- unsigned execution dry-run mode with Algorand `TX_GROUP_LIMIT` enforcement
- isolated signer policy module with locked defaults and JSONL approval/rejection audit logs
- Step 10 tiny-live readiness gates for ALGO/USDC-only first execution
- stale-route rejection before execution
- balance reconciliation receipts for dry-runs and submitted trades
- Algorand payment verification receipts
- refund/failure case queue for manual operator resolution
- live-market readiness preflight
- worker process for deploy-time scanning/execution
- public dashboard
- Docker deployment starter

## What This Is Not

- user fund manager
- copy-trading product
- guaranteed-profit system
- public execution API by default

Production Status: NOT LIVE READY. The system is collecting market data, but live execution remains locked until scanner uptime, paper-trading edge, risk gates, unsigned dry runs, signer isolation, and manual micro-trade reconciliation are proven.

Current safe mode: Scanner / Paper / Dry Run only. No user deposits, no guaranteed returns, and no live execution unless explicitly armed by admin after gates pass.

## Security Red Lines

This project must not mean:

- AI agents have signer secrets or wallet keys.
- The frontend has wallet keys.
- A main wallet or treasury wallet signs trades.
- An unknown repo, dependency, or unreviewed service signs transactions.
- The bot trades every asset it sees.
- The bot accepts user funds.
- The bot performs sandwich attacks or predatory MEV.

The only acceptable signing path is a dedicated tiny hot wallet inside an isolated signer with explicit policy limits.

## Real Arb Bot Path

Read these before moving past scanner/dry-run work:

- `docs/PRODUCT_THESIS.md` defines the product: AlgoPulse Market Engine, not a generic arb bot.
- `docs/CAPABILITY_CATALOG.md` defines the public product capabilities: intelligence, spreads, simulations, liquidity, research, own-funds proof, delayed data, and receipts.
- `docs/PRODUCTION_READINESS.md` defines phase gates, environment promotion, go/no-go, rollback, live micro-execution, and public-claims checklists.
- `docs/OBSERVABILITY.md` defines required metrics, alerts, health states, log fields, and reconciliation evidence.
- `docs/PNET_FEE_FLOW.md` defines the Pera-signed PNET fee flow for scans, reports, simulations, credits, and non-admin restrictions.
- Admin `Control Room` dashboard tab visualizes Phase 0 gates, service pipeline, source labels, paper score, rejection funnel, and live lock state from `/api/ops/*`.
- `docs/PNET_DASHBOARD_COCKPIT.md` defines the role-based Admin Cockpit and connected PNET access portal.
- `docs/PNET_PAYMENT_FLOW.md` defines the Pera-signed PNET market-data fee flow and receipt boundary.
- `docs/CONTRIBUTION_PROTOCOL.md` defines the local-review PNET credit contribution protocol, bounded unlocks, dashboard flow, and AlgoFlow integration boundary.
- `docs/CONTRIBUTION_CREDIT_CONTRACT.md` defines the non-deployed smart-contract blueprint for future credit usage.
- `docs/COMMUNITY_GROWTH_SYSTEM.md` defines local-review referrals, contributor leaderboard, onboarding, reputation, and abuse boundaries.
- `docs/PNET_CONTENT_SYSTEM.md` defines the 30-day content calendar, X thread templates, blog templates, and publishing checklist for evidence-first PNET communications.
- `docs/PNET_WEBSITE_COPY.md` defines conservative website copy for tokenomics, contribution, utility, and transparency sections.
- `docs/PNET_VISUAL_ASSETS.md` defines Mermaid visual assets and export guardrails for PNET diagrams.
- `docs/TRANSPARENCY_SYSTEM.md` defines the public-safe proof ledger, automated proof checks, GitHub dossier snapshot generator, and dashboard boundaries.
- `docs/AUDIT_READINESS_PACKAGE.md` defines the audit checklist, threat model, blocked claims, and evidence package before external demos or public claims.
- `docs/X402_GATE_LOG.md` preserves the current x402 gate status, 4D operating model, open PR context, and approval blockers.
- `docs/X402_GOPLAUSIBLE_TESTNET_POC_PLAN.md` defines the docs-only Gate 2 plan for official GoPlausible TestNet x402 readiness before any Mainnet or eligibility claim.
- `docs/IMAGE_PIPELINE.md` defines the safe GitHub docs pipeline for screenshots, diagrams, demo GIFs, redaction checks, and visual evidence receipts.
- `docs/PNET_DOCUMENTATION_AND_AUDIT_READINESS.md` defines the internal tokenomics, use-case, roadmap, audit-readiness, and publication-gate checklist before any external listing, exchange, audit, or launch claim.
- `docs/CODEX_HANDOFF.md` summarizes the current safe control-plane scope and latest implementation points.
- `docs/API_CONTRACT.md` defines role-gated API envelopes, public config, admin stubs, and PNET fee stubs.
- `docs/ALERT_CATALOG.md` defines Phase 0 scanner, connector, quote, route, storage, risk, signer-boundary, wallet, loss-limit, live-trade, and reconciliation alerts.
- `docs/POLICY_CONTROLS.md` defines the admin-gated hard-stop catalog for input caps, fee caps, allowlists, route hashes, reserve, daily spend, and kill switch.
- `docs/RISK_POLICY.md` documents the pure risk gate and initial limits.
- `docs/PHASE_GATES.md` is the Gate 1-to-10 evidence checklist before Phase 1.
- `docs/DEPLOYMENTS.md` captures local/deployment repo policy and commands.
- `docs/RUNBOOK.md` lays out the Phase 0 daily control-plane check.
- `docs/TEST_MATRIX.md` maps unit, integration, and security requirements to pytest files.
- `docs/VERSION_LADDER.md` is the official v0.1-to-v1.0 build sequence. Do not start with live execution.
- `docs/REPO_ADOPTION_RED_FLAGS.md` is the external-repo filter. Do not clone or run repos that ask for unsafe wallet or routing patterns.
- `FOUNDER_AUTOMATION_PLAYBOOK.md` lays out the founder-led, automation-first phase plan from scanner to tiny live execution.
- `REAL_ARB_BOT_ARCHITECTURE.md` explains how the real bot should evolve, where smart contracts fit, and why simple Algorand arb can start with SDK-built atomic transaction groups.
- `ALGORAND_ARB_AGENT_RULES.md` distills the project-specific AI, UI/UX, and red-team rules for future Claude/Codex work.

Short version: this bot does not need a custom PyTeal contract for basic two-leg venue arb. It needs reliable off-chain search, exact SDK transaction construction, atomic grouping, dry-run receipts, wallet inventory checks, and balance reconciliation first. Smart contracts become relevant later for vaults, pooled capital, custom permissioning, or flash-liquidity style flows.

## Product Thesis

Use public repos as references, especially Arbitron-style projects and simple educational scanners, but build the controlled system here around official Tinyman, Pact, and Algorand SDKs.

The correct product is AlgoPulse Market Engine: market intelligence, scanner, route engine, paper trading, risk engine, execution controls, public dashboard, and PNET access layer. The Phase 0 signal is evidence and trust, not a black-box trading script.

## Version Ladder

The first version worth building is deliberately staged:

| Version | Scope |
| --- | --- |
| v0.1 | read-only scanner |
| v0.2 | Tinyman + Pact quote comparison |
| v0.3 | ALGO/USDC route engine |
| v0.4 | paper trading with 5s/30s recheck |
| v0.5 | dashboard showing delayed spreads |
| v0.6 | risk engine |
| v0.7 | unsigned transaction builder |
| v0.8 | signer service |
| v0.9 | one manual tiny trade |
| v1.0 | fully automated tiny own-funds micro-arb |

Live execution starts only at v0.9, manually, after scanner, quotes, route logic, paper replay, delayed dashboard, risk checks, unsigned groups, and signer isolation are already reviewed.

## Deployment Modes

Phase 0 promotes through three explicit modes:

- Local: mock data, scanner optional, no signer, no real submission.
- Staging: live scanner, live quotes, paper trading, no live signing, delayed dashboard.
- Production Phase 0: live scanner, route engine, paper trading, risk engine, admin dashboard, public delayed dashboard, isolated signer only after gates, tiny own-funds hot wallet only.

The same contract is exposed by `GET /api/config/public` and rendered in the dashboard.

## TestNet Readiness

Phase 3 now has a fail-closed TestNet configuration gate. It checks network-scoped endpoints and asset IDs, read-only Tinyman/Pact coverage, the 15-minute public delay, and disabled execution/signer flags. It does not connect or sign with a wallet.

Use `.env.testnet.example` as the local starting profile, then inspect `GET /api/testnet/readiness`. The profile intentionally remains blocked until a human configures a TestNet-only PNET ASA and reviews connect-only Pera/Defly integration. See `docs/TESTNET_READINESS.md`.

A read-only TestNet probe has confirmed algod/Indexer access and one Tinyman ALGO/USDC pool. Pact's configured TestNet API returned HTTP 502 during that probe and is now surfaced as degraded connector evidence instead of a healthy scan.

For sustained evidence, use the local soak runner (never remote-started):

```powershell
python -m algopulse.testnet_soak --once
python -m algopulse.testnet_soak --duration-hours 24 --interval-seconds 60
```

Inspect progress in the admin Control Room **TestNet Soak** panel or `GET /api/ops/testnet-soak`. A one-shot run does not complete the 24-hour gate.

## Repo Adoption Filter

Do not clone, run, fund, or integrate a repo that asks for `secret.json` wallet material, signer secrets in `config.py`, committed wallet `.env` files, wallet keys in frontend code, unlimited asset routing, missing app ID allowlists, missing daily loss caps, no kill switch, or no paper-trading history.

## Quick Start

Fresh local Python-first setup:

```bash
mkdir algopulse-market-engine
cd algopulse-market-engine
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install py-algorand-sdk fastapi uvicorn pydantic sqlalchemy psycopg2-binary redis python-dotenv
pip install git+https://github.com/tinymanorg/tinyman-py-sdk.git
pip install pactsdk
```

Inside this repo, use the pinned project install:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
python -m algopulse.cli scan --cycles 5
uvicorn algopulse.api:app --host 127.0.0.1 --port 8765
```

Then open:

```text
http://127.0.0.1:8765
```

SDK install notes:

- Tinyman's Python SDK is not published on PyPI and is installed from GitHub.
- Pact's Algorand Python SDK package is `pactsdk`.
- `sqlalchemy`, `psycopg2-binary`, and `redis` are included for the planned Postgres/logs/alerts service split. Phase 0 still runs on SQLite locally.

## Team Handoff And Version Control

Read these before handing the project to another developer or agent:

- `TEAM_HANDOFF.md` is the team source-of-truth map.
- `VERSION_CONTROL.md` defines branch, commit, PR, tag, and public/private repo policy.
- `CHANGELOG.md` records notable project changes.
- `docs/RELEASE_CHECKLIST.md` is the pre-release and live-safety gate.

## Commands

Run one mock scanner cycle:

```bash
python -m algopulse.cli scan --cycles 1
```

Run live read-only mainnet scanner:

```bash
set ALGO_PULSE_CONNECTORS=tinyman,pact
set ALGO_PULSE_ASSET_PAIRS=0-31566704,0-3169177585
set ALGO_PULSE_TARGET_ASSET_ID=3169177585
set ALGO_PULSE_USE_VESTIGE_DISCOVERY=true
python -m algopulse.cli scan --cycles 1
```

Run the synthetic 5 ALGO to 10 ALGO pipeline proof:

```bash
python -m algopulse.cli demo-run
```

Run a live-market readiness preflight:

```bash
set ALGO_PULSE_CONNECTORS=tinyman,pact
set ALGO_PULSE_ASSET_PAIRS=0-31566704,0-3169177585
python -m algopulse.cli readiness --scan
```

Run worker in dry-run execution mode:

```bash
set ALGO_PULSE_CONNECTORS=tinyman,pact
set ALGO_PULSE_TRADER_ADDRESS=YOUR_REVIEWED_HOT_WALLET
set ALGO_PULSE_ALLOW_NON_ALGO_STARTING_ROUTES=true
set ALGO_PULSE_ENABLE_LIVE_EXECUTION=false
set ALGO_PULSE_EXECUTE_APPROVED=false
python -m algopulse.cli worker --execute-approved
```

The following tiny-live command is future runbook material only. It is not authorized during Phase 3 and remains blocked until all prior gates and human reviews pass:

```bash
set ALGO_PULSE_ENABLE_LIVE_EXECUTION=true
set ALGO_PULSE_EXECUTE_APPROVED=true
python -m algopulse.cli worker --loop --execute-approved
```

Signer secrets must be provisioned only on the isolated signer host through a local secret manager, signer-host environment, or sealed file outside this repo.

Run tests:

```bash
pytest
```

## API

- `GET /health`
- `GET /api/health`
- `GET /api/config/public`
- `GET /api/session/wallet/{address}`
- `GET /api/pulse`
- `GET /api/pools`
- `GET /api/opportunities`
- `GET /api/paper-trades`
- `GET /api/live-trades`
- `GET /api/reconciliations`
- `GET /api/payment-verifications`
- `GET /api/refund-cases`
- `GET /api/risk-policy`
- `GET /api/demo-run`
- `GET /api/live-readiness`
- `GET /api/live-readiness?run_scan=true`
- `GET /api/admin/preflight` requires admin role headers
- `GET /api/reports/paper/daily`
- `POST /api/scan`
- `POST /api/verify-payment`
- `POST /api/refund-cases`
- `POST /api/refund-cases/{case_id}/status`
- `POST /api/user/pnet/fee-quote`
- `POST /api/user/pnet/fee-confirm`
- `POST /api/admin/scan-now` requires admin role headers
- `POST /api/admin/scanner/start` requires admin role headers
- `POST /api/admin/scanner/pause` requires admin role headers
- `POST /api/admin/routes/run` requires admin role headers
- `POST /api/admin/paper/start` requires admin role headers
- `POST /api/admin/dry-run/build` requires admin role headers
- `POST /api/admin/live/arm` requires admin role headers and remains blocked when live execution is disabled
- `POST /api/execute-best` requires `ALGO_PULSE_ALLOW_API_EXECUTION=true`

## Architecture

Current Phase 0 local app:

```text
Tinyman/Pact/Mock Connector
  <- Vestige larger-pool discovery for PNET
  -> Scanner
  -> Route Engine
  -> Risk Engine
  -> Paper Trade Log
  -> Optional Atomic Execution Builder
  -> SQLite Store
  -> FastAPI Dashboard
```

Target production split:

```text
Pool Scanner
  -> Quote Engine
  -> Route Engine
  -> Simulator / Paper Trader
  -> Risk Engine
  -> Unsigned Executor
  -> Isolated Signer
  -> Algorand Network

All services
  -> Postgres
  -> Logs
  -> Alerts
  -> Delayed public dashboard
```

The isolated signer is the hard security boundary. The public dashboard should read only delayed/redacted data.

## Database Tables

The current SQLite store now mirrors the minimum production Postgres shape:

- `assets`: ASA/ALGO metadata, verification, allowlist, freeze/clawback flags
- `venues`: Tinyman, Pact, and future venue metadata
- `pools`: stable pool identity, venue/app IDs, pair assets, fee bps, active status
- `pool_snapshots`: time-series reserves, prices, block round, captured time
- `quotes`: route-leg quote records with venue, pool, input/output assets, input size, expected output, fee estimate, price impact, block round, capture time, and expiry
- `opportunities`: route candidates, profit breakdown, confidence score, skip reason, status, route JSON
- `paper_trades`: candidate paper-trade replay records with would-execute/skip status, delayed 5s/30s checks, simulated output, quote decay, and profit-delta audit fields
- `risk_decisions`: approval/rejection receipt for each scanned route
- `live_trades`: dry-run and submitted execution receipts
- `service_health`: scanner/worker/signer health snapshots
- `alerts`: operational alerts for stale scans, signer rejects, balance drift, low fee balance, and refund review

SQLite is the Phase 0 local store. Production should migrate this shape to Postgres before multiple services or workers run.

## Read-Only Scanner Contract

The scanner is read-only. It must run without signer secret material or a signing service.

Each pool scan collects:

- venue
- pool ID and app ID
- asset A and asset B
- reserves
- fee bps
- liquidity estimate
- spot price
- block round
- timestamp
- data freshness

Exit gate for Phase 0A: run the scanner for 24 hours with no crashes, no signer secret material configured, and no submitted transactions. Only after that should dry-run execution and isolated signer work advance.

## Quote Engine Sizes

The quote engine should compare standard ALGO-sized probes:

- 1 ALGO
- 5 ALGO
- 10 ALGO
- 25 ALGO
- 50 ALGO
- 100 ALGO

These are quote/paper-trade probe sizes, not automatic live execution sizes. Live execution remains capped separately by `ALGO_PULSE_MAX_LIVE_TRADE_SIZE`.

Every stored quote row must include:

- venue
- pool
- input asset
- output asset
- input amount
- expected output
- price impact
- fee estimate
- block round
- captured_at
- expires_at

## Route Engine Shapes

The route engine currently generates scanner and paper-trade candidates for:

- `ALGO -> USDC on Tinyman -> ALGO on Pact`
- `ALGO -> ASA on Pact -> ALGO on Tinyman`
- `ALGO -> ASA -> USDC -> ALGO`
- `ALGO -> USDC -> ASA -> ALGO`

The first two are two-leg venue-arb routes over the same pair. The last two are three-leg triangle routes through the ALGO/USDC anchor. Vestige-discovered target pools are merged with configured anchor pairs so the scanner can complete triangles instead of seeing only isolated PNET pairs.

Live atomic execution is still intentionally limited to two-leg routes. Three-leg routes are stored, risk-scored, and paper-traded only until the executor is upgraded and reviewed for 3-leg transaction groups.

## Opportunity Breakdown Contract

Every opportunity must calculate and store:

- gross profit
- estimated network fees
- DEX fee estimate from quoted route legs
- max and total price impact
- slippage/safety buffer
- net expected profit
- confidence score
- skip reason when rejected

DEX fees are already included in the AMM quote outputs, so they are reported for auditability and are not subtracted a second time from net expected profit.

## Paper Trading Contract

Paper trading runs before real funds and records every route candidate, not only approved routes.

For each candidate, the bot must:

- capture the original route quote and opportunity breakdown
- decide `would_execute=true` only when risk approved
- store rejected candidates with a clear skip reason
- recheck fresh pool state after 5 seconds and 30 seconds on later scanner cycles
- estimate the simulated actual output from the refreshed pool state
- record quote decay from expected output to simulated output
- record expected-vs-simulated profit delta

This is still no-funds mode. Paper replay must not require signer secret material, signing, custody, or submitted transactions.

## Automation Policy

Allowed to run automatically:

- scanning pools
- comparing quotes
- recording paper trades
- rejecting routes through risk rules
- constructing unsigned transaction groups

Signing is different. Automated signing belongs only inside a tiny, isolated, policy-limited signer that revalidates every unsigned group before signing. The main scanner/API process should not hold signer secrets and should not be able to bypass signer policy.

## Execution Dry-Run Contract

Before live trading, the executor builds unsigned Algorand atomic transaction groups only from a risk-approved opportunity. The group receives a group id for inspection, but the default path does not sign or submit it.

Step 8 dry-run receipts must show:

- `dry_run=true`
- `unsigned_group=true`
- `signed=false`
- `submitted=false`
- transaction count
- max group size from the installed Algorand SDK `TX_GROUP_LIMIT`
- group size pass/fail
- expected fee and conservative output
- balance reconciliation plan

The SDK constant currently reports `TX_GROUP_LIMIT=16`; any route that would build more than 16 transactions is rejected before signing can be reached. `ALGO_PULSE_UNSIGNED_EXECUTOR_ONLY=true` stays on until the isolated signer review is complete.

## Isolated Signer Contract

Step 9 adds `src/algopulse/signer.py` as the tiny policy-limited signer boundary. It is separate from route discovery and the main executor.

The signer:

- holds hot-wallet key material only inside signer policy
- accepts typed unsigned transaction groups plus narrow execution metadata
- rejects arbitrary executor instructions such as `instructions`, `command`, `prompt`, or `tool`
- validates route hash allowlist
- validates app IDs and asset IDs against allowlists
- validates actual app IDs, asset IDs, input amount, transaction count, and group id against the route intent supplied by the unsigned executor
- validates max input amount, max group fee, transaction types, atomic group size, sender wallet, no rekey/close-out, and wallet reserve
- checks the kill switch
- logs every approval or rejection to an append-only JSONL audit log without storing signed transaction blobs

The main executor no longer signs or submits directly. If live flags are armed and unsigned-only is disabled, it still returns a dry-run receipt with `signer_handoff` and `signing_blocked=true`.

Signer env defaults stay locked:

- `ALGO_PULSE_SIGNER_ENABLED=false`
- `ALGO_PULSE_SIGNER_KILL_SWITCH=true`
- `ALGO_PULSE_SIGNER_ALLOWED_ROUTE_HASHES=`
- `ALGO_PULSE_SIGNER_AUDIT_LOG=./data/signer-audit.jsonl`
- `ALGO_PULSE_SIGNER_MIN_WALLET_RESERVE_ALGOS=0.2`

## Tiny Live Execution Gate

Step 10 is documented in `STEP10_TINY_LIVE_EXECUTION_RUNBOOK.md`.

Tiny live mode is a readiness gate for the first ALGO/USDC-only execution:

- new hot wallet with 100-250 ALGO
- ALGO/USDC only
- max trade size 10 ALGO
- daily loss limit 20 ALGO
- daily submitted trade cap 20
- max route length 3 swaps
- max concurrent execution 1
- manual first route hash approval
- Lora txid recorded
- expected-vs-actual reconciliation confirmed before tiny automation

Use `.env.tiny-live.example` as the starting template. `ALGO_PULSE_TINY_LIVE_ALLOW_AUTOMATION=false` stays false until the first live route is manually verified and reconciled.

## Risk Engine Contract

The risk engine is intentionally supposed to reject most opportunities. Scanner/paper mode can observe broad markets, but approval requires every starting rule to pass:

- own funds only
- asset allowlist only
- app ID allowlist only
- quote freshness under 5 seconds
- profit buffer at least 2x expected total fees
- max price impact around 50 bps for major pairs
- minimum profit greater than both 0.25 starting-asset units and 0.35% of trade size
- max trade size capped at 10-25 ALGO through `ALGO_PULSE_MAX_LIVE_TRADE_SIZE`
- max daily loss 20 ALGO
- max daily submitted trades 20
- max route length 3 swaps
- max concurrent execution 1

Missing reviewed app IDs means a route can still be discovered and paper-traded, but it should not be approved for execution.

## Connector Roadmap

Initial executable venues:

- Tinyman
- Pact

Later expansion:

- Vestige data for richer market intelligence, discovery, pool ranking, and validation
- Folks routes when there is a safe SDK/API path for executable route construction
- other Algorand AMMs after connector math, transaction construction, app IDs, fees, slippage, and balance reconciliation are reviewed

Vestige is a data/discovery source, not an execution venue. Tinyman and Pact are the first venues where the bot should try to build executable swap groups.

## Route Pair Policy

Production route expansion should start with the deepest and easiest-to-reconcile pairs:

- ALGO / USDC
- ALGO / major ASAs
- USDC / major ASAs

Later, after liquidity verification:

- goBTC routes
- goETH routes

Major ASAs should be treated as an allowlist, not an open wildcard. Add an ASA only after it has enough pool depth, realistic volume, stable quote behavior, reviewed app IDs, wallet opt-in readiness, and clean balance reconciliation. Wrapped majors like goBTC and goETH can look attractive, but they should stay disabled until route size, slippage, and exit liquidity are proven.

## Execution Safety

The worker enforces:

- fresh approved route only
- unsigned group construction only by default via `ALGO_PULSE_UNSIGNED_EXECUTOR_ONLY=true`
- max route age cutoff via `ALGO_PULSE_MAX_ROUTE_AGE_SECONDS`
- max live trade size
- max route length via `ALGO_PULSE_MAX_ROUTE_LEGS`
- configurable probe sizes via `ALGO_PULSE_TRADE_SIZES`
- minimum net-profit floor after DEX quotes, estimated network fees, and safety buffer
- minimum profit bps floor so tiny gross spreads are not traded for volume
- 2x expected-fee profit buffer via `ALGO_PULSE_MIN_FEE_BUFFER_MULTIPLIER`
- app ID allowlist via `ALGO_PULSE_ALLOWED_APP_IDS`
- asset allowlist via `ALGO_PULSE_ALLOWED_ASSET_IDS` or configured route pairs
- ALGO-starting routes can submit after live flags are armed
- non-ALGO starting routes require `ALGO_PULSE_ALLOW_NON_ALGO_STARTING_ROUTES=true` for atomic dry-run review
- non-ALGO live signing stays blocked unless `ALGO_PULSE_ALLOW_NON_ALGO_LIVE_SUBMISSION=true` is explicitly reviewed
- main executor never signs directly; it produces signer handoff metadata only
- main executor requires `status=approved` plus a passing `risk_rules` receipt before building a group
- isolated signer policy must approve route hash, route intent, app IDs, asset IDs, fees, transaction types, wallet reserve, and kill switch before any signed blobs are produced
- wallet opt-in verification
- wallet input-asset inventory and spendable ALGO fee-budget verification
- max 16 transaction group size
- no rekey, payment close, or asset close-out fields
- expected app IDs and ASA IDs only
- first-leg minimum output used as second-leg input
- conservative final profit after fees
- pre-trade balance snapshot and post-trade reconciliation for submitted trades
- max group fee ceiling
- daily submitted-trade loss gate
- daily submitted-trade count gate
- one execution slot by default
- disabled public API execution by default

Use a tiny hot wallet. Never accept user deposits.

Provision signer secrets only through a host secret manager, signer-host environment, or sealed file outside this repo. Do not put signer secrets in shell history, browser env, docs, screenshots, or repo-managed files.

Default profit guard settings:

```bash
ALGO_PULSE_MIN_NET_PROFIT_ALGOS=0.25
ALGO_PULSE_MIN_NET_PROFIT_INPUT_UNITS=0.25
ALGO_PULSE_MIN_PROFIT_BPS=35
ALGO_PULSE_ESTIMATED_NETWORK_FEE_ALGOS=0.006
ALGO_PULSE_SAFETY_BUFFER_BPS=15
ALGO_PULSE_MIN_FEE_BUFFER_MULTIPLIER=2
ALGO_PULSE_MAX_PRICE_IMPACT_BPS=50
ALGO_PULSE_TRADE_SIZES=1,5,10,25,50,100
ALGO_PULSE_MAX_ROUTE_AGE_SECONDS=5
ALGO_PULSE_MAX_ROUTE_LEGS=3
ALGO_PULSE_MAX_DAILY_LOSS=20
ALGO_PULSE_MAX_DAILY_TRADES=20
ALGO_PULSE_MAX_CONCURRENT_EXECUTION=1
ALGO_PULSE_REQUIRE_APP_ID_ALLOWLIST=true
ALGO_PULSE_UNSIGNED_EXECUTOR_ONLY=true
```

The scanner rejects routes that do not clear both the net-profit floor and the bps floor. For non-ALGO paper scans, the absolute net-profit floor is applied in the route's starting asset units; the bps floor is the cross-asset guard. The execution builder now separates starting-asset profit from ALGO fee budget so PNET routes are not treated as if PNET units were ALGO.

ALGO-starting routes check final minimum ALGO output after slippage and real transaction fees before signing. Non-ALGO routes can be built as dry-run atomic groups for review when enabled, but live signing should stay disabled until an ALGO-equivalent profit/reconciliation layer is reviewed.

## Live-Market Readiness

The dashboard includes a live readiness panel backed by `/api/live-readiness`. It checks live connector configuration, observed venues, scan freshness, hot-wallet funding, required ASA opt-ins, daily loss room, route availability, and whether the current best approved route can build a safe atomic dry-run group.

Readiness checks never submit transactions. Even if live execution flags are enabled, the readiness preflight uses a disarmed executor.

The readiness response and dashboard also expose the active profit guard and max quote age. A zero or disabled profit guard makes the bot not live-ready.

## Balance Reconciliation

Execution receipts are stored through `/api/live-trades`. Balance reconciliation receipts are stored through `/api/reconciliations`.

Dry-run plans record expected balance deltas from conservative minimum output. Submitted trades also capture post-confirmation balances and compare actual deltas against the minimum expected deltas. If actual deltas fall below the expected floor, the receipt is marked as a variance.

## Algorand Payment Verification

The dashboard includes a read-only payment verification panel backed by `/api/verify-payment`.

The verifier looks up a txid through the configured Algorand indexer and checks:

- confirmed round and minimum confirmations
- ALGO payment or ASA transfer type
- expected receiver
- expected raw/display amount
- optional sender
- optional note text or note prefix
- no rekey field
- no payment close or asset close-out field

Every verification attempt is stored locally and exposed through `/api/payment-verifications`.

This is verification only. It does not custody funds, create invoices, submit transactions, or enable live execution.

## Refund / Failure Handling

The dashboard includes a manual refund/failure queue backed by `/api/refund-cases`.

Refund cases can be created from an existing payment verification receipt or as a failure-only record. The decision engine classifies cases as:

- `refund_ready`: a verified inbound payment has sender, amount, and confirmed round.
- `needs_review`: an inbound payment reached the expected receiver but did not fully verify.
- `not_refundable`: no confirmed sender/amount or no receipt is attached.

The queue never sends funds. Operators must manually review service delivery, duplicate cases, and payment details before sending any refund. If a refund is sent, record the refund txid through `/api/refund-cases/{case_id}/status`.

## PNET Pool Discovery

Set `ALGO_PULSE_USE_VESTIGE_DISCOVERY=true` with `ALGO_PULSE_TARGET_ASSET_ID=3169177585` to have the scanner pull the larger PNET pools from Vestige composition data. The discovery stage ranks pools by target-asset reserve, prioritizes ALGO/PNET and USDC/PNET because they are more execution-useful, and then hands those asset pairs to the Tinyman/Pact connectors.

Vestige is used for discovery and market context. Tinyman/Pact SDK calls remain the source for executable pool reserves and transaction construction.

For the initial PNET testing universe from the Vestige pool screenshot, set:

```bash
ALGO_PULSE_VESTIGE_PINNED_PAIR_ASSET_IDS=1290751153,3436365167,1893942045,31566704,1390638935,2644742542,3249403496,3427156477,1119722936,3410350791,846652486,3427041827,1674484158,3227174563
ALGO_PULSE_VESTIGE_INCLUDE_FALLBACK_PAIRS=false
```

See `INITIAL_TEST_POOLS.md` for the symbol-to-ASA mapping.

## Demo Proof Run

The dashboard includes a synthetic "5 To 10 Test Run" panel and `/api/demo-run` endpoint. It proves the presentation and pipeline shape for a route that starts with 5 ALGO and ends with 10 ALGO.

It is intentionally labeled synthetic and uses no live market data or funds.
