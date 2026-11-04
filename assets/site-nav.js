(function () {
  var STATES = [
    ["Alabama", "/AL/"],
    ["Colorado", "/CO/"],
    ["Hawaii", "/HI/"],
    ["Iowa", "/IA/"],
    ["Indiana", "/IN/"],
    ["Kansas", "/KS/"],
    ["Kentucky", "/KY/"],
    ["Louisiana", "/LA/"],
    ["Michigan", "/MI/"],
    ["Oregon", "/OR/"],
    ["West Virginia", "/WV/"],
    ["Wyoming", "/WY/"]
  ];
  var PRIMARY = [
    ["Landmarks", "/pages/landmarks/"],
    ["Tools", "/tools/"],
    ["Earning Guides", "/pages/guides/"],
    ["Games", "/freebrowsergames/"],
    ["Algorand", "/pages/PNET/"]
  ];

  function el(tag, attrs, html) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (key) {
        if (key === "class") node.className = attrs[key];
        else node.setAttribute(key, attrs[key]);
      });
    }
    if (html != null) node.innerHTML = html;
    return node;
  }

  function linkList(pairs) {
    return pairs.map(function (pair) {
      return '<li><a href="' + pair[1] + '">' + pair[0] + '</a></li>';
    }).join("");
  }

  var header = el("header", { class: "pn-header" });
  header.innerHTML =
    '<div class="pn-bar">' +
      '<a class="pn-brand" href="/"><img src="/assets/profitnet-logo.webp" width="32" height="32" alt="Profitnet logo">Profitnet</a>' +
      '<nav class="pn-links" aria-label="Primary">' +
        PRIMARY.map(function (pair) {
          return '<a href="' + pair[1] + '">' + pair[0] + '</a>';
        }).join("") +
      '</nav>' +
      '<button type="button" class="pn-burger" aria-expanded="false" aria-controls="pn-menu">Menu</button>' +
    '</div>';

  var menu = el("div", { class: "pn-menu", id: "pn-menu", hidden: "" });
  menu.innerHTML =
    '<div class="pn-menu-top"><a class="pn-brand" href="/">Profitnet</a>' +
    '<button type="button" data-close>Close</button></div>' +
    '<h2>Sections</h2><ul>' + linkList(PRIMARY) + '</ul>' +
    '<h2>States</h2><ul>' + linkList(STATES) + '</ul>';

  var footer = el("footer", { class: "pn-footer" });
  footer.innerHTML =
    '<div class="pn-foot-grid">' +
      '<section><h2>Landmarks by state</h2><ul>' + linkList([["All landmarks", "/pages/landmarks/"]].concat(STATES)) + '</ul></section>' +
      '<section><h2>Tools</h2><ul>' + linkList([
        ["All tools", "/tools/"],
        ["What is my IP address", "/CheckIP/"],
        ["Tax-loss estimate", "/Crypto%20Tax-Loss%20Harvester/"],
        ["Freelance rate", "/Freelance%20Rate%20Fairness%20Checker/"],
        ["Impermanent loss", "/Impermanent%20Loss%20Visualizer/"]
      ]) + '</ul></section>' +
      '<section><h2>Guides and games</h2><ul>' + linkList([
        ["Earning guides", "/pages/guides/"],
        ["EarnApp review", "/pages/earnapp/"],
        ["Honeygain review", "/pages/honeygain/"],
        ["Bubble Cash review", "/pages/bubblecash/"],
        ["Games", "/freebrowsergames/"]
      ]) + '</ul></section>' +
      '<section><h2>About</h2><ul>' + linkList([
        ["Home", "/"],
        ["Data sharing opt-out", "/pages/data-sharing-opt-out/"],
        ["Landmark archive", "/pages/parks/"]
      ]) + '</ul><p>Profitnet landmark guides and tools.</p></section>' +
    '</div>';

  function setOpen(open) {
    var button = header.querySelector(".pn-burger");
    menu.hidden = !open;
    button.setAttribute("aria-expanded", open ? "true" : "false");
    document.body.style.overflow = open ? "hidden" : "";
  }

  header.querySelector(".pn-burger").addEventListener("click", function () {
    setOpen(menu.hidden);
  });
  menu.querySelector("[data-close]").addEventListener("click", function () { setOpen(false); });
  menu.querySelectorAll("a").forEach(function (a) {
    a.addEventListener("click", function () { setOpen(false); });
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") setOpen(false);
  });

  function stateFromPage() {
    var path = location.pathname;
    if (/^\/[A-Z]{2}\/?$/.test(path)) return null;
    if (/^\/pages\/landmarks\/?$/.test(path)) return null;
    var folder = path.match(/^\/([A-Z]{2})\//);
    if (folder) {
      for (var i = 0; i < STATES.length; i++) {
        if (STATES[i][1] === "/" + folder[1] + "/") return STATES[i];
      }
    }
    var crumbs = document.querySelectorAll("nav a[href], .crumbs a[href], .lg-crumbs a[href], .tp-seo-crumbs a[href]");
    for (var j = 0; j < crumbs.length; j++) {
      var href = crumbs[j].getAttribute("href") || "";
      var match = href.match(/^\/([A-Z]{2})\/$/);
      if (!match) continue;
      for (var k = 0; k < STATES.length; k++) {
        if (STATES[k][1] === "/" + match[1] + "/") return STATES[k];
      }
    }
    return null;
  }

  function addLandmarkButtons() {
    var state = stateFromPage();
    if (!state) return;
    var main = document.querySelector("main") || document.body;
    if (main.querySelector(".pn-back")) return;
    var wrap = el("div", { class: "pn-back" });
    wrap.innerHTML =
      '<a class="pn-back-btn" href="' + state[1] + '">Back to ' + state[0] + '</a>' +
      '<a class="pn-back-btn" href="/pages/landmarks/">All landmarks</a>';
    main.appendChild(wrap);
  }

  var path = location.pathname;
  var slim = /^\/freebrowsergames\/.+/.test(path) ||
    path.indexOf("/libreng-browser-laro/") === 0 ||
    path.indexOf("/Algohub/") === 0;
  var app = !slim && (
    path.indexOf("/pages/PNET/") === 0 ||
    path.indexOf("/pages/tokenomics/") === 0 ||
    path.indexOf("/tokenomics/") === 0 ||
    path.indexOf("/scam-scan/") === 0 ||
    path.indexOf("/pages/data-sharing-opt-out/") === 0 ||
    path.indexOf("/pages/algoflow/") === 0 ||
    path.indexOf("/pages/inspector/") === 0 ||
    path.indexOf("/pages/launchpad/") === 0 ||
    path.indexOf("/pages/multisend/") === 0 ||
    path.indexOf("/pages/nfts/") === 0 ||
    path.indexOf("/pages/genesis/") === 0 ||
    path.indexOf("/pages/Security%20Lab/") === 0 ||
    path.indexOf("/pages/Security Lab/") === 0 ||
    path.indexOf("/TikTok%20Shop") === 0 ||
    path.indexOf("/TikTok Shop") === 0 ||
    path.indexOf("/US%20Kitchen") === 0 ||
    path.indexOf("/US Kitchen") === 0 ||
    path.indexOf("/pages/things%20to%20do%20in%20vail") === 0 ||
    path.indexOf("/pages/things to do in vail") === 0 ||
    path.indexOf("/gameinfo/") === 0 ||
    path === "/404.html"
  );

  document.body.classList.add("pn-has-nav");
  if (slim) document.body.classList.add("pn-slim");
  if (app) document.body.classList.add("pn-app");
  document.body.insertBefore(header, document.body.firstChild);
  document.body.appendChild(menu);
  if (slim) {
    var shells = [];
    Array.prototype.forEach.call(document.body.children, function (node) {
      if (node === header || node === footer || node === menu) return;
      var pos = window.getComputedStyle(node).position;
      if (pos === "absolute" || pos === "fixed") return;
      if (node.matches && node.matches("script, link, style")) return;
      shells.push(node);
    });
    var chosen = null;
    shells.forEach(function (node) {
      if (node.querySelector && node.querySelector("canvas, #game-container, #game-wrapper, #root")) chosen = node;
    });
    if (!chosen && shells.length) chosen = shells[0];
    if (chosen) chosen.classList.add("pn-slim-fill");
  }
  if (!slim) addLandmarkButtons();
  document.body.appendChild(footer);
})();
