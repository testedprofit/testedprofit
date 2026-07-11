# API Exposure Review Checklist

Use this checklist after reading `docs/API_EXPOSURE_INVENTORY.md` and before approving any production deployment, wallet/payment work, auth change, dry-run change, or execution-adjacent work.

This is a documentation-only review artifact. It does not authorize backend fixes by itself.

## Prompt Guardrails Applied

Discernment:

- Judge whether the API exposure inventory is evidence-based and useful.
- Require route-level evidence from `src/algopulse/api.py` before accepting a conclusion.
- Separate repo facts from assumptions and unknown deployment details.

Diligence:

- Do not jump from audit into risky backend fixes.
- Treat wallet, signing, payment, refund, admin auth, dry-run, live execution, risk policy, and public claims as human-review-required.
- Keep live trading, signer changes, transaction submission, hot-wallet logic, risk-limit changes, and secrets out of scope.

Description:

- Produce a specific, reviewable artifact for deciding what can be safely exposed.
- Review public, connected-user, admin, local-only, disabled, mock, payment, refund, route, and execution-adjacent surfaces.
- Use the inventory counts as the review baseline: `60` exposed surfaces, including `59` decorated FastAPI endpoints and `1` static asset mount.

Delegation:

- Safe Codex task type: docs-only review preparation.
- Unsafe delegation without human approval: implementing auth, wallet proof, signer behavior, payment mutation changes, execution controls, live trading, or deployment rules.

## Stop Conditions

Stop the review and do not approve production exposure if any item is true:

- [ ] Any route can sign, submit, or trigger live transactions without a separate approved execution gate.
- [ ] Any public route exposes fresh executable opportunity data.
- [ ] Any public route exposes private wallet, payment, refund, balance, or reconciliation details.
- [ ] Any route relies on `local-review-mock` auth outside local review.
- [ ] `POST /api/execute-best` can become public execution through an environment flag alone.
- [ ] Mock PNET confirmations can grant real production credits.
- [ ] Static assets can serve `.env`, secret, mnemonic, seed, key, or private build artifacts.
- [ ] Public copy implies guaranteed returns, passive income, copy trading, managed strategy, or user deposits.

## Inventory Completeness Check

- [ ] Confirm `docs/API_EXPOSURE_INVENTORY.md` lists `60` exposed surfaces.
- [ ] Confirm `src/algopulse/api.py` has no unlisted `@app.get`, `@app.post`, `@app.put`, `@app.delete`, `@app.patch`, or mounted route.
- [ ] Confirm no additional `APIRouter`, `include_router`, `add_api_route`, or Starlette mount exists outside the inventory.
- [ ] Confirm each route has method, path, function evidence, current access behavior, intended access, data type, risk, redaction/delay requirement, tests, and human-review status.

Evidence to inspect:

- `src/algopulse/api.py`
- `docs/API_EXPOSURE_INVENTORY.md`

## Public Route Review

Routes currently intended as public or public-safe after review:

- `/`
- `/static/*`
- `/health`
- `/api/health`
- `/api/config/public`
- `/api/events/user-action`
- `/api/pulse`
- `/api/pools`
- `/api/opportunities`
- `/api/risk-policy`
- `/api/reports/paper/daily`
- `/api/reports/market/daily`
- `/api/reports/market/archive`
- `/api/reports/market/daily/export`

Checklist:

- [ ] Public health/config responses expose no secrets, private endpoints, wallet data, or production credentials.
- [ ] Public market data is delayed, aggregate, or non-actionable.
- [ ] `/api/opportunities` cannot expose fresh executable routes.
- [ ] `/api/events/user-action` has bounded payloads, accepted taxonomy only, and no sensitive user metadata.
- [ ] Static assets contain only public frontend files.
- [ ] Public reports are framed as market intelligence, simulation, paper trading, or research.

Required tests before production:

- [ ] Health/config smoke tests.
- [ ] Public config secret-redaction test.
- [ ] Fresh-route exclusion test for public opportunities.
- [ ] Static asset negative check for `.env` and secret file exposure.
- [ ] Product analytics payload validation and rate-limit plan.

## Local-Only Or Mock Route Review

Routes to keep local-only or clearly mock until replaced:

- `/api/session/wallet/{address}`
- `/api/demo-run`

Checklist:

- [ ] `/api/session/wallet/{address}` is not treated as real wallet proof.
- [ ] Any admin role returned by the mock wallet session is labeled `local-review-mock`.
- [ ] `/api/demo-run` remains synthetic and cannot be presented as production performance.
- [ ] Production mode rejects or hides local-only routes unless human-approved.

Required tests before production:

- [ ] Production-mode rejection test for mock wallet sessions.
- [ ] Synthetic demo labeling test.
- [ ] Non-admin cannot obtain admin access through frontend role state.

## Connected User And PNET Review

Routes intended for connected users after real wallet/session proof:

- `/api/user/pnet/access-check`
- `/api/user/pnet/fee-quote`
- `/api/user/pnet/fee-confirm`
- `/api/verify-payment`

