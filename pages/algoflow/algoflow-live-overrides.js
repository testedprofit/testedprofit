(function () {
  "use strict";

  var NFT_HASH = "#nfts";
  var GENESIS_HASHES = ["#genesis", "#pnetlaunch", "#pnet-genesis"];
  var STYLE_ID = "algoflow-live-overrides-style";
  var PANEL_ID = "algoflow-nft-studio";
  var NAV_ID = "algoflow-nft-nav";
  var ALGOSDK_IMPORT_URL = "https://esm.sh/algosdk@3.6.0";
  var PERA_IMPORT_URL = "https://esm.sh/@perawallet/connect@1.5.2";
  var DEFLY_IMPORT_URL = "https://esm.sh/@blockshake/defly-connect@1.2.1";
  var PINATA_FILE_ENDPOINT = "https://api.pinata.cloud/pinning/pinFileToIPFS";
  var PROD_NFT_BROKER_URL = "https://algoflow-nft-ipfs-broker.testedprofit.workers.dev";
  var TESTNET = {
    chainId: 416002,
    label: "Algorand TestNet",
    algod: "https://testnet-api.algonode.cloud",
    txExplorer: "https://testnet.explorer.perawallet.app/tx/",
    assetExplorer: "https://testnet.explorer.perawallet.app/asset/"
  };
  var originalMainDisplay = "";
  var scheduled = false;
  var nftMintState = {
    modulesPromise: null,
    wallets: {},
    activeWallet: "pera",
    account: "",
    lastMetadataHash: "",
    mediaFile: null,
    mediaObjectUrl: "",
    mediaHash: "",
    metadataJson: "",
    metadataBlobUrl: "",
    pinnedMediaCid: "",
    pinnedMetadataCid: ""
  };

  function isDedicatedNftPage() {
    var path = window.location.pathname.replace(/\/index\.html$/i, "/").toLowerCase();
    return path === "/pages/nfts/" || path === "/pages/nfts";
  }

  function isLocalDevHost() {
    var host = window.location.hostname.toLowerCase();
    return host === "localhost" || host === "127.0.0.1" || host === "::1" || host === "[::1]" || window.location.protocol === "file:";
  }

  function defaultUploadBrokerUrl() {
    var host = window.location.hostname.toLowerCase();
    if (host === "testedprofit.com" || host === "testedprofit.github.io") return PROD_NFT_BROKER_URL;
    return "/api/nft";
  }

  function escapeAttr(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function isNftRoute() {
    return window.location.hash.toLowerCase() === NFT_HASH || isDedicatedNftPage();
  }

  function isGenesisRoute() {
    return GENESIS_HASHES.indexOf(window.location.hash.toLowerCase()) !== -1;
  }

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = [
      "[data-algoflow-genesis-hidden='true']{display:none!important}",
      ".af-tool-pill.af-nft-active{color:#f8fafc;border-color:rgba(168,85,247,.48);background:linear-gradient(135deg,rgba(14,165,233,.16),rgba(168,85,247,.18))}",
      ".af-nft-studio{min-height:calc(100vh - 110px);padding:4.5rem 1.5rem 5rem;background:radial-gradient(circle at 22% 16%,rgba(20,184,166,.16),transparent 34%),radial-gradient(circle at 78% 26%,rgba(99,102,241,.16),transparent 36%),#080818;color:#e5e7eb}",
      ".af-nft-wrap{max-width:1120px;margin:0 auto}",
      ".af-nft-eyebrow{display:inline-flex;align-items:center;gap:.5rem;margin-bottom:1rem;padding:.42rem .9rem;border:1px solid rgba(45,212,191,.25);border-radius:999px;background:rgba(20,184,166,.1);color:#2dd4bf;font-size:.72rem;font-weight:900;letter-spacing:.14em;text-transform:uppercase}",
      ".af-nft-head{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(280px,.75fr);gap:1.4rem;align-items:stretch;margin-bottom:1.2rem}",
      ".af-nft-title{font-size:clamp(2.25rem,5vw,4.8rem);line-height:1.02;margin:0;color:#fff;font-weight:950;letter-spacing:-.05em}",
      ".af-nft-title span{background:linear-gradient(90deg,#2dd4bf,#60a5fa,#c084fc);-webkit-background-clip:text;background-clip:text;color:transparent}",
      ".af-nft-copy{max-width:680px;margin:1rem 0 0;color:#94a3b8;font-size:1.05rem;line-height:1.75;font-weight:600}",
      ".af-nft-status{display:grid;gap:.75rem;padding:1rem;border:1px solid rgba(255,255,255,.1);border-radius:18px;background:rgba(15,23,42,.72);box-shadow:0 22px 60px rgba(0,0,0,.18)}",
      ".af-nft-status-row{display:flex;align-items:center;justify-content:space-between;gap:.75rem;padding:.75rem .8rem;border-radius:12px;background:rgba(255,255,255,.045);color:#cbd5e1;font-size:.88rem;font-weight:800}",
      ".af-nft-status-row strong{color:#f8fafc}",
      ".af-nft-pill{display:inline-flex;align-items:center;gap:.38rem;border-radius:999px;padding:.28rem .58rem;background:rgba(45,212,191,.13);color:#5eead4;font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;font-weight:950;white-space:nowrap}",
      ".af-nft-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;margin-top:1.2rem}",
      ".af-nft-card{border:1px solid rgba(255,255,255,.09);border-radius:18px;background:rgba(15,23,42,.66);padding:1.1rem;min-height:210px;display:flex;flex-direction:column;gap:.8rem}",
      ".af-nft-card h3{margin:0;color:#fff;font-size:1.08rem;letter-spacing:-.02em}",
      ".af-nft-card p{margin:0;color:#94a3b8;line-height:1.6;font-size:.92rem;font-weight:600}",
      ".af-nft-card ul{margin:.1rem 0 0;padding-left:1.05rem;color:#cbd5e1;font-size:.86rem;line-height:1.7;font-weight:650}",
      ".af-nft-stage{align-self:flex-start;border-radius:999px;padding:.28rem .6rem;background:rgba(96,165,250,.13);border:1px solid rgba(96,165,250,.24);color:#93c5fd;font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;font-weight:950}",
      ".af-nft-safe{margin-top:1.2rem;border:1px solid rgba(16,185,129,.24);background:rgba(6,95,70,.14);border-radius:18px;padding:1rem 1.1rem;color:#a7f3d0;font-weight:750;line-height:1.65}",
      ".af-nft-flow{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.8rem;margin-top:1.2rem}",
      ".af-nft-step{border:1px solid rgba(255,255,255,.08);border-radius:14px;background:rgba(255,255,255,.045);padding:.85rem;color:#cbd5e1;font-size:.84rem;line-height:1.5;font-weight:700}",
      ".af-nft-step b{display:block;color:#fff;margin-bottom:.3rem}",
      ".af-nft-actions{display:flex;gap:.7rem;flex-wrap:wrap;margin-top:1.3rem}",
      ".af-nft-btn{appearance:none;border:1px solid rgba(45,212,191,.25);border-radius:12px;background:linear-gradient(90deg,#14b8a6,#3b82f6);color:#06111f;font-weight:950;padding:.78rem 1.05rem;cursor:pointer}",
      ".af-nft-btn-secondary{background:rgba(255,255,255,.06);color:#e5e7eb;border-color:rgba(255,255,255,.12)}",
      ".af-nft-note{margin-top:.8rem;color:#64748b;font-size:.8rem;font-weight:700;line-height:1.6}",
      ".af-nft-mint{margin-top:1.2rem;display:grid;grid-template-columns:minmax(0,1.05fr) minmax(280px,.75fr);gap:1rem;align-items:start}",
      ".af-nft-mint-panel{border:1px solid rgba(255,255,255,.09);border-radius:18px;background:rgba(15,23,42,.72);padding:1rem}",
      ".af-nft-mint-panel h2,.af-nft-mint-panel h3{margin:.1rem 0 .6rem;color:#fff;letter-spacing:-.02em}",
      ".af-nft-form{display:grid;gap:.82rem}",
      ".af-nft-field{display:grid;gap:.34rem}",
      ".af-nft-field label{color:#cbd5e1;font-size:.78rem;font-weight:900;text-transform:uppercase;letter-spacing:.09em}",
      ".af-nft-input,.af-nft-textarea{width:100%;box-sizing:border-box;border:1px solid rgba(255,255,255,.1);border-radius:12px;background:rgba(2,6,23,.72);color:#f8fafc;padding:.75rem .85rem;font:inherit;font-size:.92rem;outline:none}",
      ".af-nft-input:focus,.af-nft-textarea:focus{border-color:rgba(45,212,191,.48);box-shadow:0 0 0 3px rgba(45,212,191,.1)}",
      ".af-nft-textarea{min-height:82px;resize:vertical}",
      ".af-nft-help{color:#64748b;font-size:.78rem;line-height:1.55;font-weight:700}",
      ".af-nft-drop{border:1px dashed rgba(45,212,191,.38);border-radius:16px;background:rgba(20,184,166,.07);padding:1rem;text-align:center;color:#cbd5e1;font-weight:850;cursor:pointer;transition:border-color .18s,background .18s}",
      ".af-nft-drop:hover,.af-nft-drop.is-dragging{border-color:rgba(96,165,250,.7);background:rgba(59,130,246,.12)}",
      ".af-nft-file-input{position:absolute;inline-size:1px;block-size:1px;opacity:0;pointer-events:none}",
      ".af-nft-media-preview{min-height:140px;border-radius:14px;border:1px solid rgba(255,255,255,.08);background:rgba(2,6,23,.66);display:flex;align-items:center;justify-content:center;overflow:hidden;color:#64748b;font-weight:800}",
      ".af-nft-media-preview img,.af-nft-media-preview video{width:100%;max-height:280px;object-fit:contain;background:#020617}",
      ".af-nft-metadata-box{max-height:180px;overflow:auto;white-space:pre-wrap;border-radius:12px;background:rgba(2,6,23,.8);border:1px solid rgba(255,255,255,.08);padding:.75rem;color:#cbd5e1;font-size:.78rem;line-height:1.5}",
      ".af-nft-inline-output{display:grid;gap:.55rem;margin-top:.7rem}",
      ".af-nft-form-row{display:grid;grid-template-columns:1fr 1fr;gap:.75rem}",
      ".af-nft-wallet-row{display:flex;align-items:center;justify-content:space-between;gap:.8rem;padding:.8rem;border:1px solid rgba(255,255,255,.09);border-radius:14px;background:rgba(255,255,255,.045);margin-bottom:.85rem}",
      ".af-nft-wallet-row code{color:#5eead4;font-weight:800;font-size:.78rem;word-break:break-all}",
      ".af-nft-status-box{min-height:42px;border-radius:12px;padding:.75rem .85rem;background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.08);color:#cbd5e1;font-size:.85rem;font-weight:700;line-height:1.5}",
      ".af-nft-status-box.is-error{border-color:rgba(248,113,113,.32);background:rgba(127,29,29,.18);color:#fecaca}",
      ".af-nft-status-box.is-success{border-color:rgba(45,212,191,.3);background:rgba(20,83,45,.2);color:#bbf7d0}",
      ".af-nft-preview{display:grid;gap:.65rem;color:#94a3b8;font-size:.86rem;line-height:1.55;font-weight:650}",
      ".af-nft-preview-row{display:flex;justify-content:space-between;gap:.8rem;padding:.65rem .7rem;border-radius:12px;background:rgba(255,255,255,.045)}",
      ".af-nft-preview-row strong{color:#f8fafc}",
      ".af-nft-preview-row span:last-child{text-align:right;word-break:break-word}",
      ".af-nft-output a{color:#5eead4;font-weight:900;text-decoration:none}",
      ".af-nft-output a:hover{text-decoration:underline}",
      ".af-nft-provider{display:grid;gap:.7rem;border:1px solid rgba(45,212,191,.16);border-radius:14px;background:rgba(20,184,166,.06);padding:.85rem}",
      ".af-nft-provider-title{display:flex;justify-content:space-between;gap:.8rem;align-items:center;color:#e2e8f0;font-weight:950}",
      ".af-nft-provider-title span{color:#5eead4;font-size:.72rem;text-transform:uppercase;letter-spacing:.1em}",
      ".af-nft-inline-code{color:#5eead4;word-break:break-all;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-size:.78rem}",
      ".af-nft-details{border:1px solid rgba(255,255,255,.08);border-radius:12px;background:rgba(255,255,255,.035);padding:.7rem}",
      ".af-nft-details summary{cursor:pointer;color:#cbd5e1;font-weight:900}",
      "@media(max-width:900px){.af-nft-head,.af-nft-grid,.af-nft-flow,.af-nft-mint{grid-template-columns:1fr}.af-nft-studio{padding-top:3rem}}"
    ].join("\n");
    document.head.appendChild(style);
  }

  function textOf(element) {
    return ((element.getAttribute("aria-label") || "") + " " + element.textContent).toLowerCase();
  }

  function hideGenesisUi() {
    document.querySelectorAll("button,a,[role='button'],.af-tool-card").forEach(function (element) {
      var text = textOf(element);
      var href = (element.getAttribute("href") || "").toLowerCase();
      if (text.indexOf("genesis") !== -1 || href.indexOf("/pages/genesis") !== -1 || href.indexOf("#genesis") !== -1 || href.indexOf("#pnetlaunch") !== -1) {
        element.setAttribute("data-algoflow-genesis-hidden", "true");
        element.setAttribute("aria-hidden", "true");
        if (element.tagName === "BUTTON") element.setAttribute("tabindex", "-1");
      }
    });

    if (isGenesisRoute()) {
      window.history.replaceState(null, "", window.location.pathname + window.location.search + "#launchpad");
      scheduleApply();
    }
  }

  function ensureNftNav() {
    if (isDedicatedNftPage()) return;
    var nav = document.querySelector(".af-tool-nav") || document.querySelector("nav");
    if (!nav || document.getElementById(NAV_ID)) return;
    var button = document.createElement("a");
    button.id = NAV_ID;
    button.className = "af-tool-pill";
    button.href = NFT_HASH;
    button.setAttribute("aria-label", "Open NFT Studio inside AlgoFlow");
    button.innerHTML = "<i class=\"fa-solid fa-images\" aria-hidden=\"true\"></i><span>NFT Studio</span>";

    var shapeButton = Array.from(nav.querySelectorAll("button")).find(function (candidate) {
      return textOf(candidate).indexOf("shapemap") !== -1;
    });
    if (shapeButton) {
      nav.insertBefore(button, shapeButton);
    } else {
      nav.appendChild(button);
    }
  }

  function nftPanelHtml() {
    var brokerUrl = defaultUploadBrokerUrl();
    return [
      "<div class=\"af-nft-wrap\">",
      "  <div class=\"af-nft-eyebrow\"><span aria-hidden=\"true\">◆</span> Algorand NFT roadmap</div>",
      "  <div class=\"af-nft-head\">",
      "    <section>",
      "      <h1 class=\"af-nft-title\">NFT Studio for <span>Algorand creators.</span></h1>",
      "      <p class=\"af-nft-copy\">This is the safe first layer for adding NFTs to AlgoFlow: real ARC-3 NFT minting on Algorand TestNet, collection review, portfolio inspection, and a marketplace path that can later use reviewed TestNet contracts. It does not fake buy/sell execution before the contract work exists.</p>",
      "      <div class=\"af-nft-actions\">",
      "        <button class=\"af-nft-btn\" type=\"button\" data-nft-focus=\"mint\">Mint ARC-3 NFT</button>",
      "        <button class=\"af-nft-btn af-nft-btn-secondary\" type=\"button\" data-nft-focus=\"market\">Marketplace contract checklist</button>",
      isDedicatedNftPage() ? "" : "        <a class=\"af-nft-btn af-nft-btn-secondary\" href=\"/pages/nfts/\" aria-label=\"Open the standalone NFT Studio page\">Standalone page</a>",
      "      </div>",
      "      <p class=\"af-nft-note\">Minting is TestNet wallet-signed and non-custodial. Marketplace escrow, royalties, and MainNet listing actions stay gated until reviewed contracts and TestNet evidence exist.</p>",
      "    </section>",
      "    <aside class=\"af-nft-status\" aria-label=\"NFT Studio implementation status\">",
      "      <div class=\"af-nft-status-row\"><strong>Active mint network</strong><span class=\"af-nft-pill\">TestNet</span></div>",
      "      <div class=\"af-nft-status-row\"><strong>NFT standard path</strong><span>ARC-3 ASA NFT</span></div>",
      "      <div class=\"af-nft-status-row\"><strong>Marketplace status</strong><span>Needs TestNet contract</span></div>",
      "      <div class=\"af-nft-status-row\"><strong>Signing stance</strong><span>User wallet only</span></div>",
      "    </aside>",
      "  </div>",
      "  <section class=\"af-nft-mint\" data-nft-card=\"mint\" aria-label=\"ARC-3 NFT minting form\">",
      "    <div class=\"af-nft-mint-panel\">",
      "      <h2>Mint a real ARC-3 NFT on TestNet</h2>",
      "      <p class=\"af-nft-help\">This creates an Algorand Standard Asset with total 1 and decimals 0. Upload media, click Create TestNet NFT, then approve the ASA create transaction in your wallet.</p>",
      "      <div class=\"af-nft-wallet-row\">",
      "        <div><strong>Wallet</strong><br><code data-nft-wallet-status>Not connected</code></div>",
      "        <div style=\"display:flex;gap:.55rem;flex-wrap:wrap;justify-content:flex-end\">",
      "          <select class=\"af-nft-input\" style=\"width:auto;min-width:130px\" name=\"walletProvider\" data-nft-wallet-provider aria-label=\"Wallet provider\"><option value=\"pera\">Pera</option><option value=\"defly\">Defly</option></select>",
      "          <button class=\"af-nft-btn af-nft-btn-secondary\" type=\"button\" data-nft-wallet-connect>Connect wallet</button>",
      "        </div>",
      "      </div>",
      "      <form class=\"af-nft-form\" data-nft-mint-form>",
      "        <div class=\"af-nft-form-row\">",
      "          <div class=\"af-nft-field\"><label for=\"nft-asset-name\">NFT name</label><input class=\"af-nft-input\" id=\"nft-asset-name\" name=\"assetName\" maxlength=\"32\" placeholder=\"ProfitNet Founder Pass\" required></div>",
      "          <div class=\"af-nft-field\"><label for=\"nft-unit-name\">Unit</label><input class=\"af-nft-input\" id=\"nft-unit-name\" name=\"unitName\" maxlength=\"8\" placeholder=\"PNFT\" required></div>",
      "        </div>",
      "        <div class=\"af-nft-field\">",
      "          <label for=\"nft-media-file\">Media file optional</label>",
      "          <div class=\"af-nft-drop\" data-nft-drop-zone tabindex=\"0\" role=\"button\" aria-label=\"Upload or drag NFT media\">Drop image/video here or click to choose</div>",
      "          <input class=\"af-nft-file-input\" id=\"nft-media-file\" name=\"mediaFile\" type=\"file\" accept=\"image/*,video/*\" data-nft-file-input>",
      "          <span class=\"af-nft-help\">Images and videos can become NFTs. This builder previews and hashes locally, then pins to IPFS through the protected upload broker.</span>",
      "        </div>",
      "        <div class=\"af-nft-media-preview\" data-nft-media-preview>No media selected yet.</div>",
      "        <div class=\"af-nft-provider\">",
      "          <div class=\"af-nft-provider-title\">IPFS pinning <span>Protected broker preferred</span></div>",
      "          <div class=\"af-nft-field\"><label for=\"nft-upload-broker-url\">Upload broker URL</label><input class=\"af-nft-input\" id=\"nft-upload-broker-url\" name=\"uploadBrokerUrl\" value=\"" + escapeAttr(brokerUrl) + "\" placeholder=\"/api/nft\"><span class=\"af-nft-help\">Production path: media and metadata go through the protected Worker broker. No Pinata credential belongs in the website.</span></div>",
      isLocalDevHost() ? "          <details class=\"af-nft-details\"><summary>Local direct-token fallback</summary><div class=\"af-nft-field\" style=\"margin-top:.65rem\"><label for=\"nft-pinata-jwt\">Pinata JWT</label><input class=\"af-nft-input\" id=\"nft-pinata-jwt\" name=\"pinataJwt\" type=\"password\" autocomplete=\"off\" placeholder=\"Optional local-only limited Pinata JWT\"><span class=\"af-nft-help\">Use only for local testing. Public production should use the broker URL so users never see your Pinata credential.</span></div></details>" : "",
      "          <div class=\"af-nft-actions\">",
      "            <button class=\"af-nft-btn af-nft-btn-secondary\" type=\"button\" data-nft-pin-media>Pin media to IPFS</button>",
      "            <button class=\"af-nft-btn af-nft-btn-secondary\" type=\"button\" data-nft-pin-metadata>Pin metadata JSON</button>",
      "          </div>",
      "          <div class=\"af-nft-help\" data-nft-pin-output>No files pinned yet.</div>",
      "        </div>",
      "        <div class=\"af-nft-field\"><label for=\"nft-media-url\">Pinned media URL</label><input class=\"af-nft-input\" id=\"nft-media-url\" name=\"mediaUrl\" placeholder=\"ipfs://CID/art.png or https://...\"><span class=\"af-nft-help\">Paste the permanent media URL after pinning the image/video. The generated metadata will point to this URL.</span></div>",
      "        <div class=\"af-nft-field\"><label for=\"nft-description\">Description</label><textarea class=\"af-nft-textarea\" id=\"nft-description\" name=\"description\" maxlength=\"1000\" placeholder=\"Short public description for the NFT metadata\"></textarea></div>",
      "        <div class=\"af-nft-field\"><label for=\"nft-traits\">Traits optional</label><textarea class=\"af-nft-textarea\" id=\"nft-traits\" name=\"traits\" maxlength=\"1000\" placeholder=\"One per line, like: Background: Neon\"></textarea><span class=\"af-nft-help\">Traits are saved under metadata properties. Keep this public-safe; do not include private owner info.</span></div>",
      "        <div class=\"af-nft-actions\">",
      "          <button class=\"af-nft-btn af-nft-btn-secondary\" type=\"button\" data-nft-build-metadata>Build metadata JSON</button>",
      "          <button class=\"af-nft-btn af-nft-btn-secondary\" type=\"button\" data-nft-download-metadata disabled>Download metadata JSON</button>",
      "        </div>",
      "        <div class=\"af-nft-inline-output\"><div class=\"af-nft-metadata-box\" data-nft-metadata-preview>Metadata JSON will appear here after you add a pinned media URL and build it.</div></div>",
      "        <div class=\"af-nft-field\"><label for=\"nft-metadata-url\">ARC-3 metadata URL</label><input class=\"af-nft-input\" id=\"nft-metadata-url\" name=\"metadataUrl\" placeholder=\"ipfs://CID/metadata.json#arc3\" required><span class=\"af-nft-help\">Pin your metadata JSON first, then paste the URL here. IPFS and HTTPS URLs are accepted; <code>#arc3</code> is required.</span></div>",
      "        <div class=\"af-nft-field\"><label for=\"nft-metadata-hash\">Metadata SHA-256 hash</label><input class=\"af-nft-input\" id=\"nft-metadata-hash\" name=\"metadataHash\" placeholder=\"Auto-fill from Fetch & hash metadata, or paste 64 hex chars\"><span class=\"af-nft-help\">The hash becomes the ASA metadata hash. If the metadata URL cannot be fetched because of CORS, paste the SHA-256 manually.</span></div>",
      "        <div class=\"af-nft-field\"><label for=\"nft-note\">Creator note optional</label><textarea class=\"af-nft-textarea\" id=\"nft-note\" name=\"note\" maxlength=\"512\" placeholder=\"Optional public note included in the mint transaction\"></textarea></div>",
      "        <div class=\"af-nft-actions\">",
      "          <button class=\"af-nft-btn\" type=\"button\" data-nft-create-flow>Create TestNet NFT</button>",
      "          <span class=\"af-nft-help\">Guided flow: pin media, build metadata, pin metadata, open wallet, and submit the TestNet mint.</span>",
      "        </div>",
      "        <div class=\"af-nft-actions\">",
      "          <button class=\"af-nft-btn af-nft-btn-secondary\" type=\"button\" data-nft-hash-metadata>Fetch & hash metadata</button>",
      "          <button class=\"af-nft-btn af-nft-btn-secondary\" type=\"submit\" data-nft-mint-submit>Mint with pinned metadata</button>",
      "        </div>",
      "      </form>",
      "      <div class=\"af-nft-status-box\" data-nft-mint-status>Ready. Upload media, add a name and unit, then click Create TestNet NFT.</div>",
      "    </div>",
      "    <aside class=\"af-nft-mint-panel\">",
      "      <h3>Mint preview</h3>",
      "      <div class=\"af-nft-preview\">",
      "        <div class=\"af-nft-preview-row\"><strong>Network</strong><span>Algorand TestNet</span></div>",
      "        <div class=\"af-nft-preview-row\"><strong>ASA total</strong><span>1</span></div>",
      "        <div class=\"af-nft-preview-row\"><strong>Decimals</strong><span>0</span></div>",
      "        <div class=\"af-nft-preview-row\"><strong>Freeze / clawback</strong><span>Disabled</span></div>",
      "        <div class=\"af-nft-preview-row\"><strong>Estimated chain cost</strong><span>~0.101 ALGO minimum balance + fee</span></div>",
      "      </div>",
      "      <div class=\"af-nft-safe\" style=\"margin-top:1rem\">This is real TestNet minting with optional IPFS pinning. It does not create marketplace listings, escrow NFTs, or run MainNet transactions.</div>",
      "      <div class=\"af-nft-output\" data-nft-mint-output></div>",
      "    </aside>",
      "  </section>",
      "  <div class=\"af-nft-grid\">",
      "    <article class=\"af-nft-card\">",
      "      <span class=\"af-nft-stage\">Active first layer</span>",
      "      <h3>ARC-3 minting</h3>",
      "      <p>Creator flow for pinned metadata and ASA creation with total 1 and decimals 0.</p>",
      "      <ul><li>TestNet Pera or Defly signing</li><li>Metadata SHA-256 hash</li><li>No freeze or clawback</li></ul>",
      "    </article>",
      "    <article class=\"af-nft-card\">",
      "      <span class=\"af-nft-stage\">Useful now</span>",
      "      <h3>Portfolio scanner</h3>",
      "      <p>Inspect a wallet's NFT holdings without signing. This can build on the existing Inspector pattern.</p>",
      "      <ul><li>NFT holdings by wallet</li><li>Metadata preview</li><li>Risk flags for clawback/freeze</li></ul>",
      "    </article>",
      "    <article class=\"af-nft-card\" data-nft-card=\"market\">",
      "      <span class=\"af-nft-stage\">Contract gated</span>",
      "      <h3>Buy, sell, trade</h3>",
      "      <p>Marketplace actions need an audited escrow/listing contract, atomic payment + NFT transfer, and TestNet proof.</p>",
      "      <ul><li>Fixed-price listings</li><li>Offers and auctions later</li><li>Royalties after contract review</li></ul>",
      "    </article>",
      "  </div>",
      "  <div class=\"af-nft-flow\" aria-label=\"NFT implementation flow\">",
      "    <div class=\"af-nft-step\"><b>1. Metadata</b>Upload media, pin metadata, preview traits and hashes.</div>",
      "    <div class=\"af-nft-step\"><b>2. Mint</b>Create a standards-aligned ASA NFT after wallet confirmation.</div>",
      "    <div class=\"af-nft-step\"><b>3. List</b>Move to TestNet marketplace contract only after review.</div>",
      "    <div class=\"af-nft-step\"><b>4. Trade</b>Buy/sell with atomic groups after escrow and fees are proven.</div>",
      "  </div>",
      "  <div class=\"af-nft-safe\">Genesis is hidden from this front end because it is not working. NFT marketplace execution is intentionally staged: no custody, no escrow, no fake listings, no MainNet marketplace actions until the contract path is reviewed and tested.</div>",
      "</div>"
    ].join("");
  }

  function showNftPanel() {
    var main = document.querySelector("main.pn-main") || document.querySelector("main:not(#" + PANEL_ID + ")");
    if (main) {
      if (!main.hasAttribute("data-nft-original-display")) {
        originalMainDisplay = main.style.display || "";
        main.setAttribute("data-nft-original-display", originalMainDisplay);
      }
      main.style.display = "none";
    }

    var panel = document.getElementById(PANEL_ID);
    if (!panel) {
      panel = document.createElement("main");
      panel.id = PANEL_ID;
      panel.className = "af-nft-studio";
      var root = document.getElementById("root");
      if (root && root.parentNode) {
        root.parentNode.insertBefore(panel, root.nextSibling);
      } else {
        document.body.appendChild(panel);
      }
    }
    if (panel.getAttribute("data-nft-rendered") !== "nft-studio-v4") {
      panel.innerHTML = nftPanelHtml();
      panel.setAttribute("data-nft-rendered", "nft-studio-v4");
    }

    document.querySelectorAll(".af-tool-pill").forEach(function (button) {
      button.classList.remove("active");
      button.classList.remove("af-nft-active");
    });
    var navButton = document.getElementById(NAV_ID);
    if (navButton) navButton.classList.add("active", "af-nft-active");
  }

  function hideNftPanel() {
    var panel = document.getElementById(PANEL_ID);
    if (panel) panel.remove();
    var main = document.querySelector("main.pn-main") || document.querySelector("main[data-nft-original-display]");
    if (main && main.hasAttribute("data-nft-original-display")) {
      main.style.display = main.getAttribute("data-nft-original-display") || "";
      main.removeAttribute("data-nft-original-display");
    }
    var navButton = document.getElementById(NAV_ID);
    if (navButton) navButton.classList.remove("active", "af-nft-active");
  }

  function shortAddress(address) {
    if (!address || address.length < 16) return address || "Not connected";
    return address.slice(0, 8) + "..." + address.slice(-6);
  }

  function getMintElement(selector) {
    return document.querySelector(selector);
  }

  function setMintStatus(message, type) {
    var status = getMintElement("[data-nft-mint-status]");
    if (!status) return;
    status.classList.remove("is-error", "is-success");
    if (type === "error") status.classList.add("is-error");
    if (type === "success") status.classList.add("is-success");
    status.textContent = message;
  }

  function setMintOutput(html) {
    var output = getMintElement("[data-nft-mint-output]");
    if (output) output.innerHTML = html || "";
  }

  function setMetadataPreview(text) {
    var preview = getMintElement("[data-nft-metadata-preview]");
    if (preview) preview.textContent = text || "Metadata JSON will appear here after you add a pinned media URL and build it.";
  }

  function setDownloadEnabled(enabled) {
    var button = getMintElement("[data-nft-download-metadata]");
    if (button) button.disabled = !enabled;
  }

  function setPinOutput(html) {
    var output = getMintElement("[data-nft-pin-output]");
    if (output) output.innerHTML = html || "No files pinned yet.";
  }

  function updateWalletStatus() {
    var walletStatus = getMintElement("[data-nft-wallet-status]");
    if (walletStatus) walletStatus.textContent = nftMintState.account ? shortAddress(nftMintState.account) : "Not connected";
  }

  function clearMediaObjectUrl() {
    if (nftMintState.mediaObjectUrl) {
      URL.revokeObjectURL(nftMintState.mediaObjectUrl);
      nftMintState.mediaObjectUrl = "";
    }
  }

  function clearMetadataBlobUrl() {
    if (nftMintState.metadataBlobUrl) {
      URL.revokeObjectURL(nftMintState.metadataBlobUrl);
      nftMintState.metadataBlobUrl = "";
    }
  }

  function renderMediaPreview(file) {
    var preview = getMintElement("[data-nft-media-preview]");
    if (!preview) return;
    preview.innerHTML = "";
    if (!file || !nftMintState.mediaObjectUrl) {
      preview.textContent = "No media selected yet.";
      return;
    }
    var media;
    if (file.type.indexOf("video/") === 0) {
      media = document.createElement("video");
      media.controls = true;
      media.muted = true;
      media.playsInline = true;
    } else {
      media = document.createElement("img");
      media.alt = file.name || "Selected NFT media preview";
    }
    media.src = nftMintState.mediaObjectUrl;
    preview.appendChild(media);
  }

  function mediaKindFromFile(file) {
    if (!file || !file.type) return "";
    if (file.type.indexOf("image/") === 0) return "image";
    if (file.type.indexOf("video/") === 0) return "video";
    return "";
  }

  function mediaKindFromUrl(url) {
    var clean = urlWithoutFragment(String(url || "").toLowerCase()).split("?")[0];
    if (/\.(mp4|webm|mov|m4v|ogg)$/.test(clean)) return "video";
    return "image";
  }

  function parseTraits(text) {
    var properties = {};
    String(text || "").split(/\r?\n/).forEach(function (line) {
      var trimmed = line.trim();
      if (!trimmed) return;
      var separator = trimmed.indexOf(":");
      if (separator === -1) {
        properties[trimmed] = true;
        return;
      }
      var key = trimmed.slice(0, separator).trim();
      var value = trimmed.slice(separator + 1).trim();
      if (key) properties[key] = value || true;
    });
    return properties;
  }

  function sanitizeMetadataFilename(name) {
    var clean = String(name || "algoflow-nft").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    return (clean || "algoflow-nft").slice(0, 48) + "-metadata.json";
  }

  function sanitizePinName(name) {
    return String(name || "algoflow-nft").replace(/[^\w.\- ]+/g, "").trim().slice(0, 80) || "algoflow-nft";
  }

  async function hashBytes(bytes) {
    if (!window.crypto || !window.crypto.subtle) throw new Error("This browser cannot compute SHA-256.");
    return bytesToHex(new Uint8Array(await window.crypto.subtle.digest("SHA-256", bytes)));
  }

  async function handleMediaFile(file) {
    try {
      if (!file) return;
      var kind = mediaKindFromFile(file);
      if (!kind) throw new Error("Choose an image or video file.");
      if (file.size > 50 * 1024 * 1024) throw new Error("Use a file under 50 MB for the browser builder.");
      clearMediaObjectUrl();
      nftMintState.pinnedMediaCid = "";
      nftMintState.pinnedMetadataCid = "";
      nftMintState.metadataJson = "";
      nftMintState.lastMetadataHash = "";
      clearMetadataBlobUrl();
      nftMintState.mediaFile = file;
      nftMintState.mediaObjectUrl = URL.createObjectURL(file);
      var mediaInput = getMintElement("[name='mediaUrl']");
      var metadataInput = getMintElement("[name='metadataUrl']");
      var hashInput = getMintElement("[name='metadataHash']");
      if (mediaInput) mediaInput.value = "";
      if (metadataInput) metadataInput.value = "";
      if (hashInput) hashInput.value = "";
      setMetadataPreview("Metadata JSON will appear here after you add a pinned media URL and build it.");
      setPinOutput("No files pinned yet.");
      setDownloadEnabled(false);
      renderMediaPreview(file);
      setMintStatus("Hashing selected " + kind + " locally...");
      nftMintState.mediaHash = await hashBytes(new Uint8Array(await file.arrayBuffer()));
      setMintStatus("Media ready: " + file.name + " (" + kind + ", sha256 " + nftMintState.mediaHash.slice(0, 12) + "..." + nftMintState.mediaHash.slice(-8) + ").", "success");
    } catch (error) {
      setMintStatus((error && error.message) || "Could not read media file.", "error");
    }
  }

  function getPinataJwt() {
    var input = getMintElement("[name='pinataJwt']");
    var token = input ? String(input.value || "").trim() : "";
    if (!token) throw new Error("Paste a limited Pinata JWT before pinning.");
    if (token.length < 40) throw new Error("Pinata JWT looks too short.");
    return token;
  }

  function getUploadBrokerUrl() {
    var input = getMintElement("[name='uploadBrokerUrl']");
    var value = input ? String(input.value || "").trim() : "";
    if (!value) return "";
    if (!/^https?:\/\//i.test(value) && value.charAt(0) !== "/") throw new Error("Upload broker URL must start with /, http://, or https://.");
    return value.replace(/\/+$/, "");
  }

  async function pinFileViaBroker(file, name, kind, brokerUrl) {
    var form = new FormData();
    form.append("file", file, sanitizePinName(name || file.name));
    form.append("kind", kind);
    form.append("name", sanitizePinName(name || file.name));
    var response = await fetch(brokerUrl + "/pin", {
      method: "POST",
      body: form
    });
    var result = await response.json().catch(function () {
      return null;
    });
    if (!response.ok || !result || result.ok !== true || !result.cid) {
      if (!result) {
        throw new Error("Upload broker at " + brokerUrl + " did not return JSON (HTTP " + response.status + "). If this domain is not proxied through Cloudflare, paste the deployed workers.dev broker URL instead of /api/nft.");
      }
      var errorCode = result.error ? result.error : "broker_upload_failed";
      throw new Error("Upload broker failed: " + errorCode + ".");
    }
    return result.cid;
  }

  async function pinFileToIpfs(file, name) {
    var brokerUrl = getUploadBrokerUrl();
    var kind = file && file.type === "application/json" ? "metadata" : "media";
    if (brokerUrl) return pinFileViaBroker(file, name, kind, brokerUrl);

    if (!isLocalDevHost()) throw new Error("Direct Pinata JWT pinning is disabled on the public site. Use the protected upload broker URL (default /api/nft).");
    var token = getPinataJwt();
    var form = new FormData();
    form.append("file", file, sanitizePinName(name || file.name));
    form.append("pinataMetadata", JSON.stringify({ name: sanitizePinName(name || file.name) }));
    form.append("pinataOptions", JSON.stringify({ cidVersion: 1 }));
    var response = await fetch(PINATA_FILE_ENDPOINT, {
      method: "POST",
      headers: { Authorization: "Bearer " + token },
      body: form
    });
    if (!response.ok) throw new Error("IPFS pin failed with HTTP " + response.status + ".");
    var result = await response.json();
    if (!result || !result.IpfsHash) throw new Error("IPFS pin response did not include a CID.");
    return result.IpfsHash;
  }

  async function pinSelectedMediaCore() {
    if (!nftMintState.mediaFile) throw new Error("Choose or drop an image/video before pinning media.");
    setMintStatus("Pinning media to IPFS...");
    var cid = await pinFileToIpfs(nftMintState.mediaFile, nftMintState.mediaFile.name || "algoflow-media");
    nftMintState.pinnedMediaCid = cid;
    var mediaInput = getMintElement("[name='mediaUrl']");
    if (mediaInput) mediaInput.value = "ipfs://" + cid;
    setPinOutput("Media pinned: <span class=\"af-nft-inline-code\">ipfs://" + cid + "</span>");
    setMintStatus("Media pinned. Build metadata JSON next.", "success");
    return cid;
  }

  async function pinSelectedMedia() {
    try {
      await pinSelectedMediaCore();
    } catch (error) {
      setMintStatus((error && error.message) || "Could not pin media.", "error");
    }
  }

  async function pinMetadataJsonCore() {
    await buildMetadataJsonCore();
    if (!nftMintState.metadataJson) throw new Error("Build metadata JSON before pinning it.");
    var values = collectMintForm();
    var filename = sanitizeMetadataFilename(values.assetName);
    var file = new File([nftMintState.metadataJson], filename, { type: "application/json" });
    setMintStatus("Pinning exact metadata JSON to IPFS...");
    var cid = await pinFileToIpfs(file, filename);
    nftMintState.pinnedMetadataCid = cid;
    var metadataInput = getMintElement("[name='metadataUrl']");
    if (metadataInput) metadataInput.value = "ipfs://" + cid + "#arc3";
    setPinOutput([
      nftMintState.pinnedMediaCid ? "Media: <span class=\"af-nft-inline-code\">ipfs://" + nftMintState.pinnedMediaCid + "</span><br>" : "",
      "Metadata: <span class=\"af-nft-inline-code\">ipfs://" + cid + "#arc3</span>"
    ].join(""));
    setMintStatus("Metadata pinned. Connect wallet and mint the ARC-3 NFT.", "success");
    return cid;
  }

  async function pinMetadataJson() {
    try {
      await pinMetadataJsonCore();
    } catch (error) {
      setMintStatus((error && error.message) || "Could not pin metadata.", "error");
    }
  }


  async function loadMintModules() {
    if (!nftMintState.modulesPromise) {
      nftMintState.modulesPromise = Promise.all([
        import(ALGOSDK_IMPORT_URL),
        import(PERA_IMPORT_URL),
        import(DEFLY_IMPORT_URL)
      ]).then(function (modules) {
        return {
          algosdk: modules[0].default || modules[0],
          PeraWalletConnect: modules[1].PeraWalletConnect,
          DeflyWalletConnect: modules[2].DeflyWalletConnect || modules[2].default
        };
      });
    }
    return nftMintState.modulesPromise;
  }

  function selectedWalletProvider() {
    var input = getMintElement("[name='walletProvider']");
    var provider = input ? String(input.value || "pera") : "pera";
    return provider === "defly" ? "defly" : "pera";
  }

  function walletProviderLabel(provider) {
    return provider === "defly" ? "Defly" : "Pera";
  }

  async function getSelectedWallet() {
    var modules = await loadMintModules();
    var provider = selectedWalletProvider();
    nftMintState.activeWallet = provider;
    if (!nftMintState.wallets[provider]) {
      var WalletClass = provider === "defly" ? modules.DeflyWalletConnect : modules.PeraWalletConnect;
      nftMintState.wallets[provider] = new WalletClass({
        chainId: TESTNET.chainId,
        shouldShowSignTxnToast: true
      });
      try {
        var accounts = await nftMintState.wallets[provider].reconnectSession();
        if (accounts && accounts.length) nftMintState.account = accounts[0];
      } catch (_) {
        nftMintState.account = "";
      }
    }
    updateWalletStatus();
    return nftMintState.wallets[provider];
  }

  async function connectNftWallet() {
    var provider = selectedWalletProvider();
    var label = walletProviderLabel(provider);
    try {
      setMintStatus("Opening " + label + " TestNet connection...");
      var wallet = await getSelectedWallet();
      var accounts = await wallet.connect();
      nftMintState.account = accounts && accounts[0] ? accounts[0] : "";
      if (wallet.connector && wallet.connector.on) {
        wallet.connector.on("disconnect", function () {
          nftMintState.account = "";
          updateWalletStatus();
        });
      }
      updateWalletStatus();
      setMintStatus("Connected " + label + " to " + shortAddress(nftMintState.account) + " on " + TESTNET.label + ".", "success");
    } catch (error) {
      if (error && error.data && error.data.type === "CONNECT_MODAL_CLOSED") {
        setMintStatus(label + " connection cancelled.");
        return;
      }
      setMintStatus("Wallet connection failed. Check " + label + " and try again.", "error");
    }
  }

  function normalizeArc3Url(value) {
    return String(value || "").trim();
  }

  function urlWithoutFragment(value) {
    return value.split("#")[0];
  }

  function toFetchableMetadataUrl(value) {
    var clean = urlWithoutFragment(normalizeArc3Url(value));
    if (clean.toLowerCase().startsWith("ipfs://")) {
      return "https://ipfs.io/ipfs/" + clean.slice("ipfs://".length);
    }
    return clean;
  }

  function bytesToHex(bytes) {
    return Array.from(bytes).map(function (byte) {
      return byte.toString(16).padStart(2, "0");
    }).join("");
  }

  function hexToBytes(hex) {
    var clean = String(hex || "").trim().toLowerCase();
    if (!/^[0-9a-f]{64}$/.test(clean)) throw new Error("Metadata hash must be exactly 64 hex characters.");
    var out = new Uint8Array(32);
    for (var index = 0; index < 32; index += 1) {
      out[index] = parseInt(clean.slice(index * 2, index * 2 + 2), 16);
    }
    return out;
  }

  async function hashMetadataUrl() {
    try {
      var input = getMintElement("[name='metadataUrl']");
      var hashInput = getMintElement("[name='metadataHash']");
      var metadataUrl = input ? normalizeArc3Url(input.value) : "";
      if (!metadataUrl) throw new Error("Paste an ARC-3 metadata URL first.");
      if (metadataUrl.toLowerCase().indexOf("#arc3") === -1) throw new Error("ARC-3 metadata URL must include #arc3.");
      if (!window.crypto || !window.crypto.subtle) throw new Error("This browser cannot compute SHA-256.");
      setMintStatus("Fetching metadata and computing SHA-256...");
      var response = await fetch(toFetchableMetadataUrl(metadataUrl), { headers: { accept: "application/json,*/*" } });
      if (!response.ok) throw new Error("Metadata URL returned HTTP " + response.status + ".");
      var bytes = new Uint8Array(await response.arrayBuffer());
      var digest = new Uint8Array(await window.crypto.subtle.digest("SHA-256", bytes));
      var hex = bytesToHex(digest);
      nftMintState.lastMetadataHash = hex;
      if (hashInput) hashInput.value = hex;
      setMintStatus("Metadata hash ready: " + hex.slice(0, 12) + "..." + hex.slice(-8), "success");
    } catch (error) {
      setMintStatus((error && error.message) || "Could not hash metadata. Paste the SHA-256 manually.", "error");
    }
  }

  function collectMintForm() {
    var form = getMintElement("[data-nft-mint-form]");
    var data = new FormData(form);
    return {
      assetName: String(data.get("assetName") || "").trim(),
      unitName: String(data.get("unitName") || "").trim().toUpperCase(),
      mediaUrl: normalizeArc3Url(data.get("mediaUrl")),
      description: String(data.get("description") || "").trim(),
      traits: String(data.get("traits") || "").trim(),
      metadataUrl: normalizeArc3Url(data.get("metadataUrl")),
      metadataHash: String(data.get("metadataHash") || "").trim().toLowerCase(),
      note: String(data.get("note") || "").trim()
    };
  }

  async function buildMetadataJsonCore() {
    nftMintState.metadataJson = "";
    clearMetadataBlobUrl();
    var values = collectMintForm();
    if (!values.assetName) throw new Error("NFT name is required before building metadata.");
    if (!values.mediaUrl) throw new Error("Paste a pinned media URL before building metadata.");
    if (!/^(ipfs:\/\/|https:\/\/)/i.test(values.mediaUrl)) throw new Error("Pinned media URL must start with ipfs:// or https://.");
    var file = nftMintState.mediaFile;
    var kind = mediaKindFromFile(file) || mediaKindFromUrl(values.mediaUrl);
    var mime = file && file.type ? file.type : (kind === "video" ? "video/mp4" : "image/png");
    var properties = parseTraits(values.traits);
    properties.generator = "AlgoFlow NFT Studio";
    properties.network = TESTNET.label;
    properties.standard = "ARC-3";
    if (file) {
      properties.media_sha256 = nftMintState.mediaHash || await hashBytes(new Uint8Array(await file.arrayBuffer()));
      properties.media_name = file.name;
      properties.media_size = file.size;
    }
    var metadata = {
      name: values.assetName,
      description: values.description || "Minted with AlgoFlow NFT Studio.",
      properties: properties
    };
    if (kind === "video") {
      metadata.animation_url = values.mediaUrl;
      metadata.animation_url_mimetype = mime;
    } else {
      metadata.image = values.mediaUrl;
      metadata.image_mimetype = mime;
    }
    var json = JSON.stringify(metadata, null, 2);
    var hashInput = getMintElement("[name='metadataHash']");
    var digest = await hashBytes(new TextEncoder().encode(json));
    clearMetadataBlobUrl();
    nftMintState.metadataJson = json;
    nftMintState.metadataBlobUrl = URL.createObjectURL(new Blob([json], { type: "application/json" }));
    if (hashInput) hashInput.value = digest;
    setMetadataPreview(json);
    setDownloadEnabled(true);
    setMintStatus("Metadata JSON built. Pin it, then mint the ARC-3 NFT.", "success");
    return json;
  }

  async function buildMetadataJson() {
    try {
      await buildMetadataJsonCore();
    } catch (error) {
      setDownloadEnabled(false);
      setMintStatus((error && error.message) || "Could not build metadata JSON.", "error");
    }
  }

  function downloadMetadataJson() {
    if (!nftMintState.metadataJson || !nftMintState.metadataBlobUrl) {
      setMintStatus("Build metadata JSON before downloading.", "error");
      return;
    }
    var values = collectMintForm();
    var link = document.createElement("a");
    link.href = nftMintState.metadataBlobUrl;
    link.download = sanitizeMetadataFilename(values.assetName);
    document.body.appendChild(link);
    link.click();
    link.remove();
    setMintStatus("Metadata JSON downloaded. Pin this JSON file, then paste its ipfs:// or https:// URL with #arc3.", "success");
  }

  function validateMintForm(values) {
    if (!values.assetName) throw new Error("NFT name is required.");
    if (values.assetName.length > 32) throw new Error("NFT name must be 32 characters or fewer.");
    if (!values.unitName) throw new Error("Unit name is required.");
    if (values.unitName.length > 8) throw new Error("Unit name must be 8 characters or fewer.");
    if (!values.metadataUrl) throw new Error("ARC-3 metadata URL is required.");
    if (values.metadataUrl.toLowerCase().indexOf("#arc3") === -1) throw new Error("ARC-3 metadata URL must include #arc3.");
    if (!/^(ipfs:\/\/|https:\/\/)/i.test(values.metadataUrl)) throw new Error("Metadata URL must start with ipfs:// or https://.");
    if (!/^[0-9a-f]{64}$/.test(values.metadataHash)) throw new Error("Metadata SHA-256 hash is required. Use Fetch & hash metadata or paste 64 hex characters.");
  }

  async function mintArc3NftCore() {
    setMintOutput("");
    var values = collectMintForm();
    validateMintForm(values);
    var modules = await loadMintModules();
    var algosdk = modules.algosdk;
    var wallet = await getSelectedWallet();
    var providerLabel = walletProviderLabel(nftMintState.activeWallet);
    if (!nftMintState.account) {
      var accounts = await wallet.connect();
      nftMintState.account = accounts && accounts[0] ? accounts[0] : "";
      updateWalletStatus();
    }
    if (!nftMintState.account) throw new Error("No wallet account selected.");

    setMintStatus("Building ARC-3 NFT mint transaction...");
    var algod = new algosdk.Algodv2("", TESTNET.algod, "");
    var suggestedParams = await algod.getTransactionParams().do();
    suggestedParams.fee = 1000;
    suggestedParams.flatFee = true;
    var note = values.note ? new TextEncoder().encode(values.note.slice(0, 512)) : undefined;
    var metadataHash = hexToBytes(values.metadataHash);
    var txn = algosdk.makeAssetCreateTxnWithSuggestedParamsFromObject({
      sender: nftMintState.account,
      total: 1,
      decimals: 0,
      defaultFrozen: false,
      unitName: values.unitName,
      assetName: values.assetName,
      assetURL: values.metadataUrl,
      assetMetadataHash: metadataHash,
      manager: nftMintState.account,
      reserve: nftMintState.account,
      freeze: undefined,
      clawback: undefined,
      note: note,
      suggestedParams: suggestedParams
    });
    var txId = txn.txID();

    setMintStatus("Sign the NFT mint transaction in " + providerLabel + "...");
    var signedTxns = await wallet.signTransaction([[{ txn: txn, signers: [nftMintState.account] }]], nftMintState.account);
    setMintStatus("Submitting signed TestNet transaction...");
    await algod.sendRawTransaction(signedTxns).do();
    var confirmation = await algosdk.waitForConfirmation(algod, txId, 4);
    var assetId = confirmation && (confirmation["asset-index"] || confirmation.assetIndex);
    if (!assetId) {
      try {
        var pending = await algod.pendingTransactionInformation(txId).do();
        assetId = pending["asset-index"] || pending.assetIndex;
      } catch (_) {}
    }
    setMintStatus("NFT minted on Algorand TestNet.", "success");
    setMintOutput([
      "<div class=\"af-nft-safe\">",
      "<strong>Mint complete.</strong><br>",
      assetId ? "Asset ID: <a href=\"" + TESTNET.assetExplorer + assetId + "\" target=\"_blank\" rel=\"noopener noreferrer\">" + assetId + "</a><br>" : "Asset ID: check the transaction details.<br>",
      "Transaction: <a href=\"" + TESTNET.txExplorer + txId + "\" target=\"_blank\" rel=\"noopener noreferrer\">" + txId.slice(0, 14) + "..." + txId.slice(-8) + "</a>",
      "</div>"
    ].join(""));
    return { txId: txId, assetId: assetId };
  }

  async function mintArc3Nft(event) {
    event.preventDefault();
    var submitButton = getMintElement("[data-nft-mint-submit]");
    try {
      if (submitButton) submitButton.disabled = true;
      await mintArc3NftCore();
    } catch (error) {
      setMintStatus((error && error.message) || "Mint failed.", "error");
    } finally {
      if (submitButton) submitButton.disabled = false;
    }
  }

  async function createTestnetNftFlow() {
    var createButton = getMintElement("[data-nft-create-flow]");
    var submitButton = getMintElement("[data-nft-mint-submit]");
    try {
      if (createButton) createButton.disabled = true;
      if (submitButton) submitButton.disabled = true;
      setMintOutput("");
      var values = collectMintForm();
      if (!values.assetName) throw new Error("Add an NFT name first.");
      if (!values.unitName) throw new Error("Add a short unit name first.");
      if (!nftMintState.mediaFile && !values.mediaUrl) throw new Error("Upload media or paste an existing media URL first.");
      if (nftMintState.mediaFile && !values.mediaUrl) await pinSelectedMediaCore();
      await pinMetadataJsonCore();
      await mintArc3NftCore();
    } catch (error) {
      setMintStatus((error && error.message) || "Could not create NFT.", "error");
    } finally {
      if (createButton) createButton.disabled = false;
      if (submitButton) submitButton.disabled = false;
    }
  }

  function wireNftMinting() {
    updateWalletStatus();
    var connect = getMintElement("[data-nft-wallet-connect]");
    if (connect && !connect.hasAttribute("data-nft-wired")) {
      connect.setAttribute("data-nft-wired", "true");
      connect.addEventListener("click", connectNftWallet);
    }
    var walletProvider = getMintElement("[data-nft-wallet-provider]");
    if (walletProvider && !walletProvider.hasAttribute("data-nft-wired")) {
      walletProvider.setAttribute("data-nft-wired", "true");
      walletProvider.addEventListener("change", function () {
        nftMintState.account = "";
        nftMintState.activeWallet = selectedWalletProvider();
        updateWalletStatus();
        setMintStatus("Selected " + walletProviderLabel(nftMintState.activeWallet) + ". Connect before minting.");
      });
    }
    var hash = getMintElement("[data-nft-hash-metadata]");
    if (hash && !hash.hasAttribute("data-nft-wired")) {
      hash.setAttribute("data-nft-wired", "true");
      hash.addEventListener("click", hashMetadataUrl);
    }
    var fileInput = getMintElement("[data-nft-file-input]");
    var dropZone = getMintElement("[data-nft-drop-zone]");
    if (fileInput && !fileInput.hasAttribute("data-nft-wired")) {
      fileInput.setAttribute("data-nft-wired", "true");
      fileInput.addEventListener("change", function () {
        handleMediaFile(fileInput.files && fileInput.files[0]);
      });
    }
    if (dropZone && !dropZone.hasAttribute("data-nft-wired")) {
      dropZone.setAttribute("data-nft-wired", "true");
      dropZone.addEventListener("click", function () {
        if (fileInput) fileInput.click();
      });
      dropZone.addEventListener("keydown", function (event) {
        if ((event.key === "Enter" || event.key === " ") && fileInput) {
          event.preventDefault();
          fileInput.click();
        }
      });
      ["dragenter", "dragover"].forEach(function (name) {
        dropZone.addEventListener(name, function (event) {
          event.preventDefault();
          dropZone.classList.add("is-dragging");
        });
      });
      ["dragleave", "drop"].forEach(function (name) {
        dropZone.addEventListener(name, function (event) {
          event.preventDefault();
          dropZone.classList.remove("is-dragging");
        });
      });
      dropZone.addEventListener("drop", function (event) {
        var file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
        handleMediaFile(file);
      });
    }
    var buildMetadata = getMintElement("[data-nft-build-metadata]");
    if (buildMetadata && !buildMetadata.hasAttribute("data-nft-wired")) {
      buildMetadata.setAttribute("data-nft-wired", "true");
      buildMetadata.addEventListener("click", buildMetadataJson);
    }
    var downloadMetadata = getMintElement("[data-nft-download-metadata]");
    if (downloadMetadata && !downloadMetadata.hasAttribute("data-nft-wired")) {
      downloadMetadata.setAttribute("data-nft-wired", "true");
      downloadMetadata.addEventListener("click", downloadMetadataJson);
    }
    var pinMedia = getMintElement("[data-nft-pin-media]");
    if (pinMedia && !pinMedia.hasAttribute("data-nft-wired")) {
      pinMedia.setAttribute("data-nft-wired", "true");
      pinMedia.addEventListener("click", pinSelectedMedia);
    }
    var pinMetadata = getMintElement("[data-nft-pin-metadata]");
    if (pinMetadata && !pinMetadata.hasAttribute("data-nft-wired")) {
      pinMetadata.setAttribute("data-nft-wired", "true");
      pinMetadata.addEventListener("click", pinMetadataJson);
    }
    var createFlow = getMintElement("[data-nft-create-flow]");
    if (createFlow && !createFlow.hasAttribute("data-nft-wired")) {
      createFlow.setAttribute("data-nft-wired", "true");
      createFlow.addEventListener("click", createTestnetNftFlow);
    }
    var form = getMintElement("[data-nft-mint-form]");
    if (form && !form.hasAttribute("data-nft-wired")) {
      form.setAttribute("data-nft-wired", "true");
      form.addEventListener("submit", mintArc3Nft);
      form.addEventListener("input", function (event) {
        if (event.target && event.target.name === "unitName") {
          event.target.value = event.target.value.toUpperCase().slice(0, 8);
        }
      });
    }
  }

  function wirePanelButtons() {
    document.querySelectorAll("[data-nft-focus]").forEach(function (button) {
      if (button.hasAttribute("data-nft-wired")) return;
      button.setAttribute("data-nft-wired", "true");
      button.addEventListener("click", function () {
        var target = document.querySelector("[data-nft-card='" + button.getAttribute("data-nft-focus") + "']");
        if (target) target.scrollIntoView({ behavior: "smooth", block: "center" });
      });
    });
    wireNftMinting();
  }

  function applyOverrides() {
    scheduled = false;
    injectStyles();
    hideGenesisUi();
    ensureNftNav();
    if (isNftRoute()) {
      showNftPanel();
      wirePanelButtons();
    } else {
      hideNftPanel();
    }
  }

  function scheduleApply() {
    if (scheduled) return;
    scheduled = true;
    if (document.hidden || typeof window.requestAnimationFrame !== "function") {
      window.setTimeout(applyOverrides, 0);
    } else {
      window.requestAnimationFrame(applyOverrides);
    }
  }

  window.addEventListener("hashchange", scheduleApply);
  window.addEventListener("DOMContentLoaded", scheduleApply);
  window.addEventListener("popstate", scheduleApply);

  ["pushState", "replaceState"].forEach(function (name) {
    var original = window.history[name];
    if (typeof original !== "function") return;
    window.history[name] = function () {
      var result = original.apply(this, arguments);
      scheduleApply();
      return result;
    };
  });

  scheduleApply();
  var startupAttempts = 0;
  var startupTimer = window.setInterval(function () {
    startupAttempts += 1;
    scheduleApply();
    if (startupAttempts >= 20) window.clearInterval(startupTimer);
  }, 250);
})();
