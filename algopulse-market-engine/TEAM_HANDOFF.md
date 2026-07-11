# Team Handoff

This is the operating handoff for people or agents joining the AlgoPulse Phase 0 arb bot project.

## Project Snapshot

Source repo: local git repo initialized here; TODO, add private GitHub remote  
Deployment repo: TODO, private deployment repo or private deploy target  
Live URL: local only, `http://127.0.0.1:8766/` in the current Codex session  
Local path: `C:\Users\rober\OneDrive\Documents\Algorand_Phase0_Arb_Bot\phase0-market-engine`  
Frontend framework: FastAPI-served static HTML, CSS, and vanilla JS  
Build command: `python -m pip install -e .`  
Test command: `python -m pytest -q`  
Run command: `python -m uvicorn algopulse.api:app --host 127.0.0.1 --port 8766`  
Deploy command: `docker compose up -d` after env review  
Python setup command: `pip install -r requirements.txt && pip install -e .`; fresh setup uses `py-algorand-sdk`, `fastapi`, `uvicorn`, `pydantic`, `sqlalchemy`, `psycopg2-binary`, `redis`, `python-dotenv`, Tinyman from GitHub, and `pactsdk`  
Current branch: `main`  
Where app IDs live: discovered from Tinyman/Pact pool state and stored in `pool_snapshots.app_id`; connector logic is in `src/algopulse/connectors/` and execution validation is in `src/algopulse/executor.py`  
Where wallet code lives: address/readiness checks in `src/algopulse/executor.py` and `src/algopulse/readiness.py`; isolated key-policy code in `src/algopulse/signer.py`; signer secrets are provisioned outside repo-managed files
Where tool list lives: API routes in `src/algopulse/api.py`; dashboard tools in `src/algopulse/static/index.html` and `src/algopulse/static/app.js`; payment verifier in `src/algopulse/payment_verification.py`; refund queue logic in `src/algopulse/refunds.py`
Where contracts live: no custom PyTeal/contract repo yet  
Where public config lives: `.env.example`, `src/algopulse/config.py`, and `GET /api/config/public`
Where product capabilities live: `GET /api/config/public`, `docs/CAPABILITY_CATALOG.md`, and dashboard Product Capabilities panel
Where production readiness lives: `docs/PRODUCTION_READINESS.md`, `docs/OBSERVABILITY.md`, `.github/workflows/ci.yml`, and `tests/test_production_readiness.py`
Where Control Room lives: admin dashboard tab `Control Room`, safe telemetry endpoints under `GET /api/ops/*`, and frontend components in `src/algopulse/static/app.js`
Where PNET fee runbook lives: `docs/PNET_FEE_FLOW.md`; historical payment-flow notes live in `docs/PNET_PAYMENT_FLOW.md`
Where database schema lives: SQLite bootstrap in `src/algopulse/store.py`; minimum production table shape is documented in `REAL_ARB_BOT_ARCHITECTURE.md`
Where quote storage lives: `src/algopulse/store.py` table `quotes`; route-leg metadata is produced in `src/algopulse/engine.py`
Where route code lives: `src/algopulse/engine.py`; pure route math is in `src/algopulse/route_math.py`; two-leg live execution builder lives separately in `src/algopulse/executor.py`
Where opportunity math lives: `src/algopulse/route_math.py` and `src/algopulse/engine.py`; stored in `opportunities` columns for gross profit, network fees, DEX fees, price impact, slippage buffer, net expected profit, confidence, and skip reason
Where risk policy lives: `src/algopulse/risk.py` for route approval gates and pure risk evaluation, `src/algopulse/config.py` for env defaults, and `src/algopulse/scanner.py` for daily/concurrent execution caps
Where PNET fee flow lives: `POST /api/user/pnet/access-check`, `POST /api/user/pnet/fee-quote`, `POST /api/user/pnet/fee-confirm`, `docs/PNET_PAYMENT_FLOW.md`, and the dashboard PNET access modal in `src/algopulse/static/app.js`
Where paper daily report lives: `MarketStore.paper_daily_report`, `GET /api/reports/paper/daily`, and dashboard panel `#paper-daily-report`
Where deployment modes live: `GET /api/config/public`, `docs/DEPLOYMENTS.md`, and dashboard panel `#deployment-modes`
Where alert catalog lives: `GET /api/admin/alerts/catalog`, `docs/ALERT_CATALOG.md`, and dashboard Logs tab for verified admin sessions
Where policy controls live: `GET /api/admin/policy/catalog`, `docs/POLICY_CONTROLS.md`, and dashboard Bot Control tab for verified admin sessions
Where unsigned execution lives: `src/algopulse/executor.py`; Step 8 builds unsigned atomic groups only and enforces SDK `TX_GROUP_LIMIT`
Where isolated signer lives: `src/algopulse/signer.py`; Step 9 validates route hash, app IDs, asset IDs, fees, input amount, wallet reserve, transaction types, kill switch, sender wallet, and audit logging
Where tiny-live gates live: `src/algopulse/readiness.py`, `.env.tiny-live.example`, and `STEP10_TINY_LIVE_EXECUTION_RUNBOOK.md`
Where paper trading lives: `src/algopulse/scanner.py` records every candidate and `src/algopulse/store.py` table `paper_trades` replays due routes at 5s/30s using fresh pool snapshots
Which repo is public: marketing site or delayed/redacted dashboard only  
Which repo is private: this arb bot, execution code, deployment config, runbooks, and operational history
Target production service chain: Pool Scanner -> Quote Engine -> Route Engine -> Simulator/Paper Trader -> Risk Engine -> Unsigned Executor -> Isolated Signer -> Algorand Network, with every service writing to Postgres/logs/alerts and a delayed public dashboard projection.
Connector priority: Tinyman and Pact first as executable venues; Vestige data for discovery/market context; later Folks routes and other AMMs only after full connector, transaction, and reconciliation review.
Route-pair priority: ALGO/USDC first, then ALGO/major ASAs and USDC/major ASAs. goBTC/goETH routes are later only after liquidity verification.
Route generation contract: generate two-leg venue arb such as `ALGO -> USDC on Tinyman -> ALGO on Pact`, opposite venue direction routes such as `ALGO -> ASA on Pact -> ALGO on Tinyman`, and three-leg ALGO/ASA/USDC triangles for scanner and paper review.
Quote size priority: quote/paper probes use 1, 5, 10, 25, 50, and 100 ALGO; live trade caps are configured separately.
Quote storage contract: every stored route-leg quote must include venue, pool, input/output assets, input amount, expected output, price impact, fee estimate, block round, `captured_at`, and `expires_at`.
Opportunity storage contract: every opportunity must include gross profit, estimated network fees, DEX fee estimate, max/total price impact, slippage/safety buffer, net expected profit, confidence score, and skip reason.
Paper trading contract: every opportunity gets a paper row before live funds; approved routes set `would_execute=true`, rejected routes preserve skip reason, and later scanner cycles record 5s/30s simulated output, quote decay, and expected-vs-simulated profit.
Risk engine contract: reject unless own-funds-only policy, asset allowlist, reviewed app IDs, quote age <=5s, fee buffer >=2x expected fees, impact <=50 bps, profit >=max(0.25 units, 35 bps), route length <=3, daily submitted trades <20, daily loss above -20 ALGO, and concurrent execution is capped at 1.
Execution dry-run contract: build unsigned atomic transaction groups only from `status=approved` opportunities with passing `risk_rules`, keep `ALGO_PULSE_UNSIGNED_EXECUTOR_ONLY=true`, reject groups above 16 transactions, and leave signing to the isolated signer phase.
Signer contract: keep `ALGO_PULSE_SIGNER_ENABLED=false` and `ALGO_PULSE_SIGNER_KILL_SWITCH=true` by default; route hashes must be allowlisted before signing; app IDs, asset IDs, input amount, transaction count, and group id must match route intent; every approval/rejection goes to the signer audit log.
Tiny-live contract: ALGO/USDC only, new 100-250 ALGO hot wallet, 10 ALGO max trade, 20 ALGO max daily loss, 20 max daily trades, route length <=3, one concurrent route, manual route hash approval, Lora txid, and reconciliation before automation.
Deployment-mode contract: local uses mock data with scanner optional, no signer, and no real submission; staging uses live scanner/live quotes/paper trading with no live signing and a delayed dashboard; production Phase 0 uses live scanner, route engine, paper trading, risk engine, admin dashboard, public delayed dashboard, isolated signer only after gates, and tiny own-funds hot wallet only.

