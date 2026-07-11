from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_JS = (ROOT / "src/algopulse/static/app.js").read_text(encoding="utf-8")
INDEX_HTML = (ROOT / "src/algopulse/static/index.html").read_text(encoding="utf-8")
STYLES_CSS = (ROOT / "src/algopulse/static/styles.css").read_text(encoding="utf-8")


def _utility_section() -> str:
    start = APP_JS.index("function utilityNumber")
    end = APP_JS.index("function renderUserPortal")
    return APP_JS[start:end]


def _function_section(name: str) -> str:
    start = APP_JS.index(f"function {name}") if f"function {name}" in APP_JS else APP_JS.index(f"async function {name}")
    next_function = APP_JS.find("\nfunction ", start + 1)
    next_async_function = APP_JS.find("\nasync function ", start + 1)
    candidates = [index for index in [next_function, next_async_function] if index != -1]
    end = min(candidates) if candidates else len(APP_JS)
    return APP_JS[start:end]


def test_utility_hub_tab_is_public_safe_and_present() -> None:
    assert 'data-dashboard-view="utility"' in INDEX_HTML
    assert 'utility: { label: "Utility", adminOnly: false' in APP_JS

    utility = _utility_section()
    assert "Safe Algorand tools" in utility
    assert "No signing" in utility
    assert "No wallet connection, signing, or submission happens here." in utility


def test_utility_hub_blocks_transaction_submission_tools() -> None:
    utility = _utility_section()

    assert "Wallet cleaner" in utility
    assert "Quick opt-in" in utility
    assert "MultiSender" in utility
    assert "Requires opt-out transactions and wallet signing; not implemented in AlgoPulse." in utility
    assert "Requires asset opt-in transactions; keep outside this safe dashboard." in utility
    assert "Batch payments would submit transactions and need a separate audited tool." in utility


def test_utility_hub_does_not_port_wallet_signing_dependencies() -> None:
    utility = _utility_section()

    blocked_fragments = [
        "PeraWalletConnect",
        "DeflyWalletConnect",
        "defly-connect",
        "@blockshake",
        "algosdk",
        "https://esm.sh",
        "sendRawTransaction",
        "signTransaction",
        "wallet.sign",
    ]
    for fragment in blocked_fragments:
        assert fragment not in utility


def test_public_navigation_hides_admin_surfaces_until_admin_session() -> None:
    assert "function visibleDashboardEntries()" in APP_JS
    assert "return Object.entries(dashboardViews).filter(([, view]) => !view.adminOnly || isAdmin);" in APP_JS
    assert "button.hidden = !visible;" in APP_JS
    assert "document.querySelector(\".nav-tabs\").addEventListener(\"click\"" in APP_JS

    static_nav = INDEX_HTML.split('<nav class="nav-tabs" aria-label="Dashboard sections">', 1)[1].split("</nav>", 1)[0]
    assert "Control Room" not in static_nav
    assert "Bot Control" not in static_nav
    assert "Logs" not in static_nav


def test_guest_journey_is_explicit_and_mock_admin_presets_are_hidden_by_default() -> None:
    assert "function renderPublicJourneyPanel()" in APP_JS
    assert "User Mission Control" in APP_JS
    assert "Admin execution and creator controls are hidden from this role." in APP_JS
    assert 'data-journey-view="${escapeHtml(view)}"' in APP_JS

    assert "SHOW_WALLET_PRESET_CONTROLS" in APP_JS
    assert 'get("demoWallets") === "1"' in APP_JS
    assert "walletStateControls.hidden = !SHOW_WALLET_PRESET_CONTROLS;" in APP_JS


def test_phase_label_rolls_from_app_constant() -> None:
    assert 'let APP_PHASE_LABEL = "AlgoPulse Phase 3: TestNet Access"' in APP_JS
    assert "config.developmentPhase || APP_PHASE_LABEL" in APP_JS
    assert "function renderAppPhaseLabel()" in APP_JS
    assert "data-app-phase-label" in INDEX_HTML
    assert "AlgoPulse Phase 0" not in INDEX_HTML
    assert "phase3-testnet-access-v1" in INDEX_HTML


