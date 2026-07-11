# Version Control

This project should be managed like a private production bot repo, even while live execution is disabled.

## Repo Model

Use two repos when this grows:

```text
private source repo: scanner, execution code, runbooks, tests, deployment configs
public repo: marketing site, public docs, delayed/redacted dashboard only
```

Do not publish wallet logic, execution flags, production logs, raw market database snapshots, or route timing details until a deliberate public-data policy exists.

## Branches

Protected branch:

```text
main
```

Working branches:

```text
feature/<short-name>
fix/<short-name>
docs/<short-name>
ops/<short-name>
risk/<short-name>
```

Examples:

```text
fix/stale-route-filter
risk/balance-reconciliation
ops/private-deploy-env
docs/claude-handoff
```

## Commit Style

Use small, reviewable commits with Conventional Commit prefixes:

```text
feat: add PNET pool discovery
fix: reject stale approved routes in readiness
risk: enforce positive net after fees in dashboard policy
docs: add deployment handoff checklist
test: cover target-scoped pool metrics
ops: add CI test workflow
chore: update dependency pins
```

Avoid vague commits like `updates`, `stuff`, or `final`.

## Pull Request Rules

Every PR should answer:

```text
What changed?
Why did it change?
What risk does it add or remove?
How was it tested?
Can it submit live transactions?
Do any env vars, app IDs, asset IDs, or wallet assumptions change?
```

Required before merge:

- `python -m pytest -q`
- changelog entry when behavior changes
- no secrets in diff
- docs updated when env vars, commands, or safety posture change
- browser QA note for dashboard changes
- explicit safety review for execution-path changes

## Release Tags

Use SemVer-like tags:

```text
v0.1.x  scanner, dashboard, dry-run, no submitted live trades
v0.2.x  testnet execution proof
v0.3.x  tiny mainnet hot-wallet execution
v1.0.0  mature production bot with monitoring and incident process
```

Tag only after the release checklist passes:

```powershell
git tag -a v0.1.0 -m "Phase 0 read-only PNET market engine"
git push origin v0.1.0
```

## Files That Must Stay Out Of Git

Never commit:

- `.env` or real env files
- signer secrets and wallet exports
- `data/`
- local SQLite databases
- production logs
- API tokens
- raw signed transactions

Examples are allowed:

- `.env.example`
- `.env.live.example`
- docs with placeholder values

## CI

The included GitHub Actions workflow runs repo hygiene, secret-safety, dashboard syntax, and Python tests on pull requests and pushes to `main`.

Expected local commands:

```powershell
python scripts/repo_guard.py
node --check src/algopulse/static/app.js
python -m pytest -q
git diff --check
```

Formatter and linter checks are wired to run when the repo adds explicit Ruff or Black configuration. Do not add a formatter dependency without a focused review.

## Hotfix Flow

For an urgent safety fix:

1. Branch from `main`.
2. Make the smallest fix.
3. Add or update a regression test.
4. Run tests.
5. Merge after one review.
6. Tag a patch release if deployed.
7. Add a short incident note to `CHANGELOG.md` or a future `docs/incidents/` file.
