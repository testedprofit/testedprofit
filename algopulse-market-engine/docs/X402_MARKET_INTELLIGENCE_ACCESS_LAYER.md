# x402 Market Intelligence Access Layer

This document defines the first safe x402 readiness step for AlgoPulse: a mock/TestNet-style paid-access boundary around delayed market intelligence reports.

It does not enable Mainnet payments, wallet custody, transaction signing, transaction submission, live trading, or fresh executable route access.

Related evidence planning: [`docs/X402_ISO20022_INSPIRED_EVIDENCE.md`](X402_ISO20022_INSPIRED_EVIDENCE.md) defines a non-compliance-claim, ISO 20022-inspired receipt and reconciliation shape for future Gate 3.5 / Gate 4A review.

## Current Readiness Endpoint

`GET /api/x402/reports/market-pulse/daily`

The endpoint is intentionally isolated from scanner control, signer code, dry-run execution, live execution, and wallet custody.

Behavior:

- An unpaid request returns HTTP `402` with a payment-required style JSON body.
- A request with the local-review mock proof header returns a distinct `premium-delayed-intelligence` payload with additional redacted detail sections and export metadata beyond the unauthenticated `public-preview` daily report.
- The response is labeled `mock-testnet-readiness`.
- The response reports `liveExecutionTouched=false` and `signerCodeTouched=false`.

Local-review proof header:

```text
X-Algopulse-Mock-X402-Proof: mock_x402_report_access
```

This header is not a real payment proof. It exists only to prove the access boundary, report redaction, and API shape before any real x402 facilitator integration.

## Local Smoke Check

Start the local API in one terminal from an editable install or a source-path shell:

```powershell
$env:PYTHONPATH = "src" # only needed if the repo is not installed with pip install -e .
uvicorn algopulse.api:app --host 127.0.0.1 --port 8765
```

Then run:

```powershell
python scripts/x402_market_pulse_smoke.py --base-url http://127.0.0.1:8765
```

The smoke script expects:

- unpaid request -> HTTP `402`
- mock proof request -> HTTP `200`
- paid response remains redacted and does not include raw route legs, signer artifacts, execution artifacts, private wallet data, or fresh executable route fields

## What Payment Unlocks

Payment may unlock only delayed or mock market intelligence evidence, such as:

- daily market pulse reports
- aggregate opportunity counts
- delayed top-pair summaries
- ALGO-only external cached market context labels when already present in the delayed report
- scanner health summaries
- liquidity health summaries
- risk/rejection explanations after redaction
- evidence-backed report exports

Payment must not unlock:

- live trading
- signer access
- wallet custody
- transaction submission
- fresh executable routes
- BTC, ETH, raw CoinMarketCap payloads, or CoinMarketCap API keys
- raw route JSON
- unsigned or signed transaction groups
- hot-wallet status
- admin-only operational logs
- guaranteed-profit or investment claims

## Future x402 Integration

For Global x402 Challenge readiness, the likely integration path is:

1. Keep this mock endpoint as the resource-server contract.
2. Rehearse with Algorand TestNet and a managed facilitator such as GoPlausible, if the selected payment asset and resource shape are supported.
3. Keep the facilitator/payment service outside the market engine and signer trust boundary.
4. Verify payment settlement before returning the report.
5. Preserve the same redaction contract used by the mock endpoint.
6. Move to Mainnet only after Rob explicitly approves challenge rules, receiver/payment asset, compliance posture, logging, and abuse controls.

`@profitnet/pnet-x402` remains useful as a PNET-first tx-ID proof reference, but this endpoint must not claim generic x402 or facilitator compatibility until that behavior is implemented and tested.

## API Boundaries

The x402 access layer may call:

- report generation
- public-safe redaction helpers
- durable payment/replay storage after a separate review
- facilitator verification after a separate review

The x402 access layer must not call:

- `/api/admin/*`
- `/api/ops/*`
- `/api/execute-best`
- signer code
- dry-run transaction construction
- live execution controls
- wallet-secret loading

## Required Tests

Tests for this surface should prove:

- unpaid requests return HTTP `402`
- wrong mock proof values still return HTTP `402`
- valid mock proof returns HTTP `200`
- report output is redacted and public-safe
- no raw route payload, signer artifact, wallet secret, transaction submission, or fresh executable route leaks
- `liveExecutionTouched=false`
- `signerCodeTouched=false`

## Whitepaper Delta

Add a future section titled `x402 Pay-Per-Request Market Intelligence`.

Safe wording:

> AlgoPulse can expose delayed market intelligence reports through an HTTP 402-style access layer. Payments unlock report/data access only. The system does not custody funds, sign transactions, submit transactions, expose live executable routes, or guarantee trading outcomes.

## x402 Challenge Delta

`x402 update recommended: the first safe readiness endpoint is a delayed market-pulse report protected by a mock/TestNet-style 402 access boundary. Mainnet facilitator integration remains blocked until challenge rules, payment asset support, receiver approval, abuse controls, and compliance wording are reviewed.`
