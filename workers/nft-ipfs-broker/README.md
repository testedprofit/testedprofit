# AlgoFlow NFT IPFS Broker

This Worker protects the Pinata account token used by NFT Studio. The browser uploads media or metadata to this Worker, and the Worker pins the file to IPFS through Pinata without exposing `PINATA_JWT` to the frontend.

## What It Does

- Accepts image/video media uploads for NFT files.
- Accepts exact ARC-3 metadata JSON uploads.
- Enforces file type and size limits before pinning.
- Optionally verifies Cloudflare Turnstile if `TURNSTILE_SECRET_KEY` is configured.
- Returns only the CID and safe metadata needed by the frontend.
- Does not mint NFTs, sign transactions, custody wallets, run MainNet actions, or create marketplace listings.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/pin` | Pin a media or metadata file |
| `POST` | `/api/nft/pin` | Same as `/pin`, useful behind a site route |

`POST /pin` expects multipart form data:

| Field | Required | Notes |
|---|---:|---|
| `file` | yes | Image/video file for `kind=media`, JSON file for `kind=metadata` |
| `kind` | yes | `media` or `metadata` |
| `name` | no | Safe display name for Pinata metadata |
| `turnstileToken` | only if configured | Required when `TURNSTILE_SECRET_KEY` is set |

Successful response:

```json
{
  "ok": true,
  "cid": "bafy...",
  "uri": "ipfs://bafy...",
  "kind": "media",
  "bytes": 12345,
  "contentType": "image/png"
}
```

## Local Setup

Production does not require a localhost broker. Use the local setup only for development or troubleshooting.

Install Wrangler if needed:

```powershell
npm install --save-dev wrangler
```

Set secrets locally in `workers/nft-ipfs-broker/.dev.vars` for local testing only. This file is ignored by git.

```text
PINATA_JWT=replace_with_limited_pinata_jwt
# Optional:
# TURNSTILE_SECRET_KEY=replace_with_turnstile_secret
```

Run locally:

```powershell
cd workers/nft-ipfs-broker
npx.cmd wrangler dev --local --port 8790
```

Then use this in NFT Studio:

```text
http://127.0.0.1:8790
```

For temporary local browser testing, add `http://127.0.0.1:8784` to `vars.ALLOWED_ORIGINS` before running `wrangler dev`, then remove it before production deploy.

## Production Setup

Do not put the Pinata token in source code, `wrangler.jsonc`, HTML, JavaScript, GitHub issues, or PR comments.

The standalone NFT page now defaults to the deployed Worker broker:

```text
https://algoflow-nft-ipfs-broker.testedprofit.workers.dev
```

This keeps NFT Studio usable while `testedprofit.com` is served from GitHub Pages. The same-domain route below is still the preferred future shape if the custom domain is later proxied through Cloudflare:

```text
https://testedprofit.com/pages/nfts/
https://testedprofit.com/api/nft
```

If the site is moved behind Cloudflare, NFT Studio can default the broker URL to:

```text
/api/nft
```

That means the Worker should be routed behind the custom domain, for example:

```text
testedprofit.com/api/nft*
```

If the GitHub Pages custom domain is not proxied through Cloudflare, keep using the deployed `workers.dev` URL in NFT Studio instead of `/api/nft`.

The allowed browser origins live in `wrangler.jsonc` under `vars.ALLOWED_ORIGINS`. Production defaults include only approved site origins:

```text
https://testedprofit.com
https://testedprofit.github.io
```

Set the secret with Wrangler:

```powershell
cd workers/nft-ipfs-broker
npx.cmd wrangler secret put PINATA_JWT
```

Optional Turnstile:

```powershell
npx.cmd wrangler secret put TURNSTILE_SECRET_KEY
```

Do not set `TURNSTILE_SECRET_KEY` until the website includes a Turnstile widget and sends `turnstileToken`; if this secret is configured before the frontend widget exists, uploads will fail closed.

Deploy only after reviewing origin allowlist and upload limits:

```powershell
npx.cmd wrangler deploy
```

## No-Secrets Validation Checklist

Run before every commit/PR that touches NFT Studio or this Worker:

```powershell
git diff --check
node --check pages\algoflow\algoflow-live-overrides.js
node --check workers\nft-ipfs-broker\worker.mjs
cd workers\nft-ipfs-broker
npx.cmd wrangler deploy --dry-run --outdir "$env:TEMP\algoflow-nft-broker-dryrun"
```

Then scan staged/changed files for secret material:

```powershell
rg -n "BEGIN (RSA|OPENSSH|PRIVATE)|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.|AKIA[0-9A-Z]{16}|pinata_[A-Za-z0-9_]{20,}|(PRIVATE_KEY|MNEMONIC|WALLET_SECRET)\s*=\s*[^\s#]+" .
```

Confirm all of the following before opening a PR:

- [ ] No Pinata JWT, API key, or bearer token in any tracked file
- [ ] No wallet mnemonic, private key, or `.dev.vars` content in code, docs, or comments
- [ ] `.dev.vars`, `.wrangler/`, and env files are ignored by git (`git status` shows none of them)
- [ ] `vars.ALLOWED_ORIGINS` in `wrangler.jsonc` contains only approved production origins (no localhost)
- [ ] Dry-run output directory was deleted after validation
- [ ] No MainNet endpoints, no backend signing, no custody logic added

## Safety Boundaries

- Keep `ALLOWED_ORIGINS` restricted to local dev and approved production domains.
- Keep `MAX_UPLOAD_BYTES` conservative until storage costs are understood.
- Use a limited Pinata token, not a master account token.
- Do not log request headers, JWTs, file contents, wallet secrets, or payment payloads.
- Do not use this Worker for MainNet marketplace escrow or buy/sell logic.
- IPFS content is public-addressed; do not upload private documents, wallet recovery phrases, wallet exports, IDs, or anything a user expects to delete permanently.

## NFT Studio Flow

1. User uploads image/video in the browser.
2. User clicks `Create TestNet NFT`.
3. Browser previews and hashes media locally.
4. Browser sends the file to this Worker.
5. Worker pins media to Pinata and returns `ipfs://CID`.
6. Browser builds exact ARC-3 metadata JSON.
7. Browser sends exact metadata JSON to this Worker.
8. Worker pins metadata and returns `ipfs://CID`.
9. Browser fills `ipfs://metadataCID#arc3`.
10. User signs the Algorand TestNet ASA create transaction in Pera or Defly.
