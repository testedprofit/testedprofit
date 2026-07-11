# Codex Handoff

## Current Safe Scope

This repo is in Phase 0 control-plane review. Codex work is limited to:

- UI/UX for the PNET and AlgoPulse dashboard
- backend role checks for mock control actions
- market-data fee quote and confirm stubs
- route math and risk math that can be tested without network calls
- delayed route intelligence and aggregate paper-trading reports

Do not change signer custody, hot-wallet execution, live transaction submission, or isolated signer policy in a UI/control-plane pass.

## Latest Control-Plane Additions

- Public config endpoint: `GET /api/config/public`
- Public product capability catalog in `GET /api/config/public`
- Production readiness scaffolding in `docs/PRODUCTION_READINESS.md`, `docs/OBSERVABILITY.md`, `docs/PNET_FEE_FLOW.md`, `.github/workflows/ci.yml`, and `tests/test_production_readiness.py`
- Admin visual Control Room in the `Control Room` tab with read-only `/api/ops/*` telemetry endpoints and mock-labeled frontend fallbacks
- Production Readiness Engine in `/api/ops/production-readiness`, backed by `production_gates` and `production_evidence`, with readiness calculated from actual pass/fail evidence instead of hardcoded percentages
- Control Room Phase 0A-0G operator ladder now uses the same computed production evidence as the Readiness tab
- Control Room live-map heartbeat with source-labeled node pulses, count deltas, activity events, and paper/risk evidence motion
- Structured service evidence contract in `/api/ops/pipeline`: scanner pools scanned, quote count, route candidates, risk rejection reasons, paper simulations, and signer disabled/locked state
- Explicit `Production Status: NOT LIVE READY` banner in the Control Room and `/api/ops/*` production status contract
- Admin Opportunity Replay Lab in the `Replay Lab` tab with `/api/ops/replay-lab`, stored paper-trade timelines, 5s/30s quote-decay inspection, route comparison mode, and live execution locked/disarmed
- Admin Route Forensics in the `Forensics` tab with `/api/ops/route-forensics`, persisted `route_forensics` audit rows, confidence math, decision trees, route comparison, and complete explanations for stored opportunities
- Admin Route Confidence Calibration in the `Confidence` tab with `/api/ops/confidence-calibration`, stored paper-trade buckets, success-rate analysis, quote-decay/profit averages, sample trade evidence, and live execution/signer untouched safety flags
- Admin Opportunity Half-Life dashboard in the `Half-Life` tab with `/api/ops/opportunity-decay`, persisted `opportunity_decay` rows, 5s/30s/60s expected-profit checkpoints, decay timeline, fastest/slowest decay, and pair/venue/route-type breakdowns
- Admin Market Pulse Heatmap in the `Heatmap` tab with `/api/ops/market-heatmap`, stored pair/venue/time buckets, density intensity, spread frequency, average spread, route count, half-life, and paper-performance analytics
- Daily Market Intelligence Reports in the `Research` tab with `/api/reports/market/daily`, `/api/reports/market/archive`, JSON/Markdown exports, persisted `market_intelligence_reports`, and stored market summary/top pairs/top spreads/liquidity/route/paper/scanner/risk sections
- Admin Failure Lab in the `Failure Lab` tab with `/api/ops/failure-lab`, mock-labeled resilience simulations for connector outages, stale quotes, database unavailability, route crashes, signer unavailability, unknown assets/apps, and daily-loss breaches
- Admin Data Provenance Viewer in the `Provenance` tab with `/api/ops/provenance`, click-to-trace metric cards, and lineage from dashboard value to source data, quote, pool snapshot, route calculation, and risk decision
- Admin Production Evidence System in the `Evidence` tab with `/api/ops/evidence`, `evidence_records`, generated component proof for scanner/quotes/routes/paper/risk/dry-run/execution/receipts, and category/service/status filters
- Admin Product Validation Engine in the `Why Return` tab with `/api/ops/product-validation`, `user_actions`, `decision_events`, approved action taxonomy, evidence-backed decision rules, persona validation, funnel analytics, feature utility ranking, dead-feature detection, and safe `POST /api/events/user-action` collection
- Milestone receipts with screenshots and short summaries under `docs/milestones/`
- Deployment-mode contract for local, staging, and production Phase 0 in public config and dashboard UI
- Admin preflight endpoint: `GET /api/admin/preflight`
- Admin alert catalog endpoint: `GET /api/admin/alerts/catalog`
- Admin hard-stop policy catalog endpoint: `GET /api/admin/policy/catalog`
- Safe admin queue endpoints under `/api/admin/*`
- PNET market-data fee quote: `POST /api/user/pnet/fee-quote`
- PNET access check: `POST /api/user/pnet/access-check`
- PNET market-data fee confirm: `POST /api/user/pnet/fee-confirm`, using mock txids for local review and on-chain verifier for real txids
- Paper-trading daily report: `GET /api/reports/paper/daily`
- Pure route math: `src/algopulse/route_math.py`
- Pure risk rules: `evaluate_risk_rules` in `src/algopulse/risk.py`

