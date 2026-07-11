# Gated Progress Tracker

Use this tracker to turn safety review into gated progress. It shows what we are doing, why it matters, what evidence exists, what is blocked, and the next safe action.

This tracker references existing docs instead of replacing them:

- `docs/AI_DEVELOPMENT_PROTOCOL.md`
- `docs/AI_WORKFLOW_GOVERNOR.md`
- `docs/HUMAN_REVIEW_GATES.md`
- `docs/SAFETY_CHECKLIST.md`
- `docs/API_EXPOSURE_INVENTORY.md`
- `docs/API_EXPOSURE_REVIEW_CHECKLIST.md`
- `docs/API_EXPOSURE_TEST_PLAN.md`
- `docs/API_WARNING_DISPOSITION.md`
- `docs/PUBLIC_RECORD_REDACTION_CONTRACT.md`
- `docs/PUBLIC_RECORD_REDACTION_REVIEW.md`
- `docs/WHITEPAPER_WORKING_DRAFT.md`
- `docs/XCHAIN_ACCOUNTS_LEARNING_TRACK.md`

## Current Project Phase

Phase: **Phase 0 control-plane readiness**

Current safe mode:

- scanner, paper trading, reports, route/risk explanation, and admin observability
- docs and tests for API exposure, mock/local-only boundaries, and public data safety
- no live trading
- no signer changes
- no transaction submission
- no hot-wallet logic
- no risk-limit changes
- no secrets
- no profit, passive-income, copy-trading, managed-strategy, or guaranteed-return claims

Current active gate: **Gate 6 - Wallet connection boundary / TestNet preflight (24h soak evidence)**

Reason: Fail-closed TestNet readiness and the read-only soak runner/Control Room panel exist. A real 24-hour live soak has not been completed. Real Pera/Defly connection and wallet proof remain human-review-required and blocked until soak evidence is reviewed.

## Status Board

| Gate | Status | Evidence | Risk | Human Review | Next Action |
|---|---|---|---|---|---|
| 1. Project orientation and repo hygiene | READY FOR REVIEW | `AI_DEVELOPMENT_PROTOCOL.md`, `HUMAN_REVIEW_GATES.md`, `SAFETY_CHECKLIST.md` | Low | No | Review and keep docs updated |
| 2. API exposure inventory | COMPLETE | `API_EXPOSURE_INVENTORY.md` | Medium | Yes for risky routes | Update when routes change |
| 3. API exposure test plan | COMPLETE | `API_EXPOSURE_TEST_PLAN.md` | Low | No | Implement first current-safety tests |
| 4. Mock/local-only guardrails | IN PROGRESS | `API_WARNING_DISPOSITION.md`, test plan | Medium | Yes for auth/wallet | Add mock/local-only safety tests |
| 5. Public/dashboard data safety | COMPLETE | Inventory, test plan, public freshness tests, report safety tests, redaction contract, allowlist redaction helper | Medium | Yes for sensitive records | Keep sensitive record exposure blocked |
| 6. Wallet connection boundary | IN PROGRESS | readiness gate, soak runner (`testnet_soak.py`), `/api/ops/testnet-soak`, Control Room panel | High | Yes | Run 24h live soak, configure TestNet PNET ASA, then review connect-only wallet design |
| 7. Paper trading evidence | IN PROGRESS | Existing paper/report tests | Medium | No | Add one scanner-to-paper evidence test or report field |
| 8. Route/risk explainability | IN PROGRESS | Existing route/risk tests | Medium | No | Add exposure and explanation coverage |
| 9. Dry-run transaction boundary | IN PROGRESS | Review checklist, test plan | High | Yes | Add unsigned-only tests before expansion |
| 10. Signer review only | BLOCKED | Human review gates | Critical | Yes | No signer changes |
| 11. Live micro-execution gate | BLOCKED | Human review gates, warning disposition | Critical | Yes | Complete prior gates first |

## Gate Roadmap

### 1. Project Orientation And Repo Hygiene

- Purpose: Keep AI work small, reviewable, and aligned with the Phase 0 product boundary.
- Safe work allowed: docs, handoff notes, safety checklists, small tests, repo inventory, scoped review artifacts.
- Unsafe work blocked: broad refactors, duplicate systems, new dependencies without justification, production behavior changes.
- Required evidence: protocol docs exist; safety checklist exists; human review gates exist; changes are scoped.
- Human review needed: No for docs-only hygiene; yes for new dependencies or public behavior changes.
- Exit criteria: Future work can identify scope, files, tests, risks, and next safe action.
- Next gate unlocked: API exposure inventory.

### 2. API Exposure Inventory

- Purpose: Make every FastAPI route and exposure surface reviewable before production deployment.
- Safe work allowed: endpoint inventory, route classification, risk labels, data-source labels, test recommendations.
- Unsafe work blocked: adding auth, removing endpoints, changing access behavior, changing execution behavior.
- Required evidence: `docs/API_EXPOSURE_INVENTORY.md` lists all decorated endpoints and static mounts.
- Human review needed: Yes for payment, refund, wallet, execution, risk-policy, and public-claims routes.
- Exit criteria: Every route has method, path, current access, intended access, data type, risk, tests, and human-review status.
- Next gate unlocked: API exposure test plan.

