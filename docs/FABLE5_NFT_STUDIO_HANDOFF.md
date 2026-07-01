# Fable 5 Handoff - AlgoFlow NFT Studio

Purpose: challenge the next agent to improve the project without drifting, breaking restored work, exposing secrets, or pretending the NFT marketplace is done before the blockchain path is proven.

## Repo And Current State

Repo/worktree:

```text
C:\Users\rober\Music\testedprofit-live-work
```

Current branch:

```text
codex/shapemap-clean-restore
```

Important context:

- This is the clean restore clone Rob asked us to use after abandoning a damaged local worktree.
- The production website is GitHub Pages/custom domain: `https://testedprofit.com`.
- Current live AlgoFlow page: `https://testedprofit.com/pages/algoflow/`.
- The original compiled AlgoFlow React bundle still contains Launchpad, MultiSend, Inspector, AlgoSocial, Markets, Learn, Burner, and ShapeMap.
- Do not remove existing finished tools while working on NFTs.
- PNET Genesis is intentionally hidden/offline from the front end because the bonding-curve flow failed and needs contract review later.

Current NFT work already added locally:

- Standalone NFT page: `pages/nfts/index.html`
- NFT Studio override/module: `pages/algoflow/algoflow-live-overrides.js`
- AlgoFlow page loads the override: `pages/algoflow/index.html`
- Genesis page front-end disabled: `pages/genesis/index.html`
- Protected IPFS broker Worker:
  - `workers/nft-ipfs-broker/worker.mjs`
  - `workers/nft-ipfs-broker/wrangler.jsonc`
  - `workers/nft-ipfs-broker/README.md`
- `.gitignore` protects `.dev.vars`, `.wrangler/`, env files, keys, and PEM files.

The NFT page is intended to be:

```text
https://testedprofit.com/pages/nfts/
```

The production upload broker is intended to be:

```text
https://testedprofit.com/api/nft
```

If `testedprofit.com` is not proxied through Cloudflare, use the deployed `workers.dev` URL in the broker field instead of `/api/nft`.

## Operating Model

Use the 4D loop:

- Delegation: AI may implement narrow code/docs/tests, but Rob must approve secrets, deploys, MainNet, public claims, and PR merges.
- Description: name files, route, expected behavior, commands, and evidence precisely.
- Discernment: verify what the repo actually does; do not assume the current implementation works.
- Diligence: preserve safety boundaries and leave reproducible validation evidence.

## Mission For Fable 5

Make the NFT Studio actually usable as a production-shaped TestNet ARC-3 minting flow.

Do not just restyle it. Prove or fix the flow:

1. User opens `/pages/nfts/`.
2. User uploads or drags in an image/video.
3. Browser previews and hashes media locally.
4. Media is pinned through a protected Worker broker, not by exposing Pinata JWT in the website.
5. ARC-3 metadata JSON is generated and pinned.
6. Metadata URL ends in `#arc3`.
7. User connects Pera or Defly on Algorand TestNet.
8. User signs an ASA create transaction.
9. UI returns the TestNet tx ID and asset ID/explorer links.

If any step is not currently true, fix the smallest concrete blocker.

## Roadmap Gates

### Gate NFT-0 - Source-Reality Check

Pass condition:

- Identify whether editable React source exists for AlgoFlow.
- If only compiled bundle exists, do not edit minified React assets for large feature work.
- Keep `/pages/nfts/` as the standalone production page unless a clean React source path is found.

Stop condition:

- You are about to overwrite compiled assets, remove existing AlgoFlow tools, or rebuild the whole app without source certainty.

### Gate NFT-1 - Standalone Page Quality

Pass condition:

- `/pages/nfts/` looks and behaves like its own product page, not a hidden hash panel.
- Header links return to AlgoFlow, Inspector, and PNET.
- Copy is TestNet-first and does not claim MainNet marketplace support.
- Mobile layout is usable.

### Gate NFT-2 - Protected IPFS Upload

Pass condition:

- Browser default broker URL is `/api/nft`.
- Worker supports `POST /pin` and `POST /api/nft/pin`.
- Worker keeps `PINATA_JWT` server-side only.
- Production allowlist is restricted to approved site origins.
- Localhost appears only in dev documentation.
- Turnstile is documented as fail-closed and should not be enabled until the frontend widget sends `turnstileToken`.

Stop condition:

- A Pinata JWT, API key, wallet secret, mnemonic, private key, or `.dev.vars` content is committed, printed, or pasted into docs/comments.

### Gate NFT-3 - TestNet ARC-3 Mint Proof

Pass condition:

- With a TestNet wallet, user can mint a real ASA NFT:
  - total `1`
  - decimals `0`
  - freeze/clawback disabled
  - metadata URL with `#arc3`
  - metadata hash set from generated/pinned JSON
- UI shows tx ID and asset ID if available.
- No custody, no backend signing, no private key handling.

Human gate:

- Rob must perform any real wallet signing/payment/mint exercise.
- Agent may provide exact commands/instructions, but must not request secrets in chat.

