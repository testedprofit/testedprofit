# API Contract

## Response Envelope

New control-plane endpoints use:

```json
{
  "ok": true,
  "requestId": "req_...",
  "data": {},
  "error": null
}
```

Errors use the same envelope with `ok=false`, `data=null`, and an `error.code`.

## Role Headers

Admin endpoints require both headers:

```text
X-Algopulse-Role: admin
X-Algopulse-Wallet: <allowlisted admin wallet>
```

Frontend checks are only UX. The backend must reject non-admin calls.

## Public And User Endpoints

- `GET /api/config/public`: non-secret dashboard config, PNET ASA id, fee receiver, supported paid actions, public delay, product capability catalog, Phase Gates, and deployment-mode contract for local/staging/production Phase 0.
- `GET /api/session/wallet/{address}`: local review wallet role mock.
- `POST /api/user/pnet/access-check`: checks wallet, network, PNET opt-in, and PNET balance for market-data access.
- `POST /api/user/pnet/fee-quote`: creates a market-data fee quote and PNET ASA transfer intent. It does not accept deposits or execution authority.
- `POST /api/user/pnet/fee-confirm`: confirms mock local txids for review and verifies real txids on-chain before granting credits.
- `GET /api/contribution-protocol/catalog`: returns local-review contribution types, credit unlocks, safety boundaries, and smart-contract blueprint status.
- `GET /api/contribution-protocol/session/{wallet}`: returns a local-review contribution-credit dashboard envelope for a wallet session.
- `POST /api/contribution-protocol/submit`: records a contribution submission for manual review. It does not grant token rewards, payouts, or governance authority.
- `POST /api/contribution-protocol/spend`: spends local-review credits on bounded access surfaces. It does not deploy contracts, move treasury, sign transactions, submit trades, or create binding governance.
- `GET /api/community-growth/overview/{wallet}`: returns local-review onboarding, referral, leaderboard, and reputation data. It does not rank users by earnings or token holdings.
- `POST /api/community-growth/referral`: records a referral receipt for manual review. It does not grant automatic payouts, token rewards, yield, or governance authority.
- `GET /api/transparency/system`: returns the public-safe transparency dashboard payload: proof checks, redacted ledger rows, GitHub snapshot summary, and audit readiness.
- `GET /api/transparency/proofs`: returns automated proof status rows for payment receipts, review receipts, x402 gate evidence, and documented limitations.
- `GET /api/transparency/public-ledger`: returns redacted payment-verification and review-event rows with hashed/suffixed references only.
- `GET /api/transparency/github-snapshot`: returns a GitHub dossier snapshot summary that can be rendered by `scripts/generate_transparency_snapshot.py`.
- `GET /api/transparency/audit-readiness`: returns checklist, threat-model, blocked-claim, and publication-gate metadata.
- `POST /api/events/user-action`: records a product-validation action from the approved action taxonomy. It stores role, wallet-connected state, source page, timestamp, and safe metadata; it must not store mnemonics, private keys, signer instructions, or wallet custody material.
- `GET /api/reports/paper/daily`: aggregate paper-trading QA report.
- `GET /api/reports/market/daily`: generates and stores a public-preview daily market intelligence report from stored scanner, route, paper-trade, risk, and service-health evidence. It exposes aggregate preview fields, an optional ALGO-only external cached market context ribbon, and labels omitted detail sections.
- `GET /api/reports/market/archive`: lists stored daily market intelligence reports for the Research Archive page.
- `GET /api/reports/market/daily/export?format=json|markdown`: exports a stored/generated daily market intelligence report as JSON or Markdown.
- `GET /api/market/pnet/recent-swaps`: returns public-safe, read-only recent PNET swap activity from the Vestige swaps API. It exposes normalized asset symbols, amounts, notional estimate, block, age, protocol label, and source labels only. It must not expose raw Vestige payloads, wallet addresses, group IDs, signer state, hot-wallet fields, transaction submission payloads, or executable route instructions.
- `GET /api/x402/reports/market-pulse/daily`: mock/TestNet x402 readiness endpoint for a premium delayed market-pulse report. Unpaid requests return HTTP 402; the local-review mock proof header or verified TestNet x402 middleware path returns a distinct redacted premium delayed-intelligence payload. This does not custody funds, sign, submit, touch live execution, or expose fresh executable routes.

Public config exposes `deploymentModes` with exactly three review-safe modes:

- `local`: mock data, scanner optional, no signer, no real submission.
- `staging`: live scanner, live quotes, paper trading, no live signing, delayed dashboard.
- `production_phase0`: live scanner, route engine, paper trading, risk engine, admin dashboard, public delayed dashboard, isolated signer only after gates, tiny own-funds hot wallet only.

Public config also exposes `productCapabilities` for market intelligence, scanner, route engine, paper trading, risk engine, execution controls, public dashboard, and PNET access layer. These are product surfaces, not signer permissions.

