# Safety Checklist

Run this checklist before merging or handing off AI-assisted changes.

## Secrets Check

- [ ] No `.env` file with real values is added.
- [ ] No mnemonics, private keys, seed phrases, wallet exports, or signer secrets appear in code, docs, logs, screenshots, tests, or fixtures.
- [ ] No `secrets.json`, `*.mnemonic`, `*.seed`, or `*.key` file is staged.
- [ ] CI secret guards pass.

## Execution Check

- [ ] No live trading is added.
- [ ] No transaction signing is added.
- [ ] No transaction submission is added.
- [ ] No hot-wallet funding, custody, or reserve logic is added.
- [ ] `ENABLE_EXECUTION=false`, `ENABLE_SIGNER=false`, and `KILL_SWITCH=true` remain the safe defaults.
- [ ] Risk limits are not loosened.

## Signer Check

- [ ] `src/algopulse/signer.py` is untouched unless a human explicitly approved signer work.
- [ ] No signer secret path is moved into the repo.
- [ ] No scanner, API, dashboard, or main executor path can sign directly.

## Public Claims Check

- [ ] No profit, passive-income, yield, safe-return, or guaranteed-return claims are introduced.
- [ ] Public copy uses market intelligence, scanner evidence, simulation, paper trading, delayed reports, or research language.
- [ ] Synthetic demos are labeled synthetic.

## Data Labeling Check

- [ ] Dashboard metrics are labeled `mock`, `stored`, `live`, `delayed`, or `unavailable`.
- [ ] Mock data is visibly marked.
- [ ] Public data is delayed, redacted, or aggregate.
- [ ] Fresh executable route data remains admin-only.

## Anti-Bloat Check

- [ ] Existing architecture and docs were inspected before adding files.
- [ ] No duplicate system was created where an existing pattern fits.
- [ ] No new dependency was added without clear justification.
- [ ] Scanner, dashboard, wallet, signer, and execution logic stay in separate modules.
- [ ] No giant file or unrelated refactor was introduced.
- [ ] Temporary, local-review, or mock code is labeled and isolated.
- [ ] Mock data is visibly labeled `mock`.
- [ ] Existing public behavior is preserved unless the task explicitly changes it.

## Tests And QA

- [ ] Relevant unit/integration/security tests were added or updated.
- [ ] `python -m pytest -q` passes, or failures are documented.
- [ ] `node --check src/algopulse/static/app.js` passes when dashboard JS changes.
- [ ] `git diff --check` passes.
- [ ] Browser QA is done for dashboard changes.

## Human Approval Check

- [ ] Wallet, signing, execution, risk-limit, public-claims, deployment, or allowlist changes are marked human-review required.
- [ ] Risky changes include evidence, reviewer, approved scope, and rollback path.
- [ ] Blocked Phase 0 items remain blocked.