def test_wallet_provider_and_network_options_are_connect_only_access_phase() -> None:
    access_gate = _function_section("renderPnetAccessGate")
    provider_switch = _function_section("renderWalletProviderSwitch")
    click_handler = _function_section("handleRoleDashboardClick")

    assert "const walletProviders" in APP_JS
    assert "const walletNetworks" in APP_JS
    assert 'walletProvider: "pera"' in APP_JS
    assert 'walletNetwork: "testnet"' in APP_JS
    assert 'key: "defly"' in APP_JS
    assert 'key: "testnet"' in APP_JS
    assert 'label: "Defly"' in APP_JS
    assert 'label: "TestNet"' in APP_JS
    assert 'method: "Pera Connect"' in APP_JS
    assert 'method: "Defly WalletConnect"' in APP_JS
    assert 'docsUrl: "https://docs.perawallet.app/references/pera-connect"' in APP_JS
    assert 'docsUrl: "https://defly.gitbook.io/defly-manual/dev/walletconnect"' in APP_JS
    assert 'id="wallet-quick-switch"' in INDEX_HTML
    assert "renderWalletProviderSwitch({ compact: true })" in APP_JS
    assert 'document.querySelector(".wallet-strip").addEventListener("click", handleRoleDashboardClick);' in APP_JS
    assert "Connect-only. No wallet keys, signing, submission, or live trading." in APP_JS
    assert "async function connectSelectedWallet()" in APP_JS
    assert "async function disconnectWallet()" in APP_JS
    assert "async function restoreWalletSession()" in APP_JS
    assert "await restoreWalletSession();" in APP_JS
    assert "function handleRemoteWalletDisconnect()" in APP_JS
    assert 'client.connector.on("disconnect", handleRemoteWalletDisconnect)' in APP_JS
    assert "async function toggleWalletConnection()" in APP_JS
    assert "WALLET_NETWORK_MISMATCH" in APP_JS
    assert 'status: "disconnected"' in click_handler
    assert "chainId: backendChainId()" in click_handler
    assert "PNET TestNet asset not configured" in APP_JS
    assert 'data-wallet-provider="${escapeHtml(item.key)}"' in provider_switch
    assert 'data-wallet-network="${escapeHtml(item.key)}"' in provider_switch
    assert "${escapeHtml(provider.method)}" in provider_switch
    assert "wallet-provider-docs" in provider_switch
    assert 'target="_blank" rel="noreferrer"' in provider_switch
    assert "walletProviders[state.walletProvider]" in APP_JS
    assert "walletNetworks[state.walletNetwork]" in APP_JS
    assert "Connect ${escapeHtml(provider.label)} Wallet" in access_gate
    assert "button.dataset.walletProvider" in click_handler
    assert "button.dataset.walletNetwork" in click_handler
    assert "connect-only" in click_handler.lower() or "Connect-only" in click_handler
    assert "MainNet mismatch" in provider_switch or "mismatch" in provider_switch
    # Real adapters load dynamically for connect-only; utility hub still excludes them.
    assert "@perawallet/connect" in APP_JS
    assert "@blockshake/defly-connect" in APP_JS
    assert "signTransaction" not in _function_section("connectSelectedWallet")
    assert "sendRawTransaction" not in APP_JS


def test_route_console_defaults_to_pnet_and_requires_click_for_other_algo() -> None:
    route_console = _function_section("renderRouteConsole")
    route_scope = _function_section("routeMatchesScope")
    route_filters = _function_section("routeMatchesFilters")

    assert 'routeScope: "pnet"' in APP_JS
    assert "routeFilters:" in APP_JS
    assert 'data-route-scope="pnet"' in route_console
    assert 'data-route-scope="algo"' in route_console
    assert "PNET focus" in route_console
    assert "Other ALGO" in route_console
    assert "All routes" in route_console
    assert 'data-route-filter="venue"' in route_console
    assert 'data-route-filter="minProfit"' in route_console
    assert 'data-route-filter="status"' in route_console
    assert 'data-route-filter-reset="true"' in route_console
    assert "routeMatchesFilters" in route_console
    assert "routeFilterSummary" in route_console
    assert 'state.routeScope === "pnet"' in route_console
    assert "pnetWatchlistRows()" in route_console
    assert "routeScopeSummary(state.routeScope, visibleRouteCount" in route_console
    assert "Other ALGO routes are hidden by default and only shown here by intent." in route_console
    assert 'scope === "algo"' in route_scope
    assert "routeTouchesAlgo(route) && !routeTouchesPnet(route)" in route_scope
    assert "routeProfitForFilter(route)" in route_filters
    assert 'recordProductAction("opened_route"' in APP_JS
    assert 'evidence_source: "route_scope_filter"' in APP_JS