### 3. API Exposure Test Plan

- Purpose: Convert route exposure concerns into concrete test coverage before code changes.
- Safe work allowed: test planning, current-behavior test design, intended-behavior test design, coverage mapping.
- Unsafe work blocked: adding production auth, changing endpoint access, changing payment or execution behavior.
- Required evidence: `docs/API_EXPOSURE_TEST_PLAN.md` separates current behavior from intended behavior and names tests.
- Human review needed: No for test planning; yes before wallet/payment/execution behavior changes.
- Exit criteria: The first safe test task is small, additive, and reviewable.
- Next gate unlocked: Mock/local-only guardrails.

### 4. Mock/Local-Only Guardrails

- Purpose: Ensure local-review mocks cannot be mistaken for production security or production payment proof.
- Safe work allowed: tests proving mock labels, synthetic demo labels, disabled execution defaults, and no signing/submission fields.
- Unsafe work blocked: real wallet auth, real production payment credits, signer changes, live execution.
- Required evidence: tests for `local-review-mock`, synthetic demo responses, public config redaction, and `/api/execute-best` default block.
- Human review needed: Yes before replacing mock wallet/session behavior.
- Exit criteria: Current mock/local-only behavior is pinned by tests and production-only behavior is either blocked or reviewed.
- Next gate unlocked: Public/dashboard data safety.

### 5. Public/Dashboard Data Safety

- Purpose: Prevent public users from seeing fresh executable routes, private operations data, or misleading claims.
- Safe work allowed: freshness/delay tests, source-label tests, public report redaction tests, redaction contract docs, copy review docs.
- Unsafe work blocked: fresh raw opportunity feeds, public strategy leakage, public payment/refund/live/reconciliation details.
- Required evidence: tests proving public opportunities and pulse respect delay/redaction policy; public report tests; public record redaction contract and human review checklist.
- Human review needed: Yes for public data policy and public claims.
- Exit criteria: Public data is delayed, aggregate, redacted, or clearly source-labeled.
- Next gate unlocked: Wallet connection boundary.

### 6. Wallet Connection Boundary

- Purpose: Define what wallet connection can and cannot prove.
- Safe work allowed: wallet UX/session planning, docs, mock-only UI labels, tests proving frontend role does not grant backend access.
- Unsafe work blocked: production wallet proof, custody, user deposits, backend key handling, payment receiver activation without review.
- Required evidence: human-approved wallet proof design and tests that backend role is not frontend-controlled.
- Human review needed: Yes.
- Exit criteria: Wallet proof, session scope, PNET access checks, and no-custody language are approved and testable.
- Next gate unlocked: Paper trading evidence.

### 7. Paper Trading Evidence

- Purpose: Prove route behavior with no funds before any execution discussion.
- Safe work allowed: paper-trade logging, 5s/30s/60s decay analysis, daily reports, confidence calibration, replay lab tests.
- Unsafe work blocked: live execution, signer use, real transaction submission, guaranteed-performance claims.
- Required evidence: paper-trade history, expected vs simulated results, quote decay, confidence calibration, daily reports.
- Human review needed: No for paper-only analytics; yes for public claims based on results.
- Exit criteria: Paper trading evidence explains wins, losses, decay, and rejection reasons over the required sample period.
- Next gate unlocked: Route/risk explainability.

### 8. Route/Risk Explainability

- Purpose: Ensure every route decision has a complete explanation.
- Safe work allowed: route forensics, risk decision tests, rejection reason coverage, confidence scoring tests.
- Unsafe work blocked: loosening risk limits, expanding app/asset allowlists without review, using risk approval as permission to trade.
- Required evidence: route hash, path, profitability, freshness, impact, liquidity, risk result, decision, and rejection reason.
- Human review needed: Yes for risk-policy changes and allowlist changes.
- Exit criteria: No route can exist without a recorded explanation and risk outcome.
- Next gate unlocked: Dry-run transaction boundary.

### 9. Dry-Run Transaction Boundary

- Purpose: Keep dry-run construction clearly unsigned and non-submitting.
- Safe work allowed: unsigned-only tests, dry-run shape validation, route-hash validation docs, non-submission assertions.
- Unsafe work blocked: signing, submitting, signer integration, hot-wallet access, production execution flags.
- Required evidence: dry-run responses contain no signed transactions, no mnemonic/private key data, and no submission receipts.
- Human review needed: Yes.
- Exit criteria: Dry-run builder can only produce reviewed unsigned artifacts and cannot submit transactions.
- Next gate unlocked: Signer review only.

### 10. Signer Review Only

