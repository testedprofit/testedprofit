# AlgoPulse / PNET Market Intelligence Engine

Subtitle: Evidence-first Algorand market intelligence and route-risk research

Status: Working draft. This paper describes Phase 0 research and intelligence work only. It does not claim live-trading readiness, guaranteed returns, passive income, copy trading, custody, or user-deposit services.

## Whitepaper Maintenance Rule

This document should evolve only when the repo, tests, staging evidence, or verified external sources support a new fact. Every development churn should ask:

1. Did this change create a new confirmed fact that belongs here?
2. Did this change alter the architecture, safety model, evidence model, or phase roadmap?
3. Did this change produce metrics, diagrams, test results, or staging evidence worth summarizing?
4. Did this change reveal a limitation or risk that should be disclosed?
5. Did this change affect public claims, PNET utility, or product positioning?

If yes, propose a small update in the handoff under `Whitepaper Delta`. Do not invent claims.

## Abstract

AlgoPulse / PNET Market Intelligence Engine is a Phase 0 Algorand research system for observing liquidity, normalizing quotes, explaining route decisions, measuring opportunity decay, and producing evidence before any live execution path is considered. The system is designed around scanner evidence, connector reliability, quote freshness, route/risk explainability, paper-trading results, unsigned dry-run validation, and delayed public-safe reporting.

The project intentionally gates live execution. Current work is focused on proving that market data can be collected, compared, rejected, simulated, and explained without signer access, hot-wallet custody, transaction submission, or user deposits.

## Introduction

Algorand liquidity can be spread across venues, asset pairs, and changing pool conditions. A route that appears useful at detection time may become stale or unsafe before it can be acted on. For a market-intelligence product, the first problem is not execution. The first problem is evidence: whether data is fresh, comparable, explainable, and safe to expose.

AlgoPulse treats arbitrage research as an observability and safety problem before it treats it as an execution problem. Phase 0 asks whether scanner output can become quote evidence, route candidates, risk decisions, and paper-trading records that remain understandable after time has passed.

## Problem Statement

The project tracks these Phase 0 problems:

- Stale quotes can make a route appear actionable when its market state is already obsolete.
- Connector degradation can make one venue look unavailable, mispriced, or falsely healthy.
- Route decay can erase apparent spread before paper or dry-run evidence can confirm it.
- Shallow liquidity can turn small theoretical spreads into poor execution estimates.
- Unsafe arbitrage assumptions can hide fees, price impact, slippage, route length, or unsupported assets.
- Public strategy leakage can expose fresh executable route intelligence before it is safe or intended.

## System Overview

AlgoPulse is organized as a read-first market engine:

- Scanner: collects pool and market snapshots without requiring key material.
- Quote engine: normalizes venue quotes and records freshness evidence.
- Connector health: labels Tinyman, Pact, algod, Indexer, and future sources as ok, degraded, down, stale, mock, stored, live, delayed, or unavailable as appropriate.
- Route engine: generates route candidates and links them to quote evidence.
- Risk engine: rejects unsafe or incomplete routes with machine-readable reasons.
- Paper trader: records expected versus simulated outcomes at later checkpoints.
- Unsigned dry-run validator: validates intent, group size, references, allowlists, fees, and route hash without signing or submitting.
- Dashboard and reporting layer: shows delayed, redacted, source-labeled market intelligence and admin evidence.

## Phase 0 Evidence Model

Phase 0 evidence should prove:

- Scanner pools and snapshots exist.
- Quotes are comparable across venues and standard input sizes.
- Quote freshness is recorded and stale quotes are rejected.
- Connector degradation is visible and affects readiness.
- Route candidates link back to quotes, venues, and pair data.
- Rejected routes include explicit reasons.
- Risk decisions explain approval, rejection, wait, or blocked states.
- Paper evidence records detected time, route hash, input amount, expected output, expected profit, simulated output at later checkpoints, quote decay, decision, and skip or failure reason.
- Readiness reports can summarize a 24-hour read-only staging period without requiring live execution metrics.

Readiness means evidence quality, not permission to trade. A ready Phase 0 report can support the next research gate; it does not make the system live-ready.

## Safety And Non-Custody Design

Current Phase 0 safety boundaries:

- No user deposits.
- No AI-held keys.
- No frontend wallet keys.
- No live transaction submission.
- No signer changes without human review.
- No hot-wallet funding or custody logic in Phase 0 automation.
- No public fresh executable route data.
- Public data must be delayed, aggregate, redacted, or clearly source-labeled.
- Mock data must be labeled as mock and must not be presented as production evidence.

