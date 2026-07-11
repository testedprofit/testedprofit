# Public Record Redaction Review

Use this checklist before changing public, user-owned, or admin-only exposure for receipts, payments, refunds, reconciliations, routes, or execution-adjacent records.

This document is review guidance only. It does not approve implementation or change application behavior.

## Review Instructions

- Use `docs/PUBLIC_RECORD_REDACTION_CONTRACT.md` as the source contract.
- Approve one small implementation task at a time.
- Keep public surfaces delayed, redacted, aggregate, or research-safe.
- Treat wallet, payment, refund, signing, execution, hot-wallet, risk-policy, and public-claims changes as human-review-required.
- Do not approve public profit, passive-income, copy-trading, managed-strategy, user-deposit, or guaranteed-return claims.

## Decision Checklist

| Area | Decision needed | Risk if exposed | Recommended default | Human reviewer notes |
|---|---|---|---|---|
| Live trade receipts | Decide whether any live/dry-run receipt summary may be public. | Can reveal strategy, timing, route hashes, wallet state, or execution details. | Admin-only until a delayed public receipt format is approved. |  |
| Failed trade receipts | Decide what failed-trade facts may be public. | Failure details can leak routes, slippage thresholds, or operational weakness. | Delayed public summary only: category, date bucket, no route legs, no wallet. |  |
| Reconciliation records | Decide public vs admin-only balance reconciliation visibility. | Exact balances and deltas reveal hot-wallet and strategy performance. | Admin-only; public only aggregate counts after review. |  |
| PNET fee payments | Decide user-owned receipt scope and global history policy. | Public payment history exposes wallets, amounts, txids, and user behavior. | User-owned after wallet proof; admin-only global history. |  |
| Refunds | Decide user-owned refund status and admin refund queue policy. | Public refund queue can expose disputes and payment metadata. | User-owned status only; admin-only queue and notes. |  |
| User-owned history | Decide how users prove ownership before viewing payment/refund history. | Frontend-only roles can leak another user's records. | Backend wallet proof required before any user-owned history. |  |
| Admin-only operational logs | Decide audit event redaction and retention. | Logs may include headers, routes, errors, wallet data, or policy internals. | Admin-only, sanitized request metadata, no secrets. |  |
| Route hashes | Decide whether route hashes are public, delayed, truncated, or admin-only. | Fresh hashes can correlate with strategy and execution opportunities. | Delayed and truncated for public; full hash admin-only unless approved. |  |
| Tx IDs / group IDs | Decide public, user-owned, or admin-only scope. | Public tx feeds can expose timing, wallet links, or route execution. | User-owned/admin-only; delayed public only after receipt policy approval. |  |
| Expected vs actual output | Decide exact vs bucketed result display. | Exact deltas reveal strategy quality, loss profiles, and wallet balance movement. | Admin-only exact; public bucketed aggregate after delay. |  |
| Net result display | Decide whether public receipts can show positive/negative net result. | Can imply profit claims or invite copy-trading interpretation. | Aggregate research language only; no guaranteed-return framing. |  |
| Failure reasons | Decide public-safe reason taxonomy. | Detailed reasons can reveal defenses, thresholds, or route logic. | Delayed category only, e.g. `slippage_exceeded`, `stale_quote`. |  |
| Timing delays | Decide delay windows for reports, receipts, route hashes, txids, and failures. | Fresh timing can turn intelligence into execution guidance. | Use configured public delay at minimum; longer delay for receipts if needed. |  |
| Dry-run summaries | Decide whether unsigned dry-run metadata may be public. | Unsigned groups are execution-adjacent and can reveal route construction. | Admin-only. |  |
| Execution queue items | Decide whether queue status can ever be public. | Queue internals reveal operational timing and execution intent. | Admin-only. |  |
| Admin audit events | Decide if any audit rollup can be public. | Audit detail can expose admin actions and operational controls. | Admin-only details; public aggregate health only. |  |
| Public report wording | Decide approved language for reports and receipts. | Bad wording can imply profit, passive income, copy trading, or managed strategy. | Market intelligence, simulation, evidence, and research language only. |  |

## Required Approvals Before Behavior Changes

- Reviewer name:
- Review date:
- Record type(s):
- Approved public fields:
- Approved delayed public fields:
- Approved user-owned fields:
- Approved admin-only fields:
- Required redactions:
- Required delay:
- Required tests:
- Explicitly blocked fields:
- Rollback plan:

## Suggested First Implementation After Review

After human review, the first safe implementation task should be one small redaction helper or one endpoint-specific redaction test, not a broad auth or endpoint rewrite.

Recommended first implementation shape:

```text
Add a public-record redaction fixture or helper for one approved record type only, with tests. Do not change signer, execution, hot-wallet, transaction submission, risk limits, or public claims.
```