Checklist:

- [ ] Wallet proof is backend-enforced, not frontend-only.
- [ ] PNET access checks are on-chain or clearly labeled local-review mock.
- [ ] Fee quotes are for market-data access, scans, simulations, reports, or credits only.
- [ ] Fee confirmation does not sign, submit, trade, or custody funds.
- [ ] Mock txids cannot grant production credits.
- [ ] Payment verification does not expose global payment history.

Required tests before production:

- [ ] PNET fee quote shape and action allowlist tests.
- [ ] Mock fee confirmation rejected outside local review.
- [ ] Real tx verification path tested with mocked indexer responses.
- [ ] Connected-user access cannot mutate admin/payment/refund records.

## Payment, Refund, And Record Review

Routes that must not be public as detailed records:

- `/api/payment-verifications`
- `/api/refund-cases`
- `/api/refund-cases/{case_id}/status`
- `/api/live-trades`
- `/api/reconciliations`
- `/api/paper-trades`

Checklist:

- [ ] Payment verification history is admin-only or user-owned and redacted.
- [ ] Refund queue and refund status mutation are admin-only.
- [ ] Live trade and reconciliation records are admin-only or public-redacted receipts.
- [ ] Paper trade details do not expose fresh route strategy publicly.
- [ ] No endpoint creates user deposit expectations.

Required tests before production:

- [ ] Non-admin rejection tests for detailed payment/refund/live/reconciliation records.
- [ ] User-owned receipt access tests if user-facing receipts are added.
- [ ] Redaction tests for wallet addresses, balances, tx details, and fresh timing.

## Admin Observability Review

Admin observability surfaces include:

- `/api/admin/preflight`
- `/api/admin/alerts/catalog`
- `/api/admin/policy/catalog`
- `/api/ops/*`

Checklist:

- [ ] Backend enforces admin access for every admin observability route.
- [ ] `local-review-mock` admin proof is replaced or blocked before production.
- [ ] Route forensics, replay, provenance, heatmap, confidence, and decay views do not become public fresh-route feeds.
- [ ] Product validation analytics are aggregated and privacy-reviewed.
- [ ] Mock, stored, live, delayed, and unavailable data are clearly labeled.

Required tests before production:

- [ ] Non-admin rejection tests for every admin observability route.
- [ ] Source-label tests for mock/stored/live/delayed/unavailable data.
- [ ] Public-safe redacted summaries tested separately from admin views.

## Admin Command Review

Admin command routes:

- `/api/admin/scan-now`
- `/api/admin/scanner/start`
- `/api/admin/scanner/pause`
- `/api/admin/routes/run`
- `/api/admin/paper/start`
- `/api/admin/dry-run/build`
- `/api/admin/live/arm`
- `/api/admin/live/disarm`
- `/api/admin/kill-switch/trigger`
- `/api/admin/kill-switch/clear`

Checklist:

- [ ] All command routes require backend admin proof.
- [ ] Scanner, route, and paper commands remain read-only or simulation-only.
- [ ] Dry-run builder remains unsigned-only.
- [ ] Live arm remains disabled until production gates pass.
- [ ] Kill-switch clear remains disabled or separately approved.
- [ ] Every command has audit logging before production.

Required tests before production:

- [ ] Non-admin rejection tests for all command routes.
- [ ] Command audit record tests.
- [ ] Dry-run unsigned-only assertion.
- [ ] Live arm blocked when execution is disabled or kill switch is active.
- [ ] Kill-switch clear rejection test.

## Disabled Or Execution-Adjacent Review

Routes requiring explicit human review before implementation changes:

- `/api/execute-best`
- `/api/admin/live/arm`
- `/api/admin/kill-switch/clear`
- `/api/admin/dry-run/build`

Checklist:

- [ ] No public execution path exists.
- [ ] Environment flags alone cannot enable public execution.
- [ ] Dry-run output cannot be signed or submitted by this API.
- [ ] Live execution remains disarmed by default.
- [ ] Signer code and secret handling remain untouched.

Required tests before production:

- [ ] `/api/execute-best` cannot execute in production without admin, kill-switch, risk, signer-isolation, and human-approved gates.
- [ ] Live arm cannot bypass disabled execution config.
- [ ] Kill-switch clear cannot be performed without a separate human-approved policy.

## Human Sign-Off Record

Before approving any risky endpoint change, record:

- Reviewer:
- Date:
- Route(s):
- Evidence reviewed:
- Approved access level:
- Required redaction or delay:
- Required tests:
- Explicit exclusions:
- Rollback plan:

## Safe Next Codex Task

After this checklist is reviewed, the next safe Codex task is test planning or docs refinement only.

Recommended prompt:

```text
Using docs/API_EXPOSURE_INVENTORY.md and docs/API_EXPOSURE_REVIEW_CHECKLIST.md, create docs/API_EXPOSURE_TEST_PLAN.md only. List the exact security and regression tests needed for public, connected-user, admin, local-only, disabled, payment/refund, and execution-adjacent routes. Do not change application logic.
```