- Purpose: Keep signer work isolated until every earlier gate is complete and reviewed.
- Safe work allowed: signer policy review docs, threat modeling, test planning, no-code architecture notes.
- Unsafe work blocked: signer code changes, mnemonic handling, private key storage, hot-wallet logic, transaction signing.
- Required evidence: human-approved signer isolation review, route-hash policy, app/asset allowlists, fee limits, kill-switch checks.
- Human review needed: Yes.
- Exit criteria: Signer policy is reviewed without changing signer code in this gate.
- Next gate unlocked: Live micro-execution gate.

### 11. Live Micro-Execution Gate

- Purpose: Prevent live execution until scanner, paper, route, risk, dry-run, and signer review evidence exists.
- Safe work allowed: docs, go/no-go checklist, manual reconciliation plan, public-safe receipts plan.
- Unsafe work blocked: live trading, transaction submission, hot-wallet funding logic, automated execution, user funds.
- Required evidence: all prior gates complete; human approval; manual tiny own-funds trade plan; reconciliation plan; rollback plan.
- Human review needed: Yes.
- Exit criteria: Not available in current Phase 0. This gate remains blocked until prior evidence exists.
- Next gate unlocked: None. This is the last Phase 0 safety gate before any future live pilot.

## Human-Review-Required Areas

Human review is required before any change involving:

- wallet proof, wallet connection boundary, or Pera production integration
- payment receiver, payment verification policy, refund policy, PNET credits, or user receipts
- signing, signer code, signer secrets, mnemonic handling, or private keys
- dry-run behavior that approaches signing or submission
- live execution, execution flags, hot-wallet funding, custody, reserve, or transaction submission
- risk limits, app allowlists, asset allowlists, or route policy
- public claims, public freshness policy, public receipts, or public strategy data
- new dependencies, broad refactors, or new systems that duplicate existing patterns

## Stop Conditions

Stop and mark the work `BLOCKED` if:

- a task asks for live trading, signing, transaction submission, hot-wallet logic, or signer changes
- a public route could expose fresh executable routes
- a mock route could be mistaken for production proof
- a payment or refund route exposes global records publicly
- a task could imply profit, passive income, copy trading, managed strategy, user deposits, or guaranteed returns
- a change requires wallet, payment, execution, risk-policy, or public-claims approval that has not happened

## Churn Prevention Rule

Codex must not leave safety concerns as open-ended warnings. Every concern must become exactly one of:

- blocked item
- human-review item
- test-planning item
- safe implementation item
- completed item

If the next action is unsafe, mark it `BLOCKED` and recommend the safest prerequisite. If the next action is safe, make it small enough for one reviewable diff.

Use `docs/API_WARNING_DISPOSITION.md` for API exposure warnings. Do not create a new checklist if an existing checklist already covers the issue.

## Whitepaper Delta Rule

Every review or coding churn should end with a `Whitepaper Delta` after the current gate status. Use it to say whether the task created a confirmed fact that belongs in `docs/WHITEPAPER_WORKING_DRAFT.md`.

Allowed outputs:

- `No whitepaper update needed this churn.`
- `Whitepaper update recommended: [section] - [specific fact/change/risk/evidence].`
- `Whitepaper update blocked: missing source/evidence needed is [specific item].`

Do not add or propose whitepaper claims unless they are backed by repo files, tests, staging evidence, or verified external sources.

## xChain Learning Delta Rule

xChain Accounts are a bounded learning/product-access track only. They do not modify Phase 0 scanner, quote, route, risk, paper, dry-run, signer, or execution gates.

Every review or coding churn should include an `xChain Learning Delta`:

- `No xChain update needed this churn.`
- `xChain learning update recommended: [specific concept/risk/use-case to document].`
- `xChain implementation not appropriate yet: [reason].`

Implementation remains blocked unless a human separately approves wallet, payment, account-linking, bridge, public-claims, and security review. Do not let xChain exploration touch signer, wallet custody, transaction submission, live execution, or fresh route access.

## Current Gate Status Template

Every Codex output should end with:

```text
## Current Gate Status

Current Gate:
- Gate name:
- Gate purpose:
- Current status: NOT STARTED / IN PROGRESS / BLOCKED / READY FOR REVIEW / COMPLETE
- Why this gate matters:
- What changed in this task:
- What evidence was produced:
- What is still unknown:
- Human review required: YES / NO
- Stop conditions:
- Next safe action:
- Next Codex prompt:

Progress Table:
| Gate | Status | Evidence | Risk | Human Review | Next Action |
|---|---|---|---|---|---|

## Whitepaper Delta

- No whitepaper update needed this churn.

## xChain Learning Delta

- No xChain update needed this churn.
```

## Next Safe Action

Return to one small core-engine evidence task:

```text
Codex, implement one small paper-trading evidence improvement. Inspect the existing scanner, quote, route, and paper-trade flow, then add a targeted test or stored evidence field that proves scanner output can become comparable quotes, route candidates, and paper-trade evidence. Do not touch signer, execution, hot-wallet, transaction submission, risk limits, wallet code, or public claims.
```
