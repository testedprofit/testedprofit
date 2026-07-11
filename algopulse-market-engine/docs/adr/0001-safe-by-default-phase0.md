# ADR 0001: Safe-By-Default Phase 0 Arb Bot

Date: 2026-06-21

## Status

Accepted.

## Context

The project needs to prove useful Algorand market intelligence and eventually tiny arbitrage execution without putting funds, reputation, or users at unnecessary risk.

Algorand supports atomic transaction groups natively, so a basic two-leg venue arb does not require a custom PyTeal contract in Phase 0. The hard part is off-chain route freshness, exact transaction construction, wallet inventory, fee control, and post-trade balance reconciliation.

## Decision

Phase 0 will remain safe by default:

- live execution disabled unless explicitly armed by env flags
- public API execution disabled by default
- tiny hot-wallet model only
- no user deposits
- no custom custody contract
- stale routes rejected before wallet checks
- routes must be positive after fees and buffers
- submitted trades must create balance reconciliation receipts
- public dashboard may show delayed/redacted market state, not private execution strategy

## Consequences

Good:

- The bot can build trust before risking funds.
- Claude/Codex/human contributors have a clear safety boundary.
- Bugs in dashboard/readiness are less likely to submit transactions.
- Future execution work has concrete gates.

Tradeoffs:

- The bot may reject some real but thin opportunities.
- Non-ALGO starting routes need more valuation/reconciliation work before live submission.
- Public dashboard claims must stay conservative.

## Follow-Up Decisions

- ADR for first testnet submitted transaction.
- ADR for first tiny mainnet hot-wallet trade.
- ADR before any custom PyTeal/custody/vault contract.
- ADR before any public execution API.

