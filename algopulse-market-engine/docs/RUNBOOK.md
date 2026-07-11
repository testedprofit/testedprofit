# Phase 0 Runbook

## Safe Startup

1. Install dependencies.
2. Copy `.env.example` to a local env file outside version control.
3. Keep `ENABLE_EXECUTION=false`, `ENABLE_SIGNER=false`, and `KILL_SWITCH=true`.
4. Run tests.
5. Start FastAPI on `127.0.0.1:8766`.
6. Open the dashboard.

## Daily Control-Plane Check

1. Review `GET /api/config/public`.
2. Connect the review admin preset in the dashboard.
3. Run admin preflight.
4. Run a read-only scan.
5. Review delayed routes and paper trades.
6. Review the paper daily report.
7. Review the admin alert catalog and confirm no new critical conditions are active.
8. Confirm PNET fee quote/confirm stubs still say market-data credit only.

## Exit Criteria For This Phase

- Scanner can run without signer operational secrets.
- Quote and route math have pure tests.
- Risk math has pure tests.
- Admin controls are backend-gated.
- Alert catalog is role-gated and covers scanner, connector, quote, route, storage, risk, signer-boundary, wallet, loss-limit, live-trade, and reconciliation failures.
- Dashboard shows delayed intelligence and paper-trading performance.
- PNET user flows are limited to market-data fees, credits, scan requests, route simulations, and reports.

Live execution work starts only in the later reviewed path.