### Gate NFT-4 - MainNet Readiness Docs Only

Pass condition:

- Add a MainNet readiness checklist only after TestNet proof.
- Include cost notes: ASA create minimum balance, transaction fee, receiver opt-in minimum balance, IPFS storage, audit/review.
- Do not enable MainNet minting until Rob approves.

### Gate NFT-5 - Marketplace Contract Later

Pass condition:

- Buy/sell remains contract-gated until an audited/reviewed Algorand marketplace contract exists.
- If designing marketplace, use official Algorand digital marketplace patterns as inspiration, but do not ship escrow/listing MainNet actions in this PR.

## Hard Boundaries

Do not:

- Deploy without explicit Rob approval.
- Touch MainNet.
- Add marketplace escrow, buy/sell, auction, royalty, or custody logic.
- Add wallet custody, mnemonics, private keys, backend signing, or transaction submission from a server.
- Touch `.env`, `.dev.vars`, secrets, Pinata JWT, wallet material, or payment payloads.
- Remove Launchpad, MultiSend, Inspector, AlgoSocial, Markets, Learn, Burner, ShapeMap, or other restored AlgoFlow tools.
- Claim NFT marketplace support, MainNet readiness, audit status, token price impact, investment upside, or guaranteed usage.
- Create hype/pump language.

## Files To Inspect First

```text
README.md
.gitignore
pages/algoflow/index.html
pages/algoflow/algoflow-live-overrides.js
pages/nfts/index.html
pages/genesis/index.html
workers/nft-ipfs-broker/README.md
workers/nft-ipfs-broker/worker.mjs
workers/nft-ipfs-broker/wrangler.jsonc
```

Also inspect:

```text
package.json
pages/algoflow/assets/
pages/algoflow/shape-enhancement.js
```

## Challenge Questions For Fable 5

Answer these before making broad edits:

1. Does `/pages/nfts/` actually render NFT Studio without relying on the AlgoFlow home screen?
2. Does the Worker route shape match the frontend's `/api/nft` broker default?
3. Does the Worker route accept production origin only, and is localhost documented as dev-only?
4. Does the direct Pinata JWT fallback create a public-site risk? Should it be hidden more aggressively, disabled in production, or kept as a local-only emergency path?
5. Does the generated ARC-3 metadata match what common Algorand wallets/explorers expect for image and video NFTs?
6. Does metadata hashing hash the exact JSON that is pinned?
7. Does the ASA create transaction use the current `algosdk@3.6.0` API correctly?
8. Are Pera and Defly TestNet connection flows correct?
9. What breaks if the custom domain is GitHub Pages-only and not Cloudflare-proxied?
10. What is the smallest fix that gets one real TestNet NFT minted end-to-end?

## Preferred Implementation Focus

Prioritize in this order:

1. Make `/pages/nfts/` first-class and obviously separate from AlgoFlow home.
2. Make the IPFS broker path production-ready without exposing Pinata credentials.
3. Remove or hard-disable direct browser Pinata JWT fallback in production if it is too risky.
4. Add clear user flow and status text for:
   - upload
   - pin media
   - build metadata
   - pin metadata
   - connect wallet
   - mint
   - confirm tx/asset ID
5. Add docs for production Worker route setup.
6. Add a no-secrets validation checklist.

## Validation Required

Run at minimum:

```powershell
git diff --check
node --check pages\algoflow\algoflow-live-overrides.js
node --check workers\nft-ipfs-broker\worker.mjs
cd workers\nft-ipfs-broker
npx.cmd wrangler deploy --dry-run --outdir "$env:TEMP\algoflow-nft-broker-dryrun"
```

Then remove any generated dry-run output and confirm `.wrangler/` is ignored.

Run a changed-file secret scan, for example:

```powershell
rg -n "BEGIN (RSA|OPENSSH|PRIVATE)|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.|AKIA[0-9A-Z]{16}|pinata_[A-Za-z0-9_]{20,}|(PRIVATE_KEY|MNEMONIC|WALLET_SECRET)\s*=\s*[^\s#]+" .
```

If doing browser validation:

- Serve the site locally only for visual/test purposes.
- Do not treat localhost as the production path.
- The production path should remain `/pages/nfts/` + `/api/nft`.

## Expected Deliverable

Open a narrow PR titled:

```text
Make NFT Studio production-ready for TestNet minting
```

PR body must include:

- What changed
- Whether `/pages/nfts/` renders independently
- Whether protected IPFS broker path was validated
- Whether TestNet mint flow was validated or what exact human gate remains
- Files changed
- Validation commands and results
- Confirmation:
  - no MainNet
  - no deploy unless explicitly approved
  - no secrets committed
  - no wallet custody/backend signing
  - no marketplace/buy/sell implementation

## Final Reminder

This work should make NFT minting real, not pretend the whole NFT marketplace is done.

The win is:

```text
Upload media -> pin media -> generate/pin ARC-3 metadata -> wallet signs TestNet ASA create -> asset ID returned
```

Not:

```text
Fake marketplace -> hidden custody -> MainNet claims -> broken UX
```
