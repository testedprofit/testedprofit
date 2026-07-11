# Deployments

## Local Review

Local path:

```text
C:\Users\rober\OneDrive\Documents\Algorand_Phase0_Arb_Bot\phase0-market-engine
```

Run command:

```powershell
python -m uvicorn algopulse.api:app --host 127.0.0.1 --port 8766
```

Browser URL:

```text
http://127.0.0.1:8766/
```

## Environment

Start from `.env.example`. It contains public config, PNET market-data fee placeholders, control-plane flags, and risk limits. It intentionally omits signer operational secrets.

## Mode Contract

`GET /api/config/public` exposes the same promotion path the dashboard renders:

| Mode | Data | Execution Boundary | Dashboard |
| --- | --- | --- | --- |
| Local | Mock data by default; scanner optional | No signer and no real submission | Local operator review dashboard |
| Staging | Live scanner, live quotes, paper trading | No live signing | Delayed dashboard |
| Production Phase 0 | Live scanner, route engine, paper trading, risk engine | Isolated signer only after gates; tiny own-funds hot wallet only | Admin dashboard plus public delayed dashboard |

Promotion is blocked until the relevant Phase Gates have evidence. Local is allowed to be visually polished and API-wired with mocks. Staging is allowed to touch live market data but not signing. Production Phase 0 is still a controlled own-funds system, not a user-funds product or public execution API.

## Repo Policy

- Source repo: private until execution code and public dashboard code are separated.
- Deployment repo: private.
- Public repo: marketing site or delayed public dashboard only.
- Branch: `main` should stay deployable in read-only scanner mode.

## Build And QA

```powershell
python -m pip install -e .
python -m pytest -q
```

Docker review starts from `Dockerfile` and `docker-compose.yml`, but production env values must be reviewed before deploy.
