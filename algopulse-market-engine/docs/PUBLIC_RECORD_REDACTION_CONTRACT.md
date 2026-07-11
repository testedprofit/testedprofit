# Public Record Redaction Contract

This contract defines which fields may appear in public, delayed public, user-owned, admin-only, redacted, or never-exposed records.

Public surfaces may provide delayed market intelligence, public-safe receipts, reports, and evidence. They must not expose fresh executable route payloads, signer material, hot-wallet state, private operational details, or execution controls.

## Classification Legend

- `public`: Safe for unauthenticated public display.
- `delayed_public`: Safe only after the approved public delay or after aggregation.
- `user_owned`: Visible only to the wallet/user that owns the record after reviewed wallet proof exists.
- `admin_only`: Visible only to reviewed backend admin roles.
- `redacted`: May be displayed only after masking, truncation, or aggregation.
- `never_expose`: Must not appear in public, user-owned, or admin response bodies unless a separate human-approved security review says otherwise.

Any field not listed in this contract is `never_expose` by default until added here with a classification, reason, examples, endpoints, and tests.

## Current Implementation Note

`src/algopulse/public_record_redaction.py` implements the Phase 0 report-surface redaction helper for:

- `paper_trade_report`
- `market_daily_report`
- `market_archive_report`

The helper is wired to the current public report endpoints and blocks sensitive record types by returning no source data until human review approves a record-specific exposure policy.

Current public-safety coverage:

- `tests/test_public_data_freshness_safety.py`
- `tests/test_public_report_data_safety.py`
- `tests/test_public_record_redaction_contract.py`

TODO after human review:

- Make every public/user/admin record pass through the policy.
- Add non-xfail endpoint tests for every sensitive record type in this contract.
- Keep execution, signer, hot-wallet, and transaction-submission fields out of public responses.

## Redaction Matrix

