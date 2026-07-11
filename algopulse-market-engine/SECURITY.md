# Security Policy

AlgoPulse is a private Phase 0 Algorand market-intelligence and arb-research repo. Treat wallet, signing, payment, refund, route, and execution-adjacent behavior as human-review-required.

## Supported Scope

Current supported scope:

- scanner, quote, route, risk, and paper-trading evidence
- delayed or redacted public dashboard data
- admin-only operational evidence
- unsigned dry-run validation
- documentation and deterministic tests

Out of scope until prior gates pass:

- live trading
- transaction signing or submission
- hot-wallet funding or custody
- user deposits
- production wallet/payment activation
- public fresh route feeds

## Reporting Sensitive Issues

If you find a secret, wallet key, mnemonic, signing path, public fresh route leak, or unsafe execution path:

1. Do not open a public issue with the sensitive value.
2. Stop the change and mark the affected gate as blocked.
3. Notify the repo owner directly.
4. Record a redacted finding in the relevant checklist or gate tracker.

## Required Local Checks

Run before handoff:

```powershell
python scripts/repo_guard.py
node --check src/algopulse/static/app.js
python -m pytest -q
git diff --check
```

See `docs/SAFETY_CHECKLIST.md` and `docs/HUMAN_REVIEW_GATES.md` for the full review policy.