## QA Command

```powershell
python -m pytest -q
```

Frontend review should run the FastAPI app on the current local port and verify the dashboard still loads, admin/user/guest gates render, PNET fee quote/confirm stubs work, and admin controls show backend accept/reject messages.

Latest Control Room QA note: admin Control Room rendered on `http://127.0.0.1:8766/` with nine service nodes, nine node-motion strips, seven activity events, source badges, explicit NOT LIVE READY production status, live execution locked, evidence drawer, live-map heartbeat/deltas, day-based 7-day paper gate, no console errors, and no horizontal overflow at desktop or 390px mobile width. Guest mode cannot enter the admin cockpit and sees no Control Room service nodes.

Latest Replay Lab QA note: admin Replay Lab rendered on `http://127.0.0.1:8766/` with 30 stored replay cards, T0/T+5s/T+30s checkpoints, timeline scrub, route comparison cards, stored source badges, live execution locked/disarmed, no console errors, and no horizontal overflow at desktop or 390px mobile width.

Latest Readiness Engine QA note: admin Readiness tab rendered on `http://127.0.0.1:8766/` with computed evidence score, gate tree, blockers, evidence records, source badges, and live execution still disarmed. The score came from `/api/ops/production-readiness`, not frontend constants.

Latest Route Forensics QA note: admin Forensics tab rendered on `http://127.0.0.1:8766/` with 5,894 stored route explanations, 50 loaded route cards, 3 comparison cards, 7 decision-tree steps, risk-rule evidence, stored source badges, locked read-only execution boundary, no console errors, and no horizontal overflow at desktop or 390px mobile width.

Latest Confidence Calibration QA note: admin Confidence tab rendered on `http://127.0.0.1:8766/#confidence` with stored source labels, 6 confidence buckets, 1,968 resolved paper trades, 12 sample paper-trade evidence rows, calibration verdict, live execution/signer untouched safety chips, guest lock, no console errors, and no desktop/390px mobile overflow. Screenshot receipt saved at `docs/milestones/screenshots/2026-06-22-route-confidence-calibration.png`.

Latest Opportunity Decay QA note: admin Half-Life tab rendered on `http://127.0.0.1:8766/#decay` with stored source labels, 1h/24h/7d controls, 2,952 stored opportunity-decay rows in the 24h view, 24 timeline buckets, 25 recent decay records, 3 breakdown cards, live execution/signer untouched safety chips, guest lock, no console errors, and no desktop/390px mobile overflow. The 1h view correctly rendered unavailable because no local records existed in that window, and existing migrated data has 0 completed 60s samples until new paper checkpoints mature. Screenshot receipt saved at `docs/milestones/screenshots/2026-06-22-opportunity-decay-analytics.png`.

