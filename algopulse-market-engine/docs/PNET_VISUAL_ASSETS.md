# PNET Visual Assets

Purpose: provide reusable diagram assets for docs, GitHub, website sections, blog posts, and presentations. Prefer Mermaid diagrams in GitHub until rendered images pass the `docs/IMAGE_PIPELINE.md` redaction checklist.

## Contribution Protocol Flow

```mermaid
flowchart LR
    A["User submits contribution"] --> B["Manual review queue"]
    B --> C{"Approved?"}
    C -- "No" --> D["Rejected with reason"]
    C -- "Yes" --> E["Credits granted in ledger"]
    E --> F["User spends credits"]
    F --> G["Delayed report, scan, simulation, comment, or preview"]
    G --> H["Receipt recorded"]
```

Safety label: credits unlock bounded access only. They do not create token rewards, staking yield, treasury control, or trading permission.

## Utility Boundary

```mermaid
flowchart TB
    P["PNET utility layer"] --> R["Delayed reports"]
    P --> C["Contribution credits"]
    P --> E["Evidence receipts"]
    P --> X["x402 paid access"]
    P --> L["Liquidity visibility"]

    P -. "blocked" .-> T["Live trading"]
    P -. "blocked" .-> S["Signer/wallet custody"]
    P -. "blocked" .-> M["Mainnet deploy without approval"]
    P -. "blocked" .-> G["Binding governance"]
```

## Content Evidence Loop

```mermaid
flowchart LR
    A["Build feature"] --> B["Run tests"]
    B --> C["Capture screenshot or receipt"]
    C --> D["Redact secrets and payloads"]
    D --> E["Write content draft"]
    E --> F["Human review"]
    F --> G["Publish only if approved"]
```

## Tokenomics Content Gate

```mermaid
flowchart TD
    A["Tokenomics copy"] --> B{"All facts verified from current sources?"}
    B -- "No" --> C["Keep as internal draft"]
    B -- "Yes" --> D{"No ROI / buy-sell / listing claims?"}
    D -- "No" --> C
    D -- "Yes" --> E{"Rob approved exact wording?"}
    E -- "No" --> C
    E -- "Yes" --> F["Eligible for public page"]
```

## Image Export Checklist

Before converting any diagram to PNG/GIF:

- [ ] No secrets, `.env`, keys, mnemonics, payment payloads, or raw headers.
- [ ] No fresh executable route data.
- [ ] No ROI, price, yield, buy/sell, CEX, audit, or production-readiness overclaim.
- [ ] Source label included: mock, local, delayed, TestNet, staged, or verified.
- [ ] Human approval recorded before public posting.