def test_phase2_completion_evidence_remains_available_after_phase_roll() -> None:
    phase2 = _function_section("Phase2CompletionPanel")

    assert "Phase 2 Completion" in phase2
    assert "User Experience Layer" in phase2
    assert "Ready for review" in phase2
    assert "PNET-first default routes" in phase2
    assert "Real route filters" in phase2
    assert "Paper simulation" in phase2
    assert "Execution lock clarity" in phase2
    assert "Next phase is TestNet readiness" in phase2
    assert "before any contract or transaction flow" in phase2


def test_testnet_soak_panel_is_wired_into_control_room_with_source_and_lock_labels() -> None:
    assert "function TestnetSoakPanel" in APP_JS
    assert "TestnetSoakPanel(data)" in APP_JS
    assert 'fetchApiData("/api/ops/testnet-soak"' in APP_JS
    assert 'fetchApiData("/api/ops/testnet-soak/observations?limit=20"' in APP_JS
    assert "productionReady=false" in APP_JS
    assert 'source === "mock" ? "mock" : source' in APP_JS
    assert "Live execution" in APP_JS
    assert ".testnet-soak-card" in STYLES_CSS


def test_testnet_soak_panel_renders_recent_observations_without_operator_controls() -> None:
    panel = _function_section("TestnetSoakPanel")
    tape = _function_section("TestnetSoakObservationTape")

    assert "TestnetSoakObservationTape(data)" in panel
    assert "Latest observations" in tape
    assert "No stored observations" in tape
    assert "Evidence unavailable" in tape
    assert "observation.completedAt" in tape
    assert "observation.poolsObserved" in tape
    assert "observation.quotesObserved" in tape
    assert "observation.algod?.latestRound" in tape
    assert "observation.indexer?.roundLag" in tape
    assert "SourceBadge(source)" in tape
    assert "data-soak-start" not in tape
    assert "data-soak-stop" not in tape
    assert ".testnet-soak-observation-list" in STYLES_CSS
    assert "position: sticky" not in STYLES_CSS


def test_testnet_readiness_panel_uses_backend_evidence_and_keeps_execution_locked() -> None:
    panel = _function_section("TestnetReadinessPanel")
    portal = _function_section("renderUserPortal")
    admin = _function_section("renderAdminDashboard")

    assert "Phase 3 / TestNet Access" in panel or "TestNet Access" in panel
    assert "state.testnetReadiness" in panel
    assert "data.readOnlyStatus" in panel or "walletConnectionReady" in panel
    assert "data.blockedReasons" in panel
    assert "data.waitReasons" in panel
    assert "connect-only" in panel.lower() or "Connect-only" in panel
    assert "signing and submission stay disarmed" in panel.lower() or "Signing and submission stay disarmed" in panel
    assert "algod" in panel
    assert "Indexer" in panel
    assert "Execution" in panel
    assert "Locked" in panel
    assert "TestnetReadinessPanel()" in portal
    assert "TestnetReadinessPanel()" in admin
    assert 'fetchApiData("/api/testnet/readiness")' in APP_JS


def test_route_filters_are_wired_to_input_change_and_reset() -> None:
    click_handler = _function_section("handleRoleDashboardClick")

    assert "button.dataset.routeFilterReset" in click_handler
    assert 'state.routeFilters = { venue: "all", status: "all", minProfit: "" }' in click_handler
    assert "event.target.closest(\"[data-route-filter]\")" in APP_JS
    assert "state.routeFilters[routeFilter.dataset.routeFilter] = routeFilter.value" in APP_JS
    assert 'addEventListener("change"' in APP_JS
    assert "Route filters reset. PNET-first route view remains active." in APP_JS


def test_bot_mode_buttons_are_real_safe_ui_controls() -> None:
    bot_panel = _function_section("renderBotControlPanel")
    click_handler = _function_section("handleRoleDashboardClick")

    assert 'botMode: "scanner"' in APP_JS
    assert 'data-bot-mode="${escapeHtml(mode)}"' in bot_panel
    assert "botModeNotice" in APP_JS
    assert "scanner-only" in APP_JS
    assert "paper trading" in APP_JS
    assert "dry-run review" in APP_JS
    assert "Live micro mode is still locked" in APP_JS
    assert "button.dataset.botMode" in click_handler
    assert "state.botMode = button.dataset.botMode" in click_handler
    assert 'state.botMode === "live-micro"' in click_handler
    assert "openLiveArmModal()" in click_handler