Latest Market Heatmap QA note: admin Heatmap tab rendered on `http://127.0.0.1:8766/` with stored source labels, 1h/6h/24h/7d controls, 16 stored pair/venue/time density cells in the 24h view, selected hot-cell inspector, paper-performance analytics, Analytics-only/Live execution untouched/Signer untouched safety chips, no console errors, and no page-level horizontal overflow at desktop or 390px mobile width.

Latest Research Archive QA note: Research tab rendered on `http://127.0.0.1:8766/#research` with stored source labels, JSON/Markdown export links, two persisted daily reports, 2026-06-21 selected, 5,384 opportunities, ALGO/USDC top pair, 2.0325% 30s paper win rate, market summary, top pairs, top spreads, liquidity changes, risk events, and live execution/signer untouched safety chips. Browser QA found no mock fallback, no console errors, and no horizontal overflow at desktop or 390px mobile width. Screenshot receipt saved at `docs/milestones/screenshots/2026-06-22-daily-market-intelligence-report.png`.

Latest Failure Lab QA note: admin Failure Lab rendered on `http://127.0.0.1:8766/#failure` with nine mock-labeled resilience simulations, expected-vs-actual response cards, generated alerts, affected services, live execution/signer untouched safety chips, no console errors, and no horizontal overflow at desktop or 390px mobile width. Guest mode cannot enter the Failure Lab. Screenshot receipt saved at `docs/milestones/screenshots/2026-06-22-failure-simulation-mode.png`.

Latest Data Provenance QA note: admin Provenance tab rendered on `http://127.0.0.1:8766/#provenance` with 17 traceable metrics, six lineage steps, stored source labels, quote/pool-snapshot/route-calculation/risk-decision chain, drawer click, guest lock, live execution/signer untouched safety chips, no console errors, and no desktop/390px mobile overflow. Screenshot receipt saved at `docs/milestones/screenshots/2026-06-22-data-provenance-viewer.png`.

Latest Production Evidence QA note: admin Evidence tab rendered on `http://127.0.0.1:8766/#evidence` with 23 stored evidence records, 8 categories, 9 services, category/service/status filters, route filter reducing to 3 route records, fail-status filter reducing to 2 failure records, metadata inspector, guest lock, live execution/signer untouched safety chips, no console errors, and no desktop/390px mobile overflow. Screenshot receipt saved at `docs/milestones/screenshots/2026-06-22-production-evidence-system.png`.

Latest Product Validation QA note: admin `Why Return` tab rendered on `http://127.0.0.1:8766/#validation` with stored source labels, 2 evidence-backed decisions, product funnel, persona validation, feature utility ranking, dead-feature detector, action taxonomy, live execution/signer untouched safety chips, guest lock, no console errors, and no desktop/390px mobile overflow. Screenshot receipt saved at `docs/milestones/screenshots/2026-06-22-product-validation-engine.png`.

Latest dashboard QA note: deployment-mode panel rendered on `http://127.0.0.1:8767/` with three modes, no refresh failures, no console errors, and no horizontal overflow at desktop or 390px mobile width.

Latest alert QA note: admin Logs tab on `http://127.0.0.1:8767/` rendered 16 backend alert catalog rows with no refresh failures, no console errors, and no horizontal overflow.

Latest PNET payment QA note: connected-user PNET Access flow on `http://127.0.0.1:8767/` rendered backend access check, payment intent, Pera signing step, backend txid verification step, and mock confirmation receipt with no refresh failures, no console errors, and no horizontal overflow.

Latest policy QA note: admin Bot Control tab on `http://127.0.0.1:8767/` rendered nine backend policy controls for input cap, fee cap, allowlists, route hash, daily spend, wallet reserve, and kill switch with no refresh failures, no console errors, and no horizontal overflow at desktop or 390px mobile width.

Latest capability QA note: Product Capabilities panel on `http://127.0.0.1:8767/` rendered eight backend capabilities for market intelligence, scanner, route engine, paper trading, risk engine, execution controls, public dashboard, and PNET access layer with no refresh failures, no console errors, and no horizontal overflow at desktop or 390px mobile width.
