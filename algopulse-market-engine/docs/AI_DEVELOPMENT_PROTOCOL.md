# AI Development Protocol

Use this protocol for Codex, Claude, and any AI-assisted change to AlgoPulse.

For non-trivial AI work, apply `docs/AI_WORKFLOW_GOVERNOR.md` first: define the outcome, choose the work mode, resolve ambiguity, execute with evidence, verify, then report the current gate status.

## Product Direction

AlgoPulse is a Phase 0 Algorand market intelligence and arbitrage research system. The product surfaces are scanner evidence, route simulation, paper trading, risk explanations, delayed/public-safe reports, PNET market-data access, and admin readiness views.

The product is not a public trading bot, user-funds system, passive-income product, or guaranteed-return product.

## Current Safe Phase

Current safe mode is scanner, paper trading, dry-run observability, and admin control-plane review. Live execution and signing remain locked until the human review gates pass.

Default safety posture:

- `ENABLE_EXECUTION=false`
- `ENABLE_SIGNER=false`
- `KILL_SWITCH=true`
- no user deposits
- no frontend wallet keys
- no raw fresh opportunities in public views

## Codex May Work On

- docs, tests, handoff notes, and release checklists
- scanner evidence and service-health observability
- route math, risk math, and paper-trading analytics with tests
- dashboard UI/UX for source-labeled mock, stored, live, delayed, and unavailable data
- admin-only readiness, provenance, evidence, reports, and failure simulation views
- PNET user flows for market-data fees, credits, reports, scans, and simulations only

## Codex Must Not Touch Without Human Review

- `src/algopulse/signer.py`
- signer secret loading or storage
- hot-wallet funding, reserve, custody, or inventory logic
- transaction signing or submission
- production risk limits
- live execution flags or automation flags
- app/asset allowlist expansion
- public claims about profit, passive income, or guaranteed returns

## Expected Codex Output

Every implementation task should return:

- files changed
- safety scope
- what is mock, stored, live, delayed, or unavailable
- tests run
- what remains blocked
- human-review-required areas
- suggested next small task
- `Whitepaper Delta` with either no update needed, a specific evidence-backed update, or a blocked update needing evidence
- `xChain Learning Delta` with either no update needed, a specific learning update, or a reason implementation is not appropriate yet

For planning tasks, separate repo facts from assumptions and unknowns.

For review, troubleshooting, or high-risk tasks, use the mode and verification rules in `docs/AI_WORKFLOW_GOVERNOR.md` before making recommendations.

Every Codex response should end with a `Current Gate Status` section using this structure:

```text
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
```

Every review or coding churn should also include:

```text
### Whitepaper Delta

- No whitepaper update needed this churn.
```

Or:

```text
### Whitepaper Delta

- Whitepaper update recommended: [section] - [specific fact/change/risk/evidence].
```

Or:

```text
### Whitepaper Delta

- Whitepaper update blocked: missing source/evidence needed is [specific item].
```

Only propose whitepaper changes backed by repo files, tests, staging evidence, or verified external sources. Use `docs/WHITEPAPER_WORKING_DRAFT.md` as the working paper and do not overstate readiness.

Every review or coding churn should also include:

```text
### xChain Learning Delta

- No xChain update needed this churn.
```

Or:

```text
### xChain Learning Delta

- xChain learning update recommended: [specific concept/risk/use-case to document].
```

Or:

```text
### xChain Learning Delta

- xChain implementation not appropriate yet: [reason].
```

Use `docs/XCHAIN_ACCOUNTS_LEARNING_TRACK.md` for bounded xChain research. Do not let xChain exploration expand Phase 0 scope or touch signer, bridge, wallet custody, transaction submission, live execution, or route-execution code.

Use these rolling gates:

1. Project orientation and repo hygiene
2. API exposure inventory
3. API exposure test plan
4. Mock/local-only guardrails
5. Public/dashboard data safety
6. Wallet connection boundary
7. Paper trading evidence
8. Route/risk explainability
9. Dry-run transaction boundary
10. Signer review only
11. Live micro-execution gate, blocked until prior evidence exists

Progress rules:

- Do not create a new checklist if an existing checklist already covers the issue.
- Convert each risk into a specific next action.
- If the next action is unsafe, mark it `BLOCKED` and recommend the safest prerequisite.
- If the next action is safe, make it small enough for one reviewable diff.
- Never recommend live trading, signer changes, transaction submission, or hot-wallet logic unless all required prior gates are complete and human-approved.

## Anti-Bloat Rules

- Inspect the existing architecture before adding files.
- Do not create duplicate systems if an existing pattern already fits.
- Prefer one small reviewable diff.
- Do not add a dependency unless it is clearly justified in the task summary.
- Do not mix scanner, dashboard, wallet, signer, and execution logic in the same module.
- Do not create giant files; split only along existing architecture boundaries.
- Do not create temporary code unless it is clearly labeled as temporary, mock, or local-review only.
- Isolate mock data and label it `mock` wherever it appears.
- Preserve existing public behavior unless the task explicitly changes it.
- Do not redesign unrelated modules.
- Do not duplicate existing docs; link or cite them.
- Add abstractions only when they remove real duplication or clarify a safety boundary.
- Avoid broad speculative architecture.
- Keep public-facing copy short and conservative.
- Add tests for changed behavior; do not add dashboards that cannot be traced to data.

## Architecture Boundaries

- Scanner is read-only and must not require key material.
- Route engine produces candidates and explanations, not permission to trade.
- Risk engine rejects most routes and records why.
- Paper trading is no-funds simulation evidence.
- Dry-run builder may construct unsigned groups only.
- Signer is an isolated future boundary, not a control-plane feature.
- Public dashboard is delayed, redacted, and source-labeled.

## Data Labeling

Every displayed metric should be labeled as one of:

- `mock`
- `stored`
- `live`
- `delayed`
- `unavailable`

Mock data must never be presented as production evidence. Live or fresh executable route data must not be exposed publicly.

## Review Size Target

A good Codex change is easy to review in one pass:

- 1 focused feature or fix
- narrow file set
- tests included
- no unrelated formatting churn
- no hidden environment or runtime behavior changes