def test_route_inspect_copy_and_json_buttons_have_safe_behaviors() -> None:
    detail = _function_section("openRouteDetailModal")
    route_action = _function_section("runRouteAction")
    json_snapshot = _function_section("openRouteJsonSnapshot")
    public_snapshot = _function_section("publicRouteSnapshot")

    assert "routeDetailRecordForHash(routeHash)" in detail
    assert "recentSwapRouteRecord" in APP_JS
    assert "pnetWatchlistRows()" in APP_JS
    assert "listLabel(route.poolIds)" in detail
    assert 'data-route-action="copy"' in detail
    assert 'data-route-action="json"' in detail

    assert 'action === "copy"' in route_action
    assert "copyTextToClipboard" in route_action
    assert 'action === "json"' in route_action
    assert "openRouteJsonSnapshot(routeHash)" in route_action

    assert "Public-safe route snapshot only" in json_snapshot
    assert "executable: false" in public_snapshot
    assert "No raw executable route JSON" in public_snapshot
    assert "signed transactions" in public_snapshot


def test_paper_simulation_button_opens_safe_simulation_modal() -> None:
    route_action = _function_section("runRouteAction")
    paper_sim = _function_section("routePaperSimulation")
    paper_modal = _function_section("openPaperSimulationModal")

    assert 'action === "paper"' in route_action
    assert 'evidence_source: "paper_simulation_modal"' in route_action
    assert "openPaperSimulationModal(routeHash)" in route_action
    assert 'runAdminAction("paper")' not in route_action

    assert "quoteDecay5s" in paper_sim
    assert "quoteDecay30s" in paper_sim
    assert "simulatedOutput5s" in paper_sim
    assert "simulatedOutput30s" in paper_sim
    assert "wouldExecute" in paper_sim
    assert "executionLocked: true" in paper_sim
    assert "const routeIsObservation" in paper_sim
    assert "const expectedProfit = routeIsObservation ? 0" in paper_sim

    assert "Paper Simulation" in paper_modal
    assert "T+5s recheck" in paper_modal
    assert "T+30s recheck" in paper_modal
    assert "No smart contract, wallet signature, signer, hot-wallet, or transaction submission is touched." in paper_modal
    assert "This output is not an executable route, signed transaction, submission payload, or contract call." in paper_modal


def test_public_utility_refresh_does_not_expose_admin_connector_internals() -> None:
    click_handler = _function_section("handleRoleDashboardClick")

    assert 'button.dataset.utilityAction === "refresh-status"' in click_handler
    assert 'currentSession().role === "admin"' in click_handler
    assert "Admin connector/status evidence refreshed." in click_handler
    assert "Public scanner/readiness status refreshed. Admin connector internals remain hidden." in click_handler


def test_research_live_refresh_uses_read_only_scan_endpoint() -> None:
    refresh = _function_section("refreshResearchFromLiveApi")
    panel = _function_section("ResearchLiveRefreshPanel")

    assert 'fetchJson("/api/scan", { method: "POST" })' in refresh
    assert "/api/execute-best" not in refresh
    assert "data-research-action=\"refresh-live\"" in panel
    assert "does not sign, submit, trade, or expose fresh executable routes" in panel
    assert "ALGO_PULSE_CONNECTORS=tinyman,pact" in panel
    assert "execution flags still disabled" in panel


def test_research_page_lists_pnet_liquidity_even_without_opportunities() -> None:
    watchlist = _function_section("PnetLiquidityWatchlist")

    assert "PNET Liquidity Watchlist" in watchlist
    assert "pnetLiquidityWatchlist" in watchlist
    assert "Shown without arb" in watchlist
    assert "not investment advice" in watchlist
    assert "impermanent loss" in watchlist


