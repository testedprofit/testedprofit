# x402 ISO 20022-Inspired Payment Evidence

Purpose:
Define a conservative, ISO 20022-inspired structure for AlgoPulse x402 payment evidence, receipts, status reasons, reconciliation metadata, and audit records.

This is a planning document only. It does not implement ISO 20022 messages, payment processing, Mainnet behavior, deployment, wallet custody, signing, transaction submission, or any public eligibility claim.

## Plain-English Explanation

ISO 20022 is a shared financial messaging vocabulary and model for payments, settlement status, references, reconciliation, and other financial business processes. It gives financial systems a common way to describe who is paying, who is receiving, what amount is being transferred, why the payment exists, what status it reached, and how the transaction can be reconciled later.

AlgoPulse is not implementing ISO 20022 XML messages, bank payment messages, or a certified ISO 20022 interface. The useful idea is narrower: borrow clear payment-evidence concepts so x402 receipts and audit records are easier to review.

Safe framing:

> AlgoPulse may use ISO 20022-inspired payment evidence fields to make x402 receipts easier to audit and reconcile. This is not a claim of ISO 20022 compliance.

## Explicit Non-Claims

AlgoPulse does not claim:

- ISO 20022 compliance
- bank-grade compliance
- ISO certification
- a regulatory-compliant payment record
- Mainnet readiness
- production payment infrastructure readiness
- financial-institution message compatibility
- support for ISO 20022 XML, ASN.1, `pain`, `pacs`, or `camt` messages

Use `ISO 20022-inspired` only. Do not use `ISO 20022-compliant`.

## Concept Mapping

| ISO 20022 concept | AlgoPulse x402 evidence meaning |
|---|---|
| Debtor | x402 payer |
| Creditor | x402 receiver |
| Payment identification | request ID, resource ID, and payment reference |
| Amount / currency | asset network, asset ID, symbol, decimals, and amount |
| Remittance information | paid delayed/redacted report purpose |
| Settlement status | `required`, `verified`, `settled`, `rejected`, `failed`, or `unknown` |
| Transaction reference | sanitized or public transaction reference if safe |
| Status reason | unpaid, fake header, invalid payment, facilitator unavailable, or config disabled |
| Audit metadata | timestamp, route, gate, response hash, redaction version, no-secret flags, and no-payment-payload flags |

## Proposed Evidence Schema

This schema is intentionally project-local and conservative. It should never include private keys, mnemonics, raw payment payloads, payment groups, signed transaction blobs, authorization headers, or full wallet-sensitive material.

```json
{
  "schema": "algopulse.x402.paymentEvidence.iso20022Inspired.v0",
  "complianceClaim": "none",
  "inspiration": "ISO 20022 payment evidence concepts",
  "gate": "Gate 3.5",
  "environment": "algorand-testnet",
  "resource": {
    "id": "algopulse.market_pulse.daily.v0",
    "route": "GET /api/x402/reports/market-pulse/daily",
    "accessTier": "premium-delayed-intelligence"
  },
  "parties": {
    "debtor": {
      "role": "payer",
      "addressHash": "sha256:redacted-payer-address-hash",
      "sameAsCreditor": false
    },
    "creditor": {
      "role": "receiver",
      "addressHash": "sha256:redacted-receiver-address-hash"
    }
  },
  "payment": {
    "assetNetwork": "algorand-testnet",
    "assetSymbol": "USDC",
    "assetId": "10458941",
    "decimals": 6,
    "amountAtomic": "10000",
    "amountDisplay": "0.01"
  },
  "identification": {
    "requestId": "req_redacted",
    "resourceReference": "market-pulse-daily-redacted",
    "paymentReference": "x402-access-redacted",
    "transactionReference": "public-or-sanitized-tx-reference-if-safe"
  },
  "remittance": {
    "purpose": "paid access to delayed/redacted market intelligence report",
    "publicClaimAllowed": false
  },
  "status": {
    "paymentStatus": "settled",
    "statusReason": "facilitator_verified_and_settled",
    "httpStatus": 200
  },
  "audit": {
    "timestamp": "2026-01-01T00:00:00Z",
    "responseSha256": "sha256:redacted-response-hash",
    "redactionVersion": "redacted-policy-version",
    "secretsPrinted": false,
    "paymentPayloadLogged": false,
    "paymentHeaderLogged": false,
    "liveExecutionTouched": false,
    "signerCodeTouched": false
  }
}
```

