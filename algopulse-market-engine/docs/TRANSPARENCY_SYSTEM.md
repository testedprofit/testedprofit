# AlgoPulse Transparency System

Purpose: make proof, review, and audit evidence the strongest public-safe part of the project without exposing secrets, payment payloads, fresh executable routes, or production claims.

## What It Shows

- Automated proof checks for payment receipts, manual review receipts, x402 gate evidence, and documented limitations.
- A public activity ledger with redacted payment-verification and review references.
- A GitHub dossier snapshot generated from the same redacted API payload.
- An audit readiness package with checklist items, threat-model rows, blocked claims, and publication gates.

## Public Dashboard

The `Transparency` dashboard tab is public. It calls:

- `GET /api/transparency/system`
- `GET /api/transparency/proofs`
- `GET /api/transparency/public-ledger`
- `GET /api/transparency/github-snapshot`
- `GET /api/transparency/audit-readiness`

The dashboard must only show public-safe proof metadata. It must not show raw wallet addresses, full txids, payment headers, payment payloads, mnemonics, private keys, `.env` contents, signer material, fresh executable route data, or live trading controls.

## Automated Proof Verification

Proof checks are status rows, not production claims.

| Check | Meaning | Current boundary |
|---|---|---|
| On-chain payment receipts | Stored payment verifications can be summarized as redacted references. | Raw txid and wallet values are hashed/suffixed only. |
| Manual review receipts | Contributions, referrals, and credit spends are visible as review events. | No automatic rewards, payouts, or governance authority. |
| Refund/failure tracking | Refund cases can be counted and summarized. | Full refund queues remain review/admin material. |
| x402 Gate 3 mechanics | Local/TestNet mechanics proof exists. | Not Mainnet, not challenge eligibility, not external-user evidence. |
| Gate 3.5 external payer | Required before external-user or Mainnet-readiness claims. | Blocked until payer != receiver proof exists. |
| Settlement-failure harness | Known limitation. | Do not force failure by tampering, underfunding, replaying payloads, or logging payment material. |

## GitHub Dossier Snapshot

Generate a redacted snapshot from a running local API:

```bash
python scripts/generate_transparency_snapshot.py --base-url http://127.0.0.1:8769
```

Write it to a file only after human review:

```bash
python scripts/generate_transparency_snapshot.py --base-url http://127.0.0.1:8769 --output docs/transparency/latest-snapshot.md
```

Recommended cadence:

- before external demos
- after proof evidence changes
- before public claims
- before audit-readiness review
- before any Gate 3.5 or Gate 4A handoff

## Redaction Policy

- Tx IDs: SHA-256 prefix plus suffix only.
- Wallet addresses: SHA-256 prefix plus suffix only.
- Payment payloads: omitted.
- Headers: omitted.
- Private notes: omitted.
- Fresh route data: omitted.
- Signer/wallet custody fields: omitted.

## Safety Boundaries

- No financial advice.
- No token price, ROI, yield, staking, or reward claim.
- No Mainnet approval.
- No deployment approval.
- No production-readiness claim.
- No public challenge eligibility claim.
- No live trading, signer custody, wallet custody, or transaction submission.
