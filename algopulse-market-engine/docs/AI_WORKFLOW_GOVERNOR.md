# AI Workflow Governor

This adapts the `ai-workflow-governor` skill from `robmadeskills.zip` into the AlgoPulse repo workflow.

Use it for complex, ambiguous, high-stakes, multi-step, tool-using, review, coding, planning, or troubleshooting tasks. It does not override `docs/AI_DEVELOPMENT_PROTOCOL.md`, `docs/HUMAN_REVIEW_GATES.md`, `docs/SAFETY_CHECKLIST.md`, platform rules, or user instructions.

## Operating Loop

1. Define the outcome.
   - State the requested deliverable in one sentence.
   - Identify success criteria, constraints, must-not-do items, and current gate.

2. Choose the work mode.
   - Use the mode that controls the highest-risk part of the task.
   - Keep mode choice internal unless naming it helps the handoff.

3. Resolve ambiguity.
   - Ask only when missing information blocks a safe or useful result.
   - Otherwise make a bounded assumption and continue.

4. Plan only as much as needed.
   - Use short plans for long or tool-heavy work.
   - Do not let planning replace execution.

5. Execute with evidence.
   - Inspect files, run tests, search source, or use current sources when the answer depends on them.
   - Do not claim to have read, tested, searched, modified, pushed, or verified anything unless it happened.

6. Verify before finalizing.
   - Check the result against the task, gate, and safety constraints.
   - Say what was not checked.

7. Deliver clearly.
   - Put the result first.
   - Include assumptions, risks, tests, and next action only when useful.

## Work Modes

| Mode | Use When | Required Evidence |
|---|---|---|
| Direct answer | Simple explanation or decision | Clear answer and stated assumptions if needed |
| Research | Current, niche, disputed, or externally verifiable facts | Primary/current sources and caveats |
| Planning | Roadmaps, operating procedures, rollout plans | Phases, dependencies, risks, first action |
| Troubleshooting | Something is failing or unclear | Symptoms, hypotheses, tests, conclusion |
| Build/edit artifact | Code, docs, files, UI, reports, templates | Changed files and validation result |
| Review/risk | QA, security, safety, compliance, maintainability | Findings separated by fact/assumption/unknown |
| Decision support | Choosing between options | Criteria, recommendation, tradeoff, switch condition |

## Verification Rules

- Use `python scripts/repo_guard.py` before handoff.
- Use `python -m pytest -q` when behavior, APIs, store logic, or tests changed.
- Use `node --check src/algopulse/static/app.js` when dashboard JS changed.
- Use `git diff --check` before commit or handoff.
- Do not call work complete if relevant checks were skipped without explaining why.

## AlgoPulse-Specific Safety Overlay

Always preserve the current safe mode unless a human explicitly approved a later gate:

- no live trading
- no signer changes
- no transaction submission
- no hot-wallet funding or custody logic
- no production risk-limit changes
- no unreviewed app/asset allowlist expansion
- no public fresh executable route data
- no profit, passive-income, copy-trading, managed-strategy, or guaranteed-return claims

Every risk must become one of:

- blocked item
- human-review item
- test-planning item
- safe implementation item
- completed item

## Communication Pattern

For non-trivial tasks:

1. Briefly say what you are checking or changing.
2. Share important findings only when they affect the result.
3. Finalize with files changed, checks run, facts proven, assumptions, unknowns, and current gate status.
4. Include a `Whitepaper Delta` when the task creates or changes confirmed architecture, safety, evidence, phase, metric, risk, PNET utility, or product-positioning facts.
5. Include an `xChain Learning Delta`; keep xChain Accounts work as learning/product-access research unless a human separately approves implementation.

Avoid repetitive progress updates, unsupported certainty, and broad speculative architecture.

## Two-Agent Production Churn

Use this workflow when Grok and Codex collaborate on the same milestone. The goal is faster production progress with one builder and one accountable reviewer, not two agents editing concurrently or approving their own claims.

### Roles

- **Grok / Builder:** implements one production capability, records runtime evidence, and stops after the handoff. It does not approve its own readiness claims, start the next task, commit, push, or broaden scope.
- **Codex / Senior QA and Integrator:** reads the actual diff and evidence, reproduces only the checks needed to verify material claims, identifies production blockers, integrates narrow fixes when requested, updates evidence-backed docs, and owns the git checkpoint.
- **Human / Product owner:** approves wallet, signing, execution, risk-policy, public-claims, deployment, and release-gate decisions.

### Churn Sequence

1. Codex gives Grok one outcome-based builder brief with acceptance criteria and stop conditions.
2. Grok implements only that brief and returns the builder handoff below.
3. Grok stops editing. No second task begins in the same handoff.
4. Codex reviews source and artifacts rather than trusting the summary alone.
5. Codex issues one verdict: `PASS`, `PASS_WITH_FIXES`, or `REJECT`.
6. Only a passing verdict may become a commit, push, deployment candidate, whitepaper fact, or input to the next production task.
7. Codex derives the next Grok brief from the verified production blocker, not from speculative feature lists.

### Single-Writer Rule

- Grok and Codex must not edit the same worktree at the same time.
- The active agent records the branch, base commit, and initial `git status --short`.
- Grok must list every changed file and disclose any running process, database, artifact, or environment profile it created.
- Codex owns milestone commits and pushes unless the human explicitly assigns that responsibility elsewhere.
- Unexpected changes are preserved and attributed; neither agent resets or rewrites the other agent's work.

### Builder Handoff

Every Grok implementation handoff must contain:

```text
Outcome:
Base branch and commit:
Files changed:
Behavior added:
Runtime processes started/stopped:
Data stores and artifacts:
Live evidence with raw timestamps/rounds:
Tests/checks run:
Known limitations:
Claims requiring Codex verification:
Exact remaining production blocker:
Safety boundaries preserved:
```

The builder must not describe sampled rounds as consecutive, mock evidence as live, generated screenshots as application proof, or refreshed timestamps as source timestamps.

### Codex QA Verdict

Codex must return:

```text
Verdict: PASS / PASS_WITH_FIXES / REJECT
Confirmed capabilities:
Unsupported or false claims:
Production-impact findings:
Required fixes before checkpoint:
Checks reproduced:
Files integrated:
Commit/push status:
Next builder brief:
```

The review must check arithmetic and temporal claims directly. Examples include round-range continuity, quote age measured from source capture time, unit consistency, process liveness, source labels, and whether a claimed live path actually uses the production code path.

### Churn Prevention

- One builder churn gets one focused senior review, not repeated audit documents.
- Every finding must become a required fix, accepted limitation, human-review decision, or blocked item.
- Do not add tests merely to increase counts. Add the minimum deterministic coverage needed to prevent the reviewed defect from returning.
- Do not repeat the full suite when no relevant code changed; run focused checks first and the release suite only at a checkpoint.
- Dashboard and documentation work must not interrupt engine work unless the UI is materially misleading or a confirmed fact belongs in the whitepaper.
- Runtime evidence must use original source rounds and capture timestamps. Never rewrite evidence to make freshness, continuity, or latency appear better.
