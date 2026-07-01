# Claude Fable 5 Handoff - NFT Studio Automation

Purpose: challenge Claude/Fable 5 to finish the next safe NFT Studio roadmap items without drifting into marketplace, MainNet, custody, or secret-handling work.

## Current Repo State

- Repo: `testedprofit/testedprofit`
- Local clone: `C:\Users\rober\Music\testedprofit-live-work`
- Base commit observed locally: `6bd31a8`
- PR #35 is merged and live.
- Worker deployed by Rob:
  - `https://algoflow-nft-ipfs-broker.testedprofit.workers.dev`
  - health endpoint returns `{"ok":true,"service":"algoflow-nft-ipfs-broker"}`
- Current local uncommitted changes before this handoff:
  - `pages/algoflow/algoflow-live-overrides.js`
  - `workers/nft-ipfs-broker/README.md`

## What Codex Changed Locally

The current local patch is intended to make NFT minting feel like the Launchpad flow:

- Production NFT Studio defaults to the deployed `workers.dev` broker instead of `/api/nft`.
- Adds one primary `Create TestNet NFT` button.
- Guided flow runs:
  1. pin selected media through the broker
  2. build ARC-3 metadata JSON
  3. pin metadata JSON through the broker
  4. connect wallet only when needed
  5. build/sign/submit the Algorand TestNet ASA create transaction
- Keeps manual/advanced controls available.
- Removes hidden wallet reconnect/module loading on page load.
- Clears stale pinned media/metadata state when a new file is selected.
- Updates Worker README to match the deployed broker reality.

## Challenge To Fable 5

Do not trust this handoff blindly. Verify the current patch from source and browser behavior. If the UI still feels broken or confusing, fix the smallest real cause and show evidence.

Fable must complete these roadmap line items before calling the work done:

1. **Make the NFT mint flow walkable**
   - User should understand the path in under 10 seconds:
     - upload media
     - enter name/unit
     - click `Create TestNet NFT`
     - approve wallet transaction
   - The production page must not require the user to paste the broker URL.
   - Manual controls may remain, but they must not be the primary path.

2. **Prove the production broker path is wired**
   - Confirm the default broker value on `https://testedprofit.com/pages/nfts/` is the deployed Worker URL after the PR is merged/live.
   - Confirm Worker health returns OK.
   - Confirm CORS preflight from `https://testedprofit.com` allows POST.
   - Do not print or inspect `PINATA_JWT`.

3. **Create a narrow PR**
   - Branch from latest `main`.
   - Include only:
     - NFT Studio frontend automation/fix
     - Worker README/docs update
     - optional tiny docs note if needed
   - Do not include unrelated AlgoFlow design changes.

4. **Run validation and paste evidence**
   - Required local validation:
     - `git diff --check`
     - `node --check pages\algoflow\algoflow-live-overrides.js`
     - `node --check workers\nft-ipfs-broker\worker.mjs`
     - `cd workers\nft-ipfs-broker`
     - `npx.cmd wrangler deploy --dry-run --config .\wrangler.jsonc`
     - changed-file secret scan
   - Browser evidence required:
     - `/pages/nfts/` renders
     - `Create TestNet NFT` button exists
     - upload broker defaults to `https://algoflow-nft-ipfs-broker.testedprofit.workers.dev` on production host
     - Connect wallet action is user-initiated, not attempted on page load

5. **Prepare Gate NFT-3, but do not bypass it**
   - Fable may prepare the final TestNet mint checklist.
   - Fable must not perform wallet signing unless Rob explicitly directs a human-gated proof mint.
   - Rob controls Pera/Defly approval and any real transaction signing.

## Hard Boundaries

Do not:

- deploy
- run MainNet
- add marketplace buy/sell
- add escrow contracts
- add backend signing
- add wallet custody
- ask Rob to paste secrets into chat
- print `.dev.vars`, `PINATA_JWT`, wallet secrets, mnemonics, private keys, or transaction payloads
- touch unrelated AlgoFlow tools
- re-enable Genesis
- remove Launchpad, AlgoLens, AlgoSocial, MultiSend, Inspector, Markets, Burner, ShapeMap, or other restored tools

## If Buttons Still Do Not Work

Diagnose in this order:

1. Check browser console for script errors.
2. Check whether `algoflow-live-overrides.js` loaded from the expected live URL.
3. Check whether the page has `#algoflow-nft-studio`.
4. Check whether `[data-nft-create-flow]`, `[data-nft-pin-media]`, `[data-nft-build-metadata]`, and `[data-nft-wallet-connect]` are present.
5. Check whether the broker input value is the deployed Worker URL on production.
6. Check Worker health and CORS preflight.
7. Only then inspect wallet import/signing behavior.

## Acceptance Criteria

Fable may call the PR complete only when:

- A PR exists against `main`.
- The PR diff is narrow and explainable.
- Validation commands above pass.
- No secret-like material appears in the changed diff.
- Browser evidence confirms the guided path exists.
- The report clearly says whether a real TestNet mint was performed or not.
- Any real mint remains a Rob-controlled human gate.

## PR Body Requirements

The PR body must include:

- Problem fixed: NFT Studio was too manual and production broker default was wrong for GitHub Pages.
- What changed.
- What intentionally did not change.
- Validation results.
- Worker health/CORS evidence.
- Remaining human gate for the real TestNet mint.

