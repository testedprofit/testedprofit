# PNET Documentation And Audit Readiness

Purpose: track the public-documentation and audit materials needed before any exchange, launch, challenge, or broader public review conversation. This is a readiness checklist only. It does not publish anything, claim listing readiness, claim production readiness, or claim that a smart contract/security audit has been completed.

## Current Position

AlgoPulse currently supports safe, local documentation preparation for PNET/ProfitNet utility:

- tokenomics facts and asset references
- use-case documentation
- roadmap and phase gates
- security/audit readiness checklists
- public-safe screenshots, diagrams, and demo evidence
- public-safe transparency ledger and GitHub dossier snapshots
- non-custody, no-signing, no-user-deposit safety language

External publication remains gated. Do not publish, submit to an exchange, claim an audit, claim production readiness, or make listing/eligibility claims without explicit human approval.

## Required Publication Materials

| Material | Current status | Safe next action | Human gate |
| --- | --- | --- | --- |
| Tokenomics page | Needed | Draft a facts-only page with PNET ASA ID, total-supply source links, utility boundaries, non-custody language, and no price/ROI claims. | Rob/public wording approval before posting. |
| Use-case documentation | In progress | Keep documenting PNET as access to delayed market intelligence, liquidity visibility, reports, scan credits, and evidence exports. | Approval before public launch copy. |
| Roadmap | In progress | Keep roadmap phase-based and evidence-based: scanner, reports, x402/TestNet proof, external payer proof, Mainnet readiness docs, then later Mainnet only if approved. | Approval before public roadmap publication. |
| Smart contract / protocol audit | Not completed | Prepare an audit-scope inventory. Do not claim audited. For current PNET ASA work, distinguish asset configuration review from smart-contract audit. | Third-party or senior security review required before any audit claim. |
| Security documentation | Strong internal base | Maintain safety gates, redaction rules, x402 evidence notes, image pipeline, dependency pinning, and no-secret/no-payload policies. | Approval before external security claims. |
| Demo evidence | Local/staged evidence only | Use `docs/IMAGE_PIPELINE.md` for screenshots, diagrams, and GIFs with redaction checks and source labels. | Approval before public demo posting. |
| Transparency dossier | In progress | Use `docs/TRANSPARENCY_SYSTEM.md`, `docs/AUDIT_READINESS_PACKAGE.md`, and `scripts/generate_transparency_snapshot.py` to produce redacted proof snapshots. | Approval before attaching snapshots to public pages, listings, audits, or submissions. |

## Tokenomics Page Draft Requirements

A public-safe tokenomics page should include only verifiable and conservative facts:

- project and token name
- Algorand ASA ID: `3169177585`
- network: Algorand
- total supply only if verified from a current primary/explorer source before publication
- utility boundaries: market-intelligence access, delayed reports, scan/report credits, and research workflows
- non-custody statement
- no wallet custody, no signing by AlgoPulse, no user deposits
- no investment advice
- no guaranteed profit, yield, return, staking reward, price target, or buy/sell language
- risk note for liquidity provision, including impermanent loss and market/liquidity risk

Do not include live market numbers, holder counts, liquidity, price, volume, supply figures, or exchange availability unless verified from current sources immediately before publication.

## Audit Readiness

Before any "audited" or "audit-ready" public statement, split the review scope:

| Scope | What to review | Current claim allowed |
| --- | --- | --- |
| PNET ASA configuration | Asset ID, manager/reserve/freeze/clawback settings, metadata, explorer records, and public references. | "Needs current asset-configuration review." |
| AlgoPulse codebase | API routes, x402 gates, redaction, dependency pins, logging, tests, and no-secret boundaries. | "Internal security QA in progress." |
| x402/payment flow | GoPlausible facilitator path, TestNet evidence, no payload logging, payer/receiver separation, idempotency, replay, and settlement evidence. | "Gate-based TestNet work only unless later approved." |
| Smart contracts | Any future TEAL/PyTeal/ARC smart contracts or app calls. | "No smart-contract audit claim unless a reviewed contract and audit report exist." |
| Frontend/dashboard | Public claims, role gates, admin visibility, screenshots, and redaction. | "Public-safe UI under review." |

## Roadmap Language

Use phase language instead of hype:

1. Read-only PNET market visibility and delayed reports.
2. Public-safe liquidity watchlist and use-case docs.
3. x402/TestNet paid access proof for delayed reports.
4. External TestNet payer proof where payer differs from receiver.
5. Mainnet readiness docs and legal/public wording review.
6. Mainnet or public launch only after explicit approval, security review, abuse controls, monitoring, and rollback plans.

Do not frame the roadmap as a promise of listing, revenue, price performance, trading profits, staking yield, or exchange adoption.

## Use-Case Documentation

Safe PNET/AlgoPulse use cases:

- delayed market-pulse reports
- liquidity-health watchlists
- connector-health summaries
- stale-route and rejection explanations
- paid access to public-safe research exports
- x402-gated delayed data access where approved
- educational LP visibility, without investment instructions

Blocked use-case claims:

- live trading signals
- fresh executable arbitrage routes
- user deposits into a bot
- wallet custody
- transaction signing or submission by AlgoPulse for users
- staking, rewards, buyback, burn, ROI, price, or exchange-listing promises
- public challenge, leaderboard, or eligibility claims before supporting evidence exists

## Image And Evidence Pipeline

Use `docs/IMAGE_PIPELINE.md` for screenshots, diagrams, demo GIFs, and visual evidence. Every image or GIF must label its source as mock, local, delayed, TestNet, staged, or unavailable and must pass redaction checks.

Do not include:

- secrets, `.env` values, mnemonics, private keys, or seed phrases
- full payment payloads, payment groups, `PAYMENT-SIGNATURE`, `X-PAYMENT`, or authorization headers
- fresh executable routes
- unsupported Mainnet, listing, eligibility, audit, ROI, or production-readiness claims

## Publication Gate

Before anything from this checklist is published externally, Rob must approve:

- exact public wording
- asset facts and sources
- audit status wording
- screenshot/GIF redaction
- legal/compliance wording
- no-investment-advice language
- no-custody/no-signing/no-deposit language
- no exchange/listing/production/challenge eligibility overclaim

Until then, this document is internal readiness material only.