def test_access_page_lists_no_gate_builds_and_keeps_hard_gates_explicit() -> None:
    no_gate = _function_section("renderPnetNoGateBuilds")
    lp_education = _function_section("renderPnetLiquidityEducation")

    assert "No-Gate Builds Available Now" in no_gate
    assert "Live PNET liquidity watchlist" in no_gate
    assert "Read-only market summary refresh" in no_gate
    assert "Unsigned utility tools" in no_gate
    assert "Contribution Protocol beta" in no_gate
    assert "without token rewards or governance control" in no_gate
    assert "Community growth beta" in no_gate
    assert "Referral receipts, onboarding, contributor leaderboard, and reputation badges" in no_gate
    assert "Content system" in no_gate
    assert "30-day calendar, X threads, blog templates, website copy, and diagrams" in no_gate
    assert "Documentation and audit readiness" in no_gate
    assert "audit-scope inventory" in no_gate
    assert "Still gated" in no_gate
    assert "Signer, wallet custody, private keys, or transaction submission" in no_gate
    assert "Mainnet deploy" in no_gate
    assert "LP incentives, rewards, staking, ROI, buy/sell, or price claims" in no_gate
    assert "CEX/listing outreach" in no_gate
    assert "audited/production-ready claims" in no_gate
    assert "On-chain credit contract deployment or binding governance" in no_gate
    assert "Automatic referral rewards, self-payment loops, or production leaderboard claims" in no_gate

    assert "PNET LP Visibility Lane" in lp_education
    assert "Education only" in lp_education
    assert "does not custody funds, sign transactions, submit transactions" in lp_education
    assert "Not financial advice" in lp_education
    assert "No ROI, rewards, staking, or price claims" in lp_education


def test_pulse_page_leads_with_pnet_arb_watch_feed() -> None:
    watch = _function_section("ArbBotWatchPanel")
    swaps = _function_section("RecentPnetSwapsPanel")
    journey = _function_section("renderPublicJourneyPanel")
    portal = _function_section("renderUserPortal")

    assert "PNET Arb Scanner" in watch
    assert "constantly looking for PNET price gaps" in watch
    assert "Public mode shows delayed/read-only candidates" in watch
    assert "does not sign, submit, custody, or trade" in watch
    assert "data-route-action=\"inspect\"" in watch
    assert "arb-feed-row" in watch
    assert "Refreshes every 15s" in watch
    assert "1. Scan pools" in watch
    assert "5. Trading stays gated" in watch
    assert "routeTouchesPnet" in APP_JS
    assert "pnetWatchlistRows" in APP_JS
    assert "PNET pool surface" in APP_JS
    assert "listed without arb" in APP_JS
    assert "RecentPnetSwapsPanel(routes)" in watch
    assert "Recent PNET swaps" in swaps
    assert "Delayed watch feed" in swaps
    assert "recent-swap-row" in swaps
    assert "swap.sample ? \"example\"" in swaps
    assert "sample-pnet-algo-swap" in APP_JS
    assert "sample-algo-pnet-swap" in APP_JS

    assert "Watch scanner" in journey
    assert "Inspect a price gap" in journey
    assert "Use PNET/x402 access for premium delayed reports only, not trading." in journey
    assert "User Mission Control" in journey
    assert "ux-priority-strip" in journey
    assert "Market feed" in journey
    assert "Execution" in journey
    assert "Phase 2 priority: make the market signal understandable first." in journey

    assert "PNET Arbitrage Watch" in portal
    assert "ArbBotWatchPanel()" in portal
    assert "Live trading\", \"Blocked\"" in portal


def test_access_page_renders_contribution_protocol_beta_boundaries() -> None:
    contribution = _function_section("ContributionProtocolDashboard")

    assert "Contribution Protocol Beta" in contribution
    assert "Credit balance" in contribution
    assert "Activity history" in contribution
    assert "data-contribution-submit" in contribution
    assert "data-credit-spend" in contribution
    assert "non-binding governance signals" in contribution
    assert "They are not token rewards, yield, revenue share, treasury control, or trading permission." in contribution
    assert "AlgoFlow integration boundary" in contribution
    assert "must not receive signer secrets, custody funds, or execute trades" in contribution


def test_access_page_renders_pnet_content_system_without_hype_claims() -> None:
    content = _function_section("PnetContentSystemPanel")

    assert "PNET Content System" in content
    assert "Tokenomics, documented as facts" in content
    assert "Verified contribution" in content
    assert "Real-world utility with receipts" in content
    assert "Visual evidence pipeline" in content
    assert "No financial advice" in content
    assert "no guaranteed earnings" in content
    assert "no CEX/listing claim" in content
    assert "no production-readiness claim" in content
    assert "ROI" in content


def test_access_page_renders_community_growth_without_reward_claims() -> None:
    community = _function_section("CommunityGrowthDashboard")

    assert "Community Growth Beta" in community
    assert "Referral receipt" in community
    assert "Contributor leaderboard" in community
    assert "Reputation" in community
    assert "Mining evidence" in community
    assert "Bandwidth evidence" in community
    assert "Verification report" in community
    assert "not earnings claims" in community
    assert "not yield, not income, not governance power, and not a token reward" in community
    assert "data-community-referral" in community
    assert "data-contribution-submit=\"mining_evidence\"" in community
