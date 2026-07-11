# Production Readiness

This checklist is for Phase 0 production readiness only. It does not authorize live trading by itself, does not change signer policy, and does not grant custody over user funds.

## Production Status

Status: NOT LIVE READY

Reason: The system is collecting market data, but live execution remains locked until scanner uptime, paper-trading edge, risk gates, unsigned dry runs, signer isolation, and manual micro-trade reconciliation are proven.

Current safe mode: Scanner / Paper / Dry Run only.

- No user deposits.
- No guaranteed returns.
- No live execution unless explicitly armed by admin after gates pass.

## Current Readiness

Current readiness is calculated by the Production Readiness Engine, not by fixed percentages in docs, frontend code, or API handlers.

- Gate definitions live in `production_gates`.
- Latest evidence rows live in `production_evidence`.
- `/api/ops/production-readiness` computes `overallPercent` as passing required evidence divided by total required evidence.
- The admin Readiness page shows the gate tree, pass/fail evidence, blockers, and evidence links.

Required evidence includes scanner uptime, quote freshness, route rejection explanations, paper-trade rechecks, dry-run validation, signer isolation, manual reconciliation, and delayed public dashboard safety.

## Phase Gates

| Gate | Name | Go Criteria |
| --- | --- | --- |
| 1 | Scanner 24h | Read-only scanner runs for 24 hours with no private key, no signer, and no submitted transactions. |
| 2 | Comparable Quotes | Tinyman and Pact quotes are captured with venue, pool, assets, amount, output, fee, impact, round, capture time, and expiry. |
| 3 | Explained Rejections | Every route stores gross profit, fees, impact, slippage buffer, net profit, confidence, and skip reason. |
| 4 | 7-Day Paper Trading | Paper trading runs for 7 days with 5s and 30s rechecks, quote decay, and expected-vs-simulated results. |
| 5 | Risk Blocks Bad Routes | Risk rejects stale, unprofitable, high-impact, oversized, over-route, or unallowlisted routes. |
| 6 | Unsigned Dry Run | Executor builds unsigned groups only, rejects over-16 transaction groups, and never signs or submits. |
| 7 | Signer Rejection Evidence | Isolated signer rejects bad route hashes, app IDs, asset IDs, amounts, fees, tx types, reserve breaches, and kill-switch state. |
| 8 | Manual First Live Trade | First tiny trade is manual, ALGO/USDC scoped, Lora verified, and reconciled. |
| 9 | Public Delayed Dashboard | Public view shows delayed or redacted data only and never exposes fresh executable routes. |
| 10 | Phase 1 Decision | Product decision uses real user demand, market history, paper results, receipts, and incident history. |

## Environment Matrix

| Environment | Scanner | Quotes | Paper Trading | Risk | Signer | Submission | Dashboard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Local | optional or mock | mock/live optional | mock optional | enabled | disabled | disabled | local operator review |
| Staging | live | live | required | enabled | disabled | disabled | delayed dashboard |
| Production Phase 0 | live | live | required | enabled | isolated only after gates | tiny own-funds only after gates | admin plus delayed public dashboard |

Required defaults:

- `ENABLE_EXECUTION=false` until the live micro-execution checklist is complete.
- `ENABLE_SIGNER=false` until signer rejection evidence is complete.
- `KILL_SWITCH=true` by default.
- No mnemonic, seed, key, or hot-wallet secret in repo files.
- PNET user payments unlock scans, reports, simulations, or credits only.

## Go / No-Go Checklist

Go only when all are true:

- Tests and CI pass on the exact deployment revision.
- No committed real `.env`, `secrets.json`, mnemonic, seed, or key files.
- Scanner and quote services have fresh health checks.
- Database migrations and backups are verified.
- Redis, Postgres, logs, and alert routing are reachable.
- Admin allowlist is set and non-admin admin calls return `403`.
- Public dashboard delay is enabled.
- PNET fee receiver, PNET ASA ID, and network are correct.
- Risk policy enforces profit, freshness, size, impact, route length, app allowlist, asset allowlist, daily loss, and concurrency limits.
- Kill switch is active unless explicitly running an approved tiny manual test.

No-go if any are true:

- Signer or execution secrets are in frontend, docs, screenshots, or repo files.
- Scanner requires a private key.
- Quotes are stale or venue connectors disagree on round/freshness.
- Paper trading is missing expected-vs-simulated records.
- Risk decisions lack skip reasons.
- Public dashboard exposes fresh executable route data.
- Refund/failure queue is not reviewable.
- Reconciliation is missing or mismatched.

## Rollback Checklist

1. Trigger or keep the kill switch active.
2. Disable live execution flags.
3. Stop scanner, quote, route, and paper workers only if they are causing damage; otherwise keep read-only capture running for incident evidence.
4. Preserve logs, alerts, receipts, and database snapshots.
5. Revert to the last known-good deployment revision.
6. Verify public dashboard shows safe degraded status or delayed data.
7. Reconcile PNET fee receipts and any pending credit/report unlocks.
8. Publish an internal incident note before re-enabling staging or production.

## Live Micro-Execution Checklist

This checklist applies only after Gates 1-7 are complete.

- Use a new platform hot wallet with loss-tolerant funds only.
- Start with ALGO/USDC only.
- Keep max trade size at 10 ALGO until manual evidence supports an increase.
- Keep daily loss limit, daily trade count, route length, and concurrency caps active.
- Manually approve the first live route.
- Verify the transaction group in Lora.
- Reconcile expected output, actual output, fees, and wallet reserve.
- Record the receipt and mark whether it was win, loss, skip, or failure.
- Do not accept user funds, user deposits, user signing authority, or user execution instructions.

## Public Claims Checklist

Public copy may say:

- AlgoPulse provides market intelligence, scanner coverage, route intelligence, paper-trading reports, risk evidence, execution controls, a public dashboard, and a PNET access layer.
- PNET can be used for scans, route simulations, delayed route reports, monitoring requests, and credits.
- Any future execution is tiny, own-funds, policy-gated, and receipt-backed.

Public copy must not say:

- Guaranteed profit.
- User deposits into the bot.
- User funds are traded.
- Live executable routes are public in real time.
- The system is fully automated before Phase 0 gates are complete.
