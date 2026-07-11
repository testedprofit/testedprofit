# Changelog

All notable changes should be recorded here.

## [Unreleased]

### Added

- Team handoff index in `TEAM_HANDOFF.md`.
- Version-control policy in `VERSION_CONTROL.md`.
- Release checklist in `docs/RELEASE_CHECKLIST.md`.
- Pull request template and CI workflow scaffolding.
- Architecture decision record for safe-by-default Phase 0 execution.
- Operator-style dashboard summary rail with readiness, route gate, wallet, scan age, and profit gate state.
- Algorand payment verification backend, API endpoints, dashboard panel, local receipts, and unit tests.
- Refund/failure handling manual operator queue, API endpoints, dashboard panel, and tests.
- Target production service chain with Postgres, logs, alerts, delayed dashboard, unsigned executor, and isolated signer boundaries.
- Connector roadmap clarifying Tinyman/Pact as initial executable venues and Vestige/Folks/other AMMs as later expansion.
- Route-pair policy prioritizing ALGO/USDC, ALGO/major ASAs, USDC/major ASAs, with goBTC/goETH gated by liquidity verification.
- Automation-boundary policy allowing unattended scanning/quoting/paper trading/risk rejection/unsigned construction while isolating signing.
- Security red lines forbidding AI/frontend wallet keys, main-wallet signing, unknown signers, user funds, universal asset trading, and predatory MEV.
- Minimum production database table spine in SQLite: pools, quotes, risk decisions, service health, and alerts added alongside existing market tables.
- Read-only scanner contract with liquidity/freshness capture, lazy live executor construction, and 24-hour no-key exit gate.
- Standard quote probe sizes set to 1, 5, 10, 25, 50, and 100 ALGO while keeping live trade caps separate.
- Quote storage now preserves venue, pool, input/output assets, input size, expected output, price impact, fee estimate, block round, capture time, and expiry for each route leg.
- Tinyman and Pact live pool scans now stamp pool/quote rows with the current algod round instead of a hardcoded zero when node status is available.
- Route engine now generates two-leg venue-arb candidates and three-leg ALGO/ASA/USDC triangle candidates for scanner, risk, quote storage, and paper-trade review.
- Vestige-discovered watchlists now retain configured routing anchors such as ALGO/USDC so triangle routes can be completed.
- Opportunity rows now persist gross profit, network fee estimate, DEX fee estimate, price impact, slippage buffer, net expected profit, confidence score, and skip reason.
- Dashboard opportunity cards now show the profit breakdown for each displayed route.
- Paper trading now records every candidate with would-execute/skip status before any live-fund path.
- Delayed paper replays now check fresh pool state at 5 seconds and 30 seconds and store simulated final output, quote decay, and expected-vs-simulated profit.
- Dashboard paper-trade rows now show expected profit, 5s/30s replay status, quote decay, and skip reasons.
- Risk engine now enforces Step 7 gates for quote freshness, 2x fee buffer, reviewed app IDs, 50 bps impact default, route length, own-funds-only policy, daily trade cap, and single concurrent execution.
- Readiness and dashboard risk panels now expose app-ID allowlist state, fee buffer, route length, daily trade count, and concurrency limits.
- Execution dry-run mode now emits unsigned-group receipts, blocks signing with `ALGO_PULSE_UNSIGNED_EXECUTOR_ONLY=true`, and enforces the Algorand SDK transaction group limit.
- Isolated signer policy module with kill switch, route-hash allowlist, app/asset validation, fee/input/reserve caps, arbitrary instruction rejection, and JSONL audit logging.
- Dashboard live readiness now exposes signer disabled/kill-switch/route-hash state.
- Executor now requires a risk-approved opportunity and passing `risk_rules` receipt before building a group.
- Signer now rejects groups that do not match route intent for app IDs, asset IDs, input amount, tx count, or group id.
- Tiny-live readiness gates, dashboard card, `.env.tiny-live.example`, and Step 10 runbook for ALGO/USDC-only first execution.
- Python-first setup docs and dependency manifests now include pydantic, SQLAlchemy, psycopg2-binary, Redis, Tinyman GitHub install, and Pact `pactsdk`.
- Operator-safe `.env.example` using deployment-facing env names, with execution/signing disabled and the kill switch on by default.
- Signer secret loading from signer-host-only env or an external sealed file path, with repo-local secret files rejected.
- v0.1-to-v1.0 version ladder documenting the read-only-first path from scanner to tiny own-funds automation.
- Dashboard build-path panel showing scanner, quote, route, paper, dashboard, risk, unsigned builder, signer, manual tiny trade, and v1.0 automation gates.
- Repo adoption red-flag checklist for rejecting unsafe Web3 bot repos before they touch AlgoPulse.
- Product thesis defining AlgoPulse Market Engine as market intelligence, scanner, route engine, paper trading, risk engine, execution controls, public dashboard, and PNET access layer.
- Role-based PNET dashboard cockpit with wallet-state UI, admin/user/guest layouts, route console, access gate, fee modal, and live-arm confirmation stub.
- Non-admin role-gate UX now marks admin nav surfaces as locked and explains which platform controls are unavailable.
- Backend mock control-plane endpoints now enforce admin role headers before queuing safe scanner/paper/dry-run control jobs.
- Control-plane docs for Codex handoff, API contract, risk policy, deployments, and Phase 0 runbook.
- Public config env keys and `/api/config/public` dashboard config hydration.
- Pure route math helpers with deterministic route hashing, constant-product quotes, and profit breakdown tests.
- Pure risk-rule evaluator with tests for stale quotes, fee buffer, daily caps, and concurrency rejection.
- PNET market-data fee confirm stub, wired dashboard quote modal, and backend-enforced admin preflight checklist.
- Aggregate paper-trading daily report endpoint and dashboard panel.
- Phase Gate 1-to-10 checklist published through public config, docs, and dashboard.
- Deployment-mode contract for local, staging, and production Phase 0 published through public config, docs, and dashboard.
- Role-gated admin alert catalog for scanner, connector, quote, route, storage, risk, signer-boundary, wallet, loss-limit, live-trade, and reconciliation failures.
- PNET access-check, payment-intent, on-chain txid verification, receipt-recording flow for market-data fees.
- Explicit Phase 0 unit, integration, and security test suites plus test-matrix documentation.
- Role-gated admin policy catalog for max input amount, transaction fee, asset/app allowlists, transaction types, route hash approval, daily spend, wallet reserve, and kill switch.
- Public product capability catalog for market intelligence, scanner, route engine, paper trading, risk engine, execution controls, public dashboard, and PNET access layer.
- Production-readiness, observability, and PNET fee-flow scaffolding with CI secret guardrails and pure guardrail tests.
- Admin Control Room with source-labeled pipeline telemetry, phase ladder, activity tape, counters, rejection funnel, paper scoreboard, risk inspector, environment matrix, and evidence drawer.
- Explicit NOT LIVE READY production status in `/api/ops/*`, Control Room, README, and handoff docs.
- Control Room live-map heartbeat with source-labeled node pulses, count deltas, activity tape motion, and paper/risk evidence labels.
- Control Room Phase 0A-0G operator ladder with Live Micro shown as locked while detailed evidence gates remain available through the ops API.
- Structured pipeline evidence rows for scanner pools, quote counts, route candidates, paper simulations, risk rejection reasons, and signer disabled/locked state.
- Production readiness summary card and `/api/ops/*` payload now showing computed current phase, overall readiness, next gate, and blocking items.
- Admin Opportunity Replay Lab with stored paper-trade timelines, 5s/30s quote-decay inspection, route comparison mode, source labels, and locked live-execution state.
- Production Readiness Engine with `production_gates`, persisted `production_evidence`, computed pass/fail gate scoring, `/api/ops/production-readiness`, and an admin Readiness page.
- Route Forensics engine with `route_forensics`, complete route-decision audit records, `/api/ops/route-forensics`, and an admin Forensics page for route inspection, comparison, confidence math, and decision trees.
- Route Confidence Calibration with paper-trade confidence/success storage, `/api/ops/confidence-calibration`, bucketed success-rate analysis, quote-decay/profit averages, and an admin Confidence Analysis page.
- Opportunity Decay Analytics with `opportunity_decay`, 5s/30s/60s expected-profit checkpoints, `/api/ops/opportunity-decay`, and an admin Half-Life dashboard for average/median half-life, fastest/slowest decay, pair/venue/type breakdowns, and timeline charts.
- Market Pulse Heatmap with pair/venue/time opportunity-density analytics, spread frequency, average spread, route count, opportunity half-life, paper performance, `/api/ops/market-heatmap`, and an admin Heatmap page.
- Daily Market Intelligence Reports with persisted `market_intelligence_reports`, JSON/Markdown exports, archive listing, market summary, top pairs/spreads, liquidity changes, opportunity counts, route/paper performance, scanner health, risk events, and a Research Archive page.
- Failure Simulation Mode with `/api/ops/failure-lab`, admin Failure Lab UI, connector/storage/route/signer-boundary/allowlist/loss-limit scenarios, expected-vs-actual response evidence, generated alerts, affected services, and graceful-degradation proof.
- Data Provenance Viewer with `/api/ops/provenance`, traceable dashboard metric cards, metric catalog, and lineage through source data, quotes, pool snapshots, route calculations, and risk decisions.
- Production Evidence System with `evidence_records`, `/api/ops/evidence`, generated component proof records, category/service/status filters, metadata inspection, and an admin Evidence Viewer.
- Product Validation Engine with approved user-action taxonomy, `user_actions`, evidence-backed `decision_events`, `/api/events/user-action`, `/api/ops/product-validation`, funnel analytics, persona validation, feature utility ranking, dead-feature detection, and an admin `Why Return` dashboard.

