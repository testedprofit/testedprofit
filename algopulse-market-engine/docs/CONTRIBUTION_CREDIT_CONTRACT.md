# Contribution Credit Contract Blueprint

Purpose: document the future smart-contract function boundary for PNET contribution credit usage without deploying or claiming a live on-chain credit system.

Reference code:

```text
contracts/pnet_credit_usage_reference.py
```

## Contract Status

Status: blueprint only, not deployed.

This is not a Mainnet contract, not a TestNet contract, and not an audit claim. It is a reviewed vocabulary for future implementation.

## Proposed Functions

| Function | Purpose | Required safety boundary |
| --- | --- | --- |
| `grant_credit(account, amount, reason_hash)` | Record reviewed contribution credit. | Admin/reviewer only; no token payout. |
| `spend_credit(account, unlock_code, amount, receipt_hash)` | Consume credits for bounded access. | No signer access, no trade submission, no fresh route exposure. |
| `record_nonbinding_signal(account, proposal_id, signal_hash)` | Record community proposal signal. | Non-binding only; no vote buying or treasury control. |
| `freeze_credit_account(account, reason_hash)` | Abuse-control freeze after review. | No asset seizure, no wallet custody, no fund movement. |

## State Model

Local state:

- `credit_balance`
- `account_frozen`
- `last_receipt_hash`

Global state:

- `admin`
- `pnet_asset_id`
- `schema_version`

## Explicit Non-Goals

The contract must not:

- emit tokens
- distribute rewards
- move treasury funds
- submit trades
- sign transactions
- custody user funds
- give vote power based on payment size
- perform automatic deployments
- control signer or hot-wallet behavior
- expose fresh executable routes

## Upgrade Review

Any move from blueprint to real contract requires review of:

- TEAL/PyTeal/ARC implementation
- state schema
- method authorization
- opt-in behavior
- freeze/unfreeze rules
- credit accounting
- abuse controls
- receipt hash format
- indexer/audit plan
- migration and rollback plan

## Deployment Gate

Deployment is blocked until Rob explicitly approves:

- TestNet contract implementation
- TestNet deployment account and admin
- PNET ASA references
- security review scope
- no-secret/no-custody handling
- public wording

Mainnet remains blocked until separate Mainnet approval.