| Record type | Field | Classification | Reason | Example safe value | Example unsafe value | Endpoint(s) affected | Test coverage status |
|---|---|---|---|---|---|---|---|
| paper_trade_report | candidates, wouldExecute, skipped, checked5s, checked30s | public | Aggregate paper-trading counts are market research. | `{"candidates": 42}` | Raw per-route trade list | `/api/reports/paper/daily` | covered |
| paper_trade_report | completionRate30s, daysCollected | public | Aggregate quality and sample-depth signals. | `0.82`, `7` | Exact operator schedule | `/api/reports/paper/daily` | covered |
| paper_trade_report | expectedNetProfit, simulatedProfit30s, averageQuoteDecay30s | delayed_public | Aggregate simulation performance, not live execution. | `0.42 ALGO aggregate` | Fresh route-specific profit with route legs | `/api/reports/paper/daily` | covered |
| paper_trade_report | bestRoute.route_hash | delayed_public | Useful paper evidence but may correlate to strategy. | `paper-report-summary-route` | Fresh executable route hash | `/api/reports/paper/daily` | needs_test |
| paper_trade_report | bestRoute.route, legs, raw route JSON | never_expose | Full route details can become executable strategy. | Not present | `[{venue,input_asset_id,expected_output}]` | `/api/reports/paper/daily` | covered |
| market_daily_report | publicSafe, source, reportDate, generatedAt, reportTier, preview, paymentUpgradeAvailable, paymentUnlocks | public | Report metadata helps users judge freshness, source, access tier, and whether x402-only detail exists. | `publicSafe=true`, `reportTier=public-preview` | Internal file paths or deployment secrets | `/api/reports/market/daily`, `/api/reports/market/daily/export`, `/api/x402/reports/market-pulse/daily` | covered |
| market_daily_report | marketContextRibbon | public | ALGO-only external cached market context for delayed reports. It may include ALGO 24h change, context label, snapshot age, availability, and source label `CoinMarketCap cached context`. | `{"symbol":"ALGO","availability":"available"}` | BTC, ETH, raw CMC payloads, `CMC_API_KEY`, route decisions, execution controls, payment fields, fresh executable signals | `/api/reports/market/daily`, `/api/reports/market/daily/export`, `/api/reports/market/archive` | covered |
| market_daily_report | marketSummary, summary, topPairs, opportunityCounts | public | Aggregate market intelligence. | `2 opportunities across 1 pair` | Full fresh route instructions | `/api/reports/market/daily`, `/api/reports/market/daily/export` | covered |
| market_daily_report | pnetLiquidityWatchlist | public | Aggregate PNET pool visibility should remain visible even when no route is approved. It may list pool id, venue, app id, pair label, reserves, liquidity estimate, fee bps, snapshot count, and conservative LP risk notices. | `{"symbol":"PNET","listedWithoutOpportunity":true}` | Buy/sell/ROI language, wallet instructions, raw route legs, signer policy, payment payloads, or fresh executable signals | `/api/reports/market/daily`, `/api/reports/market/archive`, `/api/x402/reports/market-pulse/daily` | covered |
| market_daily_report | topSpreads, routePerformance, riskEvents, premiumSections, exportMetadata, redactionPolicy | delayed_public | Research-safe summaries after aggregation; the x402 path may expose these as premium delayed-intelligence sections while still redacted. | `averageRouteLength=2`, `premiumSections=["topSpreads"]` | Raw route JSON, route legs, signer policy, payment payloads | `/api/reports/market/daily/export`, `/api/x402/reports/market-pulse/daily` | covered |
| market_daily_report | liveExecutionTouched, signerCodeTouched | public | Public safety flags can show boundaries stayed untouched. | `false` | Signer host details | `/api/reports/market/daily`, `/api/reports/market/daily/export` | covered |
| market_daily_report | route_hash, route_json, signed transactions | never_expose | Reports must not expose executable route or transaction payloads. | Not present | `fresh-report-executable-route` | `/api/reports/market/daily`, `/api/reports/market/daily/export` | covered |
| market_archive_report | reports[].summary, count, source, publicSafe | public | Archive index is public market research. | `{"count": 7}` | Raw report JSON with route legs | `/api/reports/market/archive` | covered |
| market_archive_report | reports[].topPairs, reports[].opportunityCounts | public | Aggregate/historical analytics. | `ALGO/USDC count=10` | Fresh executable route feed | `/api/reports/market/archive` | covered |
| market_archive_report | reports[].topSpreads, reports[].riskEvents | delayed_public | Historical market context. | `spread bps summary` | Raw transaction group | `/api/reports/market/archive` | covered |
| market_archive_report | markdown | redacted | Markdown may be exported intentionally, but archive API strips it. | Not present in archive | Full internal markdown with secrets | `/api/reports/market/archive` | covered |
| live_trade_receipt | receipt_id, status, dry_run flag | delayed_public | Public-safe receipts can prove activity without leaking execution timing. | `dry_run=true` | Live route instruction payload | `/api/live-trades`, future public receipts | blocked_pending_human_review |
| live_trade_receipt | route_hash | redacted | Can correlate to strategy and should be truncated or delayed. | `route_abc...789` | Full fresh route hash | `/api/live-trades`, future public receipts | blocked_pending_human_review |
| live_trade_receipt | txid, group_id | user_owned | Transaction IDs may be user/operator-owned evidence. | Owner sees full txid | Global public txid feed | `/api/live-trades`, future receipts | blocked_pending_human_review |
| live_trade_receipt | signed_txn, transaction_group, signer_response | never_expose | Signing artifacts and submission payloads are execution secrets. | Not present | Base64 signed transaction | `/api/live-trades` | needs_test |
| reconciliation_record | reconciliation_id, status, created_at | admin_only | Reconciliation reveals operational execution state. | Admin-only receipt row | Public balance audit feed | `/api/reconciliations` | blocked_pending_human_review |
| reconciliation_record | expected_output, actual_output, net_result | admin_only | Can reveal strategy and wallet deltas. | Admin-only numeric values | Public exact profit/loss per route | `/api/reconciliations` | blocked_pending_human_review |
| reconciliation_record | wallet_address, balance_before, balance_after | redacted | Wallet and balance values are sensitive. | `ADDR...XYZ`, bucketed range | Full wallet and balances | `/api/reconciliations` | blocked_pending_human_review |
| reconciliation_record | private key, mnemonic, signer metadata | never_expose | Secrets must never be serialized. | Not present | Any key material | `/api/reconciliations` | needs_test |
| pnet_fee_payment | quote_id, action, amount, asset_id | user_owned | User should see their own market-data fee details. | `pair_scan 12 PNET` | Global user payment list | `/api/verify-payment`, `/api/user/pnet/*`, `/api/payment-verifications` | blocked_pending_human_review |
| pnet_fee_payment | sender, receiver, txid | user_owned | Payment proof belongs to the paying user; public view should redact. | Owner sees txid | Public sender/receiver history | `/api/payment-verifications` | blocked_pending_human_review |
| pnet_fee_payment | verification status, credit grant status | user_owned | User needs receipt and unlock state. | `verified`, `credit_granted` | Admin fraud notes | `/api/user/pnet/fee-confirm` | needs_test |
| pnet_fee_payment | indexer raw response, API tokens | never_expose | Raw infra responses can leak implementation details. | Not present | Full indexer response with tokens | `/api/verify-payment` | needs_test |
| transparency_ledger | txReference.hash, txReference.suffix, senderReference.hash, receiverReference.hash | public | Public proof references can be verified without exposing full txids or wallets. | `tx_abcd1234...`, suffix `A1B2C3` | Full txid, full sender, full receiver | `/api/transparency/public-ledger`, `/api/transparency/system` | covered |
| transparency_ledger | status, ok, assetId, amountRaw, confirmedRound, confirmations, createdAt, source | public | Status/count metadata proves activity without custody or payment payload exposure. | `status=confirmed`, `assetId=3169177585` | Raw payment payload or raw indexer response | `/api/transparency/public-ledger`, `/api/transparency/system` | covered |
| transparency_ledger | payment headers, paymentGroup, PAYMENT-SIGNATURE, X-PAYMENT, full payment payload | never_expose | x402 and payment payload material must stay package/operator-owned and out of public proof surfaces. | Not present | Full payment header or group | `/api/transparency/*` | covered |
| transparency_ledger | review event id, kind, status, label, category, reviewMode, creditsGranted | public | Manual-review contribution/referral/credit receipts can be summarized. | `pending_review`, `creditsGranted=0` | Private review notes or identity doxxing | `/api/transparency/public-ledger`, `/api/transparency/system` | covered |
| transparency_ledger | walletReference.hash, walletReference.suffix | public | Review wallet references are redacted before public display. | `wallet_abcd1234...` | Full wallet address | `/api/transparency/public-ledger`, `/api/transparency/system` | covered |
| transparency_snapshot | proofSummary, ledgerSummary, auditSummary, validationCommands, docs | public | GitHub dossier snapshots should be reproducible without exposing private data. | `checks=6`, `docs=[...]` | `.env`, wallet secret, payment payload | `/api/transparency/github-snapshot` | covered |
| transparency_audit | checklist, threatModel, blockedClaims, requiredBeforePublication | public | Audit readiness can be reviewed publicly if it does not claim readiness. | `status=blocked`, `blockedClaims=[...]` | Legal/compliance certification claim | `/api/transparency/audit-readiness` | covered |
| refund_case | case_id, status, user-facing reason | user_owned | User needs refund status for their own case. | `reviewing_payment` | Full refund queue | `/api/refund-cases` | blocked_pending_human_review |
| refund_case | refund_address | redacted | Address may be shown only to owner/admin. | `ADDR...XYZ` | Full public refund address | `/api/refund-cases` | blocked_pending_human_review |
| refund_case | operator_action, admin notes, resolution_note | admin_only | Operational dispute workflow. | Admin-only manual note | Public internal notes | `/api/refund-cases`, `/api/refund-cases/{case_id}/status` | blocked_pending_human_review |
| refund_case | automatic refund transaction payload | never_expose | Refunds remain manual; no auto-send payloads. | Not present | Signed refund tx | `/api/refund-cases` | needs_test |
| failed_trade | failure_category, public-safe reason | delayed_public | Delayed failure receipts can build trust. | `slippage_exceeded` | Fresh route details | Future public receipt endpoint | blocked_pending_human_review |
| failed_trade | txid, group_id | user_owned | Owner/operator proof, not global public by default. | Owner sees txid | Public failed tx feed | `/api/live-trades`, future receipts | blocked_pending_human_review |
| failed_trade | route_hash, expected vs actual output | redacted | Can reveal strategy and losses. | Truncated hash, bucketed result | Exact route and deltas | Future public receipt endpoint | blocked_pending_human_review |
| failed_trade | signed transactions, signer response | never_expose | Execution artifacts are never public. | Not present | Signed tx group | `/api/live-trades` | needs_test |
| execution_queue_item | job_id, queued_at, service | admin_only | Queue internals are operational. | Admin queue row | Public queue item | `/api/admin/*`, future queue endpoint | blocked_pending_human_review |
| execution_queue_item | route_hash, unsigned_group | admin_only | Dry-run/execution planning must stay admin-scoped. | Admin-only unsigned plan | Public unsigned transaction group | `/api/admin/dry-run/build` | blocked_pending_human_review |
| execution_queue_item | signed_group, mnemonic, signer token | never_expose | Secrets and signed transactions must never appear. | Not present | Signed group payload | Any endpoint | needs_test |
| execution_queue_item | retry policy, internal error detail | admin_only | Can reveal operational posture. | Admin-only error code | Public stack trace | Admin endpoints | needs_test |
| route_detail | pair, venues, aggregate spread, status | delayed_public | Delayed intelligence can be public-safe. | `ALGO/USDC, 90 bps, rejected` | Fresh route instructions | `/api/opportunities`, future route detail | covered |
| route_detail | route_hash | delayed_public | May be used as evidence after delay. | Delayed/truncated hash | Fresh hash | `/api/opportunities`, reports | needs_test |
| route_detail | route legs, raw route JSON, pool sequence | admin_only | Full route path may be executable strategy. | Admin route forensics | Public fresh route path | `/api/ops/route-forensics`, `/api/opportunities` | needs_test |
| route_detail | signing instructions, transaction params | never_expose | Route details must not become execution instructions. | Not present | Suggested signed tx group | Any public route | covered |
| dry_run_summary | dry_run_id, route_hash, status | admin_only | Dry-run is execution-adjacent. | Admin-only dry-run receipt | Public dry-run feed | `/api/admin/dry-run/build`, `/api/live-trades` | blocked_pending_human_review |
| dry_run_summary | tx_count, group_size_ok | admin_only | Useful for admin readiness, not public by default. | `tx_count=6` | Public route construction detail | `/api/admin/dry-run/build` | blocked_pending_human_review |
| dry_run_summary | unsigned_group | admin_only | Unsigned plans are still execution-adjacent. | Admin-only reviewed plan | Public atomic group | `/api/admin/dry-run/build` | needs_test |
| dry_run_summary | signed_group, submission result | never_expose | Dry-run must not sign or submit. | Not present | Submitted txid from dry run | `/api/admin/dry-run/build` | needs_test |
| admin_audit_event | event_id, action, actor_role, created_at | admin_only | Audit logs are operational controls. | Admin audit event | Public admin activity feed | Future audit endpoint | blocked_pending_human_review |
| admin_audit_event | actor_wallet | redacted | Admin identity should be masked outside strict admin contexts. | `ADMIN...ROL` | Full admin wallet public | Future audit endpoint | blocked_pending_human_review |
| admin_audit_event | request body, headers, auth proof | admin_only | May include sensitive operational context. | Admin-only sanitized body | Raw headers or auth proof | Future audit endpoint | needs_test |
| admin_audit_event | secrets, tokens, mnemonics, private keys | never_expose | Secrets must not enter logs or responses. | Not present | Any secret material | Any endpoint/log | needs_test |

## Contract Rules For Tests

- Public report outputs may include aggregate market intelligence, delayed summaries, and paper-trading analytics.
- Public report outputs must not include raw route JSON, route legs, signing artifacts, transaction submission payloads, hot-wallet fields, private keys, mnemonics, seed phrases, or execution queue internals.
- User-owned payment/history data must not be treated as globally public.
- Admin-only execution data must not be treated as public.
- Future public receipt endpoints must be delayed, redacted, and explicitly reviewed before implementation.

## Blocked Pending Human Review

These areas require human review before implementation:

- public or user-owned live trade receipts
- reconciliation record redaction
- PNET fee payment history scope
- refund case user/public/admin visibility
- failed trade receipt wording and timing delay
- route hash truncation and delay policy
- tx ID/group ID public policy
- dry-run summary public/admin split
- admin audit event retention and redaction
