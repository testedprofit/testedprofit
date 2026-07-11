# Phase Gates

These gates decide when AlgoPulse can move from scanner/proof mode toward Phase 1. A gate is not complete just because code exists; runtime evidence matters.

| Gate | Exit Criteria | Current State |
| --- | --- | --- |
| 1 | Scanner runs 24 hours with no signer operational secrets and no submitted transactions. | Evidence needed |
| 2 | Quote engine records comparable Tinyman and Pact quotes. | Built |
| 3 | Route engine explains every rejection with skip reason and rule map. | Built |
| 4 | Paper trading runs 7 days with 5s/30s rechecks and quote decay history. | Evidence needed |
| 5 | Risk engine blocks stale, unprofitable, high-impact, over-limit, or unallowlisted routes. | Built |
| 6 | Dry-run executor builds unsigned atomic groups only. | Built |
| 7 | Signer rejects out-of-policy groups. | Built / locked |
| 8 | First live trade is manual, tiny, verified, and reconciled. | Future |
| 9 | Dashboard shows delayed and public-safe data. | Built |
| 10 | Phase 1 decision uses real user demand, market data, paper history, and tiny-live receipts. | Future |

The public dashboard reads the same gate list from `GET /api/config/public`.