Daily market intelligence reports are public-safe aggregate research. The unauthenticated daily route is a `public-preview` with market summary, top pairs, opportunity counts, scanner health, an optional `marketContextRibbon`, and omitted-detail markers. JSON/Markdown export and archive endpoints remain public-safe delayed research surfaces. They must set `publicSafe=true`, `liveExecutionTouched=false`, and `signerCodeTouched=false`, and they must not include signer instructions, user deposits, private keys, transaction submission, or live execution controls.

`marketContextRibbon` is external cached market context only. The current contract is ALGO-only: `symbol=ALGO`, `change24hPct`, `contextLabel` (`risk-on`, `neutral`, `risk-off`, or `unavailable`), snapshot age, and source label `CoinMarketCap cached context`. It must degrade to `availability=unavailable` when no cached context exists. It must not include BTC, ETH, raw CoinMarketCap payloads, `CMC_API_KEY`, route decisions, scanner decisions, execution fields, payment fields, fresh executable signals, or trading advice. Adding this ribbon does not authorize calling CoinMarketCap on user requests.

The mock/TestNet x402 readiness endpoint returns a distinct `premium-delayed-intelligence` payload with additional redacted detail sections and export metadata. Gate 3 proves payment mechanics and access gating only; it is not Mainnet, production payment support, public challenge eligibility, or external usage evidence.

Public transparency endpoints are read-only evidence surfaces. They may expose counts, status labels, hashed references, suffixes, proof matrix rows, audit checklist rows, and threat-model summaries. They must not expose full wallet addresses, full txids, payment headers, full payment payloads, `.env` contents, mnemonics, private keys, signer material, fresh executable routes, live trading controls, or public eligibility claims.

The recent PNET swaps endpoint is market-observation data, not scanner approval or trade instruction data. It may be near-real-time because public swaps are already historical on-chain/market records, but the payload must remain non-executable and source-labeled.

## Admin Endpoints

- `GET /api/ops/pipeline`
- `GET /api/ops/phase-gates`
- `GET /api/ops/production-readiness`
- `GET /api/ops/activity`
- `GET /api/ops/rejections`
- `GET /api/ops/paper-summary`
- `GET /api/ops/risk-gates`
- `GET /api/ops/environment`
- `GET /api/ops/replay-lab`
- `GET /api/ops/route-forensics`
- `GET /api/ops/confidence-calibration`
- `GET /api/ops/opportunity-decay`
- `GET /api/ops/market-heatmap`
- `GET /api/ops/failure-lab`
- `GET /api/ops/provenance`
- `GET /api/ops/evidence`
- `GET /api/ops/product-validation`
- `GET /api/admin/preflight`
- `GET /api/admin/alerts/catalog`
- `GET /api/admin/policy/catalog`
- `POST /api/admin/scan-now`
- `POST /api/admin/scanner/start`
- `POST /api/admin/scanner/pause`
- `POST /api/admin/routes/run`
- `POST /api/admin/paper/start`
- `POST /api/admin/dry-run/build`
- `POST /api/admin/live/arm`
- `POST /api/admin/live/disarm`
- `POST /api/admin/kill-switch/trigger`
- `POST /api/admin/kill-switch/clear`

These endpoints queue or reject review-mode jobs. They must not sign, fund, or submit transactions.

The `/api/ops/*` endpoints are read-only observability endpoints for the admin Control Room. They expose source-labeled pipeline telemetry, the Phase 0A-0G operator ladder, detailed phase-gate evidence, activity events, rejection buckets, paper-trading summary, risk locks, production status, and environment/source labels. They must not arm execution, clear the kill switch, sign, or submit.

`GET /api/ops/replay-lab` is an admin-only, read-only endpoint that rebuilds Opportunity Replay Lab records from stored paper-trade history. It returns each historical opportunity with route hash, route legs, expected profit, 5s/30s simulated profit, quote decay, price-impact change, pool-liquidity change, confidence, verdict, and timeline checkpoints. The payload explicitly reports that live execution and signer code were not touched.

`GET /api/ops/route-forensics` is an admin-only, read-only endpoint that returns persisted route decision audits from `route_forensics`. Every stored opportunity should have a matching forensic explanation with route hash, path, profitability, quote freshness, price impact, liquidity score, risk result, approval decision, rejection reason, confidence calculation, decision tree, source label, and completeness state. It must not sign, submit, arm, or modify signer custody code.

`GET /api/ops/confidence-calibration` is an admin-only, read-only endpoint that aggregates stored paper-trade outcomes into confidence buckets. Each resolved paper trade contributes confidence score, expected profit, simulated profit, quote decay, and success/failure. The response returns bucket count, success rate, average quote decay, average simulated profit, calibration error, sample trades, source label, and an explicit report that live execution and signer code were not touched. It must not sign, submit, arm, or modify signer custody code.

`GET /api/ops/opportunity-decay?view=1h|24h|7d` is an admin-only, read-only endpoint for Opportunity Half-Life analytics. It aggregates stored detected opportunities and paper-trade rechecks into `expected_profit`, `expected_profit_5s`, `expected_profit_30s`, and `expected_profit_60s`, then returns average half-life, median half-life, fastest decay, slowest decay, half-life by pair, venue, route type, timeline chart buckets, and recent route records. It must not sign, submit, arm, or modify signer custody code.