## Current Safety Status

Production Status: NOT LIVE READY.

Reason: The system is collecting market data, but live execution remains locked until scanner uptime, paper-trading edge, risk gates, unsigned dry runs, signer isolation, and manual micro-trade reconciliation are proven.

Current safe mode: Scanner / Paper / Dry Run only. No user deposits, no guaranteed returns, and no live execution unless explicitly armed by admin after gates pass.

Required flags are currently expected to stay false:

```text
ALGO_PULSE_ENABLE_LIVE_EXECUTION=false
ALGO_PULSE_EXECUTE_APPROVED=false
ALGO_PULSE_ALLOW_API_EXECUTION=false
```

The bot is watch-ready, not live-trade-ready. It can scan PNET markets through Tinyman/Pact, but a funded hot wallet, opt-ins, final SDK transaction review, and balance reconciliation review are still required before any submitted trade. Three-leg routes are discovery/paper-only until executor support is reviewed.

## Source Of Truth Files

Start here:

- `README.md`: app overview and commands
- `docs/PRODUCT_THESIS.md`: product definition; public repos are references, official SDKs are the implementation boundary
- `docs/PNET_DASHBOARD_COCKPIT.md`: role-based dashboard spec for Admin Cockpit, connected PNET users, guest visibility, and UI-only control gates
- `docs/PNET_PAYMENT_FLOW.md`: Pera-signed PNET market-data fee flow, payment intent, on-chain txid verification, and receipt boundary
- `docs/CODEX_HANDOFF.md`: current safe control-plane scope and latest Codex implementation points
- `docs/API_CONTRACT.md`: response envelope, role headers, admin endpoints, public config, PNET stubs, and paper report endpoint
- `docs/ALERT_CATALOG.md`: Phase 0 watched-condition taxonomy and operator response guide
- `docs/RISK_POLICY.md`: pure risk inputs, initial limits, and rejection-first policy
- `docs/PHASE_GATES.md`: Gate 1-to-10 evidence checklist before Phase 1
- `docs/DEPLOYMENTS.md`: local/deployment path, commands, repo policy, and env rules
- `docs/RUNBOOK.md`: safe startup, daily control-plane check, and exit criteria
- `docs/TEST_MATRIX.md`: unit, integration, and security test coverage map
- `docs/VERSION_LADDER.md`: v0.1-to-v1.0 build sequence; live execution starts only at manual tiny trade
- `docs/REPO_ADOPTION_RED_FLAGS.md`: external-repo filter for unsafe wallet, routing, loss-limit, kill-switch, and paper-trading patterns
- `STEP6_QA_COMPLETION_REPORT.md`: latest QA result and current readiness
- `STEP9_ISOLATED_SIGNER_REPORT.md`: signer boundary implementation and QA result
- `STEP10_TINY_LIVE_EXECUTION_RUNBOOK.md`: first live ALGO/USDC execution sequence and gates
- `HANDOFF_TO_CLAUDE.md`: deployment-focused handoff for Claude
- `LIVE_DEPLOYMENT.md`: env modes and deployment path
- `VERSION_CONTROL.md`: branch, commit, PR, tag, and repo policy
- `CHANGELOG.md`: human-readable release history
- `REAL_ARB_BOT_ARCHITECTURE.md`: target production service chain and signer-boundary architecture
- `docs/RELEASE_CHECKLIST.md`: release and live-readiness gate
- `ALGORAND_ARB_AGENT_RULES.md`: safety, red-team, and AI-agent rules