## Status And Reason Codes

Suggested payment statuses:

- `required`: payment is required before the resource can be returned
- `verified`: facilitator or package path verified the payment but settlement evidence is not yet recorded
- `settled`: payment was verified and settled according to the official x402/facilitator path
- `rejected`: payment proof was invalid, missing, fake, or unsafe
- `failed`: expected infrastructure failed closed
- `unknown`: status could not be safely determined

Suggested status reasons:

- `unpaid`
- `fake_x_payment_header`
- `fake_payment_signature_header`
- `invalid_payment`
- `facilitator_unavailable`
- `config_disabled`
- `config_unconfirmed`
- `asset_mismatch`
- `amount_mismatch`
- `payer_receiver_same_address`
- `facilitator_verified_and_settled`
- `settlement_failure_harness_unavailable`

Status reasons should be stable and safe to log. They must not include raw headers, payment payloads, signed transaction groups, secrets, or third-party exception bodies.

## Gate Impact

### Gate 3.5 - External TestNet Payer Proof

An ISO 20022-inspired evidence object can make Gate 3.5 easier to review by separating:

- payer/debtor and receiver/creditor
- payer != receiver proof
- resource identity
- amount and asset identity
- sanitized transaction reference
- status reason
- no-secret and no-payment-payload audit flags

This helps prove the external TestNet payer flow without exposing secrets or package-owned payment payloads.

### Gate 4A - Mainnet Readiness Docs Only

The schema can support Mainnet readiness documentation by defining the evidence shape before Mainnet code exists. Gate 4A can review:

- public-safe receipt fields
- redaction and hash policy
- status and rejection vocabulary
- reconciliation expectations
- logging policy
- monitoring and audit-trail requirements

Gate 4A remains docs-only. This document does not approve Mainnet implementation.

### Gate 4 - Mainnet Minimal Endpoint

Gate 4 can consider this evidence shape only after Gate 3.5 and Gate 4A pass and Rob explicitly approves Mainnet work. The schema should support review and reconciliation, but it does not itself prove eligibility, leaderboard tracking, or production readiness.

## Hard Boundaries

- no secrets
- no mnemonics or private keys
- no `PAYMENT-SIGNATURE` logging
- no `X-PAYMENT` logging
- no raw payment payload logging
- no payment group logging
- no signed transaction blob logging
- no Mainnet
- no deploy
- no payment run
- no signer, wallet, trading, or fresh-route behavior change
- no challenge eligibility or public readiness claim

## Wording To Use

Use:

- `ISO 20022-inspired payment evidence`
- `structured payment evidence`
- `receipt and reconciliation metadata`
- `audit-friendly status reasons`
- `project-local schema`

Avoid:

- `ISO 20022 compliant`
- `bank-grade compliant`
- `certified`
- `regulatory-compliant payment record`
- `official ISO 20022 x402 message`
- `Mainnet ready`
- `production payment infrastructure`

## Validation Checklist For Future PRs

- evidence records use hashed or redacted addresses unless public disclosure is explicitly approved
- no secrets, private keys, mnemonics, headers, full payment payloads, payment groups, or signed transaction blobs are stored or logged
- status reasons are stable, short, and safe
- payer and receiver roles are explicit
- asset ID, symbol, decimals, and amount are explicit
- resource route and resource ID are explicit
- response hash and redaction version are recorded when safe
- public wording says `inspired`, not `compliant`