`GET /api/ops/market-heatmap` is an admin-only, read-only endpoint that aggregates stored opportunity and paper-trade activity by pair, venue, and time. It supports `view=1h`, `6h`, `24h`, and `7d`, and returns time buckets, heatmap cells, pair summaries, venue summaries, spread frequency, average spread, average route count, opportunity half-life, paper-trade performance, density intensity, and source labels. It must not sign, submit, arm, or modify signer custody code.

`GET /api/ops/failure-lab` is an admin-only, read-only simulation endpoint for operational resilience review. It returns source-labeled scenarios for connector outages, stale quotes, database unavailability, route-engine crashes, signer unavailability, unknown assets, unknown app IDs, and daily-loss breaches. It reports expected response, actual response, alerts generated, services affected, and graceful-degradation state. It must not intentionally take production dependencies offline, sign, submit, arm, or modify signer custody code.

`GET /api/ops/provenance?metric=<metric_key>&route_hash=<optional>` is an admin-only, read-only lineage endpoint. It returns a traceable metric catalog and a selected metric chain: displayed metric, source data, quote rows, pool snapshots, route calculation, and risk decision. It must return explicit `missing` steps when source rows do not exist, and it must not sign, submit, arm, or modify signer custody code.

`GET /api/ops/evidence?category=<optional>&service=<optional>&status=<optional>` is an admin-only, read-only production evidence ledger endpoint. It refreshes deterministic `evidence_records` from stored scanner, quote, route, paper-trading, risk, dry-run, execution-lock, and receipt/report state, then returns filtered records plus summary counts. Evidence records include `evidenceId`, `service`, `category`, `title`, `summary`, `status`, `createdAt`, and `metadata`. Categories are `scanner`, `quotes`, `routes`, `paper_trading`, `risk`, `dry_run`, `execution`, and `receipts`. It must not sign, submit, arm, clear the kill switch, or modify signer custody code.

`GET /api/ops/product-validation?window_days=1..90` is an admin-only, read-only Product Validation Engine endpoint. It aggregates `user_actions` and `decision_events` into funnel conversion, persona validation, feature utility ranking, dead-feature detection, and the `Why Users Return` evidence page. Decision events are generated only for evidence-backed interactions such as opening route details, route forensics, replay, reports, receipts, scans, simulations, alerts, project pages, liquidity health, or exports; page load, scrolling, and idle time are excluded. It must not sign, submit, arm, clear the kill switch, or modify signer custody code.

`GET /api/ops/pipeline`, `GET /api/ops/phase-gates`, `GET /api/ops/production-readiness`, and `GET /api/ops/risk-gates` expose `productionReadiness` derived from actual evidence. The readiness score is calculated from passing required evidence records divided by total required evidence records; percentages must not be hardcoded in the frontend or API.

`GET /api/ops/production-readiness` returns the full readiness engine report: `phases`, `gates`, `evidence`, `metrics`, `passedEvidenceCount`, `totalEvidenceCount`, `overallPercent`, `nextGate`, and `blockingItems`. Evidence records are persisted to `production_evidence`; gate definitions are stored in `production_gates`.

`GET /api/ops/phase-gates` returns `phases` for the high-level Control Room ladder and `gates` for the deeper evidence checklist. Phase and gate percentages are computed from pass/fail evidence rows, including scanner uptime, comparable quotes, route rejection explanations, paper-trading rechecks, dry-run validation, signer isolation, manual reconciliation, and public dashboard safety.

Pipeline service nodes may include `motionLabel`, `motionState`, `approvedCount24h`, and `rejectedCount24h` for visual live-map rendering. These fields are evidence labels only and must not be interpreted as signer permission or execution readiness.

Every completed or locked pipeline service must expose structured `evidence` rows with `label`, `value`, `detail`, and `source`. Examples include scanner pool counts, quote counts, route candidate counts, risk rejection reasons, paper-trade simulation counts, and signer disabled/locked state. Frontend gates may display this evidence, but backend role checks remain authoritative.

`GET /api/ops/pipeline` and `GET /api/ops/risk-gates` expose `productionStatus` as `NOT LIVE READY` while the safe mode is scanner, paper, and dry run only. The restrictions must include no user deposits, no guaranteed returns, and no live execution unless an admin explicitly arms it after gates pass.

`GET /api/admin/alerts/catalog` returns the Phase 0 watched-condition catalog for scanner, connector, quote, route, storage, risk, signer-boundary, wallet-balance, loss-limit, live-trade, and reconciliation failures. It is role-gated because the public dashboard should show delayed/redacted health only.

`GET /api/admin/policy/catalog` returns the Phase 0 hard-stop policy catalog for max input amount, max transaction fee, asset allowlist, app ID allowlist, transaction type allowlist, route hash approval, daily spend limit, wallet reserve minimum, and kill switch. It is a role-gated control-plane contract only and does not sign, submit, or modify signer custody code.