## Team Rules

1. Treat this repo as private until execution code is separated from public marketing/dashboard code.
2. Never commit `.env`, signer secrets, wallet exports, raw production logs, or local databases.
3. Every behavior change needs tests or a written reason in the PR.
4. Every dashboard change needs a browser QA note or screenshot.
5. Every execution-path change needs a safety review against stale routes, fee ceilings, rekey/close-out checks, app ID validation, asset opt-ins, and balance reconciliation.
6. Public-facing claims must distinguish synthetic demos, observed spreads, dry-runs, and submitted trades.
7. `main` should always be deployable in read-only mode.
8. Refund cases must remain manual-only unless a separate custody, signer, and authorization review is completed.
9. The isolated signer is a hard trust boundary; unsigned execution planning and signer secret custody must not live in the same production service.
10. Automate scanning, quote comparison, paper trading, risk rejection, and unsigned construction freely; automate signing only inside the isolated signer with explicit policy limits.
11. Never give AI agents or frontend code wallet keys.
12. Never use a main wallet, unknown repo, or unreviewed service to sign transactions.
13. Never let the bot trade every asset it sees, accept user funds, or perform sandwich/predatory MEV behavior.
14. Scanner mode must remain read-only and run without signer secret material; Phase 0A requires 24 hours of no-crash scanner uptime before execution work advances.

## Next Best Team Move

Create the private source repo remote and push the existing local `main` branch. The local initial commit already exists.

```powershell
git remote add origin <private-source-repo-url>
git push -u origin main
```