### Changed

- Dashboard first viewport is denser and cleaner, with lower panels arranged in two columns on desktop.
- Radar view keeps the visual identity but gives more room to operational status and safety signals.
- Main executor no longer signs or submits directly; armed live flags produce signer handoff metadata and remain blocked until the isolated signer path is reviewed.
- Deployment docs and handoff checklists now avoid repo-managed signer secret placeholders and point secret provisioning outside the project tree.
- Dashboard admin controls now call backend mock control-plane endpoints and display backend accept/reject messages.
- Paper-trading readiness gates now use unique UTC collection days instead of treating candidate volume as a 7-day evidence window.

## [0.1.0] - 2026-06-21

### Added

- Phase 0 Algorand market scanner and dashboard.
- Live Tinyman/Pact read-only scanning.
- Vestige discovery for larger PNET pools.
- Synthetic 5 ALGO to 10 ALGO demo proof.
- Guarded two-leg atomic dry-run execution path.
- Stale-route rejection before wallet checks.
- Positive net-after-fees risk gate.
- Balance reconciliation receipt API and dashboard panel.
- Live-readiness preflight endpoint and dashboard panel.
- PNET-scoped dashboard metrics.
- Docker and docker-compose starter files.

### Security

- Live execution disabled by default.
- Public API execution disabled by default.
- Signer secrets and real env files ignored by git.
- Transaction validation rejects rekey and close-out fields.
