# AlgoPulse Version Ladder

This is the build order for the first version worth shipping. The rule is simple: do not start with live execution.

## Founder Build Sequence

| Version | Scope | Exit Gate |
| --- | --- | --- |
| v0.1 | Read-only scanner | Runs without signer secret material, records pools, reserves, app IDs, rounds, timestamps, and freshness. |
| v0.2 | Tinyman + Pact quote comparison | Compares quotes across both venues for standard probe sizes and stores quote metadata. |
| v0.3 | ALGO/USDC route engine | Generates ALGO/USDC round-trip routes and explains route blockers. |
| v0.4 | Paper trading with 5s/30s recheck | Records every candidate, rechecks after 5 seconds and 30 seconds, and stores quote decay. |
| v0.5 | Dashboard showing delayed spreads | Shows delayed/redacted route data, pool state, route gates, and no-trade reasons. |
| v0.6 | Risk engine | Rejects most routes using freshness, profit, fee-buffer, impact, app-ID, asset, route-length, and daily-limit gates. |
| v0.7 | Unsigned transaction builder | Builds reviewable unsigned atomic groups only from risk-approved routes and enforces group size. |
| v0.8 | Signer service | Runs separately, validates route intent and policy, keeps kill switch on by default, and logs every decision. |
| v0.9 | One manual tiny trade | Performs one manually approved ALGO/USDC trade with Lora verification and balance reconciliation. |
| v1.0 | Fully automated tiny own-funds micro-arb | Automates only tiny own-funds routes after v0.1-v0.9 gates are stable and reviewed. |

## Operating Rule

Anything before v0.7 must work without wallet key material. Anything before v0.9 must be no submitted mainnet trades. v1.0 is not a scale-up; it is tiny, own-funds automation after the manual-trade proof is boring and repeatable.