Signer isolation, hot-wallet limits, route-hash approval, and manual live reconciliation remain future human-review gates. They are not active product claims.

## PNET Utility Layer

PNET is planned as an access and workflow layer for market intelligence, not as a promise of trading performance. Candidate utility surfaces include:

- Gated research reports.
- Custom scan requests.
- Alert credits.
- Route simulation or replay access.
- Research exports.
- API access to delayed public-safe data.
- Founder, builder, project, and liquidity-provider intelligence pages.
- Future access research may evaluate xChain Accounts for EVM-wallet authentication to PNET-gated reports or APIs, but this is not part of Phase 0 engine evidence or execution.

User-owned payment or history records are not globally public. Payment, refund, receipt, and reconciliation exposure policies require explicit human review before production behavior changes.

## Product Phases

### Phase 0: Research And Safety Evidence

Build scanner, quote freshness, connector reliability, route decision evidence, risk explanations, paper trading, public-safe reporting, admin observability, and unsigned dry-run validation.

### Phase 1: User-Facing Market Intelligence

Expose useful delayed dashboards, reports, alerts, route forensics, liquidity-health views, project pages, and safe PNET-gated research workflows.

### Phase 2: Advanced Analytics And Network Effects

Add deeper opportunity decay analytics, confidence calibration, liquidity-provider intelligence, project intelligence, API surfaces, and daily market reports based on collected evidence.

### Phase 3: Tiny Own-Funds Execution Pilot

Only after human-reviewed gates, evaluate a tiny own-funds manual pilot with isolated signer review, strict allowlists, dry-run validation, reconciliation, and rollback plans.

### Phase 4: Hardened Production Micro-Arb

Only if prior evidence supports it, consider limited automated own-funds execution under strict policy, monitoring, kill switch, reconciliation, and public-safe receipts. This remains out of current Phase 0 scope.

## Risk, Limitations, And Disclosure

Known risks and limitations:

- No guaranteed returns.
- Quotes can decay quickly.
- Liquidity depth can be insufficient.
- Connectors can fail, lag, or disagree.
- Indexer and algod freshness can diverge.
- Paper-trading outcomes may not match future execution conditions.
- Fees, price impact, and slippage can eliminate apparent spreads.
- Public route details can leak strategy if exposed too early.
- Wallet, payment, execution, and public-claim changes require human review.
- Regulatory and financial considerations require qualified human review before public launch or monetization.

## Evaluation Plan

Phase 0 evaluation should collect:

- 24-hour read-only scanner evidence.
- 7-day paper-trading evidence.
- Quote freshness metrics.
- Connector degradation metrics.
- Route rejection reason coverage.
- Risk approval and rejection evidence.
- Opportunity decay and survival at T+5s, T+30s, and later checkpoints where available.
- Dry-run unsigned group validation evidence.
- Public dashboard redaction and delay test evidence.

## Conclusion

AlgoPulse is being built as an evidence-first Algorand market intelligence system. The core thesis is that safe execution, if ever considered, must be earned by observable scanner health, quote freshness, route explainability, risk rejection, paper-trading evidence, dry-run validation, and human-reviewed safety gates.

The immediate goal is not to turn on a bot. The immediate goal is to prove that the system can observe, explain, reject, simulate, and report market behavior safely.

## References / Source Notes

- Algorand Developer Portal: https://dev.algorand.co/
- Algorand Portal Guide and AI tools: https://dev.algorand.co/getting-started/portal-guide/
- AlgoKit LocalNet: https://dev.algorand.co/algokit/cli/localnet/
- Algorand atomic transaction groups: https://dev.algorand.co/concepts/transactions/atomic-txn-groups/
- Algorand transaction fees: https://dev.algorand.co/concepts/transactions/fees/
- Algorand keys and signing: https://dev.algorand.co/concepts/accounts/keys-signing/
- Repo product thesis: `docs/PRODUCT_THESIS.md`
- Repo gated progress tracker: `docs/GATED_PROGRESS_TRACKER.md`
- Repo public redaction contract: `docs/PUBLIC_RECORD_REDACTION_CONTRACT.md`
- Repo safety checklist: `docs/SAFETY_CHECKLIST.md`
- xChain learning track: `docs/XCHAIN_ACCOUNTS_LEARNING_TRACK.md`
