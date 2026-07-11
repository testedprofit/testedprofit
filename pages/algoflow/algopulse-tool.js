(function () {
  "use strict";

  var TOOL_HASH = "#algopulse";
  var PANEL_ID = "algoflow-algopulse-tool";
  var NAV_ID = "algoflow-algopulse-nav";
  var EVIDENCE_URL = "/algopulse-market-engine/artifacts/phase3-testnet-access-final-evidence.json";
  var SOURCE_URL = "https://github.com/testedprofit/testedprofit/tree/agent/algopulse-tool-entry/algopulse-market-engine";
  var scheduled = false;
  var evidenceRequested = false;

  function isAlgoPulseRoute() {
    return window.location.hash.toLowerCase() === TOOL_HASH;
  }

  function isLocalHost() {
    return ["localhost", "127.0.0.1", "::1"].indexOf(window.location.hostname) !== -1;
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function ensureNav() {
    var nav = document.querySelector(".af-tool-nav") || document.querySelector("#root nav");
    if (!nav || document.getElementById(NAV_ID)) return;
    var link = document.createElement("a");
    link.id = NAV_ID;
    link.className = "af-tool-pill";
    link.href = TOOL_HASH;
    link.setAttribute("aria-label", "Open AlgoPulse arbitrage intelligence");
    link.innerHTML = '<i class="fa-solid fa-wave-square" aria-hidden="true"></i><span>AlgoPulse</span>';
    nav.appendChild(link);
  }

  function localEngineAction() {
    if (!isLocalHost()) {
      return '<span class="af-algopulse-button secondary" aria-disabled="true">Backend deployment pending</span>';
    }
    return '<a class="af-algopulse-button" href="http://127.0.0.1:8777/?v=algoflow-tool#pulse">Open full local engine</a>';
  }

  function panelHtml() {
    return [
      '<div class="af-algopulse-wrap">',
      '  <header class="af-algopulse-head">',
      '    <div>',
      '      <span class="af-algopulse-kicker">AlgoFlow tool / Phase 3 TestNet Access</span>',
      '      <h1 class="af-algopulse-title">Arbitrage Intelligence</h1>',
      '      <p class="af-algopulse-copy">Read-only Algorand liquidity scanning, quote comparison, route forensics, risk decisions, and paper outcomes in one operator-grade tool.</p>',
      '    </div>',
      '    <div class="af-algopulse-lock"><span>Execution boundary</span><strong>Live execution locked</strong></div>',
      '  </header>',
      '  <section class="af-algopulse-status" aria-label="AlgoPulse tool status">',
      '    <div><span>Network</span><strong data-ap-network>TestNet</strong></div>',
      '    <div><span>Access</span><strong>Connect-only wallets</strong></div>',
      '    <div><span>Public data</span><strong>Delayed and redacted</strong></div>',
      '    <div><span>PNET asset</span><strong data-ap-pnet>Not configured</strong></div>',
      '  </section>',
      '  <section class="af-algopulse-grid" aria-label="AlgoPulse capabilities">',
      '    <article class="af-algopulse-card"><span class="af-algopulse-chip">Read only</span><h2>Pool Scanner</h2><p>Tinyman and Pact pool state, reserve depth, rounds, timestamps, and connector freshness.</p></article>',
      '    <article class="af-algopulse-card"><span class="af-algopulse-chip">Evidence</span><h2>Route Intelligence</h2><p>Two-leg and triangle candidates with comparable units, explicit fees, and decision reasons.</p></article>',
      '    <article class="af-algopulse-card"><span class="af-algopulse-chip">Paper only</span><h2>Opportunity Decay</h2><p>Exact-route T+5 and T+30 outcomes, quote decay, survival, and failure evidence.</p></article>',
      '    <article class="af-algopulse-card"><span class="af-algopulse-chip">Fail closed</span><h2>Risk Inspector</h2><p>Freshness, liquidity, impact, allowlist, fee, and profit-threshold rejection evidence.</p></article>',
      '    <article class="af-algopulse-card"><span class="af-algopulse-chip">TestNet</span><h2>Pera and Defly Access</h2><p>Connect and read account state only. No signing request, opt-in action, or submission path.</p></article>',
      '    <article class="af-algopulse-card"><span class="af-algopulse-chip">Ops</span><h2>Control Room</h2><p>Connector health, readiness gates, activity, blockers, and source-labeled evidence.</p></article>',
      '  </section>',
      '  <section class="af-algopulse-evidence" aria-live="polite">',
      '    <div class="af-algopulse-evidence-head"><h2>Latest reviewed evidence</h2><span class="af-algopulse-source" data-ap-source>Loading stored evidence</span></div>',
      '    <dl>',
      '      <div><dt>Captured</dt><dd data-ap-captured>Unavailable</dd></div>',
      '      <div><dt>algod</dt><dd data-ap-algod>Unavailable</dd></div>',
      '      <div><dt>Indexer</dt><dd data-ap-indexer>Unavailable</dd></div>',
      '      <div><dt>Safety</dt><dd>Signing and submission disabled</dd></div>',
      '    </dl>',
      '  </section>',
      '  <div class="af-algopulse-actions">',
      localEngineAction(),
      '    <a class="af-algopulse-button secondary" href="' + SOURCE_URL + '" target="_blank" rel="noopener noreferrer">Review source and evidence</a>',
      '  </div>',
      '</div>'
    ].join("");
  }

  function setText(selector, value) {
    var element = document.querySelector(selector);
    if (element) element.textContent = value;
  }

  function loadEvidence() {
    if (evidenceRequested || !window.fetch) return;
    evidenceRequested = true;
    fetch(EVIDENCE_URL, { headers: { accept: "application/json" }, cache: "no-store" })
      .then(function (response) {
        if (!response.ok) throw new Error("evidence unavailable");
        return response.json();
      })
      .then(function (evidence) {
        var captured = evidence && evidence.capturedAt ? new Date(evidence.capturedAt) : null;
        setText("[data-ap-source]", "stored evidence");
        setText("[data-ap-captured]", captured && !isNaN(captured.getTime()) ? captured.toLocaleString() : "Stored snapshot");
        setText("[data-ap-network]", evidence.profile && evidence.profile.network ? String(evidence.profile.network).toUpperCase() : "TestNet");
        setText("[data-ap-pnet]", evidence.profile && evidence.profile.pnetConfigured ? "Configured" : "Not configured");
        setText("[data-ap-algod]", connectorLabel(evidence.networkHealth && evidence.networkHealth.algod));
        setText("[data-ap-indexer]", connectorLabel(evidence.networkHealth && evidence.networkHealth.indexer));
      })
      .catch(function () {
        setText("[data-ap-source]", "evidence unavailable");
      });
  }

  function connectorLabel(connector) {
    if (!connector) return "Unavailable";
    var status = connector.status || (connector.healthy ? "ok" : "unavailable");
    var round = connector.lastRound ? " / round " + connector.lastRound : "";
    return String(status).toUpperCase() + round;
  }

  function showPanel() {
    var main = document.querySelector("main.pn-main") || document.querySelector("#root main");
    if (!main) return;
    var panel = document.getElementById(PANEL_ID);
    if (!panel) {
      panel = document.createElement("section");
      panel.id = PANEL_ID;
      panel.className = "af-algopulse-panel";
      panel.innerHTML = panelHtml();
      main.appendChild(panel);
    }
    Array.from(main.children).forEach(function (child) {
      if (child === panel || child.hasAttribute("data-algopulse-original-display")) return;
      child.setAttribute("data-algopulse-original-display", child.style.display || "");
      child.style.display = "none";
    });
    panel.style.display = "block";
    var nav = document.getElementById(NAV_ID);
    if (nav) nav.classList.add("active", "af-algopulse-active");
    loadEvidence();
  }

  function hidePanel() {
    var panel = document.getElementById(PANEL_ID);
    if (panel) panel.remove();
    document.querySelectorAll("[data-algopulse-original-display]").forEach(function (element) {
      element.style.display = element.getAttribute("data-algopulse-original-display") || "";
      element.removeAttribute("data-algopulse-original-display");
    });
    var nav = document.getElementById(NAV_ID);
    if (nav) nav.classList.remove("active", "af-algopulse-active");
    evidenceRequested = false;
  }

  function apply() {
    scheduled = false;
    ensureNav();
    if (isAlgoPulseRoute()) showPanel();
    else hidePanel();
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    window.requestAnimationFrame ? window.requestAnimationFrame(apply) : window.setTimeout(apply, 0);
  }

  window.addEventListener("DOMContentLoaded", schedule);
  window.addEventListener("hashchange", schedule);
  window.addEventListener("popstate", schedule);
  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  schedule();
})();
