/**
 * @typedef {"mock" | "stored" | "live" | "delayed" | "unavailable"} DataSource
 * @typedef {"ok" | "wait" | "blocked" | "error" | "disabled"} ServiceStatus
 * @typedef {{ label: string, value: string, detail: string, source: DataSource }} ServiceEvidence
 * @typedef {{ key: string, label: string, status: ServiceStatus, source: DataSource, lastRunAt: string | null, lastSuccessAt: string | null, inputCount24h: number, outputCount24h: number, errorCount24h: number, freshnessSeconds: number | null, summary: string, blocker?: string | null, motionLabel?: string, motionState?: string, evidence?: ServiceEvidence[], deltaInput24h?: number, deltaOutput24h?: number, deltaError24h?: number, hasDelta?: boolean }} PipelineService
 * @typedef {{ key: string, label: string, percent: number, status: ServiceStatus, requiredEvidence: string[], completedEvidence: string[], blockers: string[] }} PhaseGate
 * @typedef {{ id: string, timestamp: string, service: string, severity: "info" | "warn" | "blocked" | "critical", message: string, source: DataSource }} ActivityEvent
 * @typedef {{ reason: string, count: number, percent: number }} RejectionBucket
 * @typedef {{ daysCollected: number, targetDays: number, candidatesObserved: number, wouldExecuteCount: number, simulatedWins5s: number, simulatedWins30s: number, expectedNetAlgo: string, simulatedNetAlgo5s: string, simulatedNetAlgo30s: string, averageQuoteDecayAlgo: string, verdict: "not_ready" | "watching" | "paper_positive" | "ready_for_dry_run", source: DataSource }} PaperTradingSummary
 * @typedef {{ status: "not_live_ready" | "review" | "live_ready", headline: string, reason: string, safeMode: string, restrictions: string[], source: DataSource }} ProductionStatus
 * @typedef {{ currentPhase: string, currentPhaseKey: string, overallPercent: number, nextGate: string, blockingItems: string[], source: DataSource }} ProductionReadiness
 * @typedef {{ liveExecutionLocked: boolean, lockReasons: string[], checks: { key: string, label: string, status: ServiceStatus, evidence: string }[] }} RiskGateSummary
 * @typedef {{ connectorName: string, connectorType: "dex" | "algod" | "indexer", status: "ok" | "degraded" | "down" | "stale" | "mock", readinessImpact: "ok" | "wait" | "blocked", degradationReason: string | null, productionReady: boolean, latencyMs: number | null, freshCount24h: number, staleCount24h: number, errorCount24h: number, latestRound: number | null, expectedMinRound: number | null, source?: DataSource }} ConnectorEvidence
 * @typedef {{ totalConnectors: number, okCount: number, degradedCount: number, downCount: number, staleCount: number, mockCount: number, productionReadyCount: number, blockedReasons: object[], waitReasons: object[], overallReadiness: "ok" | "wait" | "blocked" }} ConnectorReadinessRollup
 * @typedef {{ key: string, label: string, status: string, expectedProfit: number, simulatedProfit: number | null, quoteDecay: number | null, priceImpactBps: number, priceImpactChangeBps: number | null, poolLiquidity: number | null, poolLiquidityChange: number | null, routeConfidence: number }} ReplayCheckpoint
 * @typedef {{ id: string, routeHash: string, verdict: "would_execute" | "would_skip" | "unsafe" | "stale", verdictReason: string, expectedProfit: number, simulatedProfit5s: number | null, simulatedProfit30s: number | null, quoteDecay5s: number | null, quoteDecay30s: number | null, priceImpactBps: number, priceImpactChangeBps: number | null, poolLiquidityChange: number | null, routeConfidence: number, route: object[], timeline: ReplayCheckpoint[], source: DataSource }} ReplayOpportunity
 * @typedef {{ id: number, routeHash: string, routePathLabel: string, routePath: object[], profitability: object, quoteFreshness: object, priceImpact: object, liquidityScore: object, riskResult: object, approvalDecision: object, rejectionReason: string, confidenceCalculation: object, decisionTree: object[], completeness: object, source: DataSource }} RouteForensicsRecord
 * @typedef {{ label: string, minConfidence: number, maxConfidence: number, count: number, successCount: number, failureCount: number, successRate: number, averageConfidence: number, calibrationError: number, averageQuoteDecay: number, averageExpectedProfit: number, averageSimulatedProfit: number }} ConfidenceBucket
 * @typedef {{ buckets: ConfidenceBucket[], summary: object, sampleTrades: object[], source: DataSource, liveExecutionTouched: boolean, signerCodeTouched: boolean }} ConfidenceCalibrationReport
 * @typedef {{ routeHash: string, pairLabel: string, venues: string[], routeType: string, expectedProfit: number, expectedProfit5s: number | null, expectedProfit30s: number | null, expectedProfit60s: number | null, halfLifeSeconds: number, decayRatio: number, source: DataSource }} OpportunityDecayRecord
 * @typedef {{ view: "1h" | "24h" | "7d", views: string[], summary: object, timeline: object[], byPair: object[], byVenue: object[], byRouteType: object[], records: OpportunityDecayRecord[], source: DataSource, liveExecutionTouched: boolean, signerCodeTouched: boolean }} OpportunityDecayReport
 * @typedef {{ pairKey: string, pairLabel: string, assetIds: number[], venue: string, bucketIndex: number, bucketStart: number, bucketEnd: number, opportunityCount: number, spreadFrequency: number, averageSpreadBps: number, averageRouteCount: number, opportunityHalfLifeSeconds: number, paperTradePerformance: object, intensity: number, densityLabel: string, source: DataSource }} MarketHeatmapCell
 * @typedef {{ reportDate: string, generatedAt: number, source: DataSource, marketSummary: object, topPairs: object[], topSpreads: object[], liquidityChanges: object[], opportunityCounts: object, routePerformance: object, paperTradePerformance: object, scannerHealth: object, riskEvents: object[], exports: object }} MarketIntelligenceReport
 * @typedef {{ key: string, label: string, failureType: string, severity: string, trigger: string, expectedResponse: object, actualResponse: object, alertsGenerated: string[], servicesAffected: string[], operatorAction: string, gracefulDegradation: boolean, source: DataSource }} FailureScenario
 * @typedef {{ key: string, label: string, value: string, unit: string, source: DataSource, status: string, table: string, field: string, description: string }} ProvenanceMetric
 * @typedef {{ key: string, label: string, description: string, records: object[], status: string, source: DataSource }} ProvenanceStep
 * @typedef {{ evidenceId: string, service: string, category: string, title: string, summary: string, status: "pass" | "pending" | "warn" | "fail", createdAt: number, metadata: object }} EvidenceRecord
 * @typedef {{ source: DataSource, summary: object, funnel: object[], personas: object[], featureUtility: object[], deadFeatures: object[], whyUsersReturn: object, actionTaxonomy: object[], decisionRules: object, liveExecutionTouched: boolean, signerCodeTouched: boolean }} ProductValidationReport
 */

const state = {
  refreshTimer: null,
  radarAnimation: null,
  radarPhase: 0,
  radarHits: [],
  radarSelectedPoolId: null,
  latestPools: [],
  latestOpportunities: [],
  latestReadiness: null,
  testnetReadiness: null,
  testnetReadinessError: null,
  latestPreflight: null,
  latestPaperReport: null,
  latestAlertCatalog: [],
  latestPolicyCatalog: [],
  opsControlRoom: null,
  opsLoading: false,
  opsError: null,
  testnetSoakError: null,
  testnetSoakObservationsError: null,
  opsHeartbeatTimer: null,
  opsRefreshCount: 0,
  opsLastLoadedAt: null,
  selectedServiceKey: null,
  productionReadiness: null,
  productionReadinessLoading: false,
  productionReadinessError: null,
  replayLab: null,
  replayLoading: false,
  replayError: null,
  replayStep: 0,
  replayPlaying: false,
  replayPlaybackTimer: null,
  selectedReplayId: null,
  compareReplayIds: [],
  routeForensics: null,
  routeForensicsLoading: false,
  routeForensicsError: null,
  selectedForensicsId: null,
  compareForensicsIds: [],
  confidenceCalibration: null,
  confidenceCalibrationLoading: false,
  confidenceCalibrationError: null,
  opportunityDecay: null,
  opportunityDecayLoading: false,
  opportunityDecayError: null,
  decayView: "24h",
  marketHeatmap: null,
  marketHeatmapLoading: false,
  marketHeatmapError: null,
  heatmapView: "24h",
  selectedHeatmapCellKey: null,
  failureLab: null,
  failureLabLoading: false,
  failureLabError: null,
  selectedFailureKey: null,
  dataProvenance: null,
  provenanceLoading: false,
  provenanceError: null,
  selectedProvenanceMetric: "route.expected_net_profit",
  selectedProvenanceRouteHash: null,
  evidenceSystem: null,
  evidenceLoading: false,
  evidenceError: null,
  evidenceFilters: { category: "all", service: "all", status: "all" },
  selectedEvidenceId: null,
  productValidation: null,
  productValidationLoading: false,
  productValidationError: null,
  researchArchive: null,
  researchArchiveLoading: false,
  researchArchiveError: null,
  researchLiveRefresh: null,
  researchLiveRefreshLoading: false,
  researchLiveRefreshError: null,
  recentPnetSwaps: null,
  recentPnetSwapsError: null,
  routeScope: "pnet",
  routeFilters: {
    venue: "all",
    status: "all",
    minProfit: "",
  },
  selectedReportDate: null,
  productCapabilities: [],
  phaseGates: [],
  deploymentModes: [],
  latestLpOpenings: [],
  walletPreset: "guest",
  walletProvider: "pera",
  walletNetwork: "testnet",
  walletConnection: {
    status: "disconnected", // disconnected | loading | connected | wrong_network | rejected | unavailable
    provider: null,
    address: null,
    network: null,
    chainId: null,
    algoBalance: null,
    pnetBalance: null,
    pnetOptedIn: null,
    pnetMessage: null,
    error: null,
    lastSyncedAt: null,
  },
  walletReconnectAttempted: false,
  networkHealth: null,
  activeView: "pulse",
  activeFeeAction: null,
  activeFeeQuote: null,
  botMode: "scanner",
  contributionProtocol: null,
  contributionProtocolLoading: false,
  contributionProtocolError: null,
  communityGrowth: null,
  communityGrowthLoading: false,
  communityGrowthError: null,
  transparencySystem: null,
  transparencyLoading: false,
  transparencyError: null,
  operatorNotice: "Public mode is active. Creator/admin controls stay hidden unless a verified admin session is present.",
  utilityHub: {
    qrAddress: "",
    qrAmount: "1",
    qrNote: "AlgoPulse delayed report access",
    tokenAInitial: "1",
    tokenBInitial: "1",
    tokenACurrent: "1.5",
    tokenBCurrent: "1",
    investment: "1000",
    copied: false,
  },
};

const versionLadder = [
  {
    version: "v0.1",
    title: "Read-only scanner",
    state: "done",
    gate: "No signer secrets. No submitted trades.",
  },
  {
    version: "v0.2",
    title: "Tinyman + Pact quotes",
    state: "done",
    gate: "Compare venues and store quote metadata.",
  },
  {
    version: "v0.3",
    title: "ALGO/USDC route engine",
    state: "done",
    gate: "Round-trip routes with blocker reasons.",
  },
  {
    version: "v0.4",
    title: "Paper trading",
    state: "done",
    gate: "5s / 30s recheck before real funds.",
  },
  {
    version: "v0.5",
    title: "Delayed dashboard",
    state: "done",
    gate: "Public data is delayed and redacted.",
  },
  {
    version: "v0.6",
    title: "Risk engine",
    state: "done",
    gate: "Reject most routes after fee and impact checks.",
  },
  {
    version: "v0.7",
    title: "Unsigned builder",
    state: "gated",
    gate: "Review unsigned atomic groups only.",
  },
  {
    version: "v0.8",
    title: "Signer service",
    state: "gated",
    gate: "Separate service, kill switch on by default.",
  },
  {
    version: "v0.9",
    title: "Manual tiny trade",
    state: "future",
    gate: "One ALGO/USDC trade, Lora verified.",
  },
  {
    version: "v1.0",
    title: "Tiny micro-arb",
    state: "future",
    gate: "Automated own-funds only after v0.9 proof.",
  },
];

const defaultPhaseGates = [
  {
    gate: 1,
    title: "Scanner 24h",
    status: "evidence_needed",
    exitCriteria: "Scanner runs for 24 hours with no signer operational secrets and no submitted transactions.",
  },
  {
    gate: 2,
    title: "Comparable Quotes",
    status: "built",
    exitCriteria: "Quote engine records comparable Tinyman and Pact quotes.",
  },
  {
    gate: 3,
    title: "Explained Rejections",
    status: "built",
    exitCriteria: "Route engine stores a skip reason and risk-rule map for every rejected opportunity.",
  },
  {
    gate: 4,
    title: "7-Day Paper Trading",
    status: "evidence_needed",
    exitCriteria: "Paper trading runs for 7 days with 5s/30s rechecks and quote decay history.",
  },
  {
    gate: 5,
    title: "Risk Blocks Bad Routes",
    status: "built",
    exitCriteria: "Risk rules reject stale, unprofitable, high-impact, over-limit, or unallowlisted routes.",
  },
  {
    gate: 6,
    title: "Unsigned Dry Run",
    status: "built",
    exitCriteria: "Dry-run executor builds unsigned atomic groups only.",
  },
  {
    gate: 7,
    title: "Signer Policy Rejection",
    status: "built_locked",
    exitCriteria: "Signer rejects out-of-policy groups.",
  },
  {
    gate: 8,
    title: "Manual First Live Trade",
    status: "future",
    exitCriteria: "First live trade is manual and reconciled.",
  },
  {
    gate: 9,
    title: "Delayed Public Dashboard",
    status: "built",
    exitCriteria: "Dashboard shows delayed, public-safe data.",
  },
  {
    gate: 10,
    title: "Phase 1 Decision",
    status: "future",
    exitCriteria: "Phase 1 decision uses real user and market data.",
  },
];

const defaultDeploymentModes = [
  {
    mode: "local",
    label: "Local",
    summary: "Review and UI work with mock market data by default.",
    data: "mock data",
    signer: "disabled",
    submission: "disabled",
    dashboard: "local operator dashboard",
    capabilities: ["mock data", "scanner optional", "no signer", "no real submission"],
    requiredControls: ["ENABLE_SIGNER=false", "ENABLE_EXECUTION=false", "KILL_SWITCH=true"],
  },
  {
    mode: "staging",
    label: "Staging",
    summary: "Live market sensing and paper trading without live signing.",
    data: "live quotes",
    signer: "disabled",
    submission: "disabled",
    dashboard: "delayed dashboard",
    capabilities: ["live scanner", "live quotes", "paper trading", "no live signing", "delayed dashboard"],
    requiredControls: [
      "ENABLE_SCANNER=true",
      "ENABLE_SIGNER=false",
      "ENABLE_EXECUTION=false",
      "PUBLIC_DATA_DELAY_SECONDS>0",
    ],
  },
  {
    mode: "production_phase0",
    label: "Production Phase 0",
    summary: "Public-safe market intelligence with live signing still gated.",
    data: "live scanner, route engine, paper trading, and risk engine",
    signer: "isolated only after gates",
    submission: "tiny own-funds hot wallet only after gates",
    dashboard: "admin dashboard plus public delayed dashboard",
    capabilities: [
      "live scanner",
      "route engine",
      "paper trading",
      "risk engine",
      "admin dashboard",
      "public delayed dashboard",
      "isolated signer only after gates",
      "tiny own-funds hot wallet only",
    ],
    requiredControls: [
      "Gate 1-6 evidence complete",
      "Gate 7 signer rejection evidence complete",
      "manual first trade before automation",
      "own funds only",
    ],
  },
];

const repoRedFlags = [
  {
    title: "Repo-local signer secrets",
    detail: "Reject secret files, config.py wallet material, or committed wallet env files.",
  },
  {
    title: "Frontend wallet keys",
    detail: "Reject browser env vars or frontend source that can sign trades.",
  },
  {
    title: "Unlimited asset routing",
    detail: "Reject bots that trade every asset they discover.",
  },
  {
    title: "No app ID allowlist",
    detail: "Reject routes that can hit unreviewed applications.",
  },
  {
    title: "No daily loss cap",
    detail: "Reject execution without hard loss and trade-count limits.",
  },
  {
    title: "No kill switch",
    detail: "Reject signers or executors that cannot be stopped immediately.",
  },
  {
    title: "No paper history",
    detail: "Reject live trading without replayed quote decay and skip reasons.",
  },
  {
    title: "No adoption review",
    detail: "Copy ideas only after manual review; do not wire unknown repos into execution.",
  },
];

const productThesis = [
  {
    code: "market_intelligence",
    label: "Public + PNET",
    title: "Market Intelligence",
    status: "active phase 0",
    detail: "Daily Algorand market view built from pool state, quote history, freshness, and paper results.",
  },
  {
    code: "scanner",
    label: "Admin Now",
    title: "Scanner",
    status: "active phase 0",
    detail: "Read-only Tinyman, Pact, and later Vestige/Folks market state collection with no private key required.",
  },
  {
    code: "route_engine",
    label: "PNET + Admin",
    title: "Route Engine",
    status: "active phase 0",
    detail: "Builds two-leg and three-leg candidates and explains accepted, rejected, or watched routes.",
  },
  {
    code: "paper_trading",
    label: "Admin + Reports",
    title: "Paper Trading",
    status: "active phase 0",
    detail: "Replays candidate routes with 5s/30s checks, quote decay, and expected-vs-simulated output.",
  },
  {
    code: "risk_engine",
    label: "Admin",
    title: "Risk Engine",
    status: "reject first",
    detail: "Applies freshness, allowlists, size, impact, profit, loss-limit, and route-length gates.",
  },
  {
    code: "execution_controls",
    label: "Admin Only",
    title: "Execution Controls",
    status: "gated future",
    detail: "Shows arm/disarm, kill switch, unsigned-builder, signer-lock, and future tiny own-funds controls.",
  },
  {
    code: "public_dashboard",
    label: "Public",
    title: "Public Dashboard",
    status: "active phase 0",
    detail: "Delayed route intelligence, market health, source labels, receipts, and no fresh executable strategy.",
  },
  {
    code: "pnet_access_layer",
    label: "PNET Users",
    title: "PNET Access Layer",
    status: "active phase 0",
    detail: "Algorand wallet checks, PNET fee quotes, tx verification, credits, receipts, and delayed reports.",
  },
];

const DEFAULT_APP_CONFIG = Object.freeze({
  PNET_ASA_ID: 0,
  PNET_ASA_CONFIGURED: false,
  PNET_MESSAGE: "PNET TestNet asset not configured",
  PLATFORM_FEE_RECEIVER: "PLATFORM_FEE_WALLET_REVIEW",
  PLATFORM_APP_ID: "pending",
  NETWORK: "testnet",
  CHAIN_ID: 416002,
  WALLET_ACCESS_MODE: "connect_only",
  WALLET_CONNECT_ONLY: true,
  SUPPORTED_WALLETS: ["pera", "defly"],
  BACKEND_NETWORK_AUTHORITY: true,
  API_BASE_URL: "/api",
  PUBLIC_DATA_DELAY_SECONDS: 900,
});

let APP_CONFIG = { ...DEFAULT_APP_CONFIG };
let APP_PHASE_LABEL = "AlgoPulse Phase 3: TestNet Access";
const SHOW_WALLET_PRESET_CONTROLS = new URLSearchParams(window.location.search).get("demoWallets") === "1";
const LOCAL_REVIEW_ADMIN_WALLET = "ADMIN6H2ZREVIEWWALLET9KX4CONTROL";

const walletPresets = {
  guest: {
    state: "disconnected",
    role: "guest",
    address: "",
    network: "mainnet",
    pnetBalance: 0,
    credits: 0,
    optedIn: false,
    stateLabel: "Disconnected",
    detail: "Connect a review wallet to unlock wallet-gated market intelligence.",
  },
  user: {
    state: "connected",
    role: "user",
    address: "USER7R3VIEWWALLET5QK2LZ92PNETACCESS",
    network: "mainnet",
    pnetBalance: 1284.56,
    credits: 3,
    optedIn: true,
    stateLabel: "Connected non-admin",
    detail: "PNET route intelligence and paid scan requests are available.",
  },
  admin: {
    state: "admin",
    role: "admin",
    address: "ADMIN6H2ZREVIEWWALLET9KX4CONTROL",
    network: "mainnet",
    pnetBalance: 50000,
    credits: 99,
    optedIn: true,
    stateLabel: "Connected admin",
    detail: "Admin cockpit visible. Backend policy must still authorize every action.",
  },
  wrongNetwork: {
    state: "wrong_network",
    role: "user",
    address: "USER7R3VIEWWALLET5QK2LZ92PNETACCESS",
    network: "testnet",
    pnetBalance: 1284.56,
    credits: 0,
    optedIn: true,
    stateLabel: "Wrong network",
    detail: "Switch to MainNet before paid PNET requests or admin review.",
  },
  notOptedIn: {
    state: "not_opted_in",
    role: "user",
    address: "USER7R3VIEWWALLET5QK2LZ92PNETACCESS",
    network: "mainnet",
    pnetBalance: 0,
    credits: 0,
    optedIn: false,
    stateLabel: "PNET not opted in",
    detail: "Opt in to PNET before requesting scans or route simulations.",
  },
  lowPnet: {
    state: "low_pnet",
    role: "user",
    address: "USER7R3VIEWWALLET5QK2LZ92PNETACCESS",
    network: "mainnet",
    pnetBalance: 8.25,
    credits: 0,
    optedIn: true,
    stateLabel: "PNET balance too low",
    detail: "Add PNET before fee-based market-data requests.",
  },
  feeReady: {
    state: "fee_ready",
    role: "user",
    address: "USER7R3VIEWWALLET5QK2LZ92PNETACCESS",
    network: "mainnet",
    pnetBalance: 1284.56,
    credits: 3,
    optedIn: true,
    stateLabel: "PNET fee ready",
    detail: "Wallet can request PNET-powered scans and route simulations.",
  },
  paymentPending: {
    state: "payment_pending",
    role: "user",
    address: "USER7R3VIEWWALLET5QK2LZ92PNETACCESS",
    network: "mainnet",
    pnetBalance: 1284.56,
    credits: 3,
    optedIn: true,
    stateLabel: "Payment pending",
    detail: "Waiting for review-mode payment confirmation.",
  },
  paymentConfirmed: {
    state: "payment_confirmed",
    role: "user",
    address: "USER7R3VIEWWALLET5QK2LZ92PNETACCESS",
    network: "mainnet",
    pnetBalance: 1272.56,
    credits: 4,
    optedIn: true,
    stateLabel: "Payment confirmed",
    detail: "Receipt recorded and the requested market report is unlocked.",
  },
};

const walletProviders = {
  pera: {
    key: "pera",
    label: "Pera",
    status: "connect-only",
    method: "Pera Connect",
    capability: "Connect and read TestNet account state (address, ALGO balance, optional PNET holdings).",
    boundary: "Connect-only. No transaction construction, signing requests, submission, or opt-in transactions.",
    docsUrl: "https://docs.perawallet.app/references/pera-connect",
    intentSigner: "user_connected_wallet",
  },
  defly: {
    key: "defly",
    label: "Defly",
    status: "connect-only",
    method: "Defly WalletConnect",
    capability: "Connect and read TestNet account state on the same path as Pera.",
    boundary: "Connect-only. No wallet keys, signing, submission, or live trading.",
    docsUrl: "https://defly.gitbook.io/defly-manual/dev/walletconnect",
    intentSigner: "user_connected_wallet",
  },
};

const walletNetworks = {
  mainnet: {
    key: "mainnet",
    label: "MainNet",
    status: "view-only",
    boundary: "Selecting MainNet while the backend is TestNet is rejected. Backend network is the authority.",
  },
  testnet: {
    key: "testnet",
    label: "TestNet",
    status: "access-phase",
    boundary: "TestNet Access Phase: connect and read account state only. No live trading.",
  },
};

const ALGORAND_CHAIN_IDS = { mainnet: 416001, testnet: 416002, betanet: 416003 };
const WALLET_SDK_URLS = {
  pera: "https://esm.sh/@perawallet/connect@1.3.5",
  defly: "https://esm.sh/@blockshake/defly-connect@1.1.6",
};
let _walletSdkCache = { pera: null, defly: null };
let _activeWalletClient = null;
const WALLET_PROVIDER_STORAGE_KEY = "algopulse.wallet.provider";

const pnetActions = {
  public_scan: {
    label: "Run public scan",
    fee: 4,
    receives: "Delayed market pulse refresh and liquidity health report.",
  },
  pair_scan: {
    label: "Request pair scan",
    fee: 12,
    receives: "Delayed pair-specific route intelligence and paper simulation.",
  },
  route_unlock: {
    label: "Unlock delayed best route",
    fee: 18,
    receives: "Delayed route summary with venue, spread, confidence, and risk warnings.",
  },
  run_simulation: {
    label: "Generate route simulation",
    fee: 24,
    receives: "Paper route simulation with quote decay and expected-vs-simulated result.",
  },
  pool_monitor_request: {
    label: "Request pool monitoring",
    fee: 30,
    receives: "Pool watch request for depth, stale data, and LP gap alerts.",
  },
};

const dashboardViews = {
  pulse: { label: "Pulse", adminOnly: false, userScope: "public pulse" },
  routes: { label: "Routes", adminOnly: false, userScope: "delayed routes" },
  research: { label: "Research", adminOnly: false, userScope: "daily market archive" },
  utility: { label: "Utility", adminOnly: false, userScope: "safe public utility tools" },
  transparency: { label: "Transparency", adminOnly: false, userScope: "public proof ledger" },
  pipeline: { label: "Control Room", adminOnly: true, userScope: "production observability" },
  heatmap: { label: "Heatmap", adminOnly: true, userScope: "market pulse analytics" },
  readiness: { label: "Readiness", adminOnly: true, userScope: "production gate evidence" },
  replay: { label: "Replay Lab", adminOnly: true, userScope: "opportunity replay" },
  forensics: { label: "Forensics", adminOnly: true, userScope: "route decision audit" },
  confidence: { label: "Confidence", adminOnly: true, userScope: "route confidence calibration" },
  decay: { label: "Half-Life", adminOnly: true, userScope: "opportunity decay analytics" },
  failure: { label: "Failure Lab", adminOnly: true, userScope: "resilience simulation" },
  provenance: { label: "Provenance", adminOnly: true, userScope: "data lineage" },
  evidence: { label: "Evidence", adminOnly: true, userScope: "production proof ledger" },
  validation: { label: "Why Return", adminOnly: true, userScope: "product validation evidence" },
  bot: { label: "Bot Control", adminOnly: true, userScope: "admin controls" },
  access: { label: "PNET Access", adminOnly: false, userScope: "PNET access" },
  receipts: { label: "Receipts", adminOnly: false, userScope: "public receipts" },
  logs: { label: "Logs", adminOnly: true, userScope: "operator logs" },
};

const mockPreflightRows = [
  ["Admin review wallet connected", "wait", "Connect an admin wallet before live controls are visible."],
  ["Admin wallet verified", "wait", "Backend session endpoint must verify admin allowlist membership."],
  ["Correct network", "ok", "MainNet is configured for Phase 0 market data."],
  ["Scanner online", "ok", "Read-only scanner endpoint is responding."],
  ["Pool data fresh", "ok", "Latest PNET snapshots are under the freshness window."],
  ["Tinyman connector online", "ok", "Executable venue connector present."],
  ["Pact connector online", "ok", "Executable venue connector present."],
  ["Route engine online", "ok", "Two-leg and triangle search are available."],
  ["Risk engine online", "ok", "Most opportunities are expected to reject."],
  ["Signer online", "blocked", "Signer stays locked until v0.8 review."],
  ["Kill switch clear", "blocked", "Kill switch remains active by default."],
  ["Hot wallet reserve", "wait", "Wallet balance check is required before any dry-run handoff."],
  ["App allowlist loaded", "ok", "Route app IDs are checked before execution planning."],
  ["Asset allowlist loaded", "ok", "PNET, ALGO, USDC, and reviewed ASAs only."],
  ["Public data delay enabled", "ok", "Live raw opportunities are not exposed to public users."],
];

const mockExecutionQueue = [
  ["Q-1042", "10 ALGO", "dry-run group", "awaiting signer", "expires in 18s"],
  ["Q-1041", "5 ALGO", "paper only", "risk rejected", "profit buffer too low"],
  ["Q-1039", "10 ALGO", "reconciled", "confirmed", "simulated receipt"],
];

const mockReceipts = [
  ["R-203", "ALGO/USDC", "10.0000", "10.0472", "+0.0411", "confirmed round 49392011"],
  ["R-202", "PNET/USDC", "1000.0000", "999.4000", "-0.6000", "paper loss shown"],
  ["R-201", "ALGO/PNET", "5.0000", "5.0085", "+0.0022", "dry-run only"],
];

const defaultAlertCatalog = [
  {
    code: "scanner_down",
    title: "Scanner Down",
    severity: "critical",
    trigger: "No scanner heartbeat inside the configured freshness window.",
    operatorAction: "Restart scanner and confirm no signer secrets are required.",
  },
  {
    code: "quote_age_above_threshold",
    title: "Quote Age Above Threshold",
    severity: "warning",
    trigger: "Quote age exceeds the max freshness policy.",
    operatorAction: "Reject route, refresh quotes, and preserve the stale quote reason.",
  },
  {
    code: "unknown_app_id_detected",
    title: "Unknown App ID Detected",
    severity: "high",
    trigger: "Route references an application outside the reviewed venue allowlist.",
    operatorAction: "Reject route and require connector review.",
  },
  {
    code: "kill_switch_triggered",
    title: "Kill Switch Triggered",
    severity: "critical",
    trigger: "Kill switch is active or has been manually triggered.",
    operatorAction: "Keep execution disarmed until separate production policy review.",
  },
];

const defaultPolicyCatalog = [
  {
    code: "max_input_amount",
    label: "Max Input Amount",
    status: "configured",
    configuredValue: "10 ALGO",
    rejects: "Routes whose input amount exceeds the per-trade cap.",
  },
  {
    code: "max_transaction_fee",
    label: "Max Transaction Fee",
    status: "configured",
    configuredValue: "group fee cap",
    rejects: "Unsigned groups whose fees exceed policy.",
  },
  {
    code: "asset_allowlist",
    label: "Asset Allowlist",
    status: "configured",
    configuredValue: "reviewed ASAs only",
    rejects: "Routes containing unreviewed assets.",
  },
  {
    code: "app_id_allowlist",
    label: "App ID Allowlist",
    status: "required",
    configuredValue: "reviewed apps only",
    rejects: "Routes or groups calling unknown apps.",
  },
  {
    code: "transaction_type_allowlist",
    label: "Transaction Type Allowlist",
    status: "configured",
    configuredValue: "pay, axfer, appl",
    rejects: "Any transaction type outside the narrow set.",
  },
  {
    code: "route_hash_approval",
    label: "Route Hash Approval",
    status: "locked",
    configuredValue: "explicit approvals only",
    rejects: "Groups whose route hash was not reviewed.",
  },
  {
    code: "daily_spend_limit",
    label: "Daily Spend Limit",
    status: "configured",
    configuredValue: "daily input cap",
    rejects: "Additional routes after daily exposure is reached.",
  },
  {
    code: "wallet_reserve_minimum",
    label: "Wallet Reserve Minimum",
    status: "configured",
    configuredValue: "reserve protected",
    rejects: "Groups that would take the hot wallet below reserve.",
  },
  {
    code: "kill_switch",
    label: "Kill Switch",
    status: "locked",
    configuredValue: "active by default",
    rejects: "All live arm and signing requests while active.",
  },
];

function defaultProductionStatus(source = "unavailable") {
  return {
    status: "not_live_ready",
    headline: "NOT LIVE READY",
    reason:
      "Phase 3 TestNet readiness is active: read-only scanner, quotes, routes, risk, paper, and soak evidence only. Live execution remains locked.",
    safeMode: "Phase 3 TestNet: Scanner / Paper / Dry Run only.",
    restrictions: [
      "No user deposits.",
      "No guaranteed returns.",
      "No live execution unless explicitly armed by admin after gates pass.",
    ],
    source,
  };
}

function defaultProductionReadiness(source = "unavailable") {
  return {
    currentPhase: "Phase 3: TestNet Readiness",
    currentPhaseKey: "phase_3_testnet_readiness",
    activePhase: "Phase 3: TestNet Readiness",
    historicalPhase: "Phase 0 evidence",
    overallPercent: 0,
    nextGate: "24h TestNet soak evidence",
    blockingItems: ["Production readiness endpoint unavailable."],
    passedEvidenceCount: 0,
    totalEvidenceCount: 0,
    source,
  };
}

function emptyPaperSummary(source = "unavailable") {
  return {
    daysCollected: 0,
    targetDays: 7,
    candidatesObserved: 0,
    wouldExecuteCount: 0,
    simulatedWins5s: 0,
    simulatedWins30s: 0,
    expectedNetAlgo: "0.000000",
    simulatedNetAlgo5s: "0.000000",
    simulatedNetAlgo30s: "0.000000",
    averageQuoteDecayAlgo: "0.000000",
    verdict: "not_ready",
    source,
  };
}

function emptyRiskGates(source = "unavailable") {
  return {
    liveExecutionLocked: true,
    lockReasons: ["ENABLE_EXECUTION=false", "kill switch active", "signer disabled"],
    productionStatus: defaultProductionStatus(source),
    productionReadiness: defaultProductionReadiness(source),
    source,
    checks: [
      { key: "live_execution", label: "Live execution disarmed", status: "blocked", evidence: "Live execution stays locked." },
      { key: "signer", label: "Signer state", status: "disabled", evidence: "No signer in this control room." },
      { key: "user_funds", label: "No user deposits", status: "ok", evidence: "PNET fees are market-data only." },
    ],
  };
}

function normalizeSourceLabel(source) {
  const value = String(source || "unavailable").toLowerCase();
  if (["mock", "stored", "live", "delayed", "unavailable", "degraded"].includes(value)) return value;
  return "unavailable";
}

function makeMockOpsControlRoom(reason = "Backend ops endpoints unavailable") {
  const now = new Date().toISOString();
  const tick = Math.max(1, state.opsRefreshCount || 1);
  const services = [
    ["pool_scanner", "Pool Scanner", "wait", "Read-only scanner evidence placeholder."],
    ["quote_engine", "Quote Engine", "wait", "Quote capture placeholder."],
    ["route_engine", "Route Engine", "wait", "Route candidate placeholder."],
    ["paper_trader", "Simulator / Paper Trader", "wait", "Paper-trading placeholder."],
    ["risk_engine", "Risk Engine", "blocked", "Risk rejects most routes by design."],
    ["dry_run_builder", "Dry-Run Builder", "blocked", "Unsigned groups only."],
    ["signer_gate", "Signer Gate", "disabled", "Signer stays disabled in mock mode."],
    ["live_micro_execution", "Live Micro-Execution", "disabled", "Live execution remains disarmed."],
    ["receipts_reconciliation", "Receipts / Reconciliation", "wait", "Receipt evidence placeholder."],
  ].map(([key, label, status, summary], index) => ({
    key,
    label,
    status,
    source: "mock",
    lastRunAt: index < 4 ? now : null,
    lastSuccessAt: null,
    inputCount24h: index < 5 ? index * 3 + tick : 0,
    outputCount24h: index < 4 ? index * 2 + tick : index === 4 ? tick * 2 : 0,
    errorCount24h: 0,
    freshnessSeconds: index < 4 ? 300 + index * 90 : null,
    summary,
    blocker: status === "ok" ? null : reason,
    motionLabel: index < 6 ? `mock heartbeat ${tick}` : summary,
    motionState: status === "disabled" ? "locked" : "mock",
    endpoint: `/api/ops/pipeline#${key}`,
    lastLogs: [`${label}: mock telemetry`, `source=mock`, reason],
    nextAction: "Connect backend ops endpoint or continue collecting Phase 0 evidence.",
    evidence: [
      {
        label: key === "signer_gate" ? "Signer state" : "Evidence count",
        value: key === "signer_gate" ? "disabled" : String(index < 5 ? index * 3 + tick : 0),
        detail: key === "signer_gate" ? "Mock signer remains disabled and locked." : "Mock proof placeholder until backend data loads.",
        source: "mock",
      },
      {
        label: key === "live_micro_execution" ? "Execution lock" : "Source",
        value: key === "live_micro_execution" ? "locked" : "mock",
        detail: key === "live_micro_execution" ? "Mock mode does not expose live execution." : reason,
        source: "mock",
      },
    ],
  }));
  return {
    pipeline: {
      services,
      generatedAt: now,
      liveExecutionLocked: true,
      productionStatus: defaultProductionStatus("mock"),
      productionReadiness: defaultProductionReadiness("mock"),
      source: "mock",
    },
    phaseGates: {
      source: "mock",
      phases: [
        ["phase_0a_inventory", "Phase 0A Inventory", 100, "ok", ["repo inventory", "safe-scope docs"], ["mock inventory scaffold"], []],
        ["phase_0b_scanner", "Phase 0B Scanner", 70, "wait", ["24h scanner uptime", "fresh snapshots"], ["mock scanner heartbeat"], ["runtime uptime evidence needed"]],
        ["phase_0c_route_engine", "Phase 0C Route Engine", 40, "wait", ["comparable quotes", "explained rejections"], ["mock route candidates"], ["stored route evidence needed"]],
        ["phase_0d_paper_trading", "Phase 0D Paper Trading", 20, "blocked", ["7 collection days", "5s/30s rechecks"], [], ["7-day paper run needed"]],
        ["phase_0e_risk_engine", "Phase 0E Risk Engine", 20, "blocked", ["risk rejection evidence", "profit buffer checks"], [], ["runtime rejection evidence needed"]],
        ["phase_0f_live_micro", "Phase 0F Live Micro", 0, "disabled", ["unsigned dry runs", "manual reconciliation"], [], ["LOCKED"]],
        ["phase_0g_public_dash", "Phase 0G Public Dash", 50, "wait", ["delayed public-safe data", "source labels"], ["mock dashboard labels"], ["public-safe polish needed"]],
      ].map(([key, label, percent, status, requiredEvidence, completedEvidence, blockers]) => ({
        key,
        label,
        percent,
        status,
        requiredEvidence,
        completedEvidence,
        blockers,
        source: "mock",
      })),
      gates: [
        ["scanner_24h", "Scanner 24h", 20, "wait", ["24h scanner uptime"], ["local scaffold"], ["runtime evidence needed"]],
        ["comparable_quotes", "Comparable Quotes", 30, "wait", ["Tinyman/Pact quotes"], ["mock shape"], ["stored quotes needed"]],
        ["explained_rejections", "Explained Rejections", 40, "wait", ["skip reasons"], ["risk labels"], ["stored route candidates needed"]],
        ["paper_7d", "7-Day Paper Trading", 10, "blocked", ["5s/30s rechecks"], [], ["7-day paper run needed"]],
        ["risk_blocks", "Risk Blocks Bad Routes", 60, "wait", ["risk rejection tests"], ["pure tests"], ["runtime evidence needed"]],
        ["unsigned_dry_run", "Unsigned Dry Run", 35, "blocked", ["unsigned groups only"], [], ["review dry-run receipts"]],
        ["signer_rejection", "Signer Policy Rejection", 20, "blocked", ["rejection evidence"], [], ["signer remains locked"]],
        ["manual_live", "Manual First Live Trade", 0, "disabled", ["manual Lora verification"], [], ["future gate"]],
      ].map(([key, label, percent, status, requiredEvidence, completedEvidence, blockers]) => ({
        key,
        label,
        percent,
        status,
        requiredEvidence,
        completedEvidence,
        blockers,
        source: "mock",
      })),
      productionReadiness: defaultProductionReadiness("mock"),
    },
    activity: {
      source: "mock",
      events: [
        { id: "mock-1", timestamp: now, service: "Control Room", severity: "info", message: "Mock telemetry active.", source: "mock" },
        { id: "mock-2", timestamp: now, service: "Live Micro-Execution", severity: "blocked", message: "Live execution is locked.", source: "mock" },
      ],
    },
    rejections: {
      source: "mock",
      summary: "Mock rejection funnel. Production should use stored skip reasons.",
      buckets: [
        { reason: "quote_freshness_ok", count: 12, percent: 36 },
        { reason: "fee_buffer_ok", count: 9, percent: 27 },
        { reason: "assets_allowlisted", count: 7, percent: 21 },
        { reason: "profit_bps_ok", count: 5, percent: 16 },
      ],
    },
    paperSummary: {
      daysCollected: 1,
      targetDays: 7,
      candidatesObserved: 33 + tick,
      wouldExecuteCount: 4 + Math.floor(tick / 3),
      simulatedWins5s: 2 + Math.floor(tick / 4),
      simulatedWins30s: 1,
      expectedNetAlgo: "0.000000",
      simulatedNetAlgo5s: "0.000000",
      simulatedNetAlgo30s: "0.000000",
      averageQuoteDecayAlgo: "0.000000",
      verdict: "watching",
      source: "mock",
    },
    riskGates: {
      liveExecutionLocked: true,
      lockReasons: ["mock mode", "kill switch assumed active", "signer disabled"],
      productionStatus: defaultProductionStatus("mock"),
      source: "mock",
      checks: [
        { key: "live_execution", label: "Live execution disarmed", status: "blocked", evidence: "Mock lock state." },
        { key: "signer", label: "Signer state", status: "disabled", evidence: "No signer in mock telemetry." },
        { key: "user_funds", label: "No user deposits", status: "ok", evidence: "PNET fees are market-data only." },
      ],
    },
    environment: {
      environment: "local",
      network: APP_CONFIG.NETWORK,
      items: [
        { label: "Pool data", source: "mock", status: "wait", detail: "placeholder" },
        { label: "Route data", source: "mock", status: "wait", detail: "placeholder" },
        { label: "Public dashboard", source: "delayed", status: "ok", detail: "delay policy visible" },
        { label: "Signer", source: "unavailable", status: "disabled", detail: "not configured" },
        { label: "Live execution", source: "unavailable", status: "blocked", detail: "disarmed" },
      ],
    },
    connectors: {
      source: "mock",
      status: "mock",
      blocksReadiness: false,
      readinessRollup: {
        totalConnectors: 4,
        okCount: 0,
        degradedCount: 0,
        downCount: 0,
        staleCount: 0,
        mockCount: 4,
        productionReadyCount: 0,
        blockedReasons: [],
        waitReasons: [
          { connectorName: "tinyman", status: "mock", reason: "mock_connector_not_production_ready" },
          { connectorName: "pact", status: "mock", reason: "mock_connector_not_production_ready" },
          { connectorName: "algod", status: "mock", reason: "mock_connector_not_production_ready" },
          { connectorName: "indexer", status: "mock", reason: "mock_connector_not_production_ready" },
        ],
        overallReadiness: "wait",
      },
      connectors: ["tinyman", "pact", "algod", "indexer"].map((name) => ({
        connector: name,
        connectorName: name,
        connectorType: name === "algod" ? "algod" : name === "indexer" ? "indexer" : "dex",
        status: "mock",
        readinessImpact: "wait",
        degradationReason: "mock_connector_not_production_ready",
        productionReady: false,
        latencyMs: null,
        freshCount24h: name === "tinyman" || name === "pact" ? tick : 0,
        staleCount24h: 0,
        errorCount24h: 0,
        latestRound: null,
        expectedMinRound: null,
        source: "mock",
      })),
    },
    testnetSoak: {
      runnerState: "idle",
      currentGateStatus: "not_started",
      coveragePercent: 0,
      elapsedCoverageSeconds: 0,
      expectedObservationCount: 0,
      completedObservationCount: 0,
      longestGapSeconds: 0,
      scannerSuccessRate: 0,
      poolsObserved: 0,
      quotesObserved: 0,
      freshQuotePercent: 0,
      staleQuoteCount: 0,
      connectors: {
        tinyman: { ok: 0, degraded: 0, error: 0 },
        pact: { ok: 0, degraded: 0, error: 0 },
        algod: { ok: 0, error: 0 },
        indexer: { ok: 0, error: 0 },
      },
      routes: { candidateCount: 0, rejectedCount: 0, rejectionReasons: [] },
      paper: { recheckCompleted5s: 0, recheckCompleted30s: 0 },
      blockers: ["no_live_observations", "mock_observations_do_not_count_toward_live_coverage"],
      warnings: [reason],
      source: "mock",
      productionReady: false,
      liveExecutionLocked: true,
    },
  };
}

const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 4 });
const money = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

function unwrapApiPayload(payload) {
  if (!payload || typeof payload !== "object" || !Object.prototype.hasOwnProperty.call(payload, "ok")) {
    return payload;
  }
  if (!payload.ok) {
    const message = payload.error?.message || payload.error?.code || "API request failed";
    throw new Error(message);
  }
  return payload.data;
}

function serviceByKey(snapshot) {
  return new Map((snapshot?.pipeline?.services || []).map((service) => [service.key, service]));
}

function phaseGateItems(snapshot) {
  const phaseGates = snapshot?.phaseGates || {};
  return [...(phaseGates.phases || []), ...(phaseGates.gates || [])];
}

function gateByKey(snapshot) {
  return new Map(phaseGateItems(snapshot).map((gate) => [gate.key, gate]));
}

function decoratePhaseItems(items, priorGates, previous) {
  return (items || []).map((gate) => {
    const prior = priorGates.get(gate.key) || {};
    const percentDelta = Number(gate.percent || 0) - Number(prior.percent || 0);
    return {
      ...gate,
      percentDelta,
      hasDelta: Boolean(previous && percentDelta),
    };
  });
}

function decorateOpsControlRoom(next, previous) {
  const priorServices = serviceByKey(previous);
  const priorGates = gateByKey(previous);
  const services = (next.pipeline?.services || []).map((service) => {
    const prior = priorServices.get(service.key) || {};
    const deltaInput = Number(service.inputCount24h || 0) - Number(prior.inputCount24h || 0);
    const deltaOutput = Number(service.outputCount24h || 0) - Number(prior.outputCount24h || 0);
    const deltaError = Number(service.errorCount24h || 0) - Number(prior.errorCount24h || 0);
    const hasDelta = Boolean(previous && (deltaInput || deltaOutput || deltaError || service.lastRunAt !== prior.lastRunAt));
    const source = normalizeSourceLabel(service.source);
    return {
      ...service,
      source,
      deltaInput24h: deltaInput,
      deltaOutput24h: deltaOutput,
      deltaError24h: deltaError,
      hasDelta,
      nextAction: service.nextAction || service.blocker || "Continue evidence collection.",
      evidence: (service.evidence || []).map((item) => ({
        ...item,
        source: normalizeSourceLabel(item.source || source),
      })),
    };
  });
  const phases = decoratePhaseItems(next.phaseGates?.phases || [], priorGates, previous).map((phase) => ({
    ...phase,
    source: normalizeSourceLabel(phase.source || next.phaseGates?.source),
    lane: phase.lane || "historical",
  }));
  const gates = decoratePhaseItems(next.phaseGates?.gates || [], priorGates, previous).map((gate) => ({
    ...gate,
    source: normalizeSourceLabel(gate.source || next.phaseGates?.source),
  }));

  const paperSummary = next.paperSummary
    ? {
        ...next.paperSummary,
        source: normalizeSourceLabel(next.paperSummary.source),
        // Mock paper never contributes readiness-looking positive verdicts.
        verdict:
          normalizeSourceLabel(next.paperSummary.source) === "mock"
            ? "not_ready"
            : next.paperSummary.verdict || "not_ready",
      }
    : emptyPaperSummary(next.pipeline?.source === "mock" ? "mock" : "unavailable");

  const riskGates = next.riskGates
    ? {
        ...next.riskGates,
        source: normalizeSourceLabel(next.riskGates.source),
        liveExecutionLocked: true,
      }
    : emptyRiskGates(next.pipeline?.source === "mock" ? "mock" : "unavailable");

  const productionReadiness = {
    ...(next.pipeline?.productionReadiness ||
      next.phaseGates?.productionReadiness ||
      defaultProductionReadiness(next.pipeline?.source || "unavailable")),
  };
  if (normalizeSourceLabel(productionReadiness.source) === "mock") {
    productionReadiness.overallPercent = 0;
    productionReadiness.passedEvidenceCount = 0;
    productionReadiness.blockingItems = [
      ...(productionReadiness.blockingItems || []),
      "mock_evidence_excluded_from_readiness",
    ];
  }
  productionReadiness.currentPhase = productionReadiness.activePhase || productionReadiness.currentPhase || "Phase 3: TestNet Readiness";
  productionReadiness.source = normalizeSourceLabel(productionReadiness.source);

  const connectors = next.connectors
    ? {
        ...next.connectors,
        source: normalizeSourceLabel(next.connectors.source),
        connectors: (next.connectors.connectors || []).map((item) => ({
          ...item,
          source: normalizeSourceLabel(item.source || next.connectors.source),
          productionReady: item.source === "mock" || item.status === "mock" ? false : Boolean(item.productionReady),
        })),
      }
    : { source: "unavailable", connectors: [], readinessRollup: { overallReadiness: "blocked", productionReadyCount: 0 } };

  const testnetSoak = next.testnetSoak
    ? {
        ...next.testnetSoak,
        source: normalizeSourceLabel(next.testnetSoak.source),
        productionReady: false,
        liveExecutionLocked: true,
        gateStatus: next.testnetSoak.gateStatus || next.testnetSoak.currentGateStatus || "not_started",
        currentGateStatus: next.testnetSoak.gateStatus || next.testnetSoak.currentGateStatus || "not_started",
      }
    : null;

  return {
    ...next,
    pipeline: {
      ...(next.pipeline || {}),
      services,
      liveExecutionLocked: true,
      source: normalizeSourceLabel(next.pipeline?.source),
      productionStatus: {
        ...(next.pipeline?.productionStatus || defaultProductionStatus(next.pipeline?.source)),
        source: normalizeSourceLabel(next.pipeline?.productionStatus?.source || next.pipeline?.source),
        status: "not_live_ready",
        headline: "NOT LIVE READY",
      },
      productionReadiness,
    },
    phaseGates: {
      ...(next.phaseGates || {}),
      phases,
      gates,
      activePhase: next.phaseGates?.activePhase || {
        key: "phase_3_testnet_readiness",
        label: "Phase 3: TestNet Readiness",
        status: "in_progress",
        source: productionReadiness.source,
        lane: "active",
      },
      productionReadiness,
      source: normalizeSourceLabel(next.phaseGates?.source),
    },
    activity: {
      ...(next.activity || { events: [] }),
      source: normalizeSourceLabel(next.activity?.source),
      events: (next.activity?.events || []).map((event) => ({
        ...event,
        source: normalizeSourceLabel(event.source),
      })),
    },
    rejections: {
      ...(next.rejections || { buckets: [] }),
      source: normalizeSourceLabel(next.rejections?.source),
    },
    paperSummary,
    riskGates,
    environment: {
      ...(next.environment || { items: [] }),
      items: (next.environment?.items || []).map((item) => ({
        ...item,
        source: normalizeSourceLabel(item.source),
      })),
    },
    connectors,
    testnetSoak,
    testnetSoakObservations: next.testnetSoakObservations
      ? {
          ...next.testnetSoakObservations,
          source: normalizeSourceLabel(next.testnetSoakObservations.source),
          productionReady: false,
          observations: (next.testnetSoakObservations.observations || []).map((item) => ({
            ...item,
            source: normalizeSourceLabel(item.source),
            productionReady: false,
          })),
        }
      : null,
  };
}

async function fetchApiData(url, options = {}) {
  return unwrapApiPayload(await fetchJson(url, options));
}

function apiHeaders({ json = false } = {}) {
  const session = currentSession();
  const headers = {
    "X-Algopulse-Role": session.role,
    "X-Algopulse-Wallet": session.address || "guest",
  };
  if (json) headers["Content-Type"] = "application/json";
  return headers;
}

function productSessionId() {
  try {
    const key = "algopulse_product_session_id";
    const existing = window.localStorage.getItem(key);
    if (existing) return existing;
    const generated =
      window.crypto?.randomUUID?.() || `session_${Date.now()}_${Math.random().toString(16).slice(2)}`;
    window.localStorage.setItem(key, generated);
    return generated;
  } catch (_error) {
    return "session_unavailable";
  }
}

function productActionForView(view) {
  return {
    pulse: "viewed_market_pulse",
    routes: null,
    research: "opened_daily_report",
    heatmap: "viewed_liquidity_health",
    replay: "opened_opportunity_replay",
    forensics: "inspected_route_forensics",
    decay: "opened_opportunity_replay",
    receipts: "viewed_receipt",
  }[view] || null;
}

async function recordProductAction(actionType, metadata = {}) {
  if (!actionType) return null;
  const session = currentSession();
  const payload = {
    action_type: actionType,
    user_role: session.role,
    wallet_connected: session.role !== "guest",
    source_page: metadata.source_page || metadata.page || state.activeView || "unknown",
    metadata: {
      ...metadata,
      session_id: productSessionId(),
      pnet_user: Boolean(session.optedIn && session.pnetBalance > 0),
      pnet_balance: session.pnetBalance,
      credits: session.credits,
      network: session.network,
    },
  };
  try {
    return await fetchApiData("/api/events/user-action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (_error) {
    return null;
  }
}

async function loadContributionProtocol({ render = true } = {}) {
  const session = currentSession();
  state.contributionProtocolLoading = true;
  state.contributionProtocolError = null;
  if (render) renderRoleDashboard();
  try {
    state.contributionProtocol = await fetchApiData(
      `/api/contribution-protocol/session/${encodeURIComponent(session.address || "guest")}`
    );
  } catch (error) {
    state.contributionProtocolError = error.message;
  } finally {
    state.contributionProtocolLoading = false;
    if (render) renderRoleDashboard();
  }
}

async function loadCommunityGrowth({ render = true } = {}) {
  const session = currentSession();
  state.communityGrowthLoading = true;
  state.communityGrowthError = null;
  if (render) renderRoleDashboard();
  try {
    state.communityGrowth = await fetchApiData(`/api/community-growth/overview/${encodeURIComponent(session.address || "guest")}`);
  } catch (error) {
    state.communityGrowthError = error.message;
  } finally {
    state.communityGrowthLoading = false;
    if (render) renderRoleDashboard();
  }
}

async function loadTransparencySystem({ render = true } = {}) {
  state.transparencyLoading = true;
  state.transparencyError = null;
  if (render) renderRoleDashboard();
  try {
    state.transparencySystem = await fetchApiData("/api/transparency/system");
  } catch (error) {
    state.transparencyError = error.message;
  } finally {
    state.transparencyLoading = false;
    if (render) renderRoleDashboard();
  }
}

async function submitContributionProtocol(contributionType) {
  const session = currentSession();
  const titles = {
    docs_fix: "Docs improvement suggestion",
    pool_observation: "PNET pool observation",
    bug_report: "Beta bug or safety report",
    demo_feedback: "Demo feedback",
    data_source_suggestion: "Data-source suggestion",
    mining_evidence: "Redacted mining evidence receipt",
    bandwidth_evidence: "Redacted bandwidth evidence receipt",
    verification_report: "Verification report",
  };
  try {
    await fetchApiData("/api/contribution-protocol/submit", {
      method: "POST",
      headers: apiHeaders({ json: true }),
      body: JSON.stringify({
        wallet: session.address,
        contribution_type: contributionType,
        title: titles[contributionType] || "Contribution protocol submission",
        summary:
          "Local beta dashboard submission for manual review. Replace this summary with contributor evidence before production use.",
        evidence_url: null,
      }),
    });
    state.operatorNotice = "Contribution submitted for manual review. No payout, token reward, or governance authority was granted.";
    await loadContributionProtocol({ render: false });
    await loadCommunityGrowth({ render: false });
  } catch (error) {
    state.operatorNotice = `Contribution submission rejected: ${error.message}`;
  }
  renderRoleDashboard();
}

async function spendContributionCredits(unlockCode) {
  const session = currentSession();
  try {
    await fetchApiData("/api/contribution-protocol/spend", {
      method: "POST",
      headers: apiHeaders({ json: true }),
      body: JSON.stringify({
        wallet: session.address,
        unlock_code: unlockCode,
        quantity: 1,
        note: "Local beta credit spend from dashboard.",
      }),
    });
    state.operatorNotice = "Credit spend receipt created for bounded access. No trading, signer, treasury, or binding governance action occurred.";
    await loadContributionProtocol({ render: false });
    await loadCommunityGrowth({ render: false });
  } catch (error) {
    state.operatorNotice = `Credit spend rejected: ${error.message}`;
  }
  renderRoleDashboard();
}

async function recordCommunityReferral() {
  const session = currentSession();
  try {
    await fetchApiData("/api/community-growth/referral", {
      method: "POST",
      headers: apiHeaders({ json: true }),
      body: JSON.stringify({
        wallet: session.address,
        referred_wallet: null,
        channel: "direct",
        note: "Local beta referral receipt. Review before any credit or recognition.",
      }),
    });
    state.operatorNotice = "Referral receipt recorded for manual review. No automatic payout, token reward, or governance power was granted.";
    await loadCommunityGrowth({ render: false });
  } catch (error) {
    state.operatorNotice = `Referral receipt rejected: ${error.message}`;
  }
  renderRoleDashboard();
}

function applyPublicConfig(config) {
  if (!config) return;
  APP_PHASE_LABEL = config.developmentPhase || APP_PHASE_LABEL;
  const backendNetwork = String(config.network || APP_CONFIG.NETWORK || "testnet").toLowerCase();
  APP_CONFIG = {
    ...APP_CONFIG,
    PNET_ASA_ID: Number(config.pnetAsaId ?? APP_CONFIG.PNET_ASA_ID),
    PNET_ASA_CONFIGURED: Boolean(config.pnetAsaConfigured ?? Number(config.pnetAsaId || 0) > 0),
    PNET_MESSAGE: config.pnetMessage || (Number(config.pnetAsaId || 0) > 0 ? null : "PNET TestNet asset not configured"),
    PLATFORM_FEE_RECEIVER: config.pnetFeeReceiverAddress || APP_CONFIG.PLATFORM_FEE_RECEIVER,
    PLATFORM_APP_ID: config.pnetFeeAppId || APP_CONFIG.PLATFORM_APP_ID,
    NETWORK: backendNetwork,
    CHAIN_ID: Number(config.chainId || ALGORAND_CHAIN_IDS[backendNetwork] || 0) || null,
    WALLET_ACCESS_MODE: config.walletAccessMode || "connect_only",
    WALLET_CONNECT_ONLY: config.walletConnectOnly !== false,
    SUPPORTED_WALLETS: Array.isArray(config.supportedWallets) ? config.supportedWallets : ["pera", "defly"],
    PUBLIC_DATA_DELAY_SECONDS: Number(config.publicRouteDelaySeconds ?? APP_CONFIG.PUBLIC_DATA_DELAY_SECONDS),
    BACKEND_NETWORK_AUTHORITY: config.backendNetworkAuthority !== false,
    CAPABILITIES: config.capabilities || APP_CONFIG.CAPABILITIES || {},
  };
  // Backend is network authority: force selector to backend network when disconnected.
  if (!state.walletConnection?.address) {
    state.walletNetwork = backendNetwork;
  }
  state.phaseGates = Array.isArray(config.phaseGates) ? config.phaseGates : state.phaseGates;
  state.deploymentModes = Array.isArray(config.deploymentModes) ? config.deploymentModes : state.deploymentModes;
  state.productCapabilities = Array.isArray(config.productCapabilities) ? config.productCapabilities : state.productCapabilities;
  pnetActions.public_scan.fee = 4;
  renderAppPhaseLabel();
}

async function loadAdminPreflight({ render = true } = {}) {
  if (currentSession().role !== "admin") {
    state.latestPreflight = null;
    if (render) renderRoleDashboard();
    return null;
  }
  try {
    state.latestPreflight = await fetchApiData("/api/admin/preflight", {
      headers: apiHeaders(),
    });
  } catch (error) {
    state.latestPreflight = {
      checklist: [
        {
          label: "Backend preflight",
          status: "blocked",
          detail: error.message,
        },
      ],
    };
  }
  if (render) renderRoleDashboard();
  return state.latestPreflight;
}

async function loadAdminAlertCatalog({ render = true } = {}) {
  if (currentSession().role !== "admin") {
    state.latestAlertCatalog = [];
    if (render) renderRoleDashboard();
    return null;
  }
  try {
    const result = await fetchApiData("/api/admin/alerts/catalog", {
      headers: apiHeaders(),
    });
    state.latestAlertCatalog = Array.isArray(result.alerts) ? result.alerts : [];
  } catch (error) {
    state.latestAlertCatalog = [
      {
        code: "alert_catalog_unavailable",
        title: "Alert Catalog Unavailable",
        severity: "warning",
        trigger: "Backend alert catalog request failed.",
        operatorAction: error.message,
      },
    ];
  }
  if (render) renderRoleDashboard();
  return state.latestAlertCatalog;
}

async function loadAdminPolicyCatalog({ render = true } = {}) {
  if (currentSession().role !== "admin") {
    state.latestPolicyCatalog = [];
    if (render) renderRoleDashboard();
    return null;
  }
  try {
    const result = await fetchApiData("/api/admin/policy/catalog", {
      headers: apiHeaders(),
    });
    state.latestPolicyCatalog = Array.isArray(result.controls) ? result.controls : [];
  } catch (error) {
    state.latestPolicyCatalog = [
      {
        code: "policy_catalog_unavailable",
        label: "Policy Catalog Unavailable",
        status: "warning",
        configuredValue: "backend check failed",
        rejects: error.message,
      },
    ];
  }
  if (render) renderRoleDashboard();
  return state.latestPolicyCatalog;
}

async function loadOpsControlRoom({ render = true, quiet = false } = {}) {
  if (currentSession().role !== "admin") {
    state.opsControlRoom = null;
    state.opsError = null;
    state.opsLoading = false;
    if (render) renderRoleDashboard();
    return null;
  }
  if (state.opsLoading && quiet) {
    return state.opsControlRoom;
  }
  state.opsLoading = true;
  if (render && !quiet) renderRoleDashboard();
  try {
    const settled = await Promise.allSettled([
      fetchApiData("/api/ops/pipeline", { headers: apiHeaders() }),
      fetchApiData("/api/ops/phase-gates", { headers: apiHeaders() }),
      fetchApiData("/api/ops/activity", { headers: apiHeaders() }),
      fetchApiData("/api/ops/rejections", { headers: apiHeaders() }),
      fetchApiData("/api/ops/paper-summary", { headers: apiHeaders() }),
      fetchApiData("/api/ops/risk-gates", { headers: apiHeaders() }),
      fetchApiData("/api/ops/environment", { headers: apiHeaders() }),
      fetchApiData("/api/ops/connectors", { headers: apiHeaders() }),
      fetchApiData("/api/ops/testnet-soak", { headers: apiHeaders() }),
      fetchApiData("/api/ops/testnet-soak/observations?limit=20", { headers: apiHeaders() }),
    ]);
    const valueAt = (index) => (settled[index].status === "fulfilled" ? settled[index].value : null);
    const errorAt = (index) =>
      settled[index].status === "rejected" ? settled[index].reason?.message || String(settled[index].reason) : null;

    const pipeline = valueAt(0);
    const phaseGates = valueAt(1);
    const activity = valueAt(2);
    const rejections = valueAt(3);
    const paperSummary = valueAt(4);
    const riskGates = valueAt(5);
    const environment = valueAt(6);
    const connectors = valueAt(7);
    const testnetSoak = valueAt(8);
    const testnetSoakObservations = valueAt(9);

    const coreFailed = !pipeline && !phaseGates && !activity;
    if (coreFailed) {
      throw new Error(errorAt(0) || errorAt(1) || errorAt(2) || "Control Room ops endpoints unavailable");
    }

    const previous = state.opsControlRoom;
    state.opsRefreshCount += 1;
    state.opsLastLoadedAt = new Date();
    state.testnetSoakError = testnetSoak ? null : errorAt(8);
    state.testnetSoakObservationsError = testnetSoakObservations ? null : errorAt(9);
    const partialErrors = [errorAt(0), errorAt(1), errorAt(2), errorAt(3), errorAt(4), errorAt(5), errorAt(6), errorAt(7)]
      .filter(Boolean);
    state.opsControlRoom = decorateOpsControlRoom(
      {
        pipeline: pipeline || previous?.pipeline || null,
        phaseGates: phaseGates || previous?.phaseGates || null,
        activity: activity || previous?.activity || { events: [], source: "unavailable" },
        rejections: rejections || previous?.rejections || { buckets: [], source: "unavailable" },
        paperSummary: paperSummary || previous?.paperSummary || null,
        riskGates: riskGates || previous?.riskGates || null,
        environment: environment || previous?.environment || null,
        connectors: connectors || previous?.connectors || null,
        testnetSoak: testnetSoak || previous?.testnetSoak || null,
        testnetSoakObservations: testnetSoakObservations || previous?.testnetSoakObservations || null,
      },
      previous
    );
    state.opsError = partialErrors.length ? `Partial ops load: ${partialErrors.slice(0, 2).join("; ")}` : null;
  } catch (error) {
    const previous = state.opsControlRoom;
    state.opsRefreshCount += 1;
    state.opsLastLoadedAt = new Date();
    state.opsControlRoom = decorateOpsControlRoom(makeMockOpsControlRoom(error.message), previous);
    state.opsError = error.message;
  } finally {
    state.opsLoading = false;
  }
  if (render) renderRoleDashboard();
  return state.opsControlRoom;
}

function normalizeReplaySelection(data) {
  const replays = data?.replays || [];
  if (!replays.length) {
    state.selectedReplayId = null;
    state.compareReplayIds = [];
    return;
  }
  if (!state.selectedReplayId || !replays.some((item) => item.id === state.selectedReplayId)) {
    state.selectedReplayId = replays[0].id;
  }
  const defaults = data.compareDefaults?.length ? data.compareDefaults : replays.slice(0, 3).map((item) => item.id);
  state.compareReplayIds = state.compareReplayIds.filter((id) => replays.some((item) => item.id === id)).slice(0, 3);
  if (!state.compareReplayIds.length) state.compareReplayIds = defaults.slice(0, 3);
}

async function loadReplayLab({ render = true } = {}) {
  if (currentSession().role !== "admin") {
    state.replayLab = null;
    state.replayError = null;
    state.replayLoading = false;
    stopReplayPlayback();
    if (render) renderRoleDashboard();
    return null;
  }
  state.replayLoading = true;
  if (render) renderRoleDashboard();
  try {
    state.replayLab = await fetchApiData("/api/ops/replay-lab?limit=30", { headers: apiHeaders() });
    normalizeReplaySelection(state.replayLab);
    state.replayError = null;
  } catch (error) {
    state.replayLab = makeMockReplayLab(error.message);
    normalizeReplaySelection(state.replayLab);
    state.replayError = error.message;
  } finally {
    state.replayLoading = false;
  }
  if (render) renderRoleDashboard();
  return state.replayLab;
}

function normalizeRouteForensicsSelection(data) {
  const routes = data?.routes || [];
  if (!routes.length) {
    state.selectedForensicsId = null;
    state.compareForensicsIds = [];
    return;
  }
  if (!state.selectedForensicsId || !routes.some((item) => String(item.id) === String(state.selectedForensicsId))) {
    state.selectedForensicsId = routes[0].id;
  }
  const defaults = data.compareDefaults?.length ? data.compareDefaults : routes.slice(0, 3).map((item) => item.id);
  state.compareForensicsIds = state.compareForensicsIds
    .filter((id) => routes.some((item) => String(item.id) === String(id)))
    .slice(0, 3);
  if (!state.compareForensicsIds.length) state.compareForensicsIds = defaults.slice(0, 3);
}

async function loadRouteForensics({ render = true } = {}) {
  if (currentSession().role !== "admin") {
    state.routeForensics = null;
    state.routeForensicsError = null;
    state.routeForensicsLoading = false;
    if (render) renderRoleDashboard();
    return null;
  }
  state.routeForensicsLoading = true;
  if (render) renderRoleDashboard();
  try {
    state.routeForensics = await fetchApiData("/api/ops/route-forensics?limit=50", { headers: apiHeaders() });
    normalizeRouteForensicsSelection(state.routeForensics);
    state.routeForensicsError = null;
  } catch (error) {
    state.routeForensics = makeMockRouteForensics(error.message);
    normalizeRouteForensicsSelection(state.routeForensics);
    state.routeForensicsError = error.message;
  } finally {
    state.routeForensicsLoading = false;
  }
  if (render) renderRoleDashboard();
  return state.routeForensics;
}

async function loadConfidenceCalibration({ render = true } = {}) {
  if (currentSession().role !== "admin") {
    state.confidenceCalibration = null;
    state.confidenceCalibrationError = null;
    state.confidenceCalibrationLoading = false;
    if (render) renderRoleDashboard();
    return null;
  }
  state.confidenceCalibrationLoading = true;
  if (render) renderRoleDashboard();
  try {
    state.confidenceCalibration = await fetchApiData("/api/ops/confidence-calibration", { headers: apiHeaders() });
    state.confidenceCalibrationError = null;
  } catch (error) {
    state.confidenceCalibration = makeMockConfidenceCalibration(error.message);
    state.confidenceCalibrationError = error.message;
  } finally {
    state.confidenceCalibrationLoading = false;
  }
  if (render) renderRoleDashboard();
  return state.confidenceCalibration;
}

async function loadOpportunityDecay({ render = true } = {}) {
  if (currentSession().role !== "admin") {
    state.opportunityDecay = null;
    state.opportunityDecayError = null;
    state.opportunityDecayLoading = false;
    if (render) renderRoleDashboard();
    return null;
  }
  state.opportunityDecayLoading = true;
  if (render) renderRoleDashboard();
  try {
    state.opportunityDecay = await fetchApiData(`/api/ops/opportunity-decay?view=${encodeURIComponent(state.decayView)}`, {
      headers: apiHeaders(),
    });
    state.opportunityDecayError = null;
  } catch (error) {
    state.opportunityDecay = makeMockOpportunityDecay(error.message, state.decayView);
    state.opportunityDecayError = error.message;
  } finally {
    state.opportunityDecayLoading = false;
  }
  if (render) renderRoleDashboard();
  return state.opportunityDecay;
}

async function loadMarketHeatmap({ render = true } = {}) {
  if (currentSession().role !== "admin") {
    state.marketHeatmap = null;
    state.marketHeatmapError = null;
    state.marketHeatmapLoading = false;
    if (render) renderRoleDashboard();
    return null;
  }
  state.marketHeatmapLoading = true;
  if (render) renderRoleDashboard();
  try {
    state.marketHeatmap = await fetchApiData(`/api/ops/market-heatmap?view=${encodeURIComponent(state.heatmapView)}`, {
      headers: apiHeaders(),
    });
    normalizeHeatmapSelection(state.marketHeatmap);
    state.marketHeatmapError = null;
  } catch (error) {
    state.marketHeatmap = makeMockMarketHeatmap(error.message, state.heatmapView);
    normalizeHeatmapSelection(state.marketHeatmap);
    state.marketHeatmapError = error.message;
  } finally {
    state.marketHeatmapLoading = false;
  }
  if (render) renderRoleDashboard();
  return state.marketHeatmap;
}

function normalizeFailureSelection(data) {
  const scenarios = data?.scenarios || [];
  if (!scenarios.length) {
    state.selectedFailureKey = null;
    return;
  }
  if (!state.selectedFailureKey || !scenarios.some((item) => item.key === state.selectedFailureKey)) {
    state.selectedFailureKey = scenarios[0].key;
  }
}

async function loadFailureLab({ render = true } = {}) {
  if (currentSession().role !== "admin") {
    state.failureLab = null;
    state.failureLabError = null;
    state.failureLabLoading = false;
    if (render) renderRoleDashboard();
    return null;
  }
  state.failureLabLoading = true;
  if (render) renderRoleDashboard();
  try {
    state.failureLab = await fetchApiData("/api/ops/failure-lab", { headers: apiHeaders() });
    normalizeFailureSelection(state.failureLab);
    state.failureLabError = null;
  } catch (error) {
    state.failureLab = makeMockFailureLab(error.message);
    normalizeFailureSelection(state.failureLab);
    state.failureLabError = error.message;
  } finally {
    state.failureLabLoading = false;
  }
  if (render) renderRoleDashboard();
  return state.failureLab;
}

async function loadDataProvenance({ metric = state.selectedProvenanceMetric, routeHash = state.selectedProvenanceRouteHash, render = true } = {}) {
  if (currentSession().role !== "admin") {
    state.dataProvenance = null;
    state.provenanceError = null;
    state.provenanceLoading = false;
    if (render) renderRoleDashboard();
    return null;
  }
  state.selectedProvenanceMetric = metric || "route.expected_net_profit";
  state.selectedProvenanceRouteHash = routeHash || null;
  state.provenanceLoading = true;
  if (render) renderRoleDashboard();
  const params = new URLSearchParams({ metric: state.selectedProvenanceMetric });
  if (state.selectedProvenanceRouteHash) params.set("route_hash", state.selectedProvenanceRouteHash);
  try {
    state.dataProvenance = await fetchApiData(`/api/ops/provenance?${params.toString()}`, { headers: apiHeaders() });
    state.provenanceError = null;
  } catch (error) {
    state.dataProvenance = makeMockDataProvenance(error.message, state.selectedProvenanceMetric);
    state.provenanceError = error.message;
  } finally {
    state.provenanceLoading = false;
  }
  if (render) renderRoleDashboard();
  return state.dataProvenance;
}

function normalizeEvidenceSelection(data) {
  const records = data?.records || [];
  if (!records.length) {
    state.selectedEvidenceId = null;
    return;
  }
  if (!state.selectedEvidenceId || !records.some((item) => item.evidenceId === state.selectedEvidenceId)) {
    state.selectedEvidenceId = records[0].evidenceId;
  }
}

async function loadEvidenceSystem({ render = true } = {}) {
  if (currentSession().role !== "admin") {
    state.evidenceSystem = null;
    state.evidenceError = null;
    state.evidenceLoading = false;
    if (render) renderRoleDashboard();
    return null;
  }
  state.evidenceLoading = true;
  if (render) renderRoleDashboard();
  const params = new URLSearchParams();
  Object.entries(state.evidenceFilters).forEach(([key, value]) => {
    if (value && value !== "all") params.set(key, value);
  });
  const suffix = params.toString() ? `?${params.toString()}` : "";
  try {
    state.evidenceSystem = await fetchApiData(`/api/ops/evidence${suffix}`, { headers: apiHeaders() });
    normalizeEvidenceSelection(state.evidenceSystem);
    state.evidenceError = null;
  } catch (error) {
    state.evidenceSystem = makeMockEvidenceSystem(error.message);
    normalizeEvidenceSelection(state.evidenceSystem);
    state.evidenceError = error.message;
  } finally {
    state.evidenceLoading = false;
  }
  if (render) renderRoleDashboard();
  return state.evidenceSystem;
}

async function loadProductValidation({ render = true } = {}) {
  if (currentSession().role !== "admin") {
    state.productValidation = null;
    state.productValidationError = null;
    state.productValidationLoading = false;
    if (render) renderRoleDashboard();
    return null;
  }
  state.productValidationLoading = true;
  if (render) renderRoleDashboard();
  try {
    state.productValidation = await fetchApiData("/api/ops/product-validation?window_days=30", { headers: apiHeaders() });
    state.productValidationError = null;
  } catch (error) {
    state.productValidation = makeMockProductValidation(error.message);
    state.productValidationError = error.message;
  } finally {
    state.productValidationLoading = false;
  }
  if (render) renderRoleDashboard();
  return state.productValidation;
}

function normalizeResearchSelection(data) {
  const reports = data?.reports || [];
  if (!reports.length) {
    state.selectedReportDate = null;
    return;
  }
  if (!state.selectedReportDate || !reports.some((report) => report.reportDate === state.selectedReportDate)) {
    state.selectedReportDate = reports[0].reportDate;
  }
}

async function loadResearchArchive({ render = true } = {}) {
  state.researchArchiveLoading = true;
  if (render) renderRoleDashboard();
  try {
    state.researchArchive = await fetchApiData("/api/reports/market/archive?limit=14");
    normalizeResearchSelection(state.researchArchive);
    state.researchArchiveError = null;
  } catch (error) {
    state.researchArchive = makeMockResearchArchive(error.message);
    normalizeResearchSelection(state.researchArchive);
    state.researchArchiveError = error.message;
  } finally {
    state.researchArchiveLoading = false;
  }
  if (render) renderRoleDashboard();
  return state.researchArchive;
}

async function refreshResearchFromLiveApi() {
  state.researchLiveRefreshLoading = true;
  state.researchLiveRefreshError = null;
  renderRoleDashboard();
  try {
    const scan = await fetchJson("/api/scan", { method: "POST" });
    state.researchLiveRefresh = {
      ...scan,
      refreshedAt: Math.floor(Date.now() / 1000),
      mode: "read-only-scan",
    };
    await loadResearchArchive({ render: false });
  } catch (error) {
    state.researchLiveRefreshError = error.message;
  } finally {
    state.researchLiveRefreshLoading = false;
    renderRoleDashboard();
  }
}

async function loadProductionReadiness({ render = true } = {}) {
  if (currentSession().role !== "admin") {
    state.productionReadiness = null;
    state.productionReadinessError = null;
    state.productionReadinessLoading = false;
    if (render) renderRoleDashboard();
    return null;
  }
  state.productionReadinessLoading = true;
  if (render) renderRoleDashboard();
  try {
    state.productionReadiness = await fetchApiData("/api/ops/production-readiness", { headers: apiHeaders() });
    state.productionReadinessError = null;
  } catch (error) {
    state.productionReadiness = makeUnavailableProductionReadiness(error.message);
    state.productionReadinessError = error.message;
  } finally {
    state.productionReadinessLoading = false;
  }
  if (render) renderRoleDashboard();
  return state.productionReadiness;
}

function assetLabel(id) {
  const labels = {
    0: "ALGO",
    31566704: "USDC",
    3169177585: "PNET",
    1290751153: "XDB",
    3436365167: "BSF",
    1893942045: "ELGSQ",
    1390638935: "Max",
    2644742542: "FUCKAI",
    3249403496: "BSB",
    3427156477: "crashout",
    1119722936: "THC",
    3410350791: "BLOBOB",
    846652486: "DERS",
    3427041827: "AURA",
    1674484158: "AETF",
    3227174563: "Pawbucks",
    3214347764: "DDAO",
    1115850955: "CAIN",
    3148132803: "GAAL",
    388592191: "CHIPS",
    793124631: "gALGO",
  };
  return labels[id] || `ASA ${id}`;
}

function ago(epochSeconds) {
  const seconds = Math.max(0, Math.floor(Date.now() / 1000 - epochSeconds));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}

function secondsLabel(value) {
  const seconds = Math.max(0, Number(value || 0));
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  return `${Math.round(seconds / 3600)}h`;
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function checkClass(check) {
  if (check.skipped) return "skipped";
  if (!check.blocking && !check.ok) return "waiting";
  return check.ok ? "passed" : "failed";
}

function checkLabel(check) {
  if (check.skipped) return "skipped";
  if (check.ok) return "ok";
  return check.blocking ? "fix" : "wait";
}

function gateLabel(reason) {
  const labels = {
    net_profit_after_fees_ok: "profit floor",
    profit_bps_ok: "bps floor",
    price_impact_ok: "price impact",
    trade_size_ok: "trade size",
    quote_freshness_ok: "quote freshness",
    fee_buffer_ok: "fee buffer",
    assets_allowlisted: "asset allowlist",
    app_ids_allowlisted: "app ID allowlist",
    own_funds_only: "own funds only",
    pool_reserves_ok: "pool reserves",
    route_leg_count_ok: "route length",
    pair_skipped_low_cross_venue_liquidity: "low cross-venue liquidity",
  };
  // Paper verified registry path: do not present app allowlist as the live blocker
  // when risk rules already passed app_ids_allowlisted.
  if (reason === "app_ids_allowlisted") {
    return "app ID not in paper verified registry";
  }
  return labels[reason] || String(reason || "unknown").replaceAll("_", " ");
}

function shortGateLabel(reason) {
  const label = gateLabel(reason);
  return label.length > 20 ? `${label.slice(0, 18)}...` : label;
}

function signedAmount(value, assetId) {
  const amount = Number(value || 0);
  const sign = amount > 0 ? "+" : "";
  return `${sign}${fmt.format(amount)} ${assetLabel(assetId)}`;
}

function setOptionalText(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}

function renderVersionLadder() {
  const target = document.getElementById("version-ladder");
  if (!target) return;
  target.innerHTML = versionLadder
    .map(
      (item) => `
        <article class="version-step ${item.state}">
          <span>${item.version}</span>
          <strong>${item.title}</strong>
          <em>${item.state === "done" ? "built" : item.state}</em>
          <p>${item.gate}</p>
        </article>`
    )
    .join("");
}

function gateStatusLabel(status) {
  const labels = {
    built: "built",
    built_locked: "built / locked",
    evidence_needed: "needs runtime proof",
    future: "future",
  };
  return labels[status] || String(status || "review");
}

function renderPhaseGates() {
  const target = document.getElementById("phase-gates");
  if (!target) return;
  const gates = state.phaseGates.length ? state.phaseGates : defaultPhaseGates;
  target.innerHTML = gates
    .map(
      (gate) => `
        <article class="phase-gate ${escapeHtml(gate.status)}">
          <span>Gate ${escapeHtml(gate.gate)}</span>
          <strong>${escapeHtml(gate.title)}</strong>
          <em>${escapeHtml(gateStatusLabel(gate.status))}</em>
          <p>${escapeHtml(gate.exitCriteria)}</p>
        </article>`
    )
    .join("");
}

function renderDeploymentModes() {
  const target = document.getElementById("deployment-modes");
  if (!target) return;
  const modes = state.deploymentModes.length ? state.deploymentModes : defaultDeploymentModes;
  target.innerHTML = modes
    .map(
      (mode) => `
        <article class="deployment-mode ${escapeHtml(mode.mode)}">
          <div>
            <span>${escapeHtml(mode.label)}</span>
            <strong>${escapeHtml(mode.summary)}</strong>
          </div>
          <dl>
            <div>
              <dt>Data</dt>
              <dd>${escapeHtml(mode.data)}</dd>
            </div>
            <div>
              <dt>Signer</dt>
              <dd>${escapeHtml(mode.signer)}</dd>
            </div>
            <div>
              <dt>Submission</dt>
              <dd>${escapeHtml(mode.submission)}</dd>
            </div>
            <div>
              <dt>Dashboard</dt>
              <dd>${escapeHtml(mode.dashboard)}</dd>
            </div>
          </dl>
          <div class="deployment-chip-row">
            ${(mode.capabilities || []).map((capability) => `<em>${escapeHtml(capability)}</em>`).join("")}
          </div>
        </article>`
    )
    .join("");
}

function renderRepoRedFlags() {
  const target = document.getElementById("repo-red-flags");
  if (!target) return;
  target.innerHTML = repoRedFlags
    .map(
      (item) => `
        <article class="red-flag-item">
          <span>Do not clone</span>
          <strong>${item.title}</strong>
          <p>${item.detail}</p>
        </article>`
    )
    .join("");
}

function renderProductThesis() {
  const target = document.getElementById("product-thesis");
  if (!target) return;
  const capabilities = state.productCapabilities.length ? state.productCapabilities : productThesis;
  target.innerHTML = capabilities
    .map(
      (item) => `
        <article class="thesis-item">
          <span>${escapeHtml(item.audience || item.label || "capability")}</span>
          <strong>${escapeHtml(item.label && item.audience ? item.label : item.title)}</strong>
          <em>${escapeHtml(item.status || "phase 0")}</em>
          <p>${escapeHtml(item.detail || "Capability detail pending.")}</p>
        </article>`
    )
    .join("");
}

function currentSession() {
  const live = state.walletConnection;
  if (live && live.address && (live.status === "connected" || live.status === "wrong_network")) {
    const backendNetwork = APP_CONFIG.NETWORK || "testnet";
    const wrong = live.status === "wrong_network" || live.network !== backendNetwork;
    const isAdmin = String(live.address).toUpperCase() === String(LOCAL_REVIEW_ADMIN_WALLET || "").toUpperCase();
    return {
      state: wrong ? "wrong_network" : "connected",
      role: isAdmin ? "admin" : "user",
      address: live.address,
      network: live.network || state.walletNetwork || backendNetwork,
      pnetBalance: live.pnetBalance == null ? 0 : Number(live.pnetBalance),
      credits: 0,
      optedIn: Boolean(live.pnetOptedIn),
      stateLabel: wrong
        ? "Wrong network"
        : live.status === "loading"
          ? "Connecting"
          : `Connected (${state.walletProvider || live.provider || "wallet"})`,
      detail: wrong
        ? `Backend is ${backendNetwork}; reconnect on the matching network.`
        : live.pnetMessage || "Connect-only account read. No signing or submission.",
      provider: live.provider || state.walletProvider,
      algoBalance: live.algoBalance,
      pnetMessage: live.pnetMessage,
      live: true,
    };
  }
  if (live && live.status === "loading") {
    return {
      ...(walletPresets.guest || {}),
      state: "loading",
      role: "guest",
      address: null,
      network: APP_CONFIG.NETWORK || state.walletNetwork || "testnet",
      pnetBalance: 0,
      credits: 0,
      optedIn: false,
      stateLabel: "Connecting",
      detail: `Connecting ${currentWalletProvider().label}…`,
      live: true,
    };
  }
  if (live && (live.status === "wrong_network" || live.status === "rejected" || live.status === "unavailable")) {
    return {
      ...(walletPresets.guest || {}),
      state: live.status,
      role: "guest",
      address: null,
      network: APP_CONFIG.NETWORK || state.walletNetwork || "testnet",
      pnetBalance: 0,
      credits: 0,
      optedIn: false,
      stateLabel:
        live.status === "wrong_network"
          ? "Wrong network"
          : live.status === "unavailable"
            ? "Wallet unavailable"
            : "Connection rejected",
      detail: live.error || "Wallet connection failed.",
      live: true,
    };
  }
  // Demo presets only when explicitly enabled (?demoWallets=1).
  if (SHOW_WALLET_PRESET_CONTROLS && state.walletPreset && state.walletPreset !== "guest") {
    const session = walletPresets[state.walletPreset] || walletPresets.guest;
    return {
      ...session,
      network: state.walletNetwork || session.network || APP_CONFIG.NETWORK,
      live: false,
    };
  }
  const session = walletPresets.guest;
  return {
    ...session,
    network: APP_CONFIG.NETWORK || state.walletNetwork || session.network,
    live: false,
  };
}

function currentWalletProvider() {
  return walletProviders[state.walletProvider] || walletProviders.pera;
}

function currentWalletNetwork() {
  return walletNetworks[state.walletNetwork] || walletNetworks[APP_CONFIG.NETWORK] || walletNetworks.testnet;
}

async function loadWalletSdk(providerKey) {
  if (_walletSdkCache[providerKey]) return _walletSdkCache[providerKey];
  const url = WALLET_SDK_URLS[providerKey];
  if (!url) throw new Error(`unsupported_wallet_provider:${providerKey}`);
  const mod = await import(/* webpackIgnore: true */ url);
  if (providerKey === "pera") {
    const Ctor = mod.PeraWalletConnect || mod.default?.PeraWalletConnect || mod.default;
    if (!Ctor) throw new Error("pera_sdk_unavailable");
    _walletSdkCache.pera = Ctor;
    return Ctor;
  }
  const Ctor = mod.DeflyWalletConnect || mod.default?.DeflyWalletConnect || mod.default;
  if (!Ctor) throw new Error("defly_sdk_unavailable");
  _walletSdkCache.defly = Ctor;
  return Ctor;
}

function backendChainId() {
  return Number(APP_CONFIG.CHAIN_ID || ALGORAND_CHAIN_IDS[APP_CONFIG.NETWORK] || ALGORAND_CHAIN_IDS.testnet);
}

function assertNetworkMatchesBackend(selectedNetwork) {
  const backend = String(APP_CONFIG.NETWORK || "testnet").toLowerCase();
  const selected = String(selectedNetwork || "").toLowerCase();
  if (selected && selected !== backend) {
    const err = new Error(
      `Wallet/network mismatch: backend is ${backend}; UI selected ${selected}. Switch the selector to ${backend} or reconnect on the backend network.`
    );
    err.code = "WALLET_NETWORK_MISMATCH";
    throw err;
  }
  return backend;
}

async function connectSelectedWallet() {
  const providerKey = state.walletProvider || "pera";
  const provider = currentWalletProvider();
  state.walletConnection = {
    ...state.walletConnection,
    status: "loading",
    provider: providerKey,
    error: null,
  };
  state.operatorNotice = `Connecting ${provider.label} (connect-only, no signing)…`;
  renderWalletSession();
  try {
    const backendNetwork = assertNetworkMatchesBackend(state.walletNetwork || APP_CONFIG.NETWORK);
    const chainId = backendChainId();
    const Ctor = await loadWalletSdk(providerKey);
    // Disconnect any prior client before opening a new session.
    if (_activeWalletClient && typeof _activeWalletClient.disconnect === "function") {
      try {
        await _activeWalletClient.disconnect();
      } catch (_e) {
        /* ignore prior disconnect errors */
      }
    }
    const client = new Ctor({ chainId });
    _activeWalletClient = client;
    let accounts = [];
    if (typeof client.reconnectSession === "function") {
      try {
        const existing = await client.reconnectSession();
        if (Array.isArray(existing) && existing.length) accounts = existing;
      } catch (_e) {
        /* fall through to fresh connect */
      }
    }
    if (!accounts.length) {
      accounts = await client.connect();
    }
    if (client.connector && typeof client.connector.on === "function") {
      client.connector.on("disconnect", handleRemoteWalletDisconnect);
    }
    const address = Array.isArray(accounts) ? accounts[0] : accounts?.addr || accounts;
    if (!address || typeof address !== "string") {
      throw new Error("wallet_returned_no_address");
    }
    await syncConnectedAccount({
      address,
      provider: providerKey,
      network: backendNetwork,
      chainId,
    });
    try {
      localStorage.setItem(WALLET_PROVIDER_STORAGE_KEY, providerKey);
    } catch (_e) {
      /* optional preference only */
    }
    state.operatorNotice = `${provider.label} connected on ${backendNetwork}. Account state is read-only.`;
  } catch (error) {
    const message = error?.message || String(error);
    const rejected = /reject|cancel|denied|closed/i.test(message);
    const unavailable = /sdk_unavailable|Failed to fetch|import|not found|unsupported/i.test(message);
    const mismatch = error?.code === "WALLET_NETWORK_MISMATCH" || /mismatch/i.test(message);
    state.walletConnection = {
      status: mismatch ? "wrong_network" : rejected ? "rejected" : unavailable ? "unavailable" : "rejected",
      provider: providerKey,
      address: null,
      network: APP_CONFIG.NETWORK,
      chainId: backendChainId(),
      algoBalance: null,
      pnetBalance: null,
      pnetOptedIn: null,
      pnetMessage: APP_CONFIG.PNET_MESSAGE || null,
      error: message,
      lastSyncedAt: null,
    };
    state.operatorNotice = mismatch
      ? `Wrong network: ${message}`
      : unavailable
        ? `${provider.label} unavailable: ${message}`
        : rejected
          ? `${provider.label} connection rejected.`
          : `Wallet connection failed: ${message}`;
  }
  renderWalletSession();
  renderRoleDashboard();
}

async function restoreWalletSession() {
  if (state.walletReconnectAttempted || state.walletConnection?.status !== "disconnected") return;
  state.walletReconnectAttempted = true;
  let providerKey = state.walletProvider || "pera";
  try {
    const storedProvider = localStorage.getItem(WALLET_PROVIDER_STORAGE_KEY);
    if (storedProvider && walletProviders[storedProvider]) providerKey = storedProvider;
  } catch (_e) {
    /* optional preference only */
  }
  state.walletProvider = providerKey;
  try {
    const backendNetwork = assertNetworkMatchesBackend(APP_CONFIG.NETWORK);
    const chainId = backendChainId();
    const Ctor = await loadWalletSdk(providerKey);
    const client = new Ctor({ chainId });
    const accounts = await client.reconnectSession();
    if (!Array.isArray(accounts) || !accounts.length) return;
    _activeWalletClient = client;
    if (client.connector && typeof client.connector.on === "function") {
      client.connector.on("disconnect", handleRemoteWalletDisconnect);
    }
    await syncConnectedAccount({ address: accounts[0], provider: providerKey, network: backendNetwork, chainId });
    state.operatorNotice = `${currentWalletProvider().label} session restored on ${backendNetwork} (connect-only).`;
    renderWalletSession();
    renderRoleDashboard();
  } catch (_e) {
    _activeWalletClient = null;
  }
}

function handleRemoteWalletDisconnect() {
  _activeWalletClient = null;
  state.walletConnection = {
    status: "disconnected",
    provider: null,
    address: null,
    network: APP_CONFIG.NETWORK || "testnet",
    chainId: backendChainId(),
    algoBalance: null,
    pnetBalance: null,
    pnetOptedIn: null,
    pnetMessage: APP_CONFIG.PNET_MESSAGE || null,
    error: null,
    lastSyncedAt: null,
  };
  state.walletPreset = "guest";
  state.operatorNotice = "Wallet session disconnected. Reconnect anytime (connect-only).";
  renderWalletSession();
  renderRoleDashboard();
}

async function syncConnectedAccount({ address, provider, network, chainId }) {
  const params = new URLSearchParams({
    network: network || APP_CONFIG.NETWORK,
    provider: provider || state.walletProvider || "pera",
  });
  if (chainId) params.set("chain_id", String(chainId));
  const account = await fetchApiData(`/api/wallet/account/${encodeURIComponent(address)}?${params.toString()}`);
  state.walletConnection = {
    status: "connected",
    provider: provider || state.walletProvider,
    address: account.address || address,
    network: account.network || network || APP_CONFIG.NETWORK,
    chainId: account.chainId || chainId || backendChainId(),
    algoBalance: account.algoBalance,
    pnetBalance: account.pnetBalance,
    pnetOptedIn: account.pnetOptedIn,
    pnetMessage: account.pnetMessage || APP_CONFIG.PNET_MESSAGE || null,
    error: null,
    lastSyncedAt: Date.now(),
  };
  state.walletNetwork = state.walletConnection.network;
  state.walletPreset = "guest";
}

async function disconnectWallet() {
  const provider = currentWalletProvider();
  try {
    if (_activeWalletClient && typeof _activeWalletClient.disconnect === "function") {
      await _activeWalletClient.disconnect();
    }
  } catch (_e) {
    /* ignore */
  }
  _activeWalletClient = null;
  state.walletConnection = {
    status: "disconnected",
    provider: null,
    address: null,
    network: APP_CONFIG.NETWORK || "testnet",
    chainId: backendChainId(),
    algoBalance: null,
    pnetBalance: null,
    pnetOptedIn: null,
    pnetMessage: APP_CONFIG.PNET_MESSAGE || null,
    error: null,
    lastSyncedAt: null,
  };
  state.walletPreset = "guest";
  state.operatorNotice = `${provider.label} disconnected. Reconnect anytime (connect-only).`;
  renderWalletSession();
  renderRoleDashboard();
}

async function toggleWalletConnection() {
  const live = state.walletConnection;
  if (live && live.address && live.status === "connected") {
    await disconnectWallet();
    return;
  }
  await connectSelectedWallet();
}

function shortAddress(address) {
  if (!address) return "No wallet connected";
  if (address.length <= 14) return address;
  return `${address.slice(0, 6)}...${address.slice(-5)}`;
}

function statusChip(label, status = "info") {
  return `<span class="status-chip ${escapeHtml(status)}">${escapeHtml(label)}</span>`;
}

function SourceBadge(source) {
  const value = source || "unavailable";
  return `<span class="source-badge ${escapeHtml(value)}">${escapeHtml(value)}</span>`;
}

function provenanceMetricKeyForLabel(label) {
  const key = String(label || "").toLowerCase();
  const map = {
    "pools scanned": "scanner.pool_count",
    "pool snapshots": "scanner.snapshot_count",
    "quote legs": "quote.count",
    "fresh quotes": "quote.fresh_count",
    "avg impact": "quote.avg_price_impact_bps",
    "average price impact": "quote.avg_price_impact_bps",
    "route candidates": "route.count",
    "routes": "route.count",
    "opportunities": "route.count",
    "approved routes": "route.approved_count",
    "rejected routes": "route.rejected_count",
    "expected net": "route.expected_net_profit",
    "net": "route.expected_net_profit",
    "profit bps": "route.expected_profit_bps",
    "confidence": "route.confidence_score",
    "route confidence": "route.confidence_score",
    "price impact": "route.price_impact_bps",
    "paper candidates": "paper.count",
    "candidates": "paper.count",
    "30s paper checks": "paper.checked_30s_count",
    "sim 30s net": "paper.checked_30s_count",
    "risk decisions": "risk.decision_count",
    "risk rejections": "risk.rejected_count",
    "live state": "live.state",
  };
  return map[key] || null;
}

function TraceableMetricArticle({ label, value, source = "unavailable", metricKey = null, routeHash = null, className = "" }) {
  const key = metricKey || provenanceMetricKeyForLabel(label);
  const isAdmin = currentSession().role === "admin";
  const tag = isAdmin && key ? "button" : "article";
  const attrs =
    isAdmin && key
      ? `type="button" data-provenance-metric="${escapeHtml(key)}"${routeHash ? ` data-provenance-route-hash="${escapeHtml(routeHash)}"` : ""}`
      : "";
  return `
    <${tag} class="${escapeHtml(className || "control-metric")} ${isAdmin && key ? "traceable-metric" : ""}" ${attrs}>
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(String(value))}</strong>
      ${source ? SourceBadge(source) : ""}
    </${tag}>`;
}

function FreshnessBadge(seconds) {
  if (seconds === null || seconds === undefined) {
    return `<span class="freshness-badge unavailable">freshness unavailable</span>`;
  }
  const value = Number(seconds);
  const tone = value <= 30 ? "ok" : value <= 300 ? "wait" : "blocked";
  return `<span class="freshness-badge ${tone}">${secondsLabel(value)} fresh</span>`;
}

function lastOpsRefreshLabel() {
  if (!state.opsLastLoadedAt) return "waiting for first refresh";
  return `updated ${state.opsLastLoadedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}`;
}

function deltaBadge(value, label) {
  const numeric = Number(value || 0);
  if (!numeric) return "";
  const sign = numeric > 0 ? "+" : "";
  const tone = numeric > 0 ? "up" : "down";
  return `<span class="delta-badge ${tone}">${escapeHtml(label)} ${sign}${fmt.format(numeric)}</span>`;
}

function serviceTone(status) {
  if (status === "ok") return "ok";
  if (status === "error" || status === "blocked") return "blocked";
  if (status === "disabled") return "disabled";
  return "wait";
}

function controlRoomData() {
  return state.opsControlRoom || makeMockOpsControlRoom("Control Room has not loaded backend ops telemetry yet.");
}

function makeUnavailableProductionReadiness(message = "Production readiness endpoint unavailable.") {
  return {
    currentPhase: "Unavailable",
    currentPhaseKey: "unavailable",
    overallPercent: 0,
    nextGate: "Backend evidence endpoint",
    blockingItems: [message],
    passedEvidenceCount: 0,
    totalEvidenceCount: 0,
    phases: [],
    gates: [],
    evidence: [],
    generatedAt: null,
    source: "unavailable",
  };
}

function makeMockReplayLab(message = "Replay endpoint unavailable.") {
  const now = Math.floor(Date.now() / 1000);
  const buildReplay = ({ id, routeHash, verdict, expectedProfit, simulatedProfit5s, simulatedProfit30s, quoteDecay30s, routeConfidence, skipReason }) => {
    const quoteDecay5s = quoteDecay30s / 3;
    const priceImpactBps = 24 + (100 - routeConfidence) * 0.18;
    const poolLiquidityStart = 182000 + routeConfidence * 700;
    const poolLiquidityLatest = poolLiquidityStart - quoteDecay30s * 1400;
    const timeline = [
      {
        key: "t0",
        label: "T0 detected",
        dueAt: now - 45,
        checkedAt: now - 45,
        status: "detected",
        expectedProfit,
        simulatedProfit: null,
        quoteDecay: 0,
        expectedVsSimulatedProfit: null,
        priceImpactBps,
        priceImpactChangeBps: 0,
        poolLiquidity: poolLiquidityStart,
        poolLiquidityChange: 0,
        routeConfidence,
      },
      {
        key: "t5",
        label: "T+5s recheck",
        dueAt: now - 40,
        checkedAt: now - 39,
        status: "checked",
        expectedProfit,
        simulatedProfit: simulatedProfit5s,
        quoteDecay: quoteDecay5s,
        expectedVsSimulatedProfit: expectedProfit - simulatedProfit5s,
        priceImpactBps: priceImpactBps + quoteDecay5s * 8,
        priceImpactChangeBps: quoteDecay5s * 8,
        poolLiquidity: poolLiquidityStart - quoteDecay5s * 1400,
        poolLiquidityChange: -quoteDecay5s * 1400,
        routeConfidence,
      },
      {
        key: "t30",
        label: "T+30s recheck",
        dueAt: now - 15,
        checkedAt: now - 14,
        status: "checked",
        expectedProfit,
        simulatedProfit: simulatedProfit30s,
        quoteDecay: quoteDecay30s,
        expectedVsSimulatedProfit: expectedProfit - simulatedProfit30s,
        priceImpactBps: priceImpactBps + quoteDecay30s * 8,
        priceImpactChangeBps: quoteDecay30s * 8,
        poolLiquidity: poolLiquidityLatest,
        poolLiquidityChange: poolLiquidityLatest - poolLiquidityStart,
        routeConfidence,
      },
    ];
    return {
      id,
      paperTradeId: id,
      routeHash,
      detectedAt: now - 45,
      inputAssetId: 0,
      inputAmount: 10,
      expectedFinalAmount: 10 + expectedProfit,
      expectedProfit,
      simulatedProfit5s,
      simulatedProfit30s,
      quoteDecay5s,
      quoteDecay30s,
      priceImpactBps,
      priceImpactChangeBps: timeline[2].priceImpactChangeBps,
      poolLiquidityStart,
      poolLiquidityLatest,
      poolLiquidityChange: poolLiquidityLatest - poolLiquidityStart,
      routeConfidence,
      wouldExecute: verdict === "would_execute",
      opportunityStatus: "mock",
      skipReason,
      lastError: null,
      verdict,
      verdictReason:
        verdict === "would_execute"
          ? "Mock replay: edge survived the 30s check."
          : verdict === "stale"
            ? "Mock replay: 30s evidence went stale before review."
            : "Mock replay: risk or decay removed the edge.",
      route: [
        {
          venue: "tinyman",
          pool_id: "mock-tinyman-algo-usdc",
          app_id: "mock-reviewed",
          input_asset_id: 0,
          output_asset_id: 31566704,
          input_amount: 10,
          expected_output: 20.02,
          price_impact_bps: priceImpactBps / 2,
        },
        {
          venue: "pact",
          pool_id: "mock-pact-usdc-algo",
          app_id: "mock-reviewed",
          input_asset_id: 31566704,
          output_asset_id: 0,
          input_amount: 20.02,
          expected_output: 10 + expectedProfit,
          price_impact_bps: priceImpactBps / 2,
        },
      ],
      timeline,
      source: "mock",
    };
  };
  const replays = [
    buildReplay({
      id: "mock-replay-1",
      routeHash: "mock-algo-usdc-survived",
      verdict: "would_execute",
      expectedProfit: 0.0375,
      simulatedProfit5s: 0.0331,
      simulatedProfit30s: 0.0264,
      quoteDecay30s: 0.0111,
      routeConfidence: 82,
      skipReason: null,
    }),
    buildReplay({
      id: "mock-replay-2",
      routeHash: "mock-algo-usdc-decayed",
      verdict: "would_skip",
      expectedProfit: 0.021,
      simulatedProfit5s: 0.004,
      simulatedProfit30s: -0.006,
      quoteDecay30s: 0.027,
      routeConfidence: 61,
      skipReason: "net_profit_after_fees_ok",
    }),
    buildReplay({
      id: "mock-replay-3",
      routeHash: "mock-route-stale",
      verdict: "stale",
      expectedProfit: 0.018,
      simulatedProfit5s: 0.012,
      simulatedProfit30s: 0.003,
      quoteDecay30s: 0.015,
      routeConfidence: 54,
      skipReason: "quote_freshness_ok",
    }),
  ];
  return {
    replays,
    count: replays.length,
    compareDefaults: replays.slice(0, 3).map((item) => item.id),
    verdictCounts: { would_execute: 1, would_skip: 1, stale: 1, unsafe: 0 },
    source: "mock",
    liveExecutionTouched: false,
    signerCodeTouched: false,
    note: message,
  };
}

function makeMockRouteForensics(message = "Route forensics endpoint unavailable.") {
  const now = Math.floor(Date.now() / 1000);
  const buildRoute = ({ id, hash, decision, rejectionReason, net, bps, freshness, impact, liquidity, confidence }) => {
    const approved = decision === "approved";
    const routePath = [
      {
        index: 0,
        venue: "tinyman",
        poolId: "mock-tinyman-algo-usdc",
        inputAssetId: 0,
        outputAssetId: 31566704,
        inputAmount: 10,
        expectedOutput: 20.01,
        feeAmount: 0.03,
        priceImpactBps: impact / 2,
        capturedAt: now - freshness,
        expiresAt: now + Math.max(0, 5 - freshness),
      },
      {
        index: 1,
        venue: "pact",
        poolId: "mock-pact-usdc-algo",
        inputAssetId: 31566704,
        outputAssetId: 0,
        inputAmount: 20.01,
        expectedOutput: 10 + net,
        feeAmount: 0.02,
        priceImpactBps: impact / 2,
        capturedAt: now - freshness,
        expiresAt: now + Math.max(0, 5 - freshness),
      },
    ];
    const riskRules = {
      quote_freshness_ok: freshness <= 5,
      net_profit_after_fees_ok: net > 0.25,
      profit_bps_ok: bps >= 35,
      price_impact_ok: impact <= 50,
      assets_allowlisted: true,
      app_ids_allowlisted: approved,
      trade_size_ok: true,
    };
    const failedRules = Object.entries(riskRules)
      .filter(([, passed]) => !passed)
      .map(([key]) => key);
    const decisionTree = [
      ["route_path", "Route path stored", true, "2 legs recorded."],
      ["quote_freshness", "Quote freshness checked", riskRules.quote_freshness_ok, `${freshness}s old.`],
      ["profitability", "Profitability calculated", riskRules.net_profit_after_fees_ok, `${fmt.format(net)} net expected.`],
      ["price_impact", "Price impact calculated", riskRules.price_impact_ok, `${fmt.format(impact)} bps max impact.`],
      ["liquidity_score", "Liquidity scored", true, `${fmt.format(liquidity)} liquidity score.`],
      ["risk_result", "Risk policy evaluated", approved, approved ? "Risk approved the route." : `Rejected: ${gateLabel(rejectionReason)}.`],
      ["approval_decision", "Final route decision", approved, approved ? "Approved for paper/dry-run review only." : "Rejected before dry-run."],
    ].map(([key, label, passed, detail]) => ({ key, label, status: passed ? "pass" : "fail", detail }));
    return {
      id,
      routeHash: hash,
      opportunityId: id,
      routePath,
      routePathLabel: "0 -> 31566704 -> 0",
      profitability: {
        inputAmount: 10,
        expectedFinalAmount: 10 + net,
        grossProfit: net + 0.08,
        estimatedNetworkFee: 0.006,
        totalDexFees: 0.05,
        slippageBuffer: 0.024,
        expectedNetProfit: net,
        expectedProfitBps: bps,
        profitableAfterFees: net > 0,
      },
      quoteFreshness: {
        status: freshness <= 5 ? "fresh" : "stale",
        maxAgeSeconds: freshness,
        secondsToExpiry: Math.max(0, 5 - freshness),
        fresh: freshness <= 5,
        detail: freshness <= 5 ? "Mock quote is inside the freshness window." : "Mock quote is stale.",
      },
      priceImpact: {
        totalBps: impact,
        maxBps: impact / 2,
        perLeg: routePath.map((leg) => ({
          index: leg.index,
          venue: leg.venue,
          poolId: leg.poolId,
          priceImpactBps: leg.priceImpactBps,
        })),
      },
      liquidityScore: {
        score: liquidity,
        status: liquidity >= 75 ? "ok" : "watch",
        totalLiquidity: 120000,
        minLegLiquidity: 58000,
        poolCount: 2,
        missingPoolIds: [],
        detail: "Mock liquidity from stored-style pool snapshots.",
      },
      riskResult: {
        approved,
        status: approved ? "approved" : "rejected",
        reason: approved ? null : rejectionReason,
        rules: riskRules,
        passedRules: Object.entries(riskRules)
          .filter(([, passed]) => passed)
          .map(([key]) => key),
        failedRules,
      },
      approvalDecision: {
        decision,
        approved,
        status: decision,
        detail: approved ? "Approved for paper/dry-run review only." : "Rejected by mock risk policy.",
      },
      rejectionReason: approved ? "none" : rejectionReason,
      confidenceCalculation: {
        score: confidence,
        computedScore: confidence,
        storedScore: confidence,
        components: [
          { key: "price_impact", label: "Price impact", weight: 0.25, score: Math.max(0, 100 - impact) },
          { key: "quote_freshness", label: "Quote freshness", weight: 0.2, score: freshness <= 5 ? 100 : 0 },
          { key: "profitability", label: "Profitability", weight: 0.2, score: Math.max(0, Math.min(100, bps)) },
          { key: "liquidity", label: "Liquidity", weight: 0.15, score: liquidity },
          { key: "risk_policy", label: "Risk policy", weight: 0.2, score: approved ? 100 : 55 },
        ],
      },
      decisionTree,
      completeness: {
        complete: true,
        missingFields: [],
      },
      source: "mock",
      createdAt: now - id * 30,
    };
  };
  const routes = [
    buildRoute({ id: 1, hash: "mock-forensics-approved", decision: "approved", rejectionReason: "none", net: 0.34, bps: 340, freshness: 2, impact: 28, liquidity: 88, confidence: 86 }),
    buildRoute({ id: 2, hash: "mock-forensics-profit-block", decision: "rejected", rejectionReason: "net_profit_after_fees_ok", net: 0.04, bps: 22, freshness: 3, impact: 32, liquidity: 76, confidence: 58 }),
    buildRoute({ id: 3, hash: "mock-forensics-stale", decision: "rejected", rejectionReason: "quote_freshness_ok", net: 0.29, bps: 81, freshness: 11, impact: 44, liquidity: 67, confidence: 49 }),
  ];
  return {
    routes,
    count: routes.length,
    summary: {
      routeCount: routes.length,
      completeCount: routes.length,
      approvedCount: 1,
      rejectedCount: 2,
      rejectionReasons: [
        { reason: "net_profit_after_fees_ok", count: 1 },
        { reason: "quote_freshness_ok", count: 1 },
      ],
    },
    decisionCounts: { approved: 1, rejected: 2, complete: routes.length, total: routes.length },
    compareDefaults: routes.map((item) => item.id),
    source: "mock",
    liveExecutionTouched: false,
    signerCodeTouched: false,
    note: message,
  };
}

function makeMockConfidenceCalibration(message = "Confidence calibration endpoint unavailable.") {
  const now = Math.floor(Date.now() / 1000);
  const buckets = [
    ["0.90-1.00", 0.9, 1.0, 11, 9, 0.012, 0.072],
    ["0.80-0.89", 0.8, 0.89, 14, 9, 0.018, 0.041],
    ["0.70-0.79", 0.7, 0.79, 12, 5, 0.026, 0.013],
    ["0.60-0.69", 0.6, 0.69, 8, 2, 0.031, -0.006],
    ["0.50-0.59", 0.5, 0.59, 4, 1, 0.044, -0.018],
    ["0.00-0.49", 0.0, 0.49, 3, 0, 0.062, -0.029],
  ].map(([label, minConfidence, maxConfidence, count, successCount, averageQuoteDecay, averageSimulatedProfit]) => {
    const successRate = count ? successCount / count : 0;
    const averageConfidence = (minConfidence + maxConfidence) / 2;
    return {
      label,
      minConfidence,
      maxConfidence,
      count,
      successCount,
      failureCount: count - successCount,
      successRate,
      averageConfidence,
      calibrationError: Math.abs(successRate - averageConfidence),
      averageQuoteDecay,
      averageExpectedProfit: Math.max(0.01, averageSimulatedProfit + averageQuoteDecay),
      averageSimulatedProfit,
    };
  });
  const resolvedCount = buckets.reduce((sum, bucket) => sum + bucket.count, 0);
  const successCount = buckets.reduce((sum, bucket) => sum + bucket.successCount, 0);
  const weightedConfidence = buckets.reduce((sum, bucket) => sum + bucket.averageConfidence * bucket.count, 0);
  const weightedError = buckets.reduce((sum, bucket) => sum + bucket.calibrationError * bucket.count, 0);
  return {
    buckets,
    summary: {
      paperTradeCount: resolvedCount + 5,
      resolvedCount,
      successCount,
      failureCount: resolvedCount - successCount,
      overallSuccessRate: resolvedCount ? successCount / resolvedCount : 0,
      averageConfidence: resolvedCount ? weightedConfidence / resolvedCount : 0,
      calibrationError: resolvedCount ? weightedError / resolvedCount : 0,
      verdict: "watch",
      verdictDetail: `Mock fallback only: ${message}. Use stored paper-trade history before adjusting confidence math.`,
    },
    sampleTrades: [
      {
        paperTradeId: "mock-paper-104",
        routeHash: "mock-high-confidence-win",
        confidence: 0.94,
        confidenceScore: 0.94,
        expectedProfit: 0.087,
        simulatedProfit: 0.061,
        quoteDecay: 0.019,
        success: true,
        resolved: true,
        checkpoint: "30s",
        createdAt: now - 240,
      },
      {
        paperTradeId: "mock-paper-103",
        routeHash: "mock-mid-confidence-decay",
        confidence: 0.77,
        confidenceScore: 0.77,
        expectedProfit: 0.044,
        simulatedProfit: -0.006,
        quoteDecay: 0.052,
        success: false,
        resolved: true,
        checkpoint: "30s",
        createdAt: now - 620,
      },
      {
        paperTradeId: "mock-paper-102",
        routeHash: "mock-pending-paper-check",
        confidence: 0.86,
        confidenceScore: 0.86,
        expectedProfit: 0.038,
        simulatedProfit: null,
        quoteDecay: null,
        success: false,
        resolved: false,
        checkpoint: "pending",
        createdAt: now - 75,
      },
    ],
    source: "mock",
    liveExecutionTouched: false,
    signerCodeTouched: false,
  };
}

function makeMockOpportunityDecay(message = "Opportunity decay endpoint unavailable.", view = "24h") {
  const selectedView = ["1h", "24h", "7d"].includes(view) ? view : "24h";
  const now = Math.floor(Date.now() / 1000);
  const records = [
    {
      routeHash: "mock-fast-decay",
      pairLabel: "ALGO/USDC",
      venues: ["tinyman", "pact"],
      routeType: "venue_arbitrage",
      expectedProfit: 0.086,
      expectedProfit5s: 0.038,
      expectedProfit30s: -0.004,
      expectedProfit60s: -0.009,
      halfLifeSeconds: 4.4,
      halfLifeObserved: true,
      latestObservedSeconds: 60,
      latestProfit: -0.009,
      decayRatio: 1.1,
      actionable: false,
      detectedAt: now - 420,
      source: "mock",
    },
    {
      routeHash: "mock-slow-decay",
      pairLabel: "ALGO/PNET",
      venues: ["tinyman"],
      routeType: "single_venue",
      expectedProfit: 0.052,
      expectedProfit5s: 0.047,
      expectedProfit30s: 0.032,
      expectedProfit60s: 0.021,
      halfLifeSeconds: 46.4,
      halfLifeObserved: true,
      latestObservedSeconds: 60,
      latestProfit: 0.021,
      decayRatio: 0.596,
      actionable: true,
      detectedAt: now - 980,
      source: "mock",
    },
    {
      routeHash: "mock-censored",
      pairLabel: "USDC/PNET",
      venues: ["pact"],
      routeType: "single_venue",
      expectedProfit: 0.034,
      expectedProfit5s: 0.032,
      expectedProfit30s: 0.029,
      expectedProfit60s: null,
      halfLifeSeconds: 30,
      halfLifeObserved: false,
      latestObservedSeconds: 30,
      latestProfit: 0.029,
      decayRatio: 0.147,
      actionable: true,
      detectedAt: now - 140,
      source: "mock",
    },
  ];
  const timeline = Array.from({ length: selectedView === "7d" ? 14 : selectedView === "24h" ? 24 : 12 }, (_, index) => ({
    index,
    label: selectedView === "7d" ? `D-${Math.max(0, 13 - index)}` : `${index}`,
    opportunityCount: index % 5 === 0 ? 2 : index % 3 === 0 ? 1 : 0,
    averageHalfLifeSeconds: index % 5 === 0 ? 18 : index % 3 === 0 ? 34 : 0,
    medianHalfLifeSeconds: index % 5 === 0 ? 15 : index % 3 === 0 ? 31 : 0,
    averageDecayRatio: index % 5 === 0 ? 0.72 : index % 3 === 0 ? 0.38 : 0,
  }));
  return {
    view: selectedView,
    views: ["1h", "24h", "7d"],
    windowSeconds: selectedView === "1h" ? 3600 : selectedView === "7d" ? 604800 : 86400,
    generatedAt: now,
    summary: {
      opportunityCount: records.length,
      resolvedCount: records.length,
      observedHalfLifeCount: 2,
      resolved60sCount: 2,
      averageHalfLifeSeconds: 26.9,
      medianHalfLifeSeconds: 30,
      fastestDecay: {
        routeHash: "mock-fast-decay",
        pairLabel: "ALGO/USDC",
        routeType: "venue_arbitrage",
        halfLifeSeconds: 4.4,
        expectedProfit: 0.086,
        latestProfit: -0.009,
      },
      slowestDecay: {
        routeHash: "mock-slow-decay",
        pairLabel: "ALGO/PNET",
        routeType: "single_venue",
        halfLifeSeconds: 46.4,
        expectedProfit: 0.052,
        latestProfit: 0.021,
      },
      actionableCount: 2,
      averageDecayRatio: 0.614,
    },
    timeline,
    byPair: [
      { label: "ALGO/USDC", opportunityCount: 1, averageHalfLifeSeconds: 4.4, medianHalfLifeSeconds: 4.4, fastestHalfLifeSeconds: 4.4, slowestHalfLifeSeconds: 4.4, averageDecayRatio: 1.1, actionableCount: 0 },
      { label: "ALGO/PNET", opportunityCount: 1, averageHalfLifeSeconds: 46.4, medianHalfLifeSeconds: 46.4, fastestHalfLifeSeconds: 46.4, slowestHalfLifeSeconds: 46.4, averageDecayRatio: 0.596, actionableCount: 1 },
    ],
    byVenue: [
      { label: "tinyman", opportunityCount: 2, averageHalfLifeSeconds: 25.4, medianHalfLifeSeconds: 25.4, fastestHalfLifeSeconds: 4.4, slowestHalfLifeSeconds: 46.4, averageDecayRatio: 0.848, actionableCount: 1 },
      { label: "pact", opportunityCount: 2, averageHalfLifeSeconds: 17.2, medianHalfLifeSeconds: 17.2, fastestHalfLifeSeconds: 4.4, slowestHalfLifeSeconds: 30, averageDecayRatio: 0.624, actionableCount: 1 },
    ],
    byRouteType: [
      { label: "single_venue", opportunityCount: 2, averageHalfLifeSeconds: 38.2, medianHalfLifeSeconds: 38.2, fastestHalfLifeSeconds: 30, slowestHalfLifeSeconds: 46.4, averageDecayRatio: 0.372, actionableCount: 2 },
      { label: "venue_arbitrage", opportunityCount: 1, averageHalfLifeSeconds: 4.4, medianHalfLifeSeconds: 4.4, fastestHalfLifeSeconds: 4.4, slowestHalfLifeSeconds: 4.4, averageDecayRatio: 1.1, actionableCount: 0 },
    ],
    records,
    source: "mock",
    liveExecutionTouched: false,
    signerCodeTouched: false,
    note: message,
  };
}

function heatmapCellKey(cell) {
  if (!cell) return "";
  return `${cell.pairKey}|${cell.venue}|${cell.bucketIndex}`;
}

function normalizeHeatmapSelection(data) {
  const cells = data?.cells || [];
  if (!cells.length) {
    state.selectedHeatmapCellKey = null;
    return;
  }
  if (!state.selectedHeatmapCellKey || !cells.some((cell) => heatmapCellKey(cell) === state.selectedHeatmapCellKey)) {
    state.selectedHeatmapCellKey = heatmapCellKey(cells[0]);
  }
}

function makeMockMarketHeatmap(message = "Market heatmap endpoint unavailable.", view = "24h") {
  const now = Math.floor(Date.now() / 1000);
  const views = ["1h", "6h", "24h", "7d"];
  const bucketCount = view === "7d" ? 14 : view === "24h" ? 24 : 12;
  const windowSeconds = view === "1h" ? 3600 : view === "6h" ? 21600 : view === "7d" ? 604800 : 86400;
  const bucketSeconds = Math.floor(windowSeconds / bucketCount);
  const start = now - windowSeconds;
  const timeBuckets = Array.from({ length: bucketCount }, (_, index) => ({
    index,
    startAt: start + index * bucketSeconds,
    endAt: start + (index + 1) * bucketSeconds,
    label: new Date((start + index * bucketSeconds) * 1000).toISOString().slice(11, 16),
  }));
  const pairs = [
    { pairKey: "0-31566704", pairLabel: "0/31566704", assetIds: [0, 31566704] },
    { pairKey: "0-3169177585", pairLabel: "0/3169177585", assetIds: [0, 3169177585] },
    { pairKey: "31566704-3169177585", pairLabel: "31566704/3169177585", assetIds: [31566704, 3169177585] },
  ];
  const venues = ["tinyman", "pact"];
  const cells = [];
  pairs.forEach((pair, pairIndex) => {
    venues.forEach((venue, venueIndex) => {
      timeBuckets.forEach((bucket) => {
        const wave = Math.max(0, Math.sin((bucket.index + 1) * 0.7 + pairIndex) + (venueIndex ? 0.25 : 0.45));
        const count = Math.round(wave * (4 - pairIndex));
        if (!count) return;
        cells.push({
          ...pair,
          venue,
          bucketIndex: bucket.index,
          bucketStart: bucket.startAt,
          bucketEnd: bucket.endAt,
          opportunityCount: count,
          opportunityDensity: count / Math.max(bucketSeconds / 3600, 1 / 60),
          spreadFrequency: Math.max(0, count - 1) / Math.max(bucketSeconds / 3600, 1 / 60),
          averageSpreadBps: 35 + count * 18 - pairIndex * 6,
          averageRouteCount: 2 + (pairIndex === 2 ? 1 : 0),
          opportunityHalfLifeSeconds: 5 + count * 4,
          paperTradePerformance: {
            count,
            winRate: Math.min(1, 0.35 + count * 0.12),
            averageExpectedNet: 0.02 * count,
            averageSimulated30s: 0.012 * count,
            averageQuoteDecay30s: 0.004 * count,
          },
          intensity: Math.min(1, count / 4),
          densityLabel: count >= 3 ? "hot" : count === 2 ? "active" : "watch",
          source: "mock",
        });
      });
    });
  });
  return {
    view,
    views,
    windowSeconds,
    bucketSeconds,
    generatedAt: now,
    timeBuckets,
    cells,
    pairSummaries: pairs.map((pair) => ({
      key: pair.pairKey,
      label: pair.pairLabel,
      opportunityCount: cells.filter((cell) => cell.pairKey === pair.pairKey).reduce((sum, cell) => sum + cell.opportunityCount, 0),
      averageSpreadBps: 42,
      averageHalfLifeSeconds: 14,
      paperCount: 4,
      averagePaperSimulated30s: 0.024,
    })),
    venueSummaries: venues.map((venue) => ({
      key: venue,
      label: venue,
      opportunityCount: cells.filter((cell) => cell.venue === venue).reduce((sum, cell) => sum + cell.opportunityCount, 0),
      averageSpreadBps: 38,
      averageHalfLifeSeconds: 13,
      paperCount: 4,
      averagePaperSimulated30s: 0.02,
    })),
    totals: {
      opportunityCount: cells.reduce((sum, cell) => sum + cell.opportunityCount, 0),
      activeCells: cells.length,
      pairCount: pairs.length,
      venueCount: venues.length,
      averageSpreadBps: 42,
      averageHalfLifeSeconds: 14,
      paperTradeCount: 12,
      paperWinRate: 0.58,
    },
    source: "mock",
    liveExecutionTouched: false,
    signerCodeTouched: false,
    note: message,
  };
}

function makeMockResearchArchive(message = "Market intelligence archive endpoint unavailable.") {
  const now = Math.floor(Date.now() / 1000);
  const today = new Date(now * 1000).toISOString().slice(0, 10);
  const report = {
    reportDate: today,
    generatedAt: now,
    source: "mock",
    publicSafe: true,
    liveExecutionTouched: false,
    signerCodeTouched: false,
    marketContextRibbon: {
      title: "External cached market context",
      symbol: "ALGO",
      change24hPct: -0.4,
      contextLabel: "neutral",
      snapshotAgeSeconds: 2700,
      snapshotAgeLabel: "45m old",
      sourceLabel: "CoinMarketCap cached context",
      availability: "available",
      cached: true,
      external: true,
      scope: "internal/dev/research delayed report context only",
      notice: "External cached market context only. Informational only; not investment or trading advice.",
    },
    marketSummary: {
      headline: "Mock daily intelligence report",
      narrative: "Mock fallback shows the report layout only. Stored reports load from /api/reports/market/archive when available.",
      opportunityCount: 42,
      pairCount: 4,
      venueCount: 2,
      topPair: "ALGO/PNET",
      scannerStatus: "wait",
      paperWinRate30s: 0.18,
    },
    topPairs: [
      { pairLabel: "ALGO/PNET", opportunityCount: 18, averageSpreadBps: 42, bestSpreadBps: 88, paperWinRate30s: 0.22 },
      { pairLabel: "ALGO/USDC", opportunityCount: 12, averageSpreadBps: 21, bestSpreadBps: 44, paperWinRate30s: 0.12 },
    ],
    pnetLiquidityWatchlist: {
      assetId: 3169177585,
      symbol: "PNET",
      poolCount: 1,
      totalPnetReserve: 4200000,
      source: "mock",
      listedWithoutOpportunity: true,
      publicSafe: true,
      notice: "PNET pool visibility is informational only; it is not investment advice, ROI guidance, or a request to trade.",
      lpRiskNotice: "Adding liquidity can lose value through price movement, fees, and impermanent loss. Review pool terms independently.",
      pools: [
        {
          poolId: "mock:ALGO-PNET",
          pairLabel: "ALGO/PNET",
          venue: "pact",
          pnetReserve: 4200000,
          otherReserve: 1500,
          liquidityEstimate: 79372,
          liquidityChangePct: 4.2,
          feeBps: 30,
          snapshotCount: 2,
          lpVisibilityNote: "Observed PNET liquidity surface; LP participation has risk and needs independent review.",
        },
      ],
    },
    topSpreads: [
      { pairLabel: "ALGO/PNET", venues: "tinyman -> pact", expectedProfitBps: 88, expectedNetProfit: 0.08, status: "rejected", skipReason: "mock_fallback" },
    ],
    liquidityChanges: [
      { poolId: "mock:ALGO-PNET", pairLabel: "ALGO/PNET", venue: "pact", startLiquidity: 12000, endLiquidity: 13200, changePct: 10 },
    ],
    opportunityCounts: {
      total: 42,
      approved: 2,
      rejected: 40,
      positiveSpreadCount: 7,
      bySkipReason: [{ reason: "mock_fallback", count: 40 }],
    },
    routePerformance: {
      routeCount: 42,
      averageRouteLength: 2.1,
      averageConfidence: 61,
      totalExpectedNetProfit: 0.44,
      topRejectionReasons: [{ reason: "mock_fallback", count: 40 }],
    },
    paperTradePerformance: {
      candidates: 42,
      checked5s: 36,
      checked30s: 30,
      winRate30s: 0.18,
      expectedNetProfit: 0.44,
      simulatedProfit30s: -0.12,
      averageQuoteDecay30s: 0.006,
    },
    scannerHealth: {
      status: "wait",
      poolsScanned: 14,
      snapshotCount: 80,
      checks: 3,
      errorCount: 0,
      latestDetail: message,
    },
    riskEvents: [{ reason: "mock_fallback", count: 40, approved: false }],
    exports: {
      json: `/api/reports/market/daily/export?date=${today}&format=json`,
      markdown: `/api/reports/market/daily/export?date=${today}&format=markdown`,
    },
    summary: {
      headline: "Mock daily intelligence report",
      topPair: "ALGO/PNET",
      opportunityCount: 42,
      paperWinRate30s: 0.18,
      scannerStatus: "wait",
    },
  };
  return {
    reports: [report],
    count: 1,
    source: "mock",
    publicSafe: true,
    liveExecutionTouched: false,
    signerCodeTouched: false,
    note: message,
  };
}

function makeMockFailureLab(message = "Failure simulation endpoint unavailable.") {
  const scenario = {
    key: "mock_failure_lab_unavailable",
    label: "Failure Lab Endpoint Unavailable",
    failureType: "control_plane",
    severity: "critical",
    trigger: message,
    expectedResponse: {
      status: "degraded",
      message: "Admin UI should show mock-labeled fallback and keep live execution locked.",
      blocksLiveExecution: true,
    },
    actualResponse: {
      status: "degraded",
      message: "Mock fallback rendered locally; no signer, hot-wallet, or submission authority exposed.",
      blocksLiveExecution: true,
    },
    alertsGenerated: ["failure_lab_unavailable"],
    servicesAffected: ["Dashboard", "Ops API"],
    operatorAction: "Restore /api/ops/failure-lab and rerun resilience simulation checks.",
    gracefulDegradation: true,
    source: "mock",
  };
  return {
    scenarios: [scenario],
    summary: {
      scenarioCount: 1,
      gracefulCount: 1,
      criticalCount: 1,
      blockedCount: 1,
      gracefulPercent: 100,
      headline: "1/1 fallback failures degrade safely",
    },
    source: "mock",
    mode: "simulation",
    liveExecutionTouched: false,
    signerCodeTouched: false,
    note: message,
  };
}

function makeMockDataProvenance(message = "Data provenance endpoint unavailable.", metricKey = "route.expected_net_profit") {
  const metric = {
    key: metricKey,
    label: metricKey.replaceAll("_", " ").replaceAll(".", " / "),
    value: "unavailable",
    unit: "n/a",
    source: "mock",
    status: "unavailable",
    table: "mock",
    field: "mock",
    description: message,
  };
  const missing = ["Source Data", "Quote", "Pool Snapshot", "Route Calculation", "Risk Decision"];
  return {
    metrics: [
      metric,
      { ...metric, key: "scanner.pool_count", label: "Pools scanned" },
      { ...metric, key: "quote.count", label: "Quote legs" },
      { ...metric, key: "route.count", label: "Route candidates" },
      { ...metric, key: "risk.decision_count", label: "Risk decisions" },
    ],
    selectedMetricKey: metricKey,
    selectedMetric: metric,
    lineage: [
      {
        key: "metric",
        label: "Metric",
        description: "Mock fallback metric.",
        records: [{ label: metric.label, table: "mock", field: "mock", value: "unavailable", source: "mock", detail: message }],
        status: "ok",
        source: "mock",
      },
      ...missing.map((label) => ({
        key: label.toLowerCase().replaceAll(" ", "_"),
        label,
        description: "Backend lineage unavailable.",
        records: [],
        status: "missing",
        source: "unavailable",
      })),
    ],
    lineageOrder: ["metric", "source_data", "quote", "pool_snapshot", "route_calculation", "risk_decision"],
    routeHash: null,
    complete: false,
    missingSteps: missing,
    source: "mock",
    liveExecutionTouched: false,
    signerCodeTouched: false,
    safety: {
      label: "Mock fallback only",
      detail: "No signer, hot wallet, or transaction submission path is touched.",
    },
  };
}

function makeMockEvidenceSystem(message = "Evidence endpoint unavailable.") {
  const now = Math.floor(Date.now() / 1000);
  const categories = ["scanner", "quotes", "routes", "paper_trading", "risk", "dry_run", "execution", "receipts"];
  const records = categories.map((category, index) => ({
    evidenceId: `mock.${category}`,
    service: category === "paper_trading" ? "paper_trader" : `${category}_service`,
    category,
    title: `${category.replaceAll("_", " ")} evidence unavailable`,
    summary: message,
    status: index < 2 ? "pending" : "warn",
    createdAt: now,
    metadata: {
      source: "mock",
      evidenceUrl: "/api/ops/evidence",
      liveExecutionTouched: false,
      signerCodeTouched: false,
      reason: message,
    },
  }));
  const byCategory = Object.fromEntries(categories.map((category) => [category, 1]));
  const byStatus = records.reduce((acc, item) => {
    acc[item.status] = (acc[item.status] || 0) + 1;
    return acc;
  }, {});
  return {
    records,
    count: records.length,
    summary: {
      total: records.length,
      passing: 0,
      pending: byStatus.pending || 0,
      warn: byStatus.warn || 0,
      fail: 0,
      proofPercent: 0,
      byCategory,
      byService: Object.fromEntries(records.map((item) => [item.service, 1])),
      byStatus,
      categories,
      statuses: ["pass", "pending", "warn", "fail"],
    },
    filteredSummary: {
      total: records.length,
      passing: 0,
      pending: byStatus.pending || 0,
      warn: byStatus.warn || 0,
      fail: 0,
      proofPercent: 0,
      byCategory,
      byService: Object.fromEntries(records.map((item) => [item.service, 1])),
      byStatus,
      categories,
      statuses: ["pass", "pending", "warn", "fail"],
    },
    filters: { ...state.evidenceFilters },
    services: records.map((item) => item.service),
    categories,
    statuses: ["pass", "pending", "warn", "fail"],
    generatedAt: now,
    source: "mock",
    liveExecutionTouched: false,
    signerCodeTouched: false,
  };
}

function makeMockProductValidation(message = "Product validation endpoint unavailable.") {
  const taxonomy = [
    ["viewed_market_pulse", "Market Pulse", false],
    ["opened_route", "Route Intelligence", true],
    ["inspected_route_forensics", "Route Forensics", true],
    ["viewed_liquidity_health", "Liquidity Health", true],
    ["opened_opportunity_replay", "Replay Lab", true],
    ["viewed_receipt", "Receipts", true],
    ["opened_daily_report", "Reports", true],
    ["requested_scan", "Market Scans", true],
    ["generated_simulation", "Route Simulation", true],
    ["viewed_project_page", "Project Pages", true],
    ["created_alert", "Alerts", true],
    ["exported_data", "API / Exports", true],
  ].map(([actionType, feature, decisionEligible]) => ({
    actionType,
    label: String(actionType).replaceAll("_", " "),
    feature,
    personas: [],
    decisionEligible,
    evidenceSource: feature,
  }));
  const features = ["Market Pulse", "Route Forensics", "Liquidity Health", "Replay Lab", "Reports", "Receipts", "Alerts", "API / Exports"];
  return {
    source: "mock",
    windowDays: 30,
    generatedAt: Date.now() / 1000,
    summary: {
      totalActions: 0,
      activeUsers: 0,
      repeatUsers: 0,
      repeatRate: 0,
      decisionCount: 0,
      decisionRate: 0,
      topPhase1Recommendation: message,
    },
    actionTaxonomy: taxonomy,
    funnel: ["Guest", "Connected User", "PNET User", "Report User", "Repeat User"].map((label, index) => ({
      key: label.toLowerCase().replaceAll(" ", "_"),
      label,
      users: 0,
      conversionRate: 0,
      dropOff: index === 0 ? 0 : 0,
      source: "mock",
    })),
    personas: ["Trader", "Builder", "Project Founder", "Liquidity Provider", "Researcher"].map((persona) => ({
      persona,
      activeUsers: 0,
      topActions: [],
      repeatRate: 0,
      averageSessionDepth: 0,
      evidenceBackedDecisions: 0,
      source: "mock",
    })),
    featureUtility: features.map((feature) => ({
      feature,
      opens: 0,
      repeatOpens: 0,
      sessionContribution: 0,
      decisionContribution: 0,
      decisionCount: 0,
      source: "mock",
    })),
    deadFeatures: features.map((feature) => ({
      feature,
      daysSinceUse: null,
      monthlyActivity: 0,
      decisionCount: 0,
      recommendation: "investigate",
      source: "mock",
    })),
    whyUsersReturn: {
      topActions: [],
      topPersonas: [],
      mostValuablePages: [],
      repeatUserMetrics: { activeUsers: 0, repeatUsers: 0, repeatRate: 0 },
      decisionMetrics: { decisionCount: 0, decisionsPerActiveUser: 0, dailyEvidenceBackedDecisions: [] },
    },
    decisionRules: {
      metricName: "Daily Evidence-Backed Decisions",
      includedActions: taxonomy.filter((item) => item.decisionEligible).map((item) => item.actionType),
      excludedExamples: ["page_load", "scroll", "idle_time"],
      definition: "Mock fallback. Restore /api/ops/product-validation to read stored product behavior.",
    },
    liveExecutionTouched: false,
    signerCodeTouched: false,
  };
}

function ProductionStatusBanner(data) {
  const status = data.pipeline?.productionStatus || data.riskGates?.productionStatus || defaultProductionStatus(data.pipeline?.source || "unavailable");
  const restrictions = status.restrictions || defaultProductionStatus().restrictions;
  return `
    <div class="production-status-banner ${escapeHtml(status.status || "not_live_ready")}">
      <div>
        <span>Production Status</span>
        <strong>${escapeHtml(status.headline || "NOT LIVE READY")}</strong>
        ${SourceBadge(status.source || "unavailable")}
      </div>
      <p>${escapeHtml(status.reason || defaultProductionStatus().reason)}</p>
      <div class="safe-mode-strip">
        <span>Current safe mode</span>
        <strong>${escapeHtml(status.safeMode || "Scanner / Paper / Dry Run only.")}</strong>
      </div>
      <div class="production-restrictions">
        ${restrictions.map((item) => `<em>${escapeHtml(item)}</em>`).join("")}
      </div>
    </div>`;
}

function ProductionReadinessCard(data) {
  const readiness =
    data.pipeline?.productionReadiness ||
    data.phaseGates?.productionReadiness ||
    data.riskGates?.productionReadiness ||
    defaultProductionReadiness(data.pipeline?.source || "unavailable");
  const source = normalizeSourceLabel(readiness.source || "unavailable");
  const percent =
    source === "mock" ? 0 : Math.max(0, Math.min(100, Number(readiness.overallPercent || 0)));
  const blockers = readiness.blockingItems?.length ? readiness.blockingItems : defaultProductionReadiness().blockingItems;
  const soakBlockers = (data.testnetSoak?.blockers || []).slice(0, 2);
  const displayBlockers = [...blockers.slice(0, 4), ...soakBlockers].slice(0, 6);
  return `
    <div class="production-readiness-card">
      <div class="readiness-card-head">
        <span>Production Readiness</span>
        ${SourceBadge(source)}
      </div>
      <div class="readiness-phase-row">
        <div>
          <span>Active phase</span>
          <strong>${escapeHtml(readiness.activePhase || readiness.currentPhase || "Phase 3: TestNet Readiness")}</strong>
        </div>
        <div>
          <span>Overall</span>
          <strong>${fmt.format(percent)}%</strong>
        </div>
      </div>
      <div class="readiness-progress" aria-label="Production readiness ${fmt.format(percent)}%">
        <i style="width:${percent}%"></i>
      </div>
      <div class="readiness-next-gate">
        <span>Next Gate</span>
        <strong>${escapeHtml(readiness.nextGate || "24h TestNet soak evidence")}</strong>
      </div>
      ${
        readiness.historicalPhase
          ? `<div class="readiness-next-gate"><span>Historical ladder</span><strong>${escapeHtml(readiness.historicalPhase)}</strong></div>`
          : ""
      }
      <div class="readiness-blockers">
        <span>Blocking Items</span>
        ${displayBlockers.map((item) => `<em>${escapeHtml(item)}</em>`).join("")}
      </div>
    </div>`;
}

function DataFlowCounters(data) {
  const services = data.pipeline?.services || [];
  const pipelineSource = data.pipeline?.source || "unavailable";
  const quoteEngine = services.find((service) => service.key === "quote_engine") || {};
  const routeEngine = services.find((service) => service.key === "route_engine") || {};
  const scanner = services.find((service) => service.key === "pool_scanner") || {};
  const paper = data.paperSummary || {};
  const rejected = (data.rejections?.buckets || []).reduce((sum, bucket) => sum + Number(bucket.count || 0), 0);
  const counters = [
    ["Pool snapshots", scanner.outputCount24h || 0, scanner.source || pipelineSource, "scanner.snapshot_count"],
    ["Quote legs", quoteEngine.outputCount24h || 0, quoteEngine.source || pipelineSource, "quote.count"],
    ["Route candidates", routeEngine.outputCount24h || 0, routeEngine.source || pipelineSource, "route.count"],
    ["Paper candidates", paper.candidatesObserved || 0, paper.source || "unavailable", "paper.count"],
    ["Rejected routes", rejected, data.rejections?.source || "unavailable", "route.rejected_count"],
    ["Live state", data.riskGates?.liveExecutionLocked ? "locked" : "review", data.riskGates?.source || "unavailable", "live.state"],
  ];
  return `
    <section class="cockpit-card span-3 data-flow-counters">
      <div class="panel-head">
        <h2>Data-Flow Counters</h2>
        <span>source-labeled</span>
      </div>
      <div class="control-metric-grid">
        ${counters
          .map(([label, value, source, metricKey]) =>
            TraceableMetricArticle({ label, value, source, metricKey, className: "control-metric" })
          )
          .join("")}
      </div>
    </section>`;
}

function connectorTone(connector) {
  const status = connector?.status;
  const impact = connector?.readinessImpact;
  if (status === "mock") return "mock";
  if (impact === "blocked" || status === "down" || (status === "stale" && connector?.connectorType === "algod")) return "blocked";
  if (impact === "wait" || status === "degraded" || status === "stale") return "wait";
  if (status === "ok" && impact === "ok") return "ok";
  return "wait";
}

function readinessTone(value) {
  if (value === "ok") return "ok";
  if (value === "blocked") return "blocked";
  return "wait";
}

function metricValue(value, suffix = "") {
  if (value === null || value === undefined || value === "") return "n/a";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return escapeHtml(value);
  return `${fmt.format(numeric)}${suffix}`;
}

function ConnectorReasonList(title, reasons, tone) {
  return `
    <div class="connector-reason-list ${escapeHtml(tone)}">
      <span>${escapeHtml(title)}</span>
      ${
        reasons?.length
          ? reasons
              .map(
                (item) => `
          <em>${escapeHtml(item.connectorName || "connector")} / ${escapeHtml(item.status || "wait")} / ${escapeHtml(item.reason || "reason pending")}</em>`
              )
              .join("")
          : `<em>none</em>`
      }
    </div>`;
}

function ConnectorCard(connector, source) {
  const tone = connectorTone(connector);
  const status = connector?.status || "unavailable";
  const impact = connector?.readinessImpact || "blocked";
  const productionLabel = connector?.productionReady ? "production-ready" : "not production-ready";
  return `
    <article class="connector-card ${escapeHtml(tone)}">
      <div class="connector-card-head">
        <div>
          <span>${escapeHtml(connector?.connectorType || "unknown")}</span>
          <strong>${escapeHtml(connector?.connectorName || connector?.connector || "connector")}</strong>
        </div>
        ${statusChip(status, tone === "mock" ? "wait" : tone)}
      </div>
      <p>${escapeHtml(connector?.degradationReason || (status === "ok" ? "Connector is usable for readiness evidence." : "Reason pending."))}</p>
      <div class="connector-production ${connector?.productionReady ? "ready" : "not-ready"}">
        <span>${escapeHtml(productionLabel)}</span>
        <strong>${escapeHtml(impact)}</strong>
      </div>
      <div class="connector-metrics">
        <div><span>Latency</span><strong>${metricValue(connector?.latencyMs, "ms")}</strong></div>
        <div><span>Fresh 24h</span><strong>${metricValue(connector?.freshCount24h)}</strong></div>
        <div><span>Stale 24h</span><strong>${metricValue(connector?.staleCount24h)}</strong></div>
        <div><span>Errors 24h</span><strong>${metricValue(connector?.errorCount24h)}</strong></div>
        <div><span>Latest round</span><strong>${metricValue(connector?.latestRound)}</strong></div>
        <div><span>Expected min</span><strong>${metricValue(connector?.expectedMinRound)}</strong></div>
      </div>
      <div class="connector-source-row">
        ${SourceBadge(connector?.source || source || "stored")}
        <span>${escapeHtml(impact === "blocked" ? "blocks readiness" : impact === "wait" ? "wait for evidence" : "readiness ok")}</span>
      </div>
    </article>`;
}

const expectedConnectorOrder = ["tinyman", "pact", "algod", "indexer", "mock"];

function connectorTypeForName(name) {
  if (name === "algod") return "algod";
  if (name === "indexer") return "indexer";
  return "dex";
}

function connectorFromVenueCoverage(venue, source) {
  const status = venue?.status || "down";
  const staleCount = Number(venue?.staleCount24h ?? venue?.staleQuoteCount24h ?? 0);
  const freshCount = Number(venue?.freshCount24h ?? venue?.freshQuoteCount24h ?? 0);
  const errorCount = Number(venue?.errorCount24h || 0);
  const readinessImpact = status === "ok" ? "ok" : status === "degraded" ? "wait" : "blocked";
  return {
    connector: venue?.venueId,
    connectorName: venue?.venueName || venue?.venueId,
    connectorType: "dex",
    status,
    readinessImpact,
    degradationReason:
      status === "ok"
        ? null
        : staleCount > 0
          ? "connector_quotes_stale"
          : errorCount > 0
            ? "connector_errors_present"
            : "connector_health_unavailable",
    productionReady: false,
    latencyMs: venue?.latencyMs ?? null,
    freshCount24h: freshCount,
    staleCount24h: staleCount,
    errorCount24h: errorCount,
    latestRound: null,
    expectedMinRound: null,
    source: venue?.source || source || "stored",
  };
}

function unavailableConnector(name) {
  return {
    connector: name,
    connectorName: name,
    connectorType: connectorTypeForName(name),
    status: "down",
    readinessImpact: "blocked",
    degradationReason: "connector_health_unavailable",
    productionReady: false,
    latencyMs: null,
    freshCount24h: 0,
    staleCount24h: 0,
    errorCount24h: 0,
    latestRound: null,
    expectedMinRound: null,
    source: "unavailable",
  };
}

function connectorDisplayRecords(connectorsData) {
  const source = connectorsData?.source || "unavailable";
  const records = new Map();
  (connectorsData?.connectors || []).forEach((connector) => {
    const name = connector.connectorName || connector.connector;
    if (!name) return;
    records.set(name, { source, ...connector });
  });
  (connectorsData?.venueCoverage || connectorsData?.venues || []).forEach((venue) => {
    const name = venue.venueName || venue.venueId;
    if (!["tinyman", "pact"].includes(name) || records.has(name)) return;
    records.set(name, connectorFromVenueCoverage(venue, source));
  });
  ["tinyman", "pact", "algod", "indexer"].forEach((name) => {
    if (!records.has(name)) records.set(name, unavailableConnector(name));
  });
  return [...records.values()].sort((a, b) => {
    const aIndex = expectedConnectorOrder.indexOf(a.connectorName);
    const bIndex = expectedConnectorOrder.indexOf(b.connectorName);
    return (aIndex < 0 ? 99 : aIndex) - (bIndex < 0 ? 99 : bIndex);
  });
}

function connectorDisplayRollup(connectors) {
  const blockedReasons = connectors
    .filter((item) => item.readinessImpact === "blocked")
    .map((item) => ({
      connectorName: item.connectorName,
      status: item.status,
      reason: item.degradationReason || item.status,
    }));
  const waitReasons = connectors
    .filter((item) => item.readinessImpact === "wait")
    .map((item) => ({
      connectorName: item.connectorName,
      status: item.status,
      reason: item.degradationReason || item.status,
    }));
  return {
    totalConnectors: connectors.length,
    okCount: connectors.filter((item) => item.status === "ok").length,
    degradedCount: connectors.filter((item) => item.status === "degraded").length,
    downCount: connectors.filter((item) => item.status === "down").length,
    staleCount: connectors.filter((item) => item.status === "stale").length,
    mockCount: connectors.filter((item) => item.status === "mock").length,
    productionReadyCount: connectors.filter((item) => item.productionReady).length,
    blockedReasons,
    waitReasons,
    overallReadiness: blockedReasons.length ? "blocked" : waitReasons.length ? "wait" : "ok",
  };
}

function ConnectorOpsPanel(data) {
  const connectorsData = data.connectors || {};
  const connectors = connectorDisplayRecords(connectorsData);
  const rollup = connectorDisplayRollup(connectors);
  const overall = rollup.overallReadiness || "blocked";
  const source = connectorsData.source || "unavailable";
  return `
    <section class="cockpit-card span-3 connector-ops-panel ${escapeHtml(readinessTone(overall))}">
      <div class="panel-head">
        <h2>Connector Readiness</h2>
        <span>${escapeHtml(overall)} / ${lastOpsRefreshLabel()}</span>
      </div>
      <div class="connector-rollup">
        <article class="${escapeHtml(readinessTone(overall))}">
          <span>Overall readiness</span>
          <strong>${escapeHtml(overall)}</strong>
          ${SourceBadge(source)}
        </article>
        <article>
          <span>Total connectors</span>
          <strong>${fmt.format(rollup.totalConnectors || connectors.length || 0)}</strong>
        </article>
        <article>
          <span>Production-ready</span>
          <strong>${fmt.format(rollup.productionReadyCount || 0)}</strong>
        </article>
        <article>
          <span>State mix</span>
          <strong>${fmt.format(rollup.okCount || 0)} ok / ${fmt.format(rollup.degradedCount || 0)} degraded / ${fmt.format(rollup.downCount || 0)} down / ${fmt.format(rollup.staleCount || 0)} stale / ${fmt.format(rollup.mockCount || 0)} mock</strong>
        </article>
      </div>
      <div class="connector-reasons">
        ${ConnectorReasonList("Blocked reasons", rollup.blockedReasons || [], "blocked")}
        ${ConnectorReasonList("Wait reasons", rollup.waitReasons || [], "wait")}
      </div>
      ${
        connectors.length
          ? `<div class="connector-grid">${connectors.map((connector) => ConnectorCard(connector, source)).join("")}</div>`
          : `<div class="connector-empty-state">
              <strong>No connector telemetry available</strong>
              <p>Connector readiness will stay unavailable until /api/ops/connectors returns stored or mock-labeled evidence.</p>
              ${SourceBadge(source)}
            </div>`
      }
    </section>`;
}

function PhaseGateLadder(data) {
  const active = data.phaseGates?.activePhase;
  const historical = data.phaseGates?.phases?.length ? data.phaseGates.phases : data.phaseGates?.gates || [];
  if (!active && !historical.length) {
    return `<section class="cockpit-card span-3 empty-state"><h2>Phase ladder</h2><p>No phase-gate telemetry available.</p>${SourceBadge("unavailable")}</section>`;
  }
  const activeCard = active
    ? `
      <article class="phase-ladder-step wait active-phase">
        <div>
          <span>ACTIVE</span>
          ${SourceBadge(active.source || data.phaseGates?.source || "stored")}
        </div>
        <strong>${escapeHtml(active.label || "Phase 3: TestNet Readiness")}</strong>
        <div class="progress-rail"><i style="width:${Math.max(0, Math.min(100, Number(active.percent || 0)))}%"></i></div>
        <em>${fmt.format(Number(active.percent || 0))}%</em>
        <p>${escapeHtml((active.blockers || [])[0] || "Collect read-only TestNet soak and paper evidence.")}</p>
      </article>`
    : "";
  return `
    <section class="cockpit-card span-3 production-ladder">
      <div class="panel-head">
        <h2>Phase Ladder</h2>
        <span>Phase 3 active · Phase 0 historical</span>
      </div>
      <p class="deck-note">${escapeHtml(data.phaseGates?.phaseNote || "Phase 3 TestNet readiness is active. Phase 0A–0G remain historical evidence.")}</p>
      <div class="phase-ladder-track">
        ${activeCard}
        ${historical
          .map((gate, index) => {
            const phaseCode = (gate.label || "").match(/Phase\s+0[A-G]/i)?.[0] || `Hist ${index + 1}`;
            const locked = gate.status === "disabled" || (gate.blockers || []).includes("LOCKED");
            const percent = Math.max(0, Math.min(100, Number(gate.percent || 0)));
            return `
          <article class="phase-ladder-step ${escapeHtml(serviceTone(gate.status))} ${gate.hasDelta ? "changed" : ""} ${locked ? "locked" : ""} historical-phase">
            <div>
              <span>${escapeHtml(phaseCode)} · hist</span>
              ${SourceBadge(gate.source || data.phaseGates?.source || "unavailable")}
            </div>
            <strong>${escapeHtml(gate.label)}</strong>
            <div class="progress-rail"><i style="width:${locked ? 0 : percent}%"></i></div>
            <em>${locked ? "LOCKED" : `${fmt.format(percent)}%${deltaBadge(gate.percentDelta, "gate")}`}</em>
            <p>${escapeHtml((gate.blockers || [])[0] || (gate.completedEvidence || [])[0] || "Historical gate evidence.")}</p>
          </article>`;
          })
          .join("")}
      </div>
    </section>`;
}

function ServiceEvidencePreview(service) {
  const evidence = (service.evidence || []).slice(0, 2);
  if (!evidence.length) {
    return `
      <div class="service-evidence-preview empty">
        <span>Evidence</span>
        <strong>pending</strong>
      </div>`;
  }
  return `
    <div class="service-evidence-preview">
      ${evidence
        .map(
          (item) => `
        <span>
          <em>${escapeHtml(item.label || "Evidence")}</em>
          <strong>${escapeHtml(item.value || "pending")}</strong>
        </span>`
        )
        .join("")}
    </div>`;
}

function ServiceEvidenceList(service) {
  const evidence = service.evidence || [];
  if (!evidence.length) {
    return `<p class="muted">No structured evidence has been emitted for this service yet.</p>`;
  }
  return `
    <div class="service-evidence-list">
      <span>Evidence exposed</span>
      ${evidence
        .map(
          (item) => `
        <article>
          <div>
            <span>${escapeHtml(item.label || "Evidence")}</span>
            <strong>${escapeHtml(item.value || "pending")}</strong>
            <p>${escapeHtml(item.detail || "No detail recorded.")}</p>
          </div>
          ${SourceBadge(item.source || service.source || "unavailable")}
        </article>`
        )
        .join("")}
    </div>`;
}

function ServiceNodeCard(service) {
  const tone = serviceTone(service.status);
  const activityClass = service.hasDelta ? "changed" : service.source === "mock" ? "mock-motion" : service.source === "stored" ? "heartbeat" : "";
  return `
    <button type="button" class="service-node-card ${escapeHtml(tone)} ${activityClass}" data-service-key="${escapeHtml(service.key)}">
      <span class="node-status">${escapeHtml(service.status || "wait")}</span>
      <strong>${escapeHtml(service.label)}</strong>
      <p>${escapeHtml(service.summary || "Telemetry pending.")}</p>
      <div class="node-motion ${escapeHtml(service.motionState || service.status || "wait")}">
        <i></i>
        <span>${escapeHtml(service.motionLabel || "waiting for evidence")}</span>
      </div>
      ${ServiceEvidencePreview(service)}
      <div class="node-meta">
        ${SourceBadge(service.source)}
        ${FreshnessBadge(service.freshnessSeconds)}
      </div>
      <div class="node-counts">
        <span><em>In</em>${fmt.format(service.inputCount24h || 0)}${deltaBadge(service.deltaInput24h, "in")}</span>
        <span><em>Out</em>${fmt.format(service.outputCount24h || 0)}${deltaBadge(service.deltaOutput24h, "out")}</span>
        <span><em>Err</em>${fmt.format(service.errorCount24h || 0)}${deltaBadge(service.deltaError24h, "err")}</span>
      </div>
    </button>`;
}

function ServicePipelineMap(data) {
  const services = data.pipeline?.services || [];
  return `
    <section class="cockpit-card span-3 service-pipeline-map">
      <div class="panel-head">
        <h2>Live Service Pipeline</h2>
        <span>${data.pipeline?.liveExecutionLocked ? "live locked" : "review required"} / ${lastOpsRefreshLabel()}</span>
      </div>
      <div class="pipeline-lock-banner ${data.pipeline?.liveExecutionLocked ? "locked" : "review"}">
        <strong>${data.pipeline?.liveExecutionLocked ? "Live Micro-Execution Locked" : "Live Micro-Execution Needs Review"}</strong>
        <span>No signer, hot-wallet, or submission authority is exposed in this view.</span>
        ${SourceBadge(data.pipeline?.source || "unavailable")}
      </div>
      <div class="service-pipeline-track">
        ${services.map((service) => ServiceNodeCard(service)).join("")}
      </div>
    </section>`;
}

function ActivityTape(data) {
  const events = data.activity?.events || [];
  return `
    <section class="cockpit-card activity-tape">
      <div class="panel-head">
        <h2>Activity Tape</h2>
        <span>read-only heartbeat / ${lastOpsRefreshLabel()}</span>
      </div>
      <div class="activity-list">
        ${
          events.length
            ? events
                .map(
                  (event) => `
          <article class="activity-event ${escapeHtml(event.severity || "info")}">
            <span>${escapeHtml(event.service || "service")}</span>
            <strong>${escapeHtml(event.message || "No message.")}</strong>
            <em>${escapeHtml(event.timestamp || "no timestamp")}</em>
            ${SourceBadge(event.source)}
          </article>`
                )
                .join("")
            : `<p class="muted">No activity events available.</p>`
        }
      </div>
    </section>`;
}

function RejectionFunnel(data) {
  const buckets = data.rejections?.buckets || [];
  return `
    <section class="cockpit-card rejection-funnel">
      <div class="panel-head">
        <h2>Route Rejection Funnel</h2>
        <span>expected signal</span>
      </div>
      <p class="deck-note">${escapeHtml(data.rejections?.summary || "Rejected routes are expected and useful.")}</p>
      <div class="funnel-bars">
        ${buckets
          .map(
            (bucket) => `
          <div class="funnel-row">
            <div>
              <strong>${escapeHtml(gateLabel(bucket.reason))}</strong>
              <span>${fmt.format(bucket.count || 0)} routes / ${fmt.format(bucket.percent || 0)}%</span>
            </div>
            <i style="width:${Math.max(4, Math.min(100, Number(bucket.percent || 0)))}%"></i>
          </div>`
          )
          .join("")}
      </div>
      ${SourceBadge(data.rejections?.source || "unavailable")}
    </section>`;
}

function PaperTradingScoreboard(data) {
  const paper = data.paperSummary || emptyPaperSummary(data.pipeline?.source === "mock" ? "mock" : "unavailable");
  const source = normalizeSourceLabel(paper.source || "unavailable");
  // Prefer pipeline paper node count when both are stored so counters agree.
  const paperNode = (data.pipeline?.services || []).find((service) => service.key === "paper_trader");
  const candidates =
    source !== "mock" && paperNode && normalizeSourceLabel(paperNode.source) === "stored"
      ? Number(paper.candidatesObserved ?? paperNode.outputCount24h ?? 0)
      : Number(paper.candidatesObserved || 0);
  const progress =
    source === "mock" ? 0 : Math.min(100, (Number(paper.daysCollected || 0) / Math.max(1, Number(paper.targetDays || 7))) * 100);
  return `
    <section class="cockpit-card paper-scoreboard">
      <div class="panel-head">
        <h2>Paper-Trading Scoreboard</h2>
        <span>${escapeHtml(source === "mock" ? "not_ready" : paper.verdict || "not_ready")}</span>
      </div>
      <div class="score-ring" style="--score:${progress}%">
        <strong>${fmt.format(paper.daysCollected || 0)} / ${fmt.format(paper.targetDays || 7)}</strong>
        <span>days</span>
      </div>
      <div class="paper-stat-grid">
        ${TraceableMetricArticle({ label: "Candidates", value: fmt.format(candidates), source, metricKey: "paper.count", className: "" })}
        ${TraceableMetricArticle({ label: "Would execute", value: fmt.format(source === "mock" ? 0 : paper.wouldExecuteCount || 0), source, metricKey: "paper.count", className: "" })}
        ${TraceableMetricArticle({ label: "Wins 5s / 30s", value: `${fmt.format(source === "mock" ? 0 : paper.simulatedWins5s || 0)} / ${fmt.format(source === "mock" ? 0 : paper.simulatedWins30s || 0)}`, source, metricKey: "paper.checked_30s_count", className: "" })}
        ${TraceableMetricArticle({ label: "Expected net", value: source === "mock" ? "0.000000" : paper.expectedNetAlgo || "0.000000", source, metricKey: "route.expected_net_profit", className: "" })}
        ${TraceableMetricArticle({ label: "Sim 30s net", value: source === "mock" ? "0.000000" : paper.simulatedNetAlgo30s || "0.000000", source, metricKey: "paper.checked_30s_count", className: "" })}
        ${TraceableMetricArticle({ label: "Avg decay", value: source === "mock" ? "0.000000" : paper.averageQuoteDecayAlgo || "0.000000", source, metricKey: "paper.checked_30s_count", className: "" })}
      </div>
      <div class="paper-compare-strip">
        <span>Expected vs simulated</span>
        <strong>${escapeHtml(source === "mock" ? "0.000000" : paper.expectedNetAlgo || "0.000000")} / ${escapeHtml(source === "mock" ? "0.000000" : paper.simulatedNetAlgo30s || "0.000000")}</strong>
      </div>
      ${SourceBadge(source)}
    </section>`;
}

function RiskGateInspector(data) {
  const risk = data.riskGates || emptyRiskGates(data.pipeline?.source === "mock" ? "mock" : "unavailable");
  return `
    <section class="cockpit-card risk-gate-inspector">
      <div class="panel-head">
        <h2>Risk Gate Inspector</h2>
        <span>locked</span>
      </div>
      <div class="risk-lock-state locked">
        <strong>Live execution locked</strong>
        ${(risk.lockReasons || ["kill switch active", "signer disabled"]).map((reason) => `<span>${escapeHtml(reason)}</span>`).join("")}
      </div>
      <div class="risk-check-list">
        ${(risk.checks || [])
          .map(
            (check) => `
          <div class="risk-check ${escapeHtml(serviceTone(check.status))}">
            ${statusChip(check.status || "wait", serviceTone(check.status))}
            <strong>${escapeHtml(check.label)}</strong>
            <p>${escapeHtml(check.evidence || "Evidence pending.")}</p>
          </div>`
          )
          .join("")}
      </div>
      ${SourceBadge(risk.source || "unavailable")}
    </section>`;
}

function EnvironmentMatrix(data) {
  const environment = data.environment || {};
  return `
    <section class="cockpit-card environment-matrix">
      <div class="panel-head">
        <h2>Environment / Sources</h2>
        <span>${escapeHtml(environment.environment || "local")} / ${escapeHtml(environment.network || APP_CONFIG.NETWORK)}</span>
      </div>
      <div class="environment-grid">
        ${(environment.items || [])
          .map(
            (item) => `
          <article class="environment-row ${escapeHtml(serviceTone(item.status))}">
            <span>${escapeHtml(item.label)}</span>
            <strong>${escapeHtml(item.detail || "pending")}</strong>
            ${SourceBadge(item.source)}
          </article>`
          )
          .join("")}
      </div>
    </section>`;
}

function EvidenceDrawer(service) {
  if (!service) {
    return `<p class="muted">Select a service node to inspect evidence.</p>`;
  }
  return `
    <div class="evidence-summary">
      ${statusChip(service.status || "wait", serviceTone(service.status))}
      ${SourceBadge(service.source || "unavailable")}
      ${FreshnessBadge(service.freshnessSeconds)}
      <h3>${escapeHtml(service.label)}</h3>
      <p>${escapeHtml(service.summary || "Telemetry pending.")}</p>
    </div>
    <div class="evidence-grid">
      <div><span>Endpoint / source</span><strong>${escapeHtml(service.endpoint || "/api/ops/pipeline")}</strong></div>
      <div><span>Last success</span><strong>${escapeHtml(service.lastSuccessAt || "none")}</strong></div>
      <div><span>Last run</span><strong>${escapeHtml(service.lastRunAt || "none")}</strong></div>
      <div><span>24h input / output</span><strong>${fmt.format(service.inputCount24h || 0)} / ${fmt.format(service.outputCount24h || 0)}</strong></div>
      <div><span>24h errors</span><strong>${fmt.format(service.errorCount24h || 0)}</strong></div>
      <div><span>Blockers</span><strong>${escapeHtml(service.blocker || "No blockers recorded")}</strong></div>
    </div>
    ${ServiceEvidenceList(service)}
    <div class="evidence-log-list">
      <span>Last logs</span>
      ${(service.lastLogs || []).map((line) => `<code>${escapeHtml(line)}</code>`).join("")}
    </div>
    <div class="intent-box">
      <span>Next required action</span>
      <strong>${escapeHtml(service.nextAction || service.blocker || "Continue collecting evidence.")}</strong>
    </div>`;
}

function openEvidenceDrawer(serviceKey) {
  const services = controlRoomData().pipeline?.services || [];
  const service = services.find((item) => item.key === serviceKey);
  state.selectedServiceKey = serviceKey;
  document.getElementById("evidence-drawer-title").textContent = service?.label || "Service Evidence";
  document.getElementById("evidence-drawer-body").innerHTML = EvidenceDrawer(service);
  showModal("evidence-drawer", true);
}

async function openDataProvenance(metricKey, routeHash = null) {
  const data = await loadDataProvenance({ metric: metricKey, routeHash, render: false });
  if (state.activeView === "provenance") renderRoleDashboard();
  document.getElementById("evidence-drawer-title").textContent = "Data Provenance";
  document.getElementById("evidence-drawer-body").innerHTML = ProvenanceDrawer(data || provenanceData());
  showModal("evidence-drawer", true);
}

function ProductionControlRoom() {
  const data = controlRoomData();
  const loading = state.opsLoading && !state.opsControlRoom;
  const pipelineSource = normalizeSourceLabel(data.pipeline?.source || "unavailable");
  return `
    <section class="cockpit-card span-3 control-room-hero">
      <div>
        <p class="eyebrow">Production Control Room · ${escapeHtml(APP_PHASE_LABEL)}</p>
        <h2>Read-only arb pipeline evidence</h2>
        <p>Scanner → quotes → routes → risk → paper, plus connector health and TestNet soak. Live execution stays locked.</p>
      </div>
      <div class="production-status-stack">
        ${ProductionStatusBanner(data)}
        ${ProductionReadinessCard(data)}
        <div class="control-room-lock locked">
          <span>Live Micro-Execution</span>
          <strong>LOCKED</strong>
          <em>Signer and submission controls are not exposed here.</em>
          ${SourceBadge(pipelineSource)}
        </div>
      </div>
    </section>
    ${
      loading
        ? `<section class="cockpit-card span-3 loading-state"><h2>Loading Control Room</h2><p>Reading admin-gated ops telemetry...</p></section>`
        : ""
    }
    ${
      state.opsError
        ? `<section class="cockpit-card span-3 error-state"><h2>Ops telemetry notice</h2><p>${escapeHtml(state.opsError)}. Real panels keep stored evidence where available; mock is source-labeled and does not increase readiness.</p></section>`
        : ""
    }
    ${TestnetSoakPanel(data)}
    ${ConnectorOpsPanel(data)}
    ${DataFlowCounters(data)}
    ${PhaseGateLadder(data)}
    ${ServicePipelineMap(data)}
    ${PaperTradingScoreboard(data)}
    ${RiskGateInspector(data)}
    ${EnvironmentMatrix(data)}
    ${RejectionFunnel(data)}
    ${ActivityTape(data)}`;
}

function testnetSoakData(data) {
  return data?.testnetSoak || state.opsControlRoom?.testnetSoak || null;
}

function TestnetSoakObservationTape(data) {
  const payload = data?.testnetSoakObservations || state.opsControlRoom?.testnetSoakObservations || null;
  if (state.testnetSoakObservationsError && !payload) {
    return `
      <div class="testnet-soak-observations unavailable">
        <div class="testnet-soak-observation-head">
          <div><span>Latest observations</span><strong>Evidence unavailable</strong></div>
          ${SourceBadge("unavailable")}
        </div>
        <p>${escapeHtml(state.testnetSoakObservationsError)}</p>
      </div>`;
  }

  const observations = Array.isArray(payload?.observations) ? payload.observations.slice(0, 6) : [];
  if (!observations.length) {
    return `
      <div class="testnet-soak-observations empty">
        <div class="testnet-soak-observation-head">
          <div><span>Latest observations</span><strong>No stored observations</strong></div>
          ${SourceBadge(payload?.source || "unavailable")}
        </div>
        <p>The local read-only runner has not produced inspectable evidence yet.</p>
      </div>`;
  }

  return `
    <div class="testnet-soak-observations">
      <div class="testnet-soak-observation-head">
        <div>
          <span>Latest observations</span>
          <strong>${fmt.format(payload.count || observations.length)} stored records</strong>
        </div>
        ${SourceBadge(payload.source || "stored")}
      </div>
      <div class="testnet-soak-observation-list">
        ${observations
          .map((observation) => {
            const status = String(observation.status || "unavailable");
            const tone = status === "ok" ? "ok" : status === "degraded" ? "warn" : "blocked";
            const source = observation.source || "unavailable";
            return `
              <article class="${escapeHtml(tone)}">
                <div class="testnet-soak-observation-primary">
                  ${statusChip(status, tone)}
                  <strong>${escapeHtml(evidenceCreatedLabel(observation.completedAt))}</strong>
                  ${SourceBadge(source)}
                </div>
                <div class="testnet-soak-observation-facts">
                  <span>scan ${escapeHtml(observation.scanner?.status || "unavailable")}</span>
                  <span>${fmt.format(observation.poolsObserved || 0)} pools</span>
                  <span>${fmt.format(observation.quotesObserved || 0)} quotes</span>
                  <span>algod ${escapeHtml(observation.algod?.status || "unavailable")} / ${fmt.format(observation.algod?.latestRound || 0)}</span>
                  <span>indexer lag ${fmt.format(observation.indexer?.roundLag || 0)}</span>
                </div>
              </article>`;
          })
          .join("")}
      </div>
    </div>`;
}

function TestnetSoakPanel(data) {
  if (state.opsLoading && !testnetSoakData(data) && !state.testnetSoakError) {
    return `
      <section class="cockpit-card span-3 testnet-soak-card wait">
        <div class="panel-head"><h2>TestNet Soak</h2><span>Loading</span></div>
        <p class="deck-note">Loading stored 24-hour read-only soak evidence...</p>
      </section>`;
  }
  if (state.testnetSoakError && !testnetSoakData(data)) {
    return `
      <section class="cockpit-card span-3 testnet-soak-card blocked">
        <div class="panel-head"><h2>TestNet Soak</h2><span>Unavailable</span></div>
        <p class="deck-note">Ops soak evidence failed: ${escapeHtml(state.testnetSoakError)}</p>
        ${SourceBadge("unavailable")}
      </section>`;
  }
  const soak = testnetSoakData(data);
  if (!soak) {
    return `
      <section class="cockpit-card span-3 testnet-soak-card wait">
        <div class="panel-head"><h2>TestNet Soak</h2><span>No evidence</span></div>
        <p class="deck-note">No stored soak observations yet. Start the local runner with <code>python -m algopulse.testnet_soak --once</code> or a 24h duration.</p>
        <div class="testnet-soak-lock"><span>Live execution</span><strong>Locked</strong></div>
        ${SourceBadge("unavailable")}
      </section>`;
  }

  const source = normalizeSourceLabel(soak.source || "stored");
  const gateStatus = soak.gateStatus || soak.currentGateStatus || "in_progress";
  const tone = gateStatus === "ready_for_review" ? "ok" : gateStatus === "blocked" ? "blocked" : "wait";
  const coverage = source === "mock" ? 0 : Number(soak.coveragePercent || 0);
  const elapsedHours = Number(soak.elapsedCoverageSeconds || 0) / 3600;
  const expected = Number(soak.expectedObservationCount || 0);
  const completed = Number(soak.completedObservationCount || 0);
  const blockers = soak.blockers || [];
  const warnings = soak.warnings || [];
  const connectors = soak.connectors || {};
  const tinyman = connectors.tinyman || {};
  const pact = connectors.pact || {};
  const algod = connectors.algod || {};
  const indexer = connectors.indexer || {};
  const rejectionReasons = soak.routes?.rejectionReasons || [];
  // Mock evidence can never render as production-ready.
  const sourceLabel = source === "mock" ? "mock" : source;

  return `
    <section class="cockpit-card span-3 testnet-soak-card ${escapeHtml(tone)}">
      <div class="testnet-soak-head">
        <div>
          <p class="eyebrow">Phase 3 evidence</p>
          <h2>TestNet Soak</h2>
          <p>Read-only 24-hour scanner reliability. Runner is local-operator only; this panel never starts trades or wallets.</p>
        </div>
        <div class="testnet-soak-score ${escapeHtml(tone)}">
          <span>24h coverage</span>
          <strong>${fmt.format(Math.min(100, coverage))}%</strong>
          <em>${escapeHtml(gateStatus)}</em>
        </div>
      </div>
      <div class="testnet-soak-progress" aria-hidden="true">
        <div style="width:${Math.max(0, Math.min(100, coverage))}%"></div>
      </div>
      <div class="testnet-soak-metrics">
        <article>
          <span>Runner</span>
          <strong>${escapeHtml(soak.runnerState || "idle")}</strong>
        </article>
        <article>
          <span>Elapsed</span>
          <strong>${fmt.format(elapsedHours)}h</strong>
        </article>
        <article>
          <span>Observations</span>
          <strong>${fmt.format(completed)} / ${fmt.format(expected || completed || 0)}</strong>
        </article>
        <article>
          <span>Longest gap</span>
          <strong>${fmt.format(Number(soak.longestGapSeconds || 0))}s</strong>
        </article>
        <article>
          <span>Scanner success</span>
          <strong>${fmt.format(Number(soak.scannerSuccessRate || 0) * 100)}%</strong>
        </article>
        <article>
          <span>Fresh quotes</span>
          <strong>${fmt.format(Number(soak.freshQuotePercent || 0))}%</strong>
        </article>
      </div>
      <div class="testnet-soak-grid">
        <article>
          <span>Algod</span>
          <strong>ok ${fmt.format(algod.ok || 0)} / err ${fmt.format(algod.error || 0)}</strong>
        </article>
        <article>
          <span>Indexer</span>
          <strong>ok ${fmt.format(indexer.ok || 0)} / err ${fmt.format(indexer.error || 0)}</strong>
        </article>
        <article>
          <span>Tinyman</span>
          <strong>ok ${fmt.format(tinyman.ok || 0)} / deg ${fmt.format(tinyman.degraded || 0)} / err ${fmt.format(tinyman.error || 0)}</strong>
        </article>
        <article>
          <span>Pact</span>
          <strong>ok ${fmt.format(pact.ok || 0)} / deg ${fmt.format(pact.degraded || 0)} / err ${fmt.format(pact.error || 0)}</strong>
        </article>
        <article>
          <span>Pools / quotes</span>
          <strong>${fmt.format(soak.poolsObserved || 0)} / ${fmt.format(soak.quotesObserved || 0)}</strong>
        </article>
        <article>
          <span>Stale quotes</span>
          <strong>${fmt.format(soak.staleQuoteCount || 0)}</strong>
        </article>
        <article>
          <span>Routes</span>
          <strong>${fmt.format(soak.routes?.candidateCount || 0)} cand / ${fmt.format(soak.routes?.rejectedCount || 0)} rej</strong>
        </article>
        <article>
          <span>Paper T+5 / T+30</span>
          <strong>${fmt.format(soak.paper?.recheckCompleted5s || 0)} / ${fmt.format(soak.paper?.recheckCompleted30s || 0)}</strong>
        </article>
      </div>
      <div class="testnet-soak-reasons">
        <div>
          <span>Blockers</span>
          <strong>${escapeHtml(blockers.length ? blockers.join(" / ") : "none")}</strong>
        </div>
        <div>
          <span>Warnings</span>
          <strong>${escapeHtml(warnings.length ? warnings.join(" / ") : "none")}</strong>
        </div>
        <div>
          <span>Top rejections</span>
          <strong>${escapeHtml(
            rejectionReasons.length
              ? rejectionReasons
                  .slice(0, 3)
                  .map((item) => `${item.reason}:${item.count}`)
                  .join(" / ")
              : "none"
          )}</strong>
        </div>
      </div>
      ${TestnetSoakObservationTape(data)}
      <div class="testnet-soak-footer">
        <div class="testnet-soak-lock">
          <span>Live execution</span>
          <strong>Locked</strong>
        </div>
        <div class="testnet-soak-source-row">
          ${SourceBadge(sourceLabel)}
          <span>productionReady=false</span>
        </div>
      </div>
      ${TestnetSoakObservationTape(data)}
    </section>`;
}

function replayLabData() {
  return state.replayLab || { replays: [], compareDefaults: [], verdictCounts: {}, source: "unavailable" };
}

function selectedReplay() {
  const replays = replayLabData().replays || [];
  return replays.find((item) => item.id === state.selectedReplayId) || replays[0] || null;
}

function replayStepFor(replay) {
  const maxStep = Math.max(0, (replay?.timeline || []).length - 1);
  state.replayStep = Math.max(0, Math.min(maxStep, Number(state.replayStep || 0)));
  return state.replayStep;
}

function stopReplayPlayback() {
  if (state.replayPlaybackTimer) {
    clearInterval(state.replayPlaybackTimer);
    state.replayPlaybackTimer = null;
  }
  state.replayPlaying = false;
}

function startReplayPlayback() {
  const replay = selectedReplay();
  if (!replay) return;
  stopReplayPlayback();
  state.replayPlaying = true;
  state.replayPlaybackTimer = setInterval(() => {
    const current = selectedReplay();
    const maxStep = Math.max(0, (current?.timeline || []).length - 1);
    state.replayStep = state.replayStep >= maxStep ? 0 : state.replayStep + 1;
    renderRoleDashboard();
  }, 1400);
  renderRoleDashboard();
}

function replayVerdictTone(verdict) {
  if (verdict === "would_execute") return "ok";
  if (verdict === "unsafe") return "blocked";
  if (verdict === "stale") return "wait";
  return "disabled";
}

function replayVerdictLabel(verdict) {
  const labels = {
    would_execute: "would execute",
    would_skip: "would skip",
    unsafe: "unsafe",
    stale: "stale",
  };
  return labels[verdict] || "review";
}

function replayNumber(value, suffix = "") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "pending";
  return `${fmt.format(Number(value))}${suffix}`;
}

function replaySignedAmount(value, assetId) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "pending";
  return signedAmount(value, assetId);
}

function replayLiquidity(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "pending";
  return money.format(Number(value));
}

function replayPath(replay) {
  const route = replay?.route || [];
  if (!route.length) return assetLabel(replay?.inputAssetId || 0);
  const first = route[0] || {};
  return [assetLabel(first.input_asset_id), ...route.map((leg) => assetLabel(leg.output_asset_id))].join(" -> ");
}

function ReplayRouteLegs(replay) {
  const route = replay?.route || [];
  if (!route.length) return `<p class="muted">No route legs recorded for this replay.</p>`;
  return `
    <div class="replay-route-legs">
      ${route
        .map(
          (leg, index) => `
        <article>
          <span>${escapeHtml(String(leg.venue || `venue ${index + 1}`))}</span>
          <strong>${assetLabel(leg.input_asset_id)} -> ${assetLabel(leg.output_asset_id)}</strong>
          <em>${escapeHtml(leg.pool_id || "pool unknown")}</em>
          <p>${replayNumber(leg.input_amount)} in / ${replayNumber(leg.expected_output)} out / ${replayNumber(leg.price_impact_bps, " bps")} impact</p>
        </article>`
        )
        .join("")}
    </div>`;
}

function ReplayPicker(data, activeReplay) {
  const replays = data.replays || [];
  return `
    <section class="cockpit-card replay-picker">
      <div class="panel-head">
        <h2>Historical Opportunities</h2>
        <span>${fmt.format(replays.length)} loaded</span>
      </div>
      <div class="replay-list">
        ${
          replays.length
            ? replays
                .map((replay) => {
                  const selected = replay.id === activeReplay?.id;
                  const comparing = state.compareReplayIds.includes(replay.id);
                  return `
          <article class="replay-card ${selected ? "active" : ""} ${escapeHtml(replay.verdict || "review")}">
            <button type="button" class="replay-select" data-replay-id="${escapeHtml(replay.id)}">
              <span>${escapeHtml(replay.routeHash || replay.id)}</span>
              <strong>${replaySignedAmount(replay.expectedProfit, replay.inputAssetId)}</strong>
              <em>${escapeHtml(replayPath(replay))}</em>
            </button>
            <div class="replay-card-foot">
              ${statusChip(replayVerdictLabel(replay.verdict), replayVerdictTone(replay.verdict))}
              ${SourceBadge(replay.source || data.source || "unavailable")}
              <button type="button" class="mini-button ${comparing ? "active" : ""}" data-compare-replay-id="${escapeHtml(replay.id)}">
                ${comparing ? "Comparing" : "Compare"}
              </button>
            </div>
          </article>`;
                })
                .join("")
            : `<p class="muted">No paper-trade replay history is available yet. Run paper trading to seed this lab.</p>`
        }
      </div>
    </section>`;
}

function ReplayPlaybackControls(replay, checkpoint, step) {
  const maxStep = Math.max(0, (replay.timeline || []).length - 1);
  return `
    <div class="replay-playback">
      <button type="button" data-replay-action="${state.replayPlaying ? "pause" : "play"}">${state.replayPlaying ? "Pause" : "Play"}</button>
      <button type="button" data-replay-action="pause">Pause</button>
      <input type="range" min="0" max="${maxStep}" step="1" value="${step}" data-replay-scrub aria-label="Scrub replay timeline" />
      <div>
        <span>Now inspecting</span>
        <strong>${escapeHtml(checkpoint?.label || "checkpoint")}</strong>
      </div>
    </div>`;
}

function ReplayTimeline(replay, step) {
  const timeline = replay.timeline || [];
  return `
    <div class="replay-timeline">
      ${timeline
        .map(
          (checkpoint, index) => `
        <button type="button" class="replay-checkpoint ${index === step ? "active" : ""} ${escapeHtml(checkpoint.status || "wait")}" data-replay-step="${index}">
          <span>${escapeHtml(checkpoint.label)}</span>
          <strong>${replaySignedAmount(checkpoint.simulatedProfit ?? checkpoint.expectedProfit, replay.inputAssetId)}</strong>
          <em>${escapeHtml(checkpoint.status || "pending")}</em>
        </button>`
        )
        .join("")}
    </div>`;
}

function ReplayMetrics(replay, checkpoint) {
  const source = replay.source || replayLabData().source || "unavailable";
  const liquidityChange = checkpoint?.poolLiquidityChange ?? replay.poolLiquidityChange;
  const metrics = [
    ["Expected profit", replaySignedAmount(checkpoint?.expectedProfit ?? replay.expectedProfit, replay.inputAssetId), source],
    ["Simulated profit", replaySignedAmount(checkpoint?.simulatedProfit, replay.inputAssetId), source],
    ["Quote decay", replaySignedAmount(checkpoint?.quoteDecay, replay.inputAssetId), source],
    ["Impact change", replayNumber(checkpoint?.priceImpactChangeBps ?? replay.priceImpactChangeBps, " bps"), source],
    ["Pool liquidity", replayLiquidity(checkpoint?.poolLiquidity ?? replay.poolLiquidityLatest), source],
    ["Liquidity change", replayLiquidity(liquidityChange), source],
    ["Route confidence", replayNumber(checkpoint?.routeConfidence ?? replay.routeConfidence, "%"), source],
    ["Verdict", replayVerdictLabel(replay.verdict), source],
  ];
  return `
    <div class="replay-metric-grid">
      ${metrics
        .map(
          ([label, value, itemSource]) => `
        <article>
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
          ${SourceBadge(itemSource)}
        </article>`
        )
        .join("")}
    </div>`;
}

function ReplayCompareGrid(data) {
  const replays = data.replays || [];
  const selected = state.compareReplayIds
    .map((id) => replays.find((replay) => replay.id === id))
    .filter(Boolean)
    .slice(0, 3);
  return `
    <section class="cockpit-card span-3 replay-compare">
      <div class="panel-head">
        <h2>Route Comparison Mode</h2>
        <span>${selected.length}/3 selected</span>
      </div>
      <div class="replay-compare-grid">
        ${
          selected.length
            ? selected
                .map(
                  (replay) => `
          <article class="replay-compare-card ${escapeHtml(replay.verdict || "review")}">
            <div>
              <span>${escapeHtml(replay.routeHash || replay.id)}</span>
              ${SourceBadge(replay.source || data.source || "unavailable")}
            </div>
            <strong>${escapeHtml(replayPath(replay))}</strong>
            <dl>
              <div><dt>Verdict</dt><dd>${escapeHtml(replayVerdictLabel(replay.verdict))}</dd></div>
              <div><dt>Expected</dt><dd>${replaySignedAmount(replay.expectedProfit, replay.inputAssetId)}</dd></div>
              <div><dt>Sim 5s</dt><dd>${replaySignedAmount(replay.simulatedProfit5s, replay.inputAssetId)}</dd></div>
              <div><dt>Sim 30s</dt><dd>${replaySignedAmount(replay.simulatedProfit30s, replay.inputAssetId)}</dd></div>
              <div><dt>Decay 30s</dt><dd>${replaySignedAmount(replay.quoteDecay30s, replay.inputAssetId)}</dd></div>
              <div><dt>Confidence</dt><dd>${replayNumber(replay.routeConfidence, "%")}</dd></div>
            </dl>
            <p>${escapeHtml(replay.verdictReason || "Replay reason pending.")}</p>
          </article>`
                )
                .join("")
            : `<p class="muted">Choose up to three historical opportunities to compare side by side.</p>`
        }
      </div>
    </section>`;
}

function ReplayLab() {
  const data = replayLabData();
  const replay = selectedReplay();
  const loading = state.replayLoading && !state.replayLab;
  const step = replayStepFor(replay);
  const checkpoint = replay?.timeline?.[step] || replay?.timeline?.[0] || null;
  const verdictCounts = data.verdictCounts || {};

  return `
    <section class="cockpit-card span-3 replay-hero">
      <div>
        <p class="eyebrow">Opportunity Replay Lab</p>
        <h2>Why did this route survive or fail?</h2>
        <p>Admin-only paper history replay for quote decay, simulated profit, liquidity change, route confidence, and rejection evidence. This lab does not submit transactions.</p>
      </div>
      <div class="replay-lock">
        <span>Live execution state</span>
        <strong>LOCKED / DISARMED</strong>
        <em>Replay reads stored paper-trade evidence only. Signer, keys, hot wallet, and transaction submission are untouched.</em>
        ${SourceBadge(data.source || "unavailable")}
      </div>
      <div class="replay-verdict-strip">
        ${["would_execute", "would_skip", "unsafe", "stale"]
          .map(
            (verdict) => `
          <div class="${escapeHtml(verdict)}">
            <span>${escapeHtml(replayVerdictLabel(verdict))}</span>
            <strong>${fmt.format(verdictCounts[verdict] || 0)}</strong>
          </div>`
          )
          .join("")}
      </div>
    </section>
    ${
      loading
        ? `<section class="cockpit-card span-3 loading-state"><h2>Loading Replay Lab</h2><p>Reading admin-gated paper-trade history...</p></section>`
        : ""
    }
    ${
      state.replayError
        ? `<section class="cockpit-card span-3 error-state"><h2>Replay endpoint fallback</h2><p>${escapeHtml(state.replayError)}. Showing mock-labeled replay data.</p></section>`
        : ""
    }
    ${ReplayPicker(data, replay)}
    <section class="cockpit-card span-2 replay-inspector">
      <div class="panel-head">
        <h2>${escapeHtml(replay?.routeHash || "No replay selected")}</h2>
        <span>${escapeHtml(replay ? replayVerdictLabel(replay.verdict) : "waiting")}</span>
      </div>
      ${
        replay
          ? `
        <div class="replay-summary-line">
          ${statusChip(replayVerdictLabel(replay.verdict), replayVerdictTone(replay.verdict))}
          ${SourceBadge(replay.source || data.source || "unavailable")}
          <span>${escapeHtml(replayPath(replay))}</span>
        </div>
        ${ReplayPlaybackControls(replay, checkpoint, step)}
        ${ReplayTimeline(replay, step)}
        ${ReplayMetrics(replay, checkpoint)}
        <div class="intent-box">
          <span>Replay verdict</span>
          <strong>${escapeHtml(replay.verdictReason || "Replay reason pending.")}</strong>
          <p>${escapeHtml(replay.skipReason ? `Risk skip reason: ${gateLabel(replay.skipReason)}` : "No skip reason recorded for this replay.")}</p>
        </div>`
          : `<p class="muted">No replay history is available yet.</p>`
      }
    </section>
    <section class="cockpit-card replay-route-map">
      <div class="panel-head">
        <h2>Route Evidence</h2>
        <span>${checkpoint ? escapeHtml(checkpoint.label) : "waiting"}</span>
      </div>
      ${
        replay
          ? `
        <div class="route-confidence-meter" style="--confidence:${Math.max(0, Math.min(100, Number(checkpoint?.routeConfidence ?? replay.routeConfidence ?? 0)))}%">
          <span>Route confidence</span>
          <strong>${replayNumber(checkpoint?.routeConfidence ?? replay.routeConfidence, "%")}</strong>
          <i></i>
        </div>
        ${ReplayRouteLegs(replay)}`
          : `<p class="muted">Select a replay to inspect route legs.</p>`
      }
    </section>
    ${ReplayCompareGrid(data)}`;
}

function marketHeatmapData() {
  return state.marketHeatmap || makeMockMarketHeatmap("Market heatmap has not loaded backend analytics yet.", state.heatmapView);
}

function selectedHeatmapCell() {
  const cells = marketHeatmapData().cells || [];
  return cells.find((cell) => heatmapCellKey(cell) === state.selectedHeatmapCellKey) || cells[0] || null;
}

function heatmapPairLabel(item) {
  const assets = item?.assetIds || [];
  if (assets.length >= 2) return assets.map((id) => assetLabel(id)).join("/");
  return String(item?.pairLabel || item?.label || "pair");
}

function heatmapCellTone(cell) {
  if (!cell) return "quiet";
  return cell.densityLabel || (Number(cell.intensity || 0) > 0.7 ? "hot" : Number(cell.intensity || 0) > 0.35 ? "active" : "watch");
}

function HeatmapHero(data) {
  const totals = data.totals || {};
  const liveExecutionLabel = data.liveExecutionTouched === false ? "Live execution untouched" : "Execution boundary review";
  const signerLabel = data.signerCodeTouched === false ? "Signer untouched" : "Signer boundary review";
  return `
    <section class="cockpit-card span-3 heatmap-hero">
      <div>
        <p class="eyebrow">Market Pulse Heatmap</p>
        <h2>Where is opportunity activity forming?</h2>
        <p>Read-only analytics by pair, venue, and time. Color intensity follows opportunity density, not execution readiness.</p>
      </div>
      <div class="heatmap-window-controls" aria-label="Heatmap time window">
        ${(data.views || ["1h", "6h", "24h", "7d"])
          .map(
            (view) => `
          <button type="button" class="${view === data.view ? "active" : ""}" data-heatmap-view="${escapeHtml(view)}">${escapeHtml(view)}</button>`
          )
          .join("")}
        ${SourceBadge(data.source || "unavailable")}
      </div>
      <div class="heatmap-safety-strip" aria-label="Heatmap safety boundary">
        ${statusChip("Analytics only", "wait")}
        ${statusChip(liveExecutionLabel, data.liveExecutionTouched === false ? "ok" : "blocked")}
        ${statusChip(signerLabel, data.signerCodeTouched === false ? "ok" : "blocked")}
      </div>
      <div class="heatmap-summary-strip">
        ${TraceableMetricArticle({ label: "Opportunities", value: fmt.format(totals.opportunityCount || 0), source: data.source || "unavailable", metricKey: "route.count", className: "" })}
        ${TraceableMetricArticle({ label: "Active cells", value: fmt.format(totals.activeCells || 0), source: data.source || "unavailable", metricKey: "route.count", className: "" })}
        ${TraceableMetricArticle({ label: "Avg spread", value: `${fmt.format(totals.averageSpreadBps || 0)} bps`, source: data.source || "unavailable", metricKey: "route.expected_profit_bps", className: "" })}
        ${TraceableMetricArticle({ label: "Paper win", value: `${fmt.format(Number(totals.paperWinRate || 0) * 100)}%`, source: data.source || "unavailable", metricKey: "paper.checked_30s_count", className: "" })}
      </div>
    </section>`;
}

function heatmapRows(data) {
  const cells = data.cells || [];
  const rowMap = new Map();
  cells.forEach((cell) => {
    const key = `${cell.pairKey}|${cell.venue}`;
    const row = rowMap.get(key) || {
      key,
      pairKey: cell.pairKey,
      pairLabel: heatmapPairLabel(cell),
      venue: cell.venue,
      assetIds: cell.assetIds || [],
      opportunityCount: 0,
      cells: new Map(),
    };
    row.opportunityCount += Number(cell.opportunityCount || 0);
    row.cells.set(Number(cell.bucketIndex), cell);
    rowMap.set(key, row);
  });
  return [...rowMap.values()].sort((a, b) => b.opportunityCount - a.opportunityCount).slice(0, 10);
}

function MarketHeatmapGrid(data) {
  const buckets = data.timeBuckets || [];
  const rows = heatmapRows(data);
  return `
    <section class="cockpit-card span-2 heatmap-grid-card">
      <div class="panel-head">
        <h2>Density Map</h2>
        <span>${escapeHtml(data.view || "24h")} / ${fmt.format(rows.length)} rows</span>
      </div>
      ${
        rows.length
          ? `
        <div class="heatmap-grid" style="--bucket-count:${Math.max(1, buckets.length)}">
          <div class="heatmap-axis-spacer"></div>
          <div class="heatmap-time-axis">
            ${buckets.map((bucket) => `<span>${escapeHtml(bucket.label || "")}</span>`).join("")}
          </div>
          ${rows
            .map(
              (row) => `
          <div class="heatmap-row-label">
            <strong>${escapeHtml(row.pairLabel)}</strong>
            <span>${escapeHtml(row.venue)} / ${fmt.format(row.opportunityCount)}</span>
          </div>
          <div class="heatmap-row">
            ${buckets
              .map((bucket) => {
                const cell = row.cells.get(Number(bucket.index));
                const key = heatmapCellKey(cell) || `${row.key}|${bucket.index}`;
                const intensity = Math.max(0, Math.min(1, Number(cell?.intensity || 0)));
                return `
              <button
                type="button"
                class="heatmap-cell ${cell ? heatmapCellTone(cell) : "empty"} ${key === state.selectedHeatmapCellKey ? "active" : ""}"
                style="--heat:${intensity}"
                data-heatmap-cell-key="${escapeHtml(key)}"
                ${cell ? "" : "disabled"}
                title="${cell ? `${row.pairLabel} ${row.venue}: ${fmt.format(cell.opportunityCount)} routes` : "No activity"}"
              >
                <span>${cell ? fmt.format(cell.opportunityCount) : ""}</span>
              </button>`;
              })
              .join("")}
          </div>`
            )
            .join("")}
        </div>`
          : `<p class="muted">No stored opportunity activity exists for this window yet.</p>`
      }
    </section>`;
}

function HeatmapInspector(cell) {
  const paper = cell?.paperTradePerformance || {};
  return `
    <section class="cockpit-card heatmap-inspector">
      <div class="panel-head">
        <h2>Hot Cell</h2>
        <span>${cell ? escapeHtml(heatmapCellTone(cell)) : "waiting"}</span>
      </div>
      ${
        cell
          ? `
        <div class="heatmap-cell-title">
          ${statusChip(heatmapCellTone(cell), heatmapCellTone(cell) === "hot" ? "ok" : "wait")}
          ${SourceBadge(cell.source || "unavailable")}
          <strong>${escapeHtml(heatmapPairLabel(cell))}</strong>
          <span>${escapeHtml(cell.venue)}</span>
        </div>
        <div class="heatmap-metric-stack">
          ${TraceableMetricArticle({ label: "Spread frequency", value: `${fmt.format(cell.spreadFrequency || 0)} / hr`, source: cell.source || "unavailable", metricKey: "route.count", className: "" })}
          ${TraceableMetricArticle({ label: "Average spread", value: `${fmt.format(cell.averageSpreadBps || 0)} bps`, source: cell.source || "unavailable", metricKey: "route.expected_profit_bps", className: "" })}
          ${TraceableMetricArticle({ label: "Average route count", value: fmt.format(cell.averageRouteCount || 0), source: cell.source || "unavailable", metricKey: "route.count", className: "" })}
          ${TraceableMetricArticle({ label: "Opportunity half-life", value: `${fmt.format(cell.opportunityHalfLifeSeconds || 0)}s`, source: cell.source || "unavailable", metricKey: "paper.checked_30s_count", className: "" })}
          ${TraceableMetricArticle({ label: "Paper performance", value: `${fmt.format(Number(paper.winRate || 0) * 100)}%`, source: cell.source || "unavailable", metricKey: "paper.checked_30s_count", className: "" })}
          ${TraceableMetricArticle({ label: "Simulated 30s", value: fmt.format(paper.averageSimulated30s || 0), source: cell.source || "unavailable", metricKey: "paper.checked_30s_count", className: "" })}
        </div>`
          : `<p class="muted">Select a heatmap cell to inspect its route activity.</p>`
      }
    </section>`;
}

function HeatmapSummaryPanels(data) {
  const pairs = data.pairSummaries || [];
  const venues = data.venueSummaries || [];
  const summaryList = (items, kind) => `
    <div class="heatmap-summary-list">
      ${items.length
        ? items
            .slice(0, 6)
            .map(
              (item) => `
        <article>
          <span>${escapeHtml(kind)}</span>
          <strong>${escapeHtml(kind === "pair" ? heatmapPairLabel(item) : item.label)}</strong>
          <em>${fmt.format(item.opportunityCount || 0)} opps / ${fmt.format(item.averageSpreadBps || 0)} bps / ${fmt.format(item.averageHalfLifeSeconds || 0)}s half-life</em>
        </article>`
            )
            .join("")
        : `<p class="muted">No ${escapeHtml(kind)} activity in this window.</p>`}
    </div>`;
  return `
    <section class="cockpit-card heatmap-summary-card">
      <div class="panel-head">
        <h2>Pairs</h2>
        <span>${fmt.format(pairs.length)}</span>
      </div>
      ${summaryList(pairs, "pair")}
    </section>
    <section class="cockpit-card heatmap-summary-card">
      <div class="panel-head">
        <h2>Venues</h2>
        <span>${fmt.format(venues.length)}</span>
      </div>
      ${summaryList(venues, "venue")}
    </section>`;
}

function MarketPulseHeatmap() {
  const data = marketHeatmapData();
  const cell = selectedHeatmapCell();
  return `
    ${HeatmapHero(data)}
    ${
      state.marketHeatmapLoading && !state.marketHeatmap
        ? `<section class="cockpit-card span-3 loading-state"><h2>Loading Heatmap</h2><p>Aggregating stored opportunities by pair, venue, and time...</p></section>`
        : ""
    }
    ${
      state.marketHeatmapError
        ? `<section class="cockpit-card span-3 error-state"><h2>Heatmap fallback</h2><p>${escapeHtml(state.marketHeatmapError)}. Showing mock-labeled heatmap data.</p></section>`
        : ""
    }
    ${MarketHeatmapGrid(data)}
    ${HeatmapInspector(cell)}
    ${HeatmapSummaryPanels(data)}`;
}

function researchArchiveData() {
  return state.researchArchive || makeMockResearchArchive("Research archive has not loaded stored reports yet.");
}

function selectedResearchReport() {
  const reports = researchArchiveData().reports || [];
  return reports.find((report) => report.reportDate === state.selectedReportDate) || reports[0] || null;
}

function signedPercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "unavailable";
  return `${numeric > 0 ? "+" : ""}${fmt.format(numeric)}%`;
}

function marketContextTone(context) {
  if (!context || context.availability !== "available") return "unavailable";
  const change = Number(context.change24hPct);
  if (!Number.isFinite(change)) return "unavailable";
  if (change > 0) return "ok";
  if (change < 0) return "blocked";
  return "wait";
}

function MarketContextRibbon(report) {
  const context = report?.marketContextRibbon;
  if (!context) return "";
  const tone = marketContextTone(context);
  const available = tone !== "unavailable";
  return `
    <section class="cockpit-card span-3 market-context-ribbon ${available ? "available" : "unavailable"}">
      <div class="market-context-meta">
        <div>
          <p class="eyebrow">${escapeHtml(context.title || "External cached market context")}</p>
          <strong>${escapeHtml(context.symbol || "ALGO")} delayed context</strong>
        </div>
        <div class="market-context-badges">
          <span class="source-badge delayed">${escapeHtml(context.sourceLabel || "CoinMarketCap cached context")}</span>
          ${statusChip(context.snapshotAgeLabel || "unavailable", available ? "wait" : "blocked")}
        </div>
      </div>
      <div class="market-context-main">
        <div class="market-context-asset">
          <span>${escapeHtml(context.symbol || "ALGO")} 24h</span>
          <strong class="${escapeHtml(tone)}">${signedPercent(context.change24hPct)}</strong>
        </div>
        <div class="market-context-label">
          <span>Context label</span>
          <strong>${escapeHtml(context.contextLabel || "unavailable")}</strong>
        </div>
        <p>${escapeHtml(context.notice || "External cached market context only. Informational only; not investment or trading advice.")}</p>
      </div>
    </section>`;
}

function ResearchLiveRefreshPanel() {
  const scan = state.researchLiveRefresh;
  const loading = state.researchLiveRefreshLoading;
  const error = state.researchLiveRefreshError;
  const connectors = scan?.connectors || [];
  const sourceLabel = connectors.length ? connectors.join(" / ") : "configured scanner";
  const isMockRefresh = connectors.includes("mock");
  const modeNotice = scan
    ? isMockRefresh
      ? "Current refresh is using mock connector evidence. Restart with ALGO_PULSE_CONNECTORS=tinyman,pact for live read-only DEX data."
      : "Current refresh used configured read-only market connectors."
    : "Uses the server's configured connector mode. Live read-only mode uses ALGO_PULSE_CONNECTORS=tinyman,pact with execution flags still disabled.";
  return `
    <section class="cockpit-card research-live-card">
      <div class="panel-head">
        <h2>Live API Refresh</h2>
        <span>${loading ? "running" : scan ? (isMockRefresh ? "mock source" : "live source") : "available"}</span>
      </div>
      <p class="deck-note">Runs the existing read-only scanner, stores fresh pool/route evidence, then regenerates this delayed market summary. It does not sign, submit, trade, or expose fresh executable routes.</p>
      <p class="deck-note">${escapeHtml(modeNotice)}</p>
      <button type="button" data-research-action="refresh-live" ${loading ? "disabled" : ""}>${loading ? "Refreshing..." : "Refresh live summary"}</button>
      ${
        error
          ? `<div class="utility-status-line blocked"><span></span><strong>${escapeHtml(error)}</strong></div>`
          : scan
            ? `<div class="research-live-grid">
                <div><span>Source</span><strong>${escapeHtml(sourceLabel)}</strong></div>
                <div><span>Pools</span><strong>${fmt.format(scan.pools || 0)}</strong></div>
                <div><span>Opportunities</span><strong>${fmt.format(scan.opportunities || 0)}</strong></div>
                <div><span>Approved</span><strong>${fmt.format(scan.approved || 0)}</strong></div>
                <div><span>Target ASA</span><strong>${escapeHtml(scan.target_asset_id || APP_CONFIG.PNET_ASA_ID)}</strong></div>
                <div><span>Refreshed</span><strong>${scan.refreshedAt ? ago(scan.refreshedAt) : "just now"}</strong></div>
              </div>`
            : `<div class="utility-status-line wait"><span></span><strong>Use this to pull fresh read-only scanner evidence into the report.</strong></div>`
      }
    </section>`;
}

function ResearchArchiveHero(data, report) {
  const summary = report?.marketSummary || report?.summary || {};
  return `
    <section class="cockpit-card span-3 research-hero">
      <div>
        <p class="eyebrow">Research Archive</p>
        <h2>Daily market intelligence that survives the night shift</h2>
        <p>Stored daily reports explain market activity, spreads, liquidity movement, paper results, scanner health, and risk events without touching execution.</p>
      </div>
      <div class="research-export-panel">
        <div>
          ${SourceBadge(data.source || report?.source || "unavailable")}
          ${statusChip("Public-safe report", "ok")}
          ${statusChip(report?.liveExecutionTouched === false ? "Live execution untouched" : "Execution boundary review", report?.liveExecutionTouched === false ? "ok" : "blocked")}
          ${statusChip(report?.signerCodeTouched === false ? "Signer untouched" : "Signer boundary review", report?.signerCodeTouched === false ? "ok" : "blocked")}
        </div>
        <div class="research-export-actions">
          <a href="${escapeHtml(report?.exports?.json || "/api/reports/market/daily/export?format=json")}" target="_blank" rel="noreferrer">JSON</a>
          <a href="${escapeHtml(report?.exports?.markdown || "/api/reports/market/daily/export?format=markdown")}" target="_blank" rel="noreferrer">Markdown</a>
        </div>
      </div>
      <div class="research-summary-strip">
        <div><span>Report date</span><strong>${escapeHtml(report?.reportDate || "waiting")}</strong></div>
        ${TraceableMetricArticle({ label: "Opportunities", value: fmt.format(summary.opportunityCount || 0), source: data.source || report?.source || "unavailable", metricKey: "route.count", className: "" })}
        <div><span>Top pair</span><strong>${escapeHtml(summary.topPair || "none")}</strong></div>
        ${TraceableMetricArticle({ label: "Paper 30s win", value: `${fmt.format(Number(summary.paperWinRate30s || 0) * 100)}%`, source: data.source || report?.source || "unavailable", metricKey: "paper.checked_30s_count", className: "" })}
      </div>
    </section>`;
}

function ResearchReportList(data) {
  const reports = data.reports || [];
  return `
    <section class="cockpit-card research-list-card">
      <div class="panel-head">
        <h2>Stored Reports</h2>
        <span>${fmt.format(reports.length)} days</span>
      </div>
      <div class="research-report-list">
        ${
          reports.length
            ? reports
                .map((report) => {
                  const summary = report.summary || report.marketSummary || {};
                  return `
          <button type="button" class="${report.reportDate === state.selectedReportDate ? "active" : ""}" data-report-date="${escapeHtml(report.reportDate)}">
            <span>${escapeHtml(report.reportDate)}</span>
            <strong>${escapeHtml(summary.headline || "Market report")}</strong>
            <em>${fmt.format(summary.opportunityCount || 0)} opps / ${escapeHtml(summary.scannerStatus || "unknown")}</em>
          </button>`;
                })
                .join("")
            : `<p class="muted">No stored daily reports yet. The archive endpoint will create today's report from stored evidence.</p>`
        }
      </div>
    </section>`;
}

function ResearchSummary(report) {
  const summary = report?.marketSummary || {};
  const scanner = report?.scannerHealth || {};
  const counts = report?.opportunityCounts || {};
  const route = report?.routePerformance || {};
  const paper = report?.paperTradePerformance || {};
  return `
    <section class="cockpit-card span-2 research-summary-card">
      <div class="panel-head">
        <h2>Market Summary</h2>
        <span>${escapeHtml(report?.reportDate || "waiting")}</span>
      </div>
      <p class="research-narrative">${escapeHtml(summary.narrative || "No stored report selected.")}</p>
      <div class="research-metric-grid">
        ${TraceableMetricArticle({ label: "Scanner", value: `${fmt.format(scanner.poolsScanned || 0)} pools`, source: report?.source || "unavailable", metricKey: "scanner.pool_count", className: "" })}
        ${TraceableMetricArticle({ label: "Opportunities", value: fmt.format(counts.total || 0), source: report?.source || "unavailable", metricKey: "route.count", className: "" })}
        ${TraceableMetricArticle({ label: "Routes", value: fmt.format(route.routeCount || 0), source: report?.source || "unavailable", metricKey: "route.count", className: "" })}
        ${TraceableMetricArticle({ label: "Paper", value: `${fmt.format(paper.checked30s || 0)} checks`, source: report?.source || "unavailable", metricKey: "paper.checked_30s_count", className: "" })}
      </div>
    </section>`;
}

function ResearchTable({ title, eyebrow, columns, rows, renderRow }) {
  return `
    <section class="cockpit-card research-table-card">
      <div class="panel-head">
        <h2>${escapeHtml(title)}</h2>
        <span>${escapeHtml(eyebrow)}</span>
      </div>
      <div class="research-table" style="--column-count:${columns.length}">
        <div class="research-table-head">
          ${columns.map((column) => `<span>${escapeHtml(column)}</span>`).join("")}
        </div>
        ${
          rows?.length
            ? rows.map(renderRow).join("")
            : `<p class="muted">No stored records for this section.</p>`
        }
      </div>
    </section>`;
}

function PnetLiquidityWatchlist(report) {
  const watchlist = report?.pnetLiquidityWatchlist || {};
  const pools = watchlist.pools || [];
  return `
    <section class="cockpit-card span-3 research-pnet-card">
      <div class="panel-head">
        <h2>PNET Liquidity Watchlist</h2>
        <span>${fmt.format(watchlist.poolCount || pools.length || 0)} pools</span>
      </div>
      <p class="deck-note">${escapeHtml(
        watchlist.notice || "PNET pool visibility is informational only; it is not investment advice, ROI guidance, or a request to trade."
      )}</p>
      <p class="deck-note">${escapeHtml(
        watchlist.lpRiskNotice || "Adding liquidity can lose value through price movement, fees, and impermanent loss. Review pool terms independently."
      )}</p>
      <div class="pnet-watch-summary">
        <div><span>Total observed PNET</span><strong>${fmt.format(watchlist.totalPnetReserve || 0)}</strong></div>
        <div><span>Source</span><strong>${escapeHtml(watchlist.source || report?.source || "stored")}</strong></div>
        <div><span>Shown without arb</span><strong>${watchlist.listedWithoutOpportunity === false ? "no" : "yes"}</strong></div>
      </div>
      <div class="pnet-watch-grid">
        ${
          pools.length
            ? pools
                .slice(0, 8)
                .map(
                  (item) => `
          <article>
            <span>${escapeHtml(item.venue || "unknown")}</span>
            <strong>${escapeHtml(item.pairLabel || "PNET pool")}</strong>
            <div><em>PNET reserve</em><b>${fmt.format(item.pnetReserve || 0)}</b></div>
            <div><em>Other reserve</em><b>${fmt.format(item.otherReserve || 0)}</b></div>
            <div><em>Liquidity</em><b>${fmt.format(item.liquidityEstimate || 0)}</b></div>
            <p>${escapeHtml(item.lpVisibilityNote || "Observed PNET liquidity surface; LP participation has risk and needs independent review.")}</p>
          </article>`
                )
                .join("")
            : `<p class="muted">No PNET pools were observed in this report window. Run a live read-only refresh with Vestige discovery enabled.</p>`
        }
      </div>
    </section>`;
}

function ResearchReportDetail(report) {
  if (!report) {
    return `<section class="cockpit-card span-2 empty-state"><h2>No report selected</h2><p>Run the archive endpoint after market data exists.</p></section>`;
  }
  const pairRows = report.topPairs || [];
  const spreadRows = report.topSpreads || [];
  const liquidityRows = report.liquidityChanges || [];
  const riskRows = report.riskEvents || [];
  return `
    ${ResearchSummary(report)}
    ${PnetLiquidityWatchlist(report)}
    ${ResearchTable({
      title: "Top Pairs",
      eyebrow: "activity",
      columns: ["Pair", "Opps", "Avg bps", "Best", "Paper"],
      rows: pairRows.slice(0, 6),
      renderRow: (item) => `
        <div class="research-table-row">
          <strong>${escapeHtml(item.pairLabel || "unknown")}</strong>
          <span>${fmt.format(item.opportunityCount || 0)}</span>
          <span>${fmt.format(item.averageSpreadBps || 0)}</span>
          <span>${fmt.format(item.bestSpreadBps || 0)}</span>
          <span>${fmt.format(Number(item.paperWinRate30s || 0) * 100)}%</span>
        </div>`,
    })}
    ${ResearchTable({
      title: "Top Spreads",
      eyebrow: "route candidates",
      columns: ["Pair", "Venues", "Bps", "Net", "Risk"],
      rows: spreadRows.slice(0, 6),
      renderRow: (item) => `
        <div class="research-table-row">
          <strong>${escapeHtml(item.pairLabel || "unknown")}</strong>
          <span>${escapeHtml(item.venues || "unknown")}</span>
          <span>${fmt.format(item.expectedProfitBps || 0)}</span>
          <span>${fmt.format(item.expectedNetProfit || 0)}</span>
          <span>${escapeHtml(item.skipReason || item.status || "none")}</span>
        </div>`,
    })}
    ${ResearchTable({
      title: "Liquidity Changes",
      eyebrow: "pool movement",
      columns: ["Pool", "Pair", "Venue", "Change", "Snapshots"],
      rows: liquidityRows.slice(0, 6),
      renderRow: (item) => `
        <div class="research-table-row">
          <strong>${escapeHtml(item.poolId || "unknown")}</strong>
          <span>${escapeHtml(item.pairLabel || "unknown")}</span>
          <span>${escapeHtml(item.venue || "unknown")}</span>
          <span>${fmt.format(item.changePct || 0)}%</span>
          <span>${fmt.format(item.snapshotCount || 0)}</span>
        </div>`,
    })}
    ${ResearchTable({
      title: "Risk Events",
      eyebrow: "reject-first signal",
      columns: ["Reason", "Count", "Approved", "State", "Latest"],
      rows: riskRows.slice(0, 6),
      renderRow: (item) => `
        <div class="research-table-row">
          <strong>${escapeHtml(item.reason || "unknown")}</strong>
          <span>${fmt.format(item.count || 0)}</span>
          <span>${item.approved ? "yes" : "no"}</span>
          <span>${item.approved ? "passed" : "blocked"}</span>
          <span>${item.latestAt ? ago(Number(item.latestAt)) : "stored"}</span>
        </div>`,
    })}`;
}

function ResearchArchive() {
  const data = researchArchiveData();
  const report = selectedResearchReport();
  return `
    ${ResearchArchiveHero(data, report)}
    ${ResearchLiveRefreshPanel()}
    ${
      state.researchArchiveLoading && !state.researchArchive
        ? `<section class="cockpit-card span-3 loading-state"><h2>Loading Research Archive</h2><p>Generating daily report from stored market evidence...</p></section>`
        : ""
    }
    ${
      state.researchArchiveError
        ? `<section class="cockpit-card span-3 error-state"><h2>Research fallback</h2><p>${escapeHtml(state.researchArchiveError)}. Showing mock-labeled report data.</p></section>`
        : ""
    }
    ${ResearchReportList(data)}
    ${MarketContextRibbon(report)}
    ${ResearchReportDetail(report)}`;
}

function failureLabData() {
  return state.failureLab || makeMockFailureLab("Failure Lab has not loaded backend simulation data yet.");
}

function selectedFailureScenario() {
  const scenarios = failureLabData().scenarios || [];
  return scenarios.find((scenario) => scenario.key === state.selectedFailureKey) || scenarios[0] || null;
}

function FailureLabHero(data) {
  const summary = data.summary || {};
  return `
    <section class="cockpit-card span-3 failure-hero">
      <div>
        <p class="eyebrow">Failure Lab</p>
        <h2>Operational resilience without touching execution</h2>
        <p>Simulated connector, freshness, storage, route, signer-boundary, allowlist, and loss-limit failures prove graceful degradation before production pressure.</p>
      </div>
      <div class="failure-summary-grid">
        <article><span>Scenarios</span><strong>${fmt.format(summary.scenarioCount || 0)}</strong></article>
        <article><span>Graceful</span><strong>${fmt.format(summary.gracefulPercent || 0)}%</strong></article>
        <article><span>Critical</span><strong>${fmt.format(summary.criticalCount || 0)}</strong></article>
        <article><span>Blocked/locked</span><strong>${fmt.format(summary.blockedCount || 0)}</strong></article>
      </div>
      <div class="failure-safety-strip">
        ${SourceBadge(data.source || "unavailable")}
        ${statusChip(data.mode || "simulation", "wait")}
        ${statusChip(data.liveExecutionTouched === false ? "Live execution untouched" : "Execution boundary review", data.liveExecutionTouched === false ? "ok" : "blocked")}
        ${statusChip(data.signerCodeTouched === false ? "Signer untouched" : "Signer boundary review", data.signerCodeTouched === false ? "ok" : "blocked")}
      </div>
    </section>`;
}

function FailureScenarioList(data) {
  const scenarios = data.scenarios || [];
  return `
    <section class="cockpit-card failure-list-card">
      <div class="panel-head">
        <h2>Simulation Scenarios</h2>
        <span>${fmt.format(scenarios.length)} cases</span>
      </div>
      <div class="failure-scenario-list">
        ${
          scenarios.length
            ? scenarios
                .map(
                  (scenario) => `
          <button type="button" class="${scenario.key === state.selectedFailureKey ? "active" : ""}" data-failure-key="${escapeHtml(scenario.key)}">
            <span>${escapeHtml(scenario.severity || "info")}</span>
            <strong>${escapeHtml(scenario.label || scenario.key)}</strong>
            <em>${escapeHtml(scenario.actualResponse?.status || "waiting")} / ${fmt.format((scenario.alertsGenerated || []).length)} alerts</em>
          </button>`
                )
                .join("")
            : `<p class="muted">No failure simulations available.</p>`
        }
      </div>
    </section>`;
}

function FailureResponseCard(title, response, tone) {
  return `
    <article class="failure-response-card ${escapeHtml(tone)}">
      <div>
        <span>${escapeHtml(title)}</span>
        ${statusChip(response?.status || "waiting", serviceTone(response?.status || tone))}
      </div>
      <strong>${response?.blocksLiveExecution ? "Blocks live execution" : "Review boundary"}</strong>
      <p>${escapeHtml(response?.message || "Response evidence pending.")}</p>
    </article>`;
}

function FailureScenarioDetail(scenario) {
  if (!scenario) {
    return `<section class="cockpit-card span-2 empty-state"><h2>No scenario selected</h2><p>Load the Failure Lab endpoint to inspect resilience evidence.</p></section>`;
  }
  const actualTone = scenario.gracefulDegradation ? "ok" : "blocked";
  return `
    <section class="cockpit-card span-2 failure-detail-card">
      <div class="panel-head">
        <h2>${escapeHtml(scenario.label || "Failure scenario")}</h2>
        <span>${escapeHtml(scenario.failureType || "simulation")}</span>
      </div>
      <div class="failure-trigger">
        ${statusChip(scenario.severity || "info", alertSeverityClass(scenario.severity))}
        ${SourceBadge(scenario.source || "unavailable")}
        <p>${escapeHtml(scenario.trigger || "No trigger recorded.")}</p>
      </div>
      <div class="failure-response-grid">
        ${FailureResponseCard("Expected response", scenario.expectedResponse, "wait")}
        ${FailureResponseCard("Actual response", scenario.actualResponse, actualTone)}
      </div>
      <div class="failure-operator-action">
        <span>Operator action</span>
        <strong>${escapeHtml(scenario.operatorAction || "Review failure evidence.")}</strong>
      </div>
    </section>
    <section class="cockpit-card failure-alert-card">
      <div class="panel-head">
        <h2>Alerts Generated</h2>
        <span>${fmt.format((scenario.alertsGenerated || []).length)} emitted</span>
      </div>
      <div class="failure-alert-list">
        ${(scenario.alertsGenerated || [])
          .map((alert) => `<span>${escapeHtml(alert)}</span>`)
          .join("") || `<p class="muted">No alert evidence generated.</p>`}
      </div>
    </section>
    <section class="cockpit-card failure-services-card">
      <div class="panel-head">
        <h2>Services Affected</h2>
        <span>${scenario.gracefulDegradation ? "graceful" : "review"}</span>
      </div>
      <div class="failure-service-list">
        ${(scenario.servicesAffected || [])
          .map((service) => `<span>${escapeHtml(service)}</span>`)
          .join("") || `<p class="muted">No affected services recorded.</p>`}
      </div>
      <div class="failure-lock-proof ${scenario.gracefulDegradation ? "ok" : "blocked"}">
        <strong>${scenario.gracefulDegradation ? "Graceful degradation demonstrated" : "Graceful degradation needs review"}</strong>
        <span>Live execution remains locked. Signer and hot-wallet code remain untouched.</span>
      </div>
    </section>`;
}

function FailureLab() {
  const data = failureLabData();
  const scenario = selectedFailureScenario();
  return `
    ${FailureLabHero(data)}
    ${
      state.failureLabLoading && !state.failureLab
        ? `<section class="cockpit-card span-3 loading-state"><h2>Loading Failure Lab</h2><p>Reading admin-gated resilience simulation data...</p></section>`
        : ""
    }
    ${
      state.failureLabError
        ? `<section class="cockpit-card span-3 error-state"><h2>Failure Lab fallback</h2><p>${escapeHtml(state.failureLabError)}. Showing mock-labeled resilience simulation.</p></section>`
        : ""
    }
    ${FailureScenarioList(data)}
    ${FailureScenarioDetail(scenario)}`;
}

function provenanceData() {
  return state.dataProvenance || makeMockDataProvenance("Data provenance has not loaded backend lineage yet.", state.selectedProvenanceMetric);
}

function ProvenanceHero(data) {
  const metric = data.selectedMetric || {};
  return `
    <section class="cockpit-card span-3 provenance-hero">
      <div>
        <p class="eyebrow">Data Provenance Viewer</p>
        <h2>Every number needs a receipt.</h2>
        <p>Trace dashboard metrics to source data, quote rows, pool snapshots, route calculation, and risk decision evidence.</p>
      </div>
      <div class="provenance-selected">
        <span>Selected metric</span>
        <strong>${escapeHtml(metric.label || "Metric")}</strong>
        <em>${escapeHtml(metric.value || "unavailable")} ${escapeHtml(metric.unit || "")}</em>
        <div>
          ${SourceBadge(metric.source || data.source || "unavailable")}
          ${statusChip(data.complete ? "Complete lineage" : "Missing evidence", data.complete ? "ok" : "blocked")}
          ${statusChip(data.liveExecutionTouched === false ? "Live execution untouched" : "Execution boundary review", data.liveExecutionTouched === false ? "ok" : "blocked")}
          ${statusChip(data.signerCodeTouched === false ? "Signer untouched" : "Signer boundary review", data.signerCodeTouched === false ? "ok" : "blocked")}
        </div>
      </div>
    </section>`;
}

function ProvenanceMetricCatalog(data) {
  const metrics = data.metrics || [];
  return `
    <section class="cockpit-card provenance-catalog">
      <div class="panel-head">
        <h2>Metric Catalog</h2>
        <span>${fmt.format(metrics.length)} traceable values</span>
      </div>
      <div class="provenance-metric-list">
        ${
          metrics.length
            ? metrics
                .map(
                  (metric) => `
          <button type="button" class="${metric.key === data.selectedMetricKey ? "active" : ""}" data-provenance-metric="${escapeHtml(metric.key)}">
            <span>${escapeHtml(metric.table || "table")} / ${escapeHtml(metric.field || "field")}</span>
            <strong>${escapeHtml(metric.label || metric.key)}</strong>
            <em>${escapeHtml(metric.value || "unavailable")} ${escapeHtml(metric.unit || "")}</em>
            ${SourceBadge(metric.source || "unavailable")}
          </button>`
                )
                .join("")
            : `<p class="muted">No metric catalog loaded.</p>`
        }
      </div>
    </section>`;
}

function ProvenanceRecord(record) {
  const raw = record.raw ? JSON.stringify(record.raw, null, 2) : "";
  return `
    <article class="provenance-record">
      <div>
        <span>${escapeHtml(record.table || "table")} / ${escapeHtml(record.field || "field")}</span>
        <strong>${escapeHtml(record.label || "record")}</strong>
        <p>${escapeHtml(record.detail || "No detail recorded.")}</p>
      </div>
      <div>
        <em>${escapeHtml(record.value || "unavailable")}</em>
        ${SourceBadge(record.source || "unavailable")}
      </div>
      ${raw ? `<details><summary>Raw evidence</summary><pre>${escapeHtml(raw)}</pre></details>` : ""}
    </article>`;
}

function ProvenanceLineage(data) {
  const steps = data.lineage || [];
  return `
    <section class="cockpit-card span-2 provenance-lineage">
      <div class="panel-head">
        <h2>Lineage Chain</h2>
        <span>${escapeHtml(data.routeHash || "aggregate metric")}</span>
      </div>
      <div class="provenance-chain">
        ${
          steps.length
            ? steps
                .map(
                  (step) => `
          <article class="provenance-step ${escapeHtml(step.status || "missing")}">
            <div class="provenance-step-head">
              ${statusChip(step.status || "missing", step.status === "ok" ? "ok" : "blocked")}
              <strong>${escapeHtml(step.label || "Step")}</strong>
              ${SourceBadge(step.source || "unavailable")}
            </div>
            <p>${escapeHtml(step.description || "Lineage step.")}</p>
            <div class="provenance-record-list">
              ${step.records?.length ? step.records.map(ProvenanceRecord).join("") : `<p class="muted">No stored evidence for this step yet.</p>`}
            </div>
          </article>`
                )
                .join("")
            : `<p class="muted">No lineage steps available.</p>`
        }
      </div>
    </section>`;
}

function DataProvenanceViewer() {
  const data = provenanceData();
  return `
    ${ProvenanceHero(data)}
    ${
      state.provenanceLoading && !state.dataProvenance
        ? `<section class="cockpit-card span-3 loading-state"><h2>Loading Data Provenance</h2><p>Tracing metric lineage through stored rows...</p></section>`
        : ""
    }
    ${
      state.provenanceError
        ? `<section class="cockpit-card span-3 error-state"><h2>Provenance fallback</h2><p>${escapeHtml(state.provenanceError)}. Showing mock-labeled lineage.</p></section>`
        : ""
    }
    ${ProvenanceMetricCatalog(data)}
    ${ProvenanceLineage(data)}`;
}

function ProvenanceDrawer(data) {
  const metric = data.selectedMetric || {};
  return `
    <div class="provenance-drawer">
      <div class="provenance-drawer-summary">
        <span>${escapeHtml(metric.table || "table")} / ${escapeHtml(metric.field || "field")}</span>
        <strong>${escapeHtml(metric.label || "Metric")}: ${escapeHtml(metric.value || "unavailable")}</strong>
        <p>${escapeHtml(metric.description || "No metric description recorded.")}</p>
        <div>
          ${SourceBadge(metric.source || data.source || "unavailable")}
          ${statusChip(data.complete ? "complete" : "missing evidence", data.complete ? "ok" : "blocked")}
          ${statusChip("read-only", "wait")}
        </div>
      </div>
      ${ProvenanceLineage(data)}
    </div>`;
}

function routeForensicsData() {
  return state.routeForensics || makeMockRouteForensics("Route forensics has not loaded backend evidence yet.");
}

function selectedForensicsRoute() {
  const routes = routeForensicsData().routes || [];
  return routes.find((item) => String(item.id) === String(state.selectedForensicsId)) || routes[0] || null;
}

function forensicsDecisionTone(route) {
  if (route?.approvalDecision?.approved) return "ok";
  if (route?.rejectionReason && route.rejectionReason !== "none") return "blocked";
  return "wait";
}

function forensicsNumber(value, suffix = "") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "pending";
  return `${fmt.format(Number(value))}${suffix}`;
}

function forensicsRouteLabel(route) {
  const path = route?.routePath || [];
  if (!path.length) return route?.routePathLabel || "path unavailable";
  const first = path[0] || {};
  return [assetLabel(first.inputAssetId), ...path.map((leg) => assetLabel(leg.outputAssetId))].join(" -> ");
}

function ForensicsHero(data) {
  const summary = data.summary || {};
  return `
    <section class="cockpit-card span-3 forensics-hero">
      <div>
        <p class="eyebrow">Route Forensics</p>
        <h2>Every route decision has an evidence trail.</h2>
        <p>Admin-only route audit records for hash, path, profitability, freshness, impact, liquidity, risk result, approval decision, rejection reason, confidence, and decision tree.</p>
      </div>
      <div class="forensics-lock">
        <span>Execution boundary</span>
        <strong>READ ONLY / NO SUBMISSION</strong>
        <em>Forensics reads stored route decisions only. Signer, keys, hot wallet, and transaction submission are untouched.</em>
        ${SourceBadge(data.source || "unavailable")}
      </div>
      <div class="forensics-summary-strip">
        <div><span>Total routes</span><strong>${fmt.format(summary.routeCount || data.count || 0)}</strong></div>
        <div><span>Complete</span><strong>${fmt.format(summary.completeCount || 0)}</strong></div>
        <div><span>Approved</span><strong>${fmt.format(summary.approvedCount || 0)}</strong></div>
        <div><span>Rejected</span><strong>${fmt.format(summary.rejectedCount || 0)}</strong></div>
      </div>
    </section>`;
}

function ForensicsPicker(data, selected) {
  const routes = data.routes || [];
  return `
    <section class="cockpit-card forensics-picker">
      <div class="panel-head">
        <h2>Inspect Route</h2>
        <span>${fmt.format(routes.length)} loaded</span>
      </div>
      <div class="forensics-route-list">
        ${
          routes.length
            ? routes
                .map(
                  (route) => `
          <article class="forensics-route-card ${String(route.id) === String(selected?.id) ? "active" : ""} ${escapeHtml(forensicsDecisionTone(route))}">
            <button type="button" data-forensics-id="${escapeHtml(route.id)}">
              <span>${escapeHtml(route.routeHash || "route")}</span>
              <strong>${escapeHtml(forensicsRouteLabel(route))}</strong>
              <em>${escapeHtml(route.rejectionReason && route.rejectionReason !== "none" ? gateLabel(route.rejectionReason) : "approved path")}</em>
              ${SourceBadge(route.source || data.source || "unavailable")}
            </button>
            <button type="button" data-compare-forensics-id="${escapeHtml(route.id)}">
              ${state.compareForensicsIds.some((id) => String(id) === String(route.id)) ? "Remove" : "Compare"}
            </button>
          </article>`
                )
                .join("")
            : `<p class="muted">No route-forensics records are available yet.</p>`
        }
      </div>
    </section>`;
}

function ForensicsDecisionTree(route) {
  const steps = route?.decisionTree || [];
  return `
    <div class="forensics-decision-tree">
      <span>Decision tree</span>
      ${
        steps.length
          ? steps
              .map(
                (step, index) => `
        <article class="${escapeHtml(step.status === "pass" ? "ok" : "blocked")}">
          <i>${fmt.format(index + 1)}</i>
          <div>
            <strong>${escapeHtml(step.label || step.key || "Decision step")}</strong>
            <p>${escapeHtml(step.detail || "")}</p>
          </div>
          ${statusChip(step.status || "wait", step.status === "pass" ? "ok" : "blocked")}
        </article>`
              )
              .join("")
          : `<p class="muted">No decision tree recorded.</p>`
      }
    </div>`;
}

function ForensicsConfidence(route) {
  const confidence = route?.confidenceCalculation || {};
  const score = Math.max(0, Math.min(100, Number(confidence.score || 0)));
  const components = confidence.components || [];
  return `
    <div class="forensics-confidence">
      <div class="route-confidence-meter" style="--confidence:${score}%">
        <span>Confidence calculation</span>
        <strong>${forensicsNumber(score, "%")}</strong>
        <i></i>
      </div>
      <div class="forensics-components">
        ${
          components.length
            ? components
                .map(
                  (item) => `
          <article>
            <span>${escapeHtml(item.label || item.key)}</span>
            <strong>${forensicsNumber(item.score, "%")}</strong>
            <em>weight ${forensicsNumber(Number(item.weight || 0) * 100, "%")}</em>
          </article>`
                )
                .join("")
            : `<p class="muted">No confidence components recorded.</p>`
        }
      </div>
    </div>`;
}

function ForensicsRouteLegs(route) {
  const legs = route?.routePath || [];
  if (!legs.length) return `<p class="muted">No route legs recorded.</p>`;
  return `
    <div class="forensics-leg-grid">
      ${legs
        .map(
          (leg) => `
      <article>
        <span>${escapeHtml(leg.venue || "venue")}</span>
        <strong>${assetLabel(leg.inputAssetId)} -> ${assetLabel(leg.outputAssetId)}</strong>
        <em>${escapeHtml(leg.poolId || "pool unavailable")}</em>
        <div>
          <small>in ${forensicsNumber(leg.inputAmount)}</small>
          <small>out ${forensicsNumber(leg.expectedOutput)}</small>
          <small>impact ${forensicsNumber(leg.priceImpactBps, " bps")}</small>
        </div>
      </article>`
        )
        .join("")}
    </div>`;
}

function ForensicsRiskRules(route) {
  const rules = route?.riskResult?.rules || {};
  const entries = Object.entries(rules);
  return `
    <div class="forensics-risk-rules">
      <span>Risk result</span>
      ${
        entries.length
          ? entries
              .map(
                ([key, passed]) => `
        <article class="${passed ? "ok" : "blocked"}">
          ${statusChip(passed ? "pass" : "fail", passed ? "ok" : "blocked")}
          <strong>${escapeHtml(gateLabel(key))}</strong>
        </article>`
              )
              .join("")
          : `<p class="muted">No risk rules recorded.</p>`
      }
    </div>`;
}

function ForensicsInspector(route) {
  return `
    <section class="cockpit-card span-2 forensics-inspector">
      <div class="panel-head">
        <h2>${escapeHtml(route?.routeHash || "No route selected")}</h2>
        <span>${escapeHtml(route?.approvalDecision?.decision || "waiting")}</span>
      </div>
      ${
        route
          ? `
        <div class="forensics-status-line">
          ${statusChip(route.approvalDecision?.decision || "review", forensicsDecisionTone(route))}
          ${SourceBadge(route.source || "unavailable")}
          <span>${escapeHtml(forensicsRouteLabel(route))}</span>
          <span>${route.completeness?.complete ? "complete explanation" : "missing explanation fields"}</span>
        </div>
        <div class="forensics-metric-grid">
          ${TraceableMetricArticle({ label: "Net profit", value: forensicsNumber(route.profitability?.expectedNetProfit), source: route.source || "unavailable", metricKey: "route.expected_net_profit", routeHash: route.routeHash, className: "" })}
          ${TraceableMetricArticle({ label: "Quote age", value: forensicsNumber(route.quoteFreshness?.maxAgeSeconds, "s"), source: route.source || "unavailable", metricKey: "quote.fresh_count", routeHash: route.routeHash, className: "" })}
          ${TraceableMetricArticle({ label: "Price impact", value: forensicsNumber(route.priceImpact?.maxBps, " bps"), source: route.source || "unavailable", metricKey: "route.price_impact_bps", routeHash: route.routeHash, className: "" })}
          ${TraceableMetricArticle({ label: "Liquidity score", value: forensicsNumber(route.liquidityScore?.score, "%"), source: route.source || "unavailable", metricKey: "scanner.snapshot_count", routeHash: route.routeHash, className: "" })}
          ${TraceableMetricArticle({ label: "Risk result", value: route.riskResult?.status || "unknown", source: route.source || "unavailable", metricKey: "risk.decision_count", routeHash: route.routeHash, className: "" })}
          ${TraceableMetricArticle({ label: "Rejection reason", value: route.rejectionReason === "none" ? "none" : gateLabel(route.rejectionReason), source: route.source || "unavailable", metricKey: "risk.rejected_count", routeHash: route.routeHash, className: "" })}
        </div>
        <div class="intent-box">
          <span>Forensic completeness</span>
          <strong>${route.completeness?.complete ? "Complete route explanation stored" : "Explanation has missing fields"}</strong>
          <p>${escapeHtml((route.completeness?.missingFields || []).length ? `Missing: ${route.completeness.missingFields.join(", ")}` : "Hash, path, profit, freshness, impact, liquidity, risk result, approval, rejection, confidence, and decision tree are present.")}</p>
        </div>
        ${ForensicsConfidence(route)}
        ${ForensicsDecisionTree(route)}`
          : `<p class="muted">No route forensics are available yet.</p>`
      }
    </section>`;
}

function ForensicsEvidencePanel(route) {
  return `
    <section class="cockpit-card forensics-evidence">
      <div class="panel-head">
        <h2>Route Evidence</h2>
        <span>${route ? "stored audit" : "waiting"}</span>
      </div>
      ${
        route
          ? `
        ${ForensicsRouteLegs(route)}
        ${ForensicsRiskRules(route)}`
          : `<p class="muted">Select a route to inspect evidence.</p>`
      }
    </section>`;
}

function ForensicsCompareGrid(data) {
  const routes = data.routes || [];
  const selected = state.compareForensicsIds
    .map((id) => routes.find((route) => String(route.id) === String(id)))
    .filter(Boolean);
  return `
    <section class="cockpit-card span-3 forensics-compare">
      <div class="panel-head">
        <h2>Compare Routes</h2>
        <span>${fmt.format(selected.length)} selected</span>
      </div>
      <div class="forensics-compare-grid">
        ${
          selected.length
            ? selected
                .map(
                  (route) => `
          <article class="forensics-compare-card ${escapeHtml(forensicsDecisionTone(route))}">
            <div>
              <span>${escapeHtml(route.routeHash)}</span>
              ${SourceBadge(route.source || data.source || "unavailable")}
            </div>
            <strong>${escapeHtml(forensicsRouteLabel(route))}</strong>
            <dl>
              <div><dt>Decision</dt><dd>${escapeHtml(route.approvalDecision?.decision || "unknown")}</dd></div>
              <div><dt>Net</dt><dd>${forensicsNumber(route.profitability?.expectedNetProfit)}</dd></div>
              <div><dt>Freshness</dt><dd>${forensicsNumber(route.quoteFreshness?.maxAgeSeconds, "s")}</dd></div>
              <div><dt>Impact</dt><dd>${forensicsNumber(route.priceImpact?.maxBps, " bps")}</dd></div>
              <div><dt>Liquidity</dt><dd>${forensicsNumber(route.liquidityScore?.score, "%")}</dd></div>
              <div><dt>Rejection</dt><dd>${escapeHtml(route.rejectionReason === "none" ? "none" : gateLabel(route.rejectionReason))}</dd></div>
            </dl>
          </article>`
                )
                .join("")
            : `<p class="muted">Select up to three routes to compare side by side.</p>`
        }
      </div>
    </section>`;
}

function RouteForensicsPanel() {
  const data = routeForensicsData();
  const route = selectedForensicsRoute();
  return `
    ${ForensicsHero(data)}
    ${
      state.routeForensicsLoading && !state.routeForensics
        ? `<section class="cockpit-card span-3 loading-state"><h2>Loading Route Forensics</h2><p>Reading stored route explanations...</p></section>`
        : ""
    }
    ${
      state.routeForensicsError
        ? `<section class="cockpit-card span-3 error-state"><h2>Route Forensics fallback</h2><p>${escapeHtml(state.routeForensicsError)}. Showing mock-labeled route explanations.</p></section>`
        : ""
    }
    ${ForensicsPicker(data, route)}
    ${ForensicsInspector(route)}
    ${ForensicsEvidencePanel(route)}
    ${ForensicsCompareGrid(data)}`;
}

function confidenceCalibrationData() {
  return state.confidenceCalibration || makeMockConfidenceCalibration("Confidence calibration has not loaded backend paper evidence yet.");
}

function clampRate(value) {
  return Math.max(0, Math.min(1, Number(value || 0)));
}

function confidencePercent(value) {
  return `${fmt.format(clampRate(value) * 100)}%`;
}

function confidenceAlgo(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "pending";
  const numeric = Number(value || 0);
  const sign = numeric > 0 ? "+" : "";
  return `${sign}${fmt.format(numeric)} ALGO`;
}

function confidenceVerdictTone(verdict) {
  if (verdict === "calibrated") return "ok";
  if (verdict === "needs_adjustment") return "blocked";
  if (verdict === "watch") return "wait";
  return "disabled";
}

function confidenceBucketTone(bucket) {
  if (!Number(bucket?.count || 0)) return "empty";
  const error = Number(bucket.calibrationError || 0);
  if (error <= 0.12) return "ok";
  if (error <= 0.25) return "watch";
  return "blocked";
}

function ConfidenceCalibrationHero(data) {
  const summary = data.summary || {};
  const verdict = summary.verdict || "under_sampled";
  return `
    <section class="cockpit-card span-3 confidence-hero">
      <div>
        <p class="eyebrow">Route Confidence Calibration</p>
        <h2>Do confidence scores predict paper-trade success?</h2>
        <p>Admin-only analysis of stored paper trades. Buckets compare predicted route confidence against resolved 5s/30s simulated outcomes so the scoring model can be trusted or adjusted.</p>
      </div>
      <div class="confidence-verdict ${escapeHtml(confidenceVerdictTone(verdict))}">
        <span>Calibration verdict</span>
        <strong>${escapeHtml(String(verdict).replaceAll("_", " "))}</strong>
        <p>${escapeHtml(summary.verdictDetail || "Collect paper-trade evidence before changing confidence math.")}</p>
        ${SourceBadge(data.source || "unavailable")}
      </div>
      <div class="confidence-lock">
        <span>Execution boundary</span>
        <strong>ANALYTICS ONLY</strong>
        <em>Reads paper-trade history and route confidence only. Live execution, signer, keys, hot wallet, and transaction submission stay untouched.</em>
        ${statusChip(data.liveExecutionTouched ? "live touched" : "live untouched", data.liveExecutionTouched ? "blocked" : "ok")}
        ${statusChip(data.signerCodeTouched ? "signer touched" : "signer untouched", data.signerCodeTouched ? "blocked" : "ok")}
      </div>
    </section>`;
}

function ConfidenceSummaryStrip(data) {
  const summary = data.summary || {};
  const source = data.source || "unavailable";
  return `
    <section class="cockpit-card span-3 confidence-summary-strip">
      ${TraceableMetricArticle({ label: "Paper trades", value: fmt.format(summary.paperTradeCount || 0), source, metricKey: "paper.count", className: "" })}
      ${TraceableMetricArticle({ label: "Resolved", value: fmt.format(summary.resolvedCount || 0), source, metricKey: "paper.checked_30s_count", className: "" })}
      ${TraceableMetricArticle({ label: "Success rate", value: confidencePercent(summary.overallSuccessRate), source, metricKey: "paper.checked_30s_count", className: "" })}
      ${TraceableMetricArticle({ label: "Avg confidence", value: confidencePercent(summary.averageConfidence), source, metricKey: "route.confidence_score", className: "" })}
      ${TraceableMetricArticle({ label: "Calibration gap", value: confidencePercent(summary.calibrationError), source, metricKey: "route.confidence_score", className: "" })}
    </section>`;
}

function ConfidenceBucketGrid(data) {
  const buckets = data.buckets || [];
  return `
    <section class="cockpit-card span-2 confidence-bucket-panel">
      <div class="panel-head">
        <h2>Confidence Buckets</h2>
        <span>predicted vs observed</span>
      </div>
      <div class="confidence-bucket-grid">
        ${
          buckets.length
            ? buckets
                .map((bucket) => {
                  const success = clampRate(bucket.successRate) * 100;
                  const predicted = clampRate(bucket.averageConfidence) * 100;
                  return `
          <article class="confidence-bucket-card ${escapeHtml(confidenceBucketTone(bucket))}" style="--success:${success}%; --predicted:${predicted}%">
            <div class="confidence-bucket-head">
              <strong>${escapeHtml(bucket.label)}</strong>
              ${SourceBadge(data.source || "unavailable")}
            </div>
            <div class="confidence-meter-stack">
              <span>Observed success <b>${confidencePercent(bucket.successRate)}</b></span>
              <i class="success"></i>
              <span>Predicted confidence <b>${confidencePercent(bucket.averageConfidence)}</b></span>
              <i class="predicted"></i>
            </div>
            <dl>
              <div><dt>Count</dt><dd>${fmt.format(bucket.count || 0)}</dd></div>
              <div><dt>Wins / losses</dt><dd>${fmt.format(bucket.successCount || 0)} / ${fmt.format(bucket.failureCount || 0)}</dd></div>
              <div><dt>Avg decay</dt><dd>${confidenceAlgo(bucket.averageQuoteDecay)}</dd></div>
              <div><dt>Avg profit</dt><dd>${confidenceAlgo(bucket.averageSimulatedProfit)}</dd></div>
              <div><dt>Gap</dt><dd>${confidencePercent(bucket.calibrationError)}</dd></div>
            </dl>
          </article>`;
                })
                .join("")
            : `<p class="muted">No resolved paper trades are available for confidence buckets yet.</p>`
        }
      </div>
    </section>`;
}

function ConfidenceBucketInspector(data) {
  const buckets = data.buckets || [];
  const populated = buckets.filter((bucket) => Number(bucket.count || 0));
  const strongest = populated.slice().sort((a, b) => Number(b.successRate || 0) - Number(a.successRate || 0))[0];
  const weakest = populated.slice().sort((a, b) => Number(a.successRate || 0) - Number(b.successRate || 0))[0];
  const largestGap = populated.slice().sort((a, b) => Number(b.calibrationError || 0) - Number(a.calibrationError || 0))[0];
  return `
    <section class="cockpit-card confidence-calibration-inspector">
      <div class="panel-head">
        <h2>Calibration Read</h2>
        <span>${escapeHtml(data.summary?.verdict || "waiting")}</span>
      </div>
      <div class="confidence-read-stack">
        <article>
          <span>Most reliable bucket</span>
          <strong>${escapeHtml(strongest?.label || "none yet")}</strong>
          <p>${strongest ? `${confidencePercent(strongest.successRate)} observed success over ${fmt.format(strongest.count)} trades.` : "Collect resolved paper trades to identify the best bucket."}</p>
        </article>
        <article>
          <span>Weakest bucket</span>
          <strong>${escapeHtml(weakest?.label || "none yet")}</strong>
          <p>${weakest ? `${confidencePercent(weakest.successRate)} observed success with ${confidenceAlgo(weakest.averageSimulatedProfit)} average profit.` : "No resolved buckets available yet."}</p>
        </article>
        <article>
          <span>Largest prediction gap</span>
          <strong>${escapeHtml(largestGap?.label || "none yet")}</strong>
          <p>${largestGap ? `${confidencePercent(largestGap.calibrationError)} gap between confidence and success rate.` : "No calibration gap until paper trades resolve."}</p>
        </article>
      </div>
    </section>`;
}

function ConfidenceSampleTrades(data) {
  const rows = data.sampleTrades || [];
  return `
    <section class="cockpit-card span-3 confidence-sample-panel">
      <div class="panel-head">
        <h2>Paper Trade Evidence</h2>
        <span>${fmt.format(rows.length)} samples shown</span>
      </div>
      <div class="confidence-sample-list">
        ${
          rows.length
            ? rows
                .map((trade) => {
                  const resolved = Boolean(trade.resolved);
                  const tone = !resolved ? "wait" : trade.success ? "ok" : "blocked";
                  return `
          <article class="confidence-sample-row ${tone}">
            <div>
              ${statusChip(resolved ? (trade.success ? "success" : "failure") : "pending", tone)}
              <strong>${escapeHtml(trade.routeHash || trade.paperTradeId || "paper trade")}</strong>
              <span>${escapeHtml(trade.createdAt ? ago(Number(trade.createdAt)) : "time unavailable")} / ${escapeHtml(trade.checkpoint || "pending")}</span>
            </div>
            <dl>
              <div><dt>Confidence</dt><dd>${confidencePercent(trade.confidence ?? trade.confidenceScore)}</dd></div>
              <div><dt>Expected</dt><dd>${confidenceAlgo(trade.expectedProfit)}</dd></div>
              <div><dt>Simulated</dt><dd>${confidenceAlgo(trade.simulatedProfit)}</dd></div>
              <div><dt>Decay</dt><dd>${confidenceAlgo(trade.quoteDecay)}</dd></div>
            </dl>
            ${SourceBadge(data.source || "unavailable")}
          </article>`;
                })
                .join("")
            : `<p class="muted">No paper-trade rows are available yet. Run paper trading with 5s/30s checks to seed confidence calibration.</p>`
        }
      </div>
    </section>`;
}

function ConfidenceAnalysisPanel() {
  const data = confidenceCalibrationData();
  return `
    ${ConfidenceCalibrationHero(data)}
    ${
      state.confidenceCalibrationLoading && !state.confidenceCalibration
        ? `<section class="cockpit-card span-3 loading-state"><h2>Loading Confidence Analysis</h2><p>Reading stored paper-trade confidence evidence...</p></section>`
        : ""
    }
    ${
      state.confidenceCalibrationError
        ? `<section class="cockpit-card span-3 error-state"><h2>Confidence endpoint fallback</h2><p>${escapeHtml(state.confidenceCalibrationError)}. Showing mock-labeled calibration data.</p></section>`
        : ""
    }
    ${ConfidenceSummaryStrip(data)}
    ${ConfidenceBucketGrid(data)}
    ${ConfidenceBucketInspector(data)}
    ${ConfidenceSampleTrades(data)}`;
}

function opportunityDecayData() {
  return state.opportunityDecay || makeMockOpportunityDecay("Opportunity decay has not loaded backend evidence yet.", state.decayView);
}

function secondsShort(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "pending";
  const seconds = Number(value || 0);
  if (seconds < 60) return `${fmt.format(seconds)}s`;
  if (seconds < 3600) return `${fmt.format(seconds / 60)}m`;
  return `${fmt.format(seconds / 3600)}h`;
}

function decayProfit(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "pending";
  const numeric = Number(value || 0);
  const sign = numeric > 0 ? "+" : "";
  return `${sign}${fmt.format(numeric)} ALGO`;
}

function decayPercent(value) {
  return `${fmt.format(Math.max(0, Number(value || 0)) * 100)}%`;
}

function decayRouteTypeLabel(value) {
  return String(value || "unknown").replaceAll("_", " ");
}

function OpportunityDecayHero(data) {
  const summary = data.summary || {};
  return `
    <section class="cockpit-card span-3 decay-hero">
      <div>
        <p class="eyebrow">Opportunity Half-Life Dashboard</p>
        <h2>How quickly do arb windows disappear?</h2>
        <p>Admin-only decay analytics from stored paper checkpoints. The report tracks detected profit, 5s, 30s, and 60s rechecks to quantify how long opportunities remain actionable.</p>
      </div>
      <div class="decay-window-card">
        <span>Chart window</span>
        <div class="decay-view-controls">
          ${(data.views || ["1h", "24h", "7d"])
            .map((view) => `<button type="button" class="${view === data.view ? "active" : ""}" data-decay-view="${escapeHtml(view)}">${escapeHtml(view)}</button>`)
            .join("")}
        </div>
        <strong>${secondsShort(summary.averageHalfLifeSeconds)} avg half-life</strong>
        ${SourceBadge(data.source || "unavailable")}
      </div>
      <div class="decay-lock-card">
        <span>Execution boundary</span>
        <strong>OBSERVABILITY ONLY</strong>
        <em>No signer, wallet, or transaction submission code is used. This panel reads stored opportunity and paper-trade evidence only.</em>
        ${statusChip(data.liveExecutionTouched ? "live touched" : "live untouched", data.liveExecutionTouched ? "blocked" : "ok")}
        ${statusChip(data.signerCodeTouched ? "signer touched" : "signer untouched", data.signerCodeTouched ? "blocked" : "ok")}
      </div>
    </section>`;
}

function OpportunityDecaySummary(data) {
  const summary = data.summary || {};
  const source = data.source || "unavailable";
  return `
    <section class="cockpit-card span-3 decay-summary-strip">
      ${TraceableMetricArticle({ label: "Opportunities", value: fmt.format(summary.opportunityCount || 0), source, metricKey: "route.count", className: "" })}
      ${TraceableMetricArticle({ label: "Average half-life", value: secondsShort(summary.averageHalfLifeSeconds), source, metricKey: "paper.checked_30s_count", className: "" })}
      ${TraceableMetricArticle({ label: "Median half-life", value: secondsShort(summary.medianHalfLifeSeconds), source, metricKey: "paper.checked_30s_count", className: "" })}
      ${TraceableMetricArticle({ label: "60s samples", value: fmt.format(summary.resolved60sCount || 0), source, metricKey: "paper.checked_30s_count", className: "" })}
      ${TraceableMetricArticle({ label: "Avg decay", value: decayPercent(summary.averageDecayRatio), source, metricKey: "paper.checked_30s_count", className: "" })}
    </section>`;
}

function DecayExtremeCard(label, item, tone) {
  return `
    <article class="decay-extreme-card ${escapeHtml(tone)}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(item?.routeHash || "waiting")}</strong>
      <p>${escapeHtml(item ? `${item.pairLabel} / ${decayRouteTypeLabel(item.routeType)}` : "Collect paper checkpoints to identify decay extremes.")}</p>
      <div>
        <em>${secondsShort(item?.halfLifeSeconds)}</em>
        <small>${decayProfit(item?.expectedProfit)} -> ${decayProfit(item?.latestProfit)}</small>
      </div>
    </article>`;
}

function OpportunityDecayTimeline(data) {
  const bars = data.timeline || [];
  const maxHalfLife = Math.max(1, ...bars.map((item) => Number(item.averageHalfLifeSeconds || 0)));
  const maxCount = Math.max(1, ...bars.map((item) => Number(item.opportunityCount || 0)));
  return `
    <section class="cockpit-card span-2 decay-chart-panel">
      <div class="panel-head">
        <h2>Half-Life Chart</h2>
        <span>${escapeHtml(data.view || "24h")}</span>
      </div>
      <div class="decay-chart">
        ${bars
          .map((bucket) => {
            const height = Math.max(4, (Number(bucket.averageHalfLifeSeconds || 0) / maxHalfLife) * 100);
            const density = Math.max(0.12, Number(bucket.opportunityCount || 0) / maxCount);
            return `
        <article style="--bar:${height}%; --density:${density}">
          <i></i>
          <strong>${secondsShort(bucket.averageHalfLifeSeconds)}</strong>
          <span>${escapeHtml(bucket.label || String(bucket.index))}</span>
          <em>${fmt.format(bucket.opportunityCount || 0)} routes</em>
        </article>`;
          })
          .join("")}
      </div>
    </section>`;
}

function DecayBreakdownGroup(title, rows) {
  return `
    <section class="cockpit-card decay-breakdown-card">
      <div class="panel-head">
        <h2>${escapeHtml(title)}</h2>
        <span>${fmt.format((rows || []).length)} groups</span>
      </div>
      <div class="decay-breakdown-list">
        ${
          (rows || []).length
            ? rows
                .slice(0, 6)
                .map(
                  (item) => `
        <article>
          <div>
            <strong>${escapeHtml(decayRouteTypeLabel(item.label))}</strong>
            <span>${fmt.format(item.opportunityCount || 0)} routes</span>
          </div>
          <div class="decay-mini-meter" style="--decay:${Math.min(100, Math.max(4, Number(item.averageDecayRatio || 0) * 100))}%"><i></i></div>
          <dl>
            <div><dt>avg</dt><dd>${secondsShort(item.averageHalfLifeSeconds)}</dd></div>
            <div><dt>median</dt><dd>${secondsShort(item.medianHalfLifeSeconds)}</dd></div>
            <div><dt>fastest</dt><dd>${secondsShort(item.fastestHalfLifeSeconds)}</dd></div>
            <div><dt>slowest</dt><dd>${secondsShort(item.slowestHalfLifeSeconds)}</dd></div>
          </dl>
        </article>`
                )
                .join("")
            : `<p class="muted">No decay evidence for this grouping yet.</p>`
        }
      </div>
    </section>`;
}

function OpportunityDecayRecords(data) {
  const records = data.records || [];
  return `
    <section class="cockpit-card span-3 decay-record-panel">
      <div class="panel-head">
        <h2>Recent Decay Evidence</h2>
        <span>${fmt.format(records.length)} shown</span>
      </div>
      <div class="decay-record-list">
        ${
          records.length
            ? records
                .map(
                  (record) => `
        <article class="${record.actionable ? "ok" : "blocked"}">
          <div>
            ${statusChip(record.actionable ? "still actionable" : "decayed", record.actionable ? "ok" : "blocked")}
            <strong>${escapeHtml(record.routeHash || "route")}</strong>
            ${SourceBadge(record.source || data.source || "unavailable")}
          </div>
          <span>${escapeHtml(record.pairLabel || "pair")} / ${escapeHtml((record.venues || []).join(" + "))} / ${escapeHtml(decayRouteTypeLabel(record.routeType))}</span>
          <dl>
            <div><dt>T0</dt><dd>${decayProfit(record.expectedProfit)}</dd></div>
            <div><dt>T+5s</dt><dd>${decayProfit(record.expectedProfit5s)}</dd></div>
            <div><dt>T+30s</dt><dd>${decayProfit(record.expectedProfit30s)}</dd></div>
            <div><dt>T+60s</dt><dd>${decayProfit(record.expectedProfit60s)}</dd></div>
            <div><dt>half-life</dt><dd>${secondsShort(record.halfLifeSeconds)}</dd></div>
            <div><dt>decay</dt><dd>${decayPercent(record.decayRatio)}</dd></div>
          </dl>
        </article>`
                )
                .join("")
            : `<p class="muted">No opportunity decay records are available yet. Paper trading will populate 5s, 30s, and 60s checkpoints.</p>`
        }
      </div>
    </section>`;
}

function OpportunityHalfLifeDashboard() {
  const data = opportunityDecayData();
  const summary = data.summary || {};
  return `
    ${OpportunityDecayHero(data)}
    ${
      state.opportunityDecayLoading && !state.opportunityDecay
        ? `<section class="cockpit-card span-3 loading-state"><h2>Loading Half-Life Dashboard</h2><p>Reading stored opportunity decay evidence...</p></section>`
        : ""
    }
    ${
      state.opportunityDecayError
        ? `<section class="cockpit-card span-3 error-state"><h2>Half-Life fallback</h2><p>${escapeHtml(state.opportunityDecayError)}. Showing mock-labeled decay analytics.</p></section>`
        : ""
    }
    ${OpportunityDecaySummary(data)}
    ${OpportunityDecayTimeline(data)}
    <section class="cockpit-card decay-extremes">
      <div class="panel-head">
        <h2>Decay Extremes</h2>
        <span>${fmt.format(summary.observedHalfLifeCount || 0)} observed</span>
      </div>
      ${DecayExtremeCard("Fastest decay", summary.fastestDecay, "blocked")}
      ${DecayExtremeCard("Slowest decay", summary.slowestDecay, "ok")}
    </section>
    ${DecayBreakdownGroup("Half-Life By Pair", data.byPair)}
    ${DecayBreakdownGroup("Half-Life By Venue", data.byVenue)}
    ${DecayBreakdownGroup("Half-Life By Route Type", data.byRouteType)}
    ${OpportunityDecayRecords(data)}`;
}

function productionReadinessData() {
  return state.productionReadiness || makeUnavailableProductionReadiness("Production readiness has not loaded yet.");
}

function readinessStatusTone(status) {
  if (status === "pass" || status === "ok") return "ok";
  if (status === "fail" || status === "blocked" || status === "disabled") return "blocked";
  return "wait";
}

function ReadinessHero(data) {
  const percent = Math.max(0, Math.min(100, Number(data.overallPercent || 0)));
  return `
    <section class="cockpit-card span-3 readiness-engine-hero">
      <div>
        <p class="eyebrow">Production Readiness Engine</p>
        <h2>Readiness is calculated from evidence.</h2>
        <p>Gate progress comes from stored scanner, quote, route, paper, dry-run, signer-lock, and reconciliation evidence. No frontend percentage is trusted.</p>
      </div>
      <div class="readiness-score-card">
        <span>Overall readiness</span>
        <strong>${fmt.format(percent)}%</strong>
        <div class="readiness-progress" aria-label="Production readiness ${fmt.format(percent)}%">
          <i style="width:${percent}%"></i>
        </div>
        <em>${fmt.format(data.passedEvidenceCount || 0)} / ${fmt.format(data.totalEvidenceCount || 0)} evidence records passing</em>
        ${SourceBadge(data.source || "unavailable")}
      </div>
      <div class="readiness-next-card">
        <span>Current phase</span>
        <strong>${escapeHtml(data.currentPhase || "Unavailable")}</strong>
        <span>Next gate</span>
        <strong>${escapeHtml(data.nextGate || "Backend evidence endpoint")}</strong>
      </div>
    </section>`;
}

function ReadinessBlockers(data) {
  const blockers = data.blockingItems || [];
  return `
    <section class="cockpit-card readiness-blocker-panel">
      <div class="panel-head">
        <h2>Blockers</h2>
        <span>${fmt.format(blockers.length)}</span>
      </div>
      <div class="readiness-blocker-list">
        ${
          blockers.length
            ? blockers.map((item) => `<span>${escapeHtml(item)}</span>`).join("")
            : `<p class="muted">No blockers reported by the readiness engine.</p>`
        }
      </div>
    </section>`;
}

function ReadinessGateTree(data) {
  const phases = data.phases || [];
  const gates = data.gates || [];
  const gatesByPhase = new Map();
  gates.forEach((gate) => {
    const list = gatesByPhase.get(gate.phaseKey) || [];
    list.push(gate);
    gatesByPhase.set(gate.phaseKey, list);
  });
  return `
    <section class="cockpit-card span-2 readiness-gate-tree">
      <div class="panel-head">
        <h2>Gate Tree</h2>
        <span>derived from evidence</span>
      </div>
      <div class="readiness-tree">
        ${
          phases.length
            ? phases
                .map((phase) => {
                  const phaseGates = gatesByPhase.get(phase.key) || [];
                  return `
          <article class="readiness-phase ${escapeHtml(readinessStatusTone(phase.status))}">
            <div class="readiness-phase-head">
              ${statusChip(phase.status || "wait", readinessStatusTone(phase.status))}
              <strong>${escapeHtml(phase.label)}</strong>
              <span>${fmt.format(phase.percent || 0)}%</span>
            </div>
            <div class="readiness-gates">
              ${
                phaseGates.length
                  ? phaseGates
                      .map(
                        (gate) => `
                <details class="readiness-gate ${escapeHtml(readinessStatusTone(gate.status))}" ${gate.status !== "ok" ? "open" : ""}>
                  <summary>
                    <span>${escapeHtml(gate.label)}</span>
                    <strong>${fmt.format(gate.percent || 0)}%</strong>
                  </summary>
                  <p>${escapeHtml(gate.description || "Evidence gate.")}</p>
                  <div class="readiness-evidence-mini">
                    ${(gate.evidence || [])
                      .map(
                        (item) => `
                      <div class="${escapeHtml(readinessStatusTone(item.status))}">
                        ${statusChip(item.status, readinessStatusTone(item.status))}
                        <span>${escapeHtml(item.label)}</span>
                        <strong>${escapeHtml(item.value)}</strong>
                      </div>`
                      )
                      .join("")}
                  </div>
                </details>`
                      )
                      .join("")
                  : `<p class="muted">No gates assigned to this phase.</p>`
              }
            </div>
          </article>`;
                })
                .join("")
            : `<p class="muted">Production readiness evidence endpoint is unavailable.</p>`
        }
      </div>
    </section>`;
}

function ReadinessEvidenceTable(data) {
  const evidence = data.evidence || [];
  return `
    <section class="cockpit-card span-3 readiness-evidence-panel">
      <div class="panel-head">
        <h2>Evidence Records</h2>
        <span>${fmt.format(evidence.length)} records</span>
      </div>
      <div class="readiness-evidence-table">
        ${
          evidence.length
            ? evidence
                .map(
                  (item) => `
          <article class="${escapeHtml(readinessStatusTone(item.status))}">
            ${statusChip(item.status || "wait", readinessStatusTone(item.status))}
            <div>
              <span>${escapeHtml(item.gateKey || "gate")}</span>
              <strong>${escapeHtml(item.label || "Evidence")}</strong>
              <p>${escapeHtml(item.detail || "No detail recorded.")}</p>
            </div>
            <div>
              <span>Value</span>
              <strong>${escapeHtml(item.value || "pending")}</strong>
              ${SourceBadge(item.source || "unavailable")}
            </div>
            ${
              item.evidenceUrl
                ? `<a href="${escapeHtml(item.evidenceUrl)}" target="_blank" rel="noreferrer">Evidence link</a>`
                : `<span class="muted">No link</span>`
            }
          </article>`
                )
                .join("")
            : `<p class="muted">No evidence records available.</p>`
        }
      </div>
    </section>`;
}

function ProductionReadinessPage() {
  const data = productionReadinessData();
  return `
    ${ReadinessHero(data)}
    ${
      state.productionReadinessLoading && !state.productionReadiness
        ? `<section class="cockpit-card span-3 loading-state"><h2>Loading Production Readiness</h2><p>Calculating gates from stored evidence...</p></section>`
        : ""
    }
    ${
      state.productionReadinessError
        ? `<section class="cockpit-card span-3 error-state"><h2>Readiness endpoint unavailable</h2><p>${escapeHtml(state.productionReadinessError)}.</p></section>`
        : ""
    }
    ${ReadinessGateTree(data)}
    ${ReadinessBlockers(data)}
    ${ReadinessEvidenceTable(data)}`;
}

function evidenceSystemData() {
  return state.evidenceSystem || makeMockEvidenceSystem("Evidence system has not loaded backend records yet.");
}

function evidenceStatusTone(status) {
  if (status === "pass" || status === "ok") return "ok";
  if (status === "fail") return "blocked";
  if (status === "warn") return "warn";
  return "wait";
}

function evidenceStatusLabel(status) {
  return String(status || "pending").replaceAll("_", " ");
}

function evidenceCreatedLabel(value) {
  if (!value) return "time unavailable";
  return new Date(Number(value) * 1000).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function EvidenceHero(data) {
  const summary = data.summary || {};
  const percent = Math.max(0, Math.min(100, Number(summary.proofPercent || 0)));
  return `
    <section class="cockpit-card span-3 evidence-hero">
      <div>
        <p class="eyebrow">Production Evidence System</p>
        <h2>Every gate needs a receipt.</h2>
        <p>Scanner, quote, route, paper, risk, dry-run, execution, and receipt evidence is generated from stored system state and kept inspectable by humans.</p>
        <div class="safety-strip">
          ${SourceBadge(data.source || "unavailable")}
          ${statusChip(data.liveExecutionTouched === false ? "live execution untouched" : "review execution", data.liveExecutionTouched === false ? "ok" : "blocked")}
          ${statusChip(data.signerCodeTouched === false ? "signer untouched" : "review signer", data.signerCodeTouched === false ? "ok" : "blocked")}
        </div>
      </div>
      <div class="evidence-proof-card">
        <span>Proof coverage</span>
        <strong>${fmt.format(percent)}%</strong>
        <div class="readiness-progress" aria-label="Evidence proof coverage ${fmt.format(percent)}%">
          <i style="width:${percent}%"></i>
        </div>
        <em>${fmt.format(summary.passing || 0)} / ${fmt.format(summary.total || 0)} records passing</em>
      </div>
      <div class="evidence-status-stack">
        ${["pass", "pending", "warn", "fail"]
          .map(
            (status) => `
          <article class="${escapeHtml(evidenceStatusTone(status))}">
            ${statusChip(evidenceStatusLabel(status), evidenceStatusTone(status))}
            <strong>${fmt.format((summary.byStatus || {})[status] || 0)}</strong>
          </article>`
          )
          .join("")}
      </div>
    </section>`;
}

function EvidenceCategoryMatrix(data) {
  const counts = data.summary?.byCategory || {};
  const categories = data.summary?.categories || data.categories || [];
  const maxCount = Math.max(1, ...Object.values(counts).map((value) => Number(value) || 0));
  return `
    <section class="cockpit-card evidence-category-matrix">
      <div class="panel-head">
        <h2>Component Proof</h2>
        <span>${fmt.format(categories.length)} categories</span>
      </div>
      <div class="evidence-bars">
        ${categories
          .map((category) => {
            const count = Number(counts[category] || 0);
            const width = Math.max(6, (count / maxCount) * 100);
            return `
          <button type="button" class="${state.evidenceFilters.category === category ? "active" : ""}" data-evidence-filter="category" data-evidence-value="${escapeHtml(category)}">
            <span>${escapeHtml(category.replaceAll("_", " "))}</span>
            <strong>${fmt.format(count)}</strong>
            <i style="width:${width}%"></i>
          </button>`;
          })
          .join("")}
      </div>
    </section>`;
}

function EvidenceFilterGroup(label, key, values) {
  const uniqueValues = ["all", ...Array.from(new Set(values || [])).filter(Boolean)];
  const current = state.evidenceFilters[key] || "all";
  return `
    <div class="evidence-filter-group">
      <span>${escapeHtml(label)}</span>
      <div>
        ${uniqueValues
          .map(
            (value) => `
          <button type="button" class="${current === value ? "active" : ""}" data-evidence-filter="${escapeHtml(key)}" data-evidence-value="${escapeHtml(value)}">
            ${escapeHtml(value === "all" ? "All" : value.replaceAll("_", " "))}
          </button>`
          )
          .join("")}
      </div>
    </div>`;
}

function EvidenceFilters(data) {
  return `
    <section class="cockpit-card span-2 evidence-filters">
      <div class="panel-head">
        <h2>Filters</h2>
        <span>${fmt.format(data.count || 0)} shown</span>
      </div>
      ${EvidenceFilterGroup("Category", "category", data.summary?.categories || data.categories || [])}
      ${EvidenceFilterGroup("Service", "service", data.services || [])}
      ${EvidenceFilterGroup("Status", "status", data.summary?.statuses || data.statuses || [])}
    </section>`;
}

function EvidenceRecordCard(record, selectedId) {
  const source = record.metadata?.source || "unavailable";
  const tone = evidenceStatusTone(record.status);
  return `
    <button type="button" class="evidence-record-card ${escapeHtml(tone)} ${selectedId === record.evidenceId ? "active" : ""}" data-evidence-id="${escapeHtml(record.evidenceId)}">
      <div>
        ${statusChip(evidenceStatusLabel(record.status), tone)}
        ${SourceBadge(source)}
      </div>
      <span>${escapeHtml(record.category)} / ${escapeHtml(record.service)}</span>
      <strong>${escapeHtml(record.title)}</strong>
      <p>${escapeHtml(record.summary)}</p>
      <em>${escapeHtml(evidenceCreatedLabel(record.createdAt))}</em>
    </button>`;
}

function EvidenceRecordList(data, selectedId) {
  const records = data.records || [];
  return `
    <section class="cockpit-card span-2 evidence-record-list">
      <div class="panel-head">
        <h2>Evidence Records</h2>
        <span>${fmt.format(records.length)} records</span>
      </div>
      <div class="evidence-record-scroll">
        ${
          records.length
            ? records.map((record) => EvidenceRecordCard(record, selectedId)).join("")
            : `<p class="muted">No evidence records match these filters.</p>`
        }
      </div>
    </section>`;
}

function EvidenceInspector(data, selectedId) {
  const records = data.records || [];
  const record = records.find((item) => item.evidenceId === selectedId) || records[0];
  if (!record) {
    return `
      <section class="cockpit-card evidence-inspector empty-state">
        <h2>Inspect Evidence</h2>
        <p>No evidence record is available for the current filters.</p>
      </section>`;
  }
  const metadata = record.metadata || {};
  const metadataJson = JSON.stringify(metadata, null, 2);
  return `
    <section class="cockpit-card evidence-inspector">
      <div class="panel-head">
        <h2>Inspect Evidence</h2>
        <span>${escapeHtml(record.evidenceId)}</span>
      </div>
      <div class="evidence-inspector-card">
        <div>
          ${statusChip(evidenceStatusLabel(record.status), evidenceStatusTone(record.status))}
          ${SourceBadge(metadata.source || data.source || "unavailable")}
          ${statusChip(metadata.liveExecutionTouched === false ? "read-only" : "review", metadata.liveExecutionTouched === false ? "ok" : "blocked")}
        </div>
        <span>${escapeHtml(record.category)} / ${escapeHtml(record.service)}</span>
        <strong>${escapeHtml(record.title)}</strong>
        <p>${escapeHtml(record.summary)}</p>
        <dl>
          <div><dt>Created</dt><dd>${escapeHtml(evidenceCreatedLabel(record.createdAt))}</dd></div>
          <div><dt>Evidence URL</dt><dd>${escapeHtml(metadata.evidenceUrl || "/api/ops/evidence")}</dd></div>
          <div><dt>Signer Code</dt><dd>${metadata.signerCodeTouched === false ? "untouched" : "review required"}</dd></div>
          <div><dt>Live Execution</dt><dd>${metadata.liveExecutionTouched === false ? "untouched" : "review required"}</dd></div>
        </dl>
        <details open>
          <summary>Metadata JSON</summary>
          <pre>${escapeHtml(metadataJson)}</pre>
        </details>
      </div>
    </section>`;
}

function ProductionEvidenceSystem() {
  const data = evidenceSystemData();
  const selectedId = state.selectedEvidenceId;
  return `
    ${EvidenceHero(data)}
    ${
      state.evidenceLoading && !state.evidenceSystem
        ? `<section class="cockpit-card span-3 loading-state"><h2>Loading Evidence System</h2><p>Generating proof records from stored state...</p></section>`
        : ""
    }
    ${
      state.evidenceError
        ? `<section class="cockpit-card span-3 error-state"><h2>Evidence endpoint unavailable</h2><p>${escapeHtml(state.evidenceError)}.</p></section>`
        : ""
    }
    ${EvidenceFilters(data)}
    ${EvidenceCategoryMatrix(data)}
    ${EvidenceRecordList(data, selectedId)}
    ${EvidenceInspector(data, selectedId)}`;
}

function productValidationData() {
  return state.productValidation || makeMockProductValidation("Product validation has not loaded backend behavior evidence yet.");
}

function validationPercent(value) {
  return `${fmt.format(Math.round(Number(value || 0) * 100))}%`;
}

function ValidationHero(data) {
  const summary = data.summary || {};
  return `
    <section class="cockpit-card span-3 validation-hero">
      <div>
        <p class="eyebrow">Product Validation Framework</p>
        <h2>Why do users return?</h2>
        <p>Founder view for daily evidence-backed decisions, persona pull, feature utility, and Phase 1 prioritization from collected behavior.</p>
      </div>
      <div class="validation-metric-card">
        <span>The One Metric</span>
        <strong>${fmt.format(summary.decisionCount || 0)}</strong>
        <em>Daily Evidence-Backed Decisions</em>
        ${SourceBadge(data.source || "unavailable")}
      </div>
      <div class="validation-safety-card">
        <span>Product analytics only</span>
        <strong>NO EXECUTION PATH</strong>
        <em>Records user behavior events. Does not sign, submit, arm, trade, or store wallet addresses.</em>
        ${statusChip(data.liveExecutionTouched === false ? "live untouched" : "review live", data.liveExecutionTouched === false ? "ok" : "blocked")}
        ${statusChip(data.signerCodeTouched === false ? "signer untouched" : "review signer", data.signerCodeTouched === false ? "ok" : "blocked")}
      </div>
    </section>`;
}

function ValidationSummary(data) {
  const summary = data.summary || {};
  const source = data.source || "unavailable";
  return `
    <section class="cockpit-card span-3 validation-summary-grid">
      ${TraceableMetricArticle({ label: "Actions", value: fmt.format(summary.totalActions || 0), source, metricKey: "product.actions", className: "" })}
      ${TraceableMetricArticle({ label: "Active users", value: fmt.format(summary.activeUsers || 0), source, metricKey: "product.active_users", className: "" })}
      ${TraceableMetricArticle({ label: "Repeat users", value: fmt.format(summary.repeatUsers || 0), source, metricKey: "product.repeat_users", className: "" })}
      ${TraceableMetricArticle({ label: "Repeat rate", value: validationPercent(summary.repeatRate), source, metricKey: "product.repeat_rate", className: "" })}
      ${TraceableMetricArticle({ label: "Decisions", value: fmt.format(summary.decisionCount || 0), source, metricKey: "product.decisions", className: "" })}
      ${TraceableMetricArticle({ label: "Decision rate", value: validationPercent(summary.decisionRate), source, metricKey: "product.decision_rate", className: "" })}
    </section>`;
}

function ProductFunnel(data) {
  const rows = data.funnel || [];
  const maxUsers = Math.max(1, ...rows.map((item) => Number(item.users || 0)));
  return `
    <section class="cockpit-card validation-funnel">
      <div class="panel-head">
        <h2>Product Funnel</h2>
        <span>Guest -> repeat</span>
      </div>
      <div class="validation-funnel-list">
        ${rows
          .map((item) => {
            const width = Math.max(3, (Number(item.users || 0) / maxUsers) * 100);
            return `
        <article>
          <div>
            <strong>${escapeHtml(item.label)}</strong>
            ${SourceBadge(item.source || data.source || "unavailable")}
          </div>
          <i style="width:${width}%"></i>
          <dl>
            <div><dt>users</dt><dd>${fmt.format(item.users || 0)}</dd></div>
            <div><dt>conversion</dt><dd>${validationPercent(item.conversionRate)}</dd></div>
            <div><dt>drop-off</dt><dd>${fmt.format(item.dropOff || 0)}</dd></div>
          </dl>
        </article>`;
          })
          .join("")}
      </div>
    </section>`;
}

function PersonaValidation(data) {
  return `
    <section class="cockpit-card span-2 validation-personas">
      <div class="panel-head">
        <h2>Persona Validation</h2>
        <span>${fmt.format((data.personas || []).length)} personas</span>
      </div>
      <div class="validation-table">
        ${(data.personas || [])
          .map(
            (item) => `
        <article>
          <strong>${escapeHtml(item.persona)}</strong>
          <span>${fmt.format(item.activeUsers || 0)} active</span>
          <span>${fmt.format(item.evidenceBackedDecisions || 0)} decisions</span>
          <span>${validationPercent(item.repeatRate)} repeat</span>
          <em>${(item.topActions || []).slice(0, 2).map((action) => escapeHtml(action.label)).join(", ") || "waiting for evidence"}</em>
          ${SourceBadge(item.source || "unavailable")}
        </article>`
          )
          .join("")}
      </div>
    </section>`;
}

function FeatureUtilityRanking(data) {
  const rows = data.featureUtility || [];
  return `
    <section class="cockpit-card span-2 validation-features">
      <div class="panel-head">
        <h2>Feature Utility Ranking</h2>
        <span>${fmt.format(rows.length)} features</span>
      </div>
      <div class="validation-table">
        ${rows
          .map(
            (item) => `
        <article>
          <strong>${escapeHtml(item.feature)}</strong>
          <span>${fmt.format(item.opens || 0)} opens</span>
          <span>${fmt.format(item.repeatOpens || 0)} repeat opens</span>
          <span>${fmt.format(item.decisionCount || 0)} decisions</span>
          <em>${validationPercent(item.decisionContribution)} decision contribution</em>
          ${SourceBadge(item.source || "unavailable")}
        </article>`
          )
          .join("")}
      </div>
    </section>`;
}

function DeadFeatureDetector(data) {
  const rows = data.deadFeatures || [];
  return `
    <section class="cockpit-card span-2 validation-dead-features">
      <div class="panel-head">
        <h2>Dead Feature Detector</h2>
        <span>keep / improve / remove / investigate</span>
      </div>
      <div class="validation-table">
        ${rows
          .map(
            (item) => `
        <article class="${escapeHtml(item.recommendation || "investigate")}">
          <strong>${escapeHtml(item.feature)}</strong>
          <span>${item.daysSinceUse === null || item.daysSinceUse === undefined ? "never used" : `${fmt.format(item.daysSinceUse)}d since use`}</span>
          <span>${fmt.format(item.monthlyActivity || 0)} monthly</span>
          <span>${fmt.format(item.decisionCount || 0)} decisions</span>
          ${statusChip(item.recommendation || "investigate", item.recommendation === "keep" ? "ok" : item.recommendation === "remove" ? "blocked" : "wait")}
        </article>`
          )
          .join("")}
      </div>
    </section>`;
}

function WhyUsersReturnPanel(data) {
  const why = data.whyUsersReturn || {};
  const summary = data.summary || {};
  return `
    <section class="cockpit-card validation-why">
      <div class="panel-head">
        <h2>Phase 1 Signal</h2>
        <span>${escapeHtml(data.decisionRules?.metricName || "Daily Evidence-Backed Decisions")}</span>
      </div>
      <p>${escapeHtml(summary.topPhase1Recommendation || "Collect evidence before choosing Phase 1 priorities.")}</p>
      <dl>
        <div><dt>Top actions</dt><dd>${(why.topActions || []).slice(0, 3).map((item) => `${escapeHtml(item.label)} (${fmt.format(item.count)})`).join(", ") || "waiting"}</dd></div>
        <div><dt>Top personas</dt><dd>${(why.topPersonas || []).slice(0, 3).map((item) => `${escapeHtml(item.label)} (${fmt.format(item.count)})`).join(", ") || "waiting"}</dd></div>
        <div><dt>Valuable pages</dt><dd>${(why.mostValuablePages || []).slice(0, 3).map((item) => `${escapeHtml(item.label)} (${fmt.format(item.count)})`).join(", ") || "waiting"}</dd></div>
      </dl>
    </section>`;
}

function ActionTaxonomyPanel(data) {
  return `
    <section class="cockpit-card span-3 validation-taxonomy">
      <div class="panel-head">
        <h2>User Action Taxonomy</h2>
        <span>${fmt.format((data.actionTaxonomy || []).length)} actions</span>
      </div>
      <div class="validation-taxonomy-grid">
        ${(data.actionTaxonomy || [])
          .map(
            (item) => `
        <article>
          ${statusChip(item.decisionEligible ? "decision" : "action", item.decisionEligible ? "ok" : "wait")}
          <strong>${escapeHtml(item.actionType)}</strong>
          <span>${escapeHtml(item.feature || "feature")}</span>
          <em>${escapeHtml((item.personas || []).join(", ") || "persona pending")}</em>
        </article>`
          )
          .join("")}
      </div>
    </section>`;
}

function ProductValidationDashboard() {
  const data = productValidationData();
  return `
    ${ValidationHero(data)}
    ${
      state.productValidationLoading && !state.productValidation
        ? `<section class="cockpit-card span-3 loading-state"><h2>Loading Product Validation</h2><p>Reading stored behavior evidence...</p></section>`
        : ""
    }
    ${
      state.productValidationError
        ? `<section class="cockpit-card span-3 error-state"><h2>Validation fallback</h2><p>${escapeHtml(state.productValidationError)}. Showing mock-labeled framework.</p></section>`
        : ""
    }
    ${ValidationSummary(data)}
    ${ProductFunnel(data)}
    ${WhyUsersReturnPanel(data)}
    ${PersonaValidation(data)}
    ${FeatureUtilityRanking(data)}
    ${DeadFeatureDetector(data)}
    ${ActionTaxonomyPanel(data)}`;
}

function canAccessDashboardView(view) {
  const target = dashboardViews[view];
  if (!target) return false;
  if (!target.adminOnly) return true;
  const session = currentSession();
  return session.role === "admin" && session.network === APP_CONFIG.NETWORK;
}

function visibleDashboardEntries() {
  const session = currentSession();
  const isAdmin = session.role === "admin" && session.network === APP_CONFIG.NETWORK;
  return Object.entries(dashboardViews).filter(([, view]) => !view.adminOnly || isAdmin);
}

function renderNavTabs() {
  const nav = document.querySelector(".nav-tabs");
  if (!nav) return;
  nav.innerHTML = visibleDashboardEntries()
    .map(
      ([key, view]) => `
        <button type="button" class="nav-tab" data-dashboard-view="${escapeHtml(key)}" title="${escapeHtml(
          view.userScope || view.label
        )}">${escapeHtml(view.label)}</button>`
    )
    .join("");
}

function dashboardViewFromHash() {
  const view = window.location.hash.replace(/^#/, "");
  return dashboardViews[view] ? view : "pulse";
}

function setActiveView(view) {
  const leavingReplay = state.activeView === "replay" && view !== "replay";
  if (leavingReplay) stopReplayPlayback();
  state.activeView = canAccessDashboardView(view) ? view : "pulse";
  if (window.location.hash !== `#${state.activeView}`) {
    window.history.replaceState(null, "", `#${state.activeView}`);
  }
  renderNavState();
  renderRoleDashboard();
  if (state.activeView === "pipeline" && currentSession().role === "admin" && !state.opsLoading) {
    loadOpsControlRoom({ render: true });
  }
  if (state.activeView === "heatmap" && currentSession().role === "admin" && !state.marketHeatmapLoading) {
    loadMarketHeatmap({ render: true });
  }
  if (state.activeView === "failure" && currentSession().role === "admin" && !state.failureLabLoading) {
    loadFailureLab({ render: true });
  }
  if (state.activeView === "provenance" && currentSession().role === "admin" && !state.provenanceLoading) {
    loadDataProvenance({ render: true });
  }
  if (state.activeView === "evidence" && currentSession().role === "admin" && !state.evidenceLoading) {
    loadEvidenceSystem({ render: true });
  }
  if (state.activeView === "validation" && currentSession().role === "admin" && !state.productValidationLoading) {
    loadProductValidation({ render: true });
  }
  if (state.activeView === "research" && !state.researchArchiveLoading) {
    loadResearchArchive({ render: true });
  }
  if (state.activeView === "access" && !state.contributionProtocolLoading) {
    loadContributionProtocol({ render: true });
    loadCommunityGrowth({ render: true });
  }
  if (state.activeView === "transparency" && !state.transparencyLoading) {
    loadTransparencySystem({ render: true });
  }
  if (state.activeView === "readiness" && currentSession().role === "admin" && !state.productionReadinessLoading) {
    loadProductionReadiness({ render: true });
  }
  if (state.activeView === "replay" && currentSession().role === "admin" && !state.replayLoading) {
    loadReplayLab({ render: true });
  }
  if (state.activeView === "forensics" && currentSession().role === "admin" && !state.routeForensicsLoading) {
    loadRouteForensics({ render: true });
  }
  if (state.activeView === "confidence" && currentSession().role === "admin" && !state.confidenceCalibrationLoading) {
    loadConfidenceCalibration({ render: true });
  }
  if (state.activeView === "decay" && currentSession().role === "admin" && !state.opportunityDecayLoading) {
    loadOpportunityDecay({ render: true });
  }
}

function setWalletPreset(preset) {
  state.walletPreset = walletPresets[preset] ? preset : "guest";
  if (!canAccessDashboardView(state.activeView)) {
    state.activeView = "pulse";
  }
  renderWalletSession();
  renderRoleDashboard();
}

function renderWalletSession() {
  const session = currentSession();
  const provider = currentWalletProvider();
  const role = String(session.role || "guest").toUpperCase();
  const connected = Boolean(session.address) && session.role !== "guest";
  const live = state.walletConnection || {};
  const roleBadge = document.getElementById("role-badge");
  const walletButton = document.getElementById("pera-wallet-button");
  const networkBadge = document.getElementById("network-badge");
  const walletQuickSwitch = document.getElementById("wallet-quick-switch");
  const walletStateControls = document.querySelector(".wallet-state-controls");
  const backendNetwork = APP_CONFIG.NETWORK || "testnet";
  const networkOk = String(session.network || "").toLowerCase() === String(backendNetwork).toLowerCase();

  let stateLabel = session.stateLabel;
  if (live.status === "loading") stateLabel = "Connecting…";
  if (live.status === "wrong_network") stateLabel = "Wrong network";
  if (live.status === "rejected") stateLabel = "Connection rejected";
  if (live.status === "unavailable") stateLabel = "Wallet unavailable";

  setOptionalText("wallet-state-label", stateLabel);
  setOptionalText(
    "wallet-address",
    connected ? `${shortAddress(session.address)} · ${provider.label}` : live.error ? live.error : "No wallet connected"
  );

  const pnetConfigured = APP_CONFIG.PNET_ASA_CONFIGURED !== false && Number(APP_CONFIG.PNET_ASA_ID || 0) > 0;
  if (!pnetConfigured) {
    setOptionalText("pnet-optin-status", "PNET TestNet asset not configured");
    setOptionalText("pnet-balance", "—");
  } else if (connected) {
    setOptionalText("pnet-optin-status", session.optedIn ? "PNET opted in" : session.pnetMessage || "PNET opt-in needed");
    setOptionalText(
      "pnet-balance",
      session.pnetBalance == null ? "—" : `${fmt.format(Number(session.pnetBalance))} PNET`
    );
  } else {
    setOptionalText("pnet-optin-status", "PNET status unknown");
    setOptionalText("pnet-balance", "0 PNET");
  }

  const algoText =
    connected && session.algoBalance != null
      ? `${fmt.format(Number(session.algoBalance))} ALGO`
      : connected
        ? "ALGO …"
        : "0 ALGO";
  setOptionalText("pnet-credit-balance", algoText);
  setOptionalText("kill-switch-status", "Kill switch on · connect-only");

  if (roleBadge) {
    roleBadge.textContent = role;
    roleBadge.className = `role-badge ${session.role || "guest"}`;
  }
  if (walletButton) {
    if (live.status === "loading") {
      walletButton.textContent = `Connecting ${provider.label}…`;
      walletButton.disabled = true;
    } else {
      walletButton.disabled = false;
      walletButton.textContent = connected
        ? `Disconnect ${provider.label}`
        : `Connect ${provider.label}`;
    }
    walletButton.dataset.walletAction = connected ? "disconnect" : "connect";
  }
  if (networkBadge) {
    const label = backendNetwork === "mainnet" ? "MainNet" : backendNetwork === "testnet" ? "TestNet" : backendNetwork;
    networkBadge.textContent = connected
      ? `${label} · ${provider.label}`
      : label;
    networkBadge.className = `network-badge ${networkOk ? "ok" : "warn"} ${live.status || ""}`;
  }
  if (walletQuickSwitch) {
    walletQuickSwitch.innerHTML = renderWalletProviderSwitch({ compact: true });
  }
  if (walletStateControls) {
    walletStateControls.hidden = !SHOW_WALLET_PRESET_CONTROLS;
    walletStateControls.setAttribute("aria-hidden", SHOW_WALLET_PRESET_CONTROLS ? "false" : "true");
  }

  document.querySelectorAll("[data-wallet-preset]").forEach((button) => {
    button.classList.toggle("active", button.dataset.walletPreset === state.walletPreset);
  });
  document.querySelectorAll("[data-wallet-provider]").forEach((button) => {
    button.classList.toggle("active", button.dataset.walletProvider === state.walletProvider);
  });
  document.querySelectorAll("[data-wallet-network]").forEach((button) => {
    button.classList.toggle("active", button.dataset.walletNetwork === state.walletNetwork);
  });
  renderNavState();
}

function renderAppPhaseLabel() {
  document.querySelectorAll("[data-app-phase-label]").forEach((node) => {
    node.textContent = APP_PHASE_LABEL;
  });
}

function renderNavState() {
  renderNavTabs();
  const session = currentSession();
  const isAdmin = session.role === "admin" && session.network === APP_CONFIG.NETWORK;
  document.querySelectorAll("[data-dashboard-view]").forEach((button) => {
    const view = dashboardViews[button.dataset.dashboardView] || {};
    const locked = Boolean(view.adminOnly && !isAdmin);
    const visible = !view.adminOnly || isAdmin;
    button.hidden = !visible;
    button.classList.toggle("active", button.dataset.dashboardView === state.activeView);
    button.classList.toggle("locked", locked);
    button.disabled = locked;
    button.setAttribute("aria-disabled", locked ? "true" : "false");
    button.title = locked ? `${view.label} requires an admin wallet session` : view.userScope || view.label || "";
  });
}

function routeConsoleData() {
  const liveRoutes = (state.latestOpportunities || []).slice(0, 8).map((item, index) => normalizeOpportunityRoute(item, index));
  if (liveRoutes.length) return liveRoutes;
  return [
    {
      routeHash: "mock-algo-usdc-01",
      pair: "ALGO/USDC",
      path: ["ALGO", "USDC", "ALGO"],
      venues: ["Tinyman", "Pact"],
      inputAmount: 10,
      expectedOutput: 10.061,
      grossProfit: 0.061,
      networkFees: 0.004,
      dexFees: 0.011,
      safetyBuffer: 0.016,
      netProfit: 0.03,
      profitBps: 30,
      priceImpactBps: 22,
      quoteAgeSeconds: 3,
      confidenceScore: 0.84,
      status: "approved",
      source: "mock",
      skipReason: null,
      poolIds: ["tinyman-algo-usdc", "pact-algo-usdc"],
      appIds: ["reviewed"],
      assetIds: [0, 31566704],
    },
    {
      routeHash: "mock-pnet-usdc-02",
      pair: "PNET/USDC",
      path: ["PNET", "USDC", "PNET"],
      venues: ["Pact", "Tinyman"],
      inputAmount: 1000,
      expectedOutput: 1006.4,
      grossProfit: 6.4,
      networkFees: 0.004,
      dexFees: 2.1,
      safetyBuffer: 2,
      netProfit: 2.296,
      profitBps: 23,
      priceImpactBps: 48,
      quoteAgeSeconds: 5,
      confidenceScore: 0.67,
      status: "paper",
      source: "mock",
      skipReason: "paper_only",
      poolIds: ["pact-pnet-usdc", "tinyman-pnet-usdc"],
      appIds: ["reviewed"],
      assetIds: [3169177585, 31566704],
    },
    {
      routeHash: "mock-pnet-xdb-03",
      pair: "PNET/XDB",
      path: ["PNET", "XDB", "PNET"],
      venues: ["Tinyman", "Pact"],
      inputAmount: 500,
      expectedOutput: 500.4,
      grossProfit: 0.4,
      networkFees: 0.004,
      dexFees: 0.7,
      safetyBuffer: 0.5,
      netProfit: -0.804,
      profitBps: -16,
      priceImpactBps: 82,
      quoteAgeSeconds: 8,
      confidenceScore: 0.31,
      status: "rejected",
      source: "mock",
      skipReason: "price_impact",
      poolIds: ["tinyman-pnet-xdb", "pact-pnet-xdb"],
      appIds: ["needs review"],
      assetIds: [3169177585, 1290751153],
    },
  ];
}

function normalizeOpportunityRoute(item, index) {
  const route = item.route || [];
  const firstLeg = route[0] || {};
  const lastLeg = route[route.length - 1] || {};
  const path = route.length
    ? [assetLabel(firstLeg.input_asset_id), ...route.map((leg) => assetLabel(leg.output_asset_id))]
    : [assetLabel(item.input_asset_id), assetLabel(item.input_asset_id)];
  const venues = route.map((leg) => String(leg.venue || "venue"));
  const inputAsset = item.input_asset_id ?? firstLeg.input_asset_id ?? 0;
  const outputAsset = lastLeg.output_asset_id ?? inputAsset;
  return {
    routeHash: item.route_hash || `route-${index + 1}`,
    pair: `${assetLabel(inputAsset)}/${assetLabel(outputAsset)}`,
    path,
    venues,
    inputAmount: Number(item.input_amount || firstLeg.input_amount || 0),
    expectedOutput: Number(item.expected_final_amount || 0),
    grossProfit: Number(item.gross_profit || 0),
    networkFees: Number(item.estimated_network_fee || 0),
    dexFees: Number(item.total_dex_fees || 0),
    safetyBuffer: Number(item.slippage_buffer || 0),
    netProfit: Number(item.expected_net_profit || 0),
    profitBps: Number(item.expected_profit_bps || 0),
    priceImpactBps: Number(item.total_price_impact_bps || item.max_price_impact_bps || 0),
    quoteAgeSeconds: Math.max(0, Math.round(Date.now() / 1000 - Number(item.created_at || Date.now() / 1000))),
    confidenceScore:
      Number(item.confidence_score || 0) > 1
        ? Number(item.confidence_score || 0) / 100
        : Number(item.confidence_score || 0),
    status: item.status || "paper",
    source: "stored",
    skipReason: item.skip_reason || null,
    poolIds: route.map((leg) => leg.pool_id || "pool"),
    appIds: route.map((leg) => leg.app_id || "observed"),
    assetIds: item.involved_asset_ids || route.flatMap((leg) => [leg.input_asset_id, leg.output_asset_id]).filter(Boolean),
  };
}

function renderMetricCards(items) {
  return `
    <div class="cockpit-metrics">
      ${items
        .map(
          ([label, value, tone = "info", metricKey = null]) =>
            TraceableMetricArticle({
              label,
              value,
              metricKey,
              className: `cockpit-metric ${tone}`,
            })
        )
        .join("")}
    </div>`;
}

function renderPreflightChecklist() {
  const session = currentSession();
  const apiRows = (state.latestPreflight?.checklist || []).map((item) => [
    item.label,
    item.status,
    item.detail,
  ]);
  const rows = (apiRows.length ? apiRows : mockPreflightRows).map(([label, status, detail]) => {
    if (label === "Admin review wallet connected" && session.role === "admin") return [label, "ok", "Admin review wallet is connected."];
    if (label === "Admin wallet verified" && session.role === "admin") return [label, "ok", "Address matches the configured review allowlist."];
    if (label === "Correct network" && session.network !== APP_CONFIG.NETWORK) return [label, "blocked", "Switch wallet/network context to MainNet."];
    return [label, status, detail];
  });

  return `
    <section class="cockpit-card span-2">
      <div class="panel-head">
        <h2>Preflight / Readiness</h2>
        <span>${apiRows.length ? "Backend enforced" : "Local preview"}</span>
      </div>
      <div class="preflight-list">
        ${rows
          .map(
            ([label, status, detail]) => `
          <details class="preflight-row ${status}">
            <summary>
              <span>${escapeHtml(label)}</span>
              ${statusChip(status.toUpperCase(), status)}
            </summary>
            <p>${escapeHtml(detail)}</p>
          </details>`
          )
          .join("")}
      </div>
    </section>`;
}

function renderBotControlPanel() {
  const modes = [
    ["scanner", "Scanner only"],
    ["paper", "Paper"],
    ["dry-run", "Dry run"],
    ["live-micro", "Live micro"],
  ];
  const buttons = [
    ["Scan now", "scan"],
    ["Start scanner", "start-scanner"],
    ["Pause scanner", "pause-scanner"],
    ["Run route engine", "route-engine"],
    ["Start paper trading", "paper"],
    ["Build dry-run group", "dry-run"],
    ["Arm live micro-execution", "arm-live", "danger"],
    ["Disarm live execution", "disarm"],
    ["Trigger kill switch", "kill", "danger"],
    ["Clear kill switch", "clear-kill", "danger"],
  ];
  return `
    <section class="cockpit-card">
      <div class="panel-head">
        <h2>Bot Control</h2>
        <span>Admin only</span>
      </div>
      <div class="mode-switch" aria-label="Bot mode">
        ${modes
          .map(
            ([mode, label]) => `
        <button type="button" data-bot-mode="${escapeHtml(mode)}" class="${state.botMode === mode ? "active" : ""}">${escapeHtml(label)}</button>`
          )
          .join("")}
      </div>
      <div class="control-buttons">
        ${buttons
          .map(
            ([label, action, tone]) => `
          <button type="button" class="${tone === "danger" ? "danger-button" : ""}" data-admin-action="${escapeHtml(action)}">${escapeHtml(label)}</button>`
          )
          .join("")}
      </div>
      <p class="deck-note">${escapeHtml(state.operatorNotice)}</p>
    </section>`;
}

function renderRiskPolicyPanel() {
  const risk = state.latestReadiness?.risk || {};
  const rows = [
    ["Asset allowlist", "PNET, ALGO, USDC, reviewed ASAs"],
    ["App ID allowlist", `${fmt.format(risk.allowed_app_ids_count || 0)} loaded`],
    ["Max trade size", `${fmt.format(risk.max_live_trade_size || 10)} ALGO`],
    ["Max daily loss", "20 ALGO"],
    ["Max route length", `${fmt.format(risk.max_route_legs || 3)} swaps`],
    ["Max concurrent execution", `${fmt.format(risk.max_concurrent_execution || 1)}`],
    ["Quote max age", `${fmt.format(risk.max_route_age_seconds || 5)}s`],
    ["Min net profit", `${fmt.format(risk.min_net_profit_input_units || 0.25)} start units / ${fmt.format(risk.min_profit_bps || 35)} bps`],
    ["Max price impact", `${fmt.format(risk.max_price_impact_bps || 50)} bps`],
    ["Daily trade count", `${fmt.format(risk.submitted_live_trades_24h || 0)} / ${fmt.format(risk.max_daily_trades || 20)}`],
  ];
  return `
    <section class="cockpit-card">
      <div class="panel-head">
        <h2>Risk Policy</h2>
        <span>Review required</span>
      </div>
      <div class="policy-grid">
        ${rows.map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
      </div>
      <button type="button" data-admin-action="policy-change">Request policy change</button>
    </section>`;
}

function policyStatusClass(status) {
  const normalized = String(status || "review").toLowerCase();
  if (normalized === "configured") return "configured";
  if (normalized === "locked") return "locked";
  if (normalized === "required") return "required";
  if (normalized === "warning") return "warning";
  return "review";
}

function renderSignerPolicyCatalog() {
  const controls = state.latestPolicyCatalog.length ? state.latestPolicyCatalog : defaultPolicyCatalog;
  return `
    <section class="cockpit-card span-2">
      <div class="panel-head">
        <h2>Signer Policy Controls</h2>
        <span>${fmt.format(controls.length)} hard stops</span>
      </div>
      <div class="policy-control-grid">
        ${controls
          .map(
            (control) => `
          <article class="policy-control ${escapeHtml(policyStatusClass(control.status))}">
            <span>${escapeHtml(control.status || "review")}</span>
            <strong>${escapeHtml(control.label || String(control.code || "policy").replaceAll("_", " "))}</strong>
            <em>${escapeHtml(control.configuredValue || "configured")}</em>
            <p>${escapeHtml(control.rejects || "Rejects out-of-policy requests.")}</p>
          </article>`
          )
          .join("")}
      </div>
    </section>`;
}

function renderRouteConsole({ admin = false, compact = false } = {}) {
  const allRoutes = routeConsoleData();
  const pnetRouteRows = allRoutes.filter(routeTouchesPnet);
  const pnetWatchRows = pnetWatchlistRows().filter(
    (row) => !pnetRouteRows.some((route) => route.routeHash === row.routeHash)
  );
  const visibleRoutes =
    state.routeScope === "pnet"
      ? [...pnetRouteRows, ...pnetWatchRows]
      : allRoutes.filter((route) => routeMatchesScope(route, state.routeScope));
  const scopedRouteCount = visibleRoutes.length;
  const filteredRoutes = visibleRoutes.filter(routeMatchesFilters);
  const visibleRouteCount = filteredRoutes.length;
  const routes = filteredRoutes.slice(0, compact ? 3 : 8);
  const filters = state.routeFilters || {};
  const emptyCopy =
    state.routeScope === "algo"
      ? "Other ALGO routes are hidden by default and only shown here by intent."
      : state.routeScope === "all"
        ? "No route candidates are available from the current stored feed."
        : "No PNET route candidates yet. The dashboard is still watching PNET swaps, pools, and delayed reports.";
  return `
    <section class="cockpit-card span-2 route-console-card">
      <div class="panel-head">
        <h2>${admin ? "Route Console" : "Delayed Route Results"}</h2>
        <span>${routeScopeSummary(state.routeScope, visibleRouteCount, Math.max(allRoutes.length, visibleRouteCount))}</span>
      </div>
      <div class="route-filters" aria-label="Route filters">
        <div class="mode-switch route-scope-switch" aria-label="Route scope">
          <button type="button" data-route-scope="pnet" class="${state.routeScope === "pnet" ? "active" : ""}">PNET focus</button>
          <button type="button" data-route-scope="algo" class="${state.routeScope === "algo" ? "active" : ""}">Other ALGO</button>
          <button type="button" data-route-scope="all" class="${state.routeScope === "all" ? "active" : ""}">All routes</button>
        </div>
        <select aria-label="Venue filter" data-route-filter="venue">
          <option value="all" ${filters.venue === "all" ? "selected" : ""}>All venues</option>
          <option value="tinyman" ${filters.venue === "tinyman" ? "selected" : ""}>Tinyman</option>
          <option value="pact" ${filters.venue === "pact" ? "selected" : ""}>Pact</option>
          <option value="vestige" ${filters.venue === "vestige" ? "selected" : ""}>Vestige</option>
        </select>
        <input aria-label="Minimum profit" data-route-filter="minProfit" inputmode="decimal" placeholder="Min net" value="${escapeHtml(filters.minProfit || "")}" />
        <select aria-label="Route status" data-route-filter="status">
          <option value="all" ${filters.status === "all" ? "selected" : ""}>All status</option>
          <option value="approved" ${filters.status === "approved" ? "selected" : ""}>Approved</option>
          <option value="paper" ${filters.status === "paper" ? "selected" : ""}>Paper</option>
          <option value="watch" ${filters.status === "watch" ? "selected" : ""}>Watch</option>
          <option value="rejected" ${filters.status === "rejected" ? "selected" : ""}>Rejected</option>
          <option value="observed" ${filters.status === "observed" ? "selected" : ""}>Observed</option>
        </select>
        <button type="button" data-route-filter-reset="true">Reset filters</button>
      </div>
      <p class="route-filter-status">${escapeHtml(routeFilterSummary(filteredRoutes, scopedRouteCount))}</p>
      <div class="route-console ${compact ? "compact" : ""}">
        ${
          routes.length
            ? routes
                .map(
                  (route) => `
          <article class="route-card ${escapeHtml(route.status)}">
            <div class="route-card-main">
              <span class="route-hash">${escapeHtml(route.routeHash)}</span>
              <strong>${escapeHtml(route.pair)}</strong>
              <p>${escapeHtml(route.path.join(" -> "))}</p>
              <div class="route-mini-grid">
                <span><em>Venues</em>${escapeHtml(route.venues.join(" -> ") || "observed")}</span>
                ${TraceableMetricArticle({ label: "Input", value: fmt.format(route.inputAmount), source: route.source || "unavailable", metricKey: "route.expected_net_profit", routeHash: route.routeHash, className: "route-mini-metric" })}
                ${TraceableMetricArticle({ label: "Expected", value: fmt.format(route.expectedOutput), source: route.source || "unavailable", metricKey: "route.expected_net_profit", routeHash: route.routeHash, className: "route-mini-metric" })}
                ${TraceableMetricArticle({ label: "Net", value: fmt.format(route.netProfit), source: route.source || "unavailable", metricKey: "route.expected_net_profit", routeHash: route.routeHash, className: "route-mini-metric" })}
                <span><em>Fees</em>${fmt.format(route.networkFees + route.dexFees)}</span>
                ${TraceableMetricArticle({ label: "Impact", value: `${fmt.format(route.priceImpactBps)} bps`, source: route.source || "unavailable", metricKey: "route.price_impact_bps", routeHash: route.routeHash, className: "route-mini-metric" })}
                <span><em>Buffer</em>${fmt.format(route.safetyBuffer)}</span>
                ${TraceableMetricArticle({ label: "Confidence", value: `${fmt.format(route.confidenceScore * 100)}%`, source: route.source || "unavailable", metricKey: "route.confidence_score", routeHash: route.routeHash, className: "route-mini-metric" })}
              </div>
            </div>
            <div class="route-card-side">
              ${statusChip(route.status, route.status === "approved" ? "ok" : route.status === "rejected" ? "blocked" : "wait")}
              <span class="countdown">quote ${Math.max(0, 5 - route.quoteAgeSeconds)}s</span>
              <span>${route.skipReason ? escapeHtml(gateLabel(route.skipReason)) : `${fmt.format(route.profitBps)} bps`}</span>
              <button type="button" data-route-action="inspect" data-route-hash="${escapeHtml(route.routeHash)}">Inspect</button>
              <button type="button" data-route-action="paper" data-route-hash="${escapeHtml(route.routeHash)}">Paper trade</button>
              <button type="button" data-route-action="dry-run" data-route-hash="${escapeHtml(route.routeHash)}" ${admin ? "" : "disabled"}>Dry run</button>
              <button type="button" data-route-action="queue" data-route-hash="${escapeHtml(route.routeHash)}" ${admin && route.status === "approved" ? "" : "disabled"}>Queue</button>
            </div>
          </article>`
                )
                .join("")
            : `<div class="empty-state compact"><strong>No matching routes</strong><p>${escapeHtml(emptyCopy)}</p></div>`
        }
      </div>
    </section>`;
}

function renderExecutionQueue() {
  return `
    <section class="cockpit-card">
      <div class="panel-head">
        <h2>Execution Queue</h2>
        <span>Unsigned handoff</span>
      </div>
      <div class="queue-list">
        ${mockExecutionQueue
          .map(
            ([hash, amount, status, signer, result]) => `
          <div class="queue-row">
            <span>${escapeHtml(hash)}</span>
            <strong>${escapeHtml(status)}</strong>
            <span>${escapeHtml(amount)}</span>
            <span>${escapeHtml(signer)}</span>
            <span>${escapeHtml(result)}</span>
          </div>`
          )
          .join("")}
      </div>
    </section>`;
}

function renderReceiptFeed() {
  return `
    <section class="cockpit-card span-2">
      <div class="panel-head">
        <h2>Receipts / Reconciliation</h2>
        <span>Wins and losses shown</span>
      </div>
      <div class="receipt-grid">
        ${mockReceipts
          .map(
            ([tradeId, pair, expected, actual, net, status]) => `
          <div class="receipt-card">
            <span>${escapeHtml(tradeId)} / ${escapeHtml(pair)}</span>
            <strong>${escapeHtml(net)}</strong>
            <p>Expected ${escapeHtml(expected)} / actual ${escapeHtml(actual)}</p>
            <em>${escapeHtml(status)}</em>
          </div>`
          )
          .join("")}
      </div>
    </section>`;
}

function alertSeverityClass(severity) {
  const normalized = String(severity || "info").toLowerCase();
  if (normalized === "critical") return "critical";
  if (normalized === "high" || normalized === "blocked") return "blocked";
  if (normalized === "warning" || normalized === "warn") return "warn";
  return "info";
}

function renderLogPanel() {
  const alerts = state.latestAlertCatalog.length ? state.latestAlertCatalog : defaultAlertCatalog;
  return `
    <section class="cockpit-card span-2">
      <div class="panel-head">
        <h2>Alert Catalog</h2>
        <span>${fmt.format(alerts.length)} watched conditions</span>
      </div>
      <div class="alert-feed alert-catalog">
        ${alerts
          .map(
            (alert) => `
          <div class="alert-row ${escapeHtml(alertSeverityClass(alert.severity))}">
            <span>${escapeHtml(alert.severity || "info")}</span>
            <strong>${escapeHtml(alert.title || String(alert.code || "alert").replaceAll("_", " "))}</strong>
            <p>
              <b>${escapeHtml(alert.code || "alert")}</b>
              ${escapeHtml(alert.trigger || "Trigger definition pending.")}
              <em>${escapeHtml(alert.operatorAction || "Operator action pending.")}</em>
            </p>
          </div>`
          )
          .join("")}
      </div>
    </section>`;
}

function renderAdminCommandHeader() {
  const readiness = state.latestReadiness || {};
  const preflight = state.latestPreflight || {};
  const paperReport = state.latestPaperReport || {};
  const scan = readiness.scan || {};
  const risk = readiness.risk || {};
  const signer = readiness.signer || {};
  const liveArmed = readiness.execution_flags?.enable_live_execution && readiness.execution_flags?.execute_approved;
  const cards = [
    ["Bot mode", liveArmed ? "Live Micro" : scan.ran_now ? "Scanner" : "Paper"],
    ["Live execution", liveArmed ? "Armed" : "Disarmed", liveArmed ? "danger" : "warn"],
    ["Risk gate", readiness.best_approved_route ? "Passing" : "Blocked", readiness.best_approved_route ? "ok" : "warn"],
    ["Signer", signer.enabled ? "Online" : "Locked", signer.enabled ? "ok" : "warn"],
    ["Hot wallet reserve", preflight.hotWalletReserve || readiness.wallet?.balance_detail || "lookup needed"],
    ["Paper daily", `${fmt.format(paperReport.simulatedProfit30s || 0)} net`],
    ["Daily loss room", preflight.dailyLossRemaining ? `${preflight.dailyLossRemaining} ALGO` : "20 ALGO"],
    ["Last confirmed trade", "dry-run only"],
    ["Last scan age", scan.last_scan_age_seconds === null ? "none" : `${Math.round(scan.last_scan_age_seconds || 0)}s`],
    ["Quote freshness", `${fmt.format(risk.max_route_age_seconds || 5)}s max`],
  ];
  return `
    <section class="cockpit-card span-3 admin-command-header">
      <div>
        <p class="eyebrow">Admin Cockpit</p>
        <h2>PNET Arb Control</h2>
        <p>Algorand market scanner, route engine, and controlled own-funds micro-arb execution.</p>
      </div>
      ${renderMetricCards(cards)}
    </section>`;
}

function renderPublicJourneyPanel() {
  const session = currentSession();
  if (session.role === "admin") return "";
  const swapSource = state.recentPnetSwaps?.sourceLabel || "Delayed watch feed";
  const swapSourceState = state.recentPnetSwaps?.source === "live" ? "live" : "delayed";
  const walletState = session.role === "guest" ? "Not connected" : "Connected";
  const pnetState = session.optedIn ? `${fmt.format(session.pnetBalance || 0)} PNET` : "PNET opt-in needed";
  const pillars = [
    ["Market feed", swapSource, swapSourceState],
    ["Routes", "Delayed research", "delayed"],
    ["Wallet", walletState, session.role === "guest" ? "wait" : "ok"],
    ["Access", pnetState, session.optedIn ? "ok" : "wait"],
    ["Execution", "Locked", "blocked"],
  ];
  const steps = [
    ["1", "Watch scanner", "The bot keeps checking PNET pools and route candidates from supported venues.", "Pulse", "pulse"],
    ["2", "Inspect a price gap", "Open a delayed candidate row to see why it passed, failed, or needs paper review.", "Routes", "routes"],
    ["3", "Read the summary", "Use research for delayed market-pulse context and PNET liquidity visibility.", "Research", "research"],
    ["4", "Unlock premium report", "Use PNET/x402 access for premium delayed reports only, not trading.", "PNET Access", "access"],
  ];
  return `
    <section class="cockpit-card span-3 public-journey-card">
      <div class="panel-head">
        <h2>User Mission Control</h2>
        <span>UX first</span>
      </div>
      <div class="ux-priority-strip" aria-label="Current user-facing safety and data state">
        ${pillars
          .map(
            ([label, value, tone]) => `
          <article class="${escapeHtml(tone)}">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
          </article>`
          )
          .join("")}
      </div>
      <p class="deck-note">Phase 2 priority: make the market signal understandable first. Real swaps are labeled by source, routes stay delayed/research-safe, and execution remains locked. Admin execution and creator controls are hidden from this role.</p>
      <div class="public-journey-grid">
        ${steps
          .map(
            ([step, title, detail, cta, view]) => `
          <article>
            <span>${escapeHtml(step)}</span>
            <strong>${escapeHtml(title)}</strong>
            <p>${escapeHtml(detail)}</p>
            <button type="button" data-journey-view="${escapeHtml(view)}">${escapeHtml(cta)}</button>
          </article>`
          )
          .join("")}
      </div>
    </section>`;
}

function arbActionForRoute(route) {
  const path = route.path || [];
  const first = path[0] || "";
  const last = path[path.length - 1] || "";
  if (first === "PNET" && last === "PNET") return "Loop";
  if (first === "PNET") return "Sell";
  if (last === "PNET" || path.includes("PNET")) return "Buy";
  return "Watch";
}

function arbActionTone(action, status) {
  if (status === "approved") return "buy";
  if (status === "rejected") return "blocked";
  if (action === "Sell") return "sell";
  if (action === "Buy") return "buy";
  return "watch";
}

function routeTouchesPnet(route) {
  const pnetId = Number(APP_CONFIG.PNET_ASA_ID);
  const path = (route.path || []).map((item) => String(item).toUpperCase());
  const assetIds = (route.assetIds || []).map((item) => Number(item));
  return (
    String(route.pair || "").toUpperCase().includes("PNET") ||
    path.includes("PNET") ||
    assetIds.includes(pnetId)
  );
}

function routeTouchesAlgo(route) {
  const path = (route.path || []).map((item) => String(item).toUpperCase());
  const assetIds = (route.assetIds || []).map((item) => Number(item));
  return String(route.pair || "").toUpperCase().includes("ALGO") || path.includes("ALGO") || assetIds.includes(0);
}

function routeMatchesScope(route, scope) {
  if (scope === "all") return true;
  if (scope === "algo") return routeTouchesAlgo(route) && !routeTouchesPnet(route);
  return routeTouchesPnet(route);
}

function routeProfitForFilter(route) {
  const status = String(route.status || "").toLowerCase();
  if (["watch", "observed", "example"].includes(status) || route.skipReason === "listed_without_arb") return 0;
  return Number(route.netProfit || 0);
}

function routeMatchesFilters(route) {
  const filters = state.routeFilters || {};
  const venue = String(filters.venue || "all").toLowerCase();
  const status = String(filters.status || "all").toLowerCase();
  const minProfitRaw = String(filters.minProfit || "").trim();
  const minProfit = minProfitRaw === "" ? null : Number(minProfitRaw);
  const routeVenues = listValue(route.venues).map((item) => String(item).toLowerCase());
  const routeStatus = String(route.status || "review").toLowerCase();
  if (venue !== "all" && !routeVenues.some((item) => item.includes(venue))) return false;
  if (status !== "all" && routeStatus !== status) return false;
  if (minProfit !== null && !Number.isNaN(minProfit) && routeProfitForFilter(route) < minProfit) return false;
  return true;
}

function routeFilterSummary(routes, scopedCount) {
  const active = [];
  const filters = state.routeFilters || {};
  if (filters.venue && filters.venue !== "all") active.push(`venue ${filters.venue}`);
  if (filters.status && filters.status !== "all") active.push(`status ${filters.status}`);
  if (String(filters.minProfit || "").trim()) active.push(`min ${filters.minProfit}`);
  if (!active.length) return `${fmt.format(routes.length)} shown`;
  return `${fmt.format(routes.length)} / ${fmt.format(scopedCount)} shown, ${active.join(" / ")}`;
}

function routeScopeSummary(scope, visibleCount, totalCount) {
  if (scope === "algo") return `${fmt.format(visibleCount)} other ALGO / ${fmt.format(totalCount)} total`;
  if (scope === "all") return `${fmt.format(visibleCount)} all routes`;
  return `${fmt.format(visibleCount)} PNET-first routes`;
}

function pnetWatchlistRows() {
  const report = selectedResearchReport();
  const watchlist = report?.pnetLiquidityWatchlist || {};
  return (watchlist.pools || []).slice(0, 4).map((pool, index) => {
    const pair = pool.pairLabel || "PNET pool";
    const otherAsset = pair
      .split("/")
      .map((item) => item.trim())
      .find((item) => item && item.toUpperCase() !== "PNET") || "asset";
    return {
      routeHash: `pnet-watch-${String(pool.poolId || index + 1).replace(/[^a-z0-9_-]/gi, "-")}`,
      pair,
      path: ["PNET", otherAsset],
      venues: [pool.venue || "observed venue"],
      inputAmount: Number(pool.pnetReserve || 0),
      expectedOutput: Number(pool.otherReserve || 0),
      grossProfit: 0,
      networkFees: 0,
      dexFees: 0,
      safetyBuffer: 0,
      netProfit: Number(pool.liquidityEstimate || 0),
      profitBps: Number(pool.liquidityChangePct || 0),
      priceImpactBps: 0,
      quoteAgeSeconds: Number(pool.snapshotAgeSeconds || 0),
      confidenceScore: 0,
      status: "watch",
      source: pool.source || watchlist.source || report?.source || "delayed report",
      skipReason: "listed_without_arb",
      assetIds: [APP_CONFIG.PNET_ASA_ID],
      fromAsset: "PNET",
      toAsset: otherAsset,
      action: "Watch",
      actionTone: "watch",
      ageLabel: "delayed",
      sourceLabel: `${pool.venue || "venue"} PNET pool surface`,
      netValueLabel: "LP surface",
      statusLabel: watchlist.listedWithoutOpportunity === false ? "PNET route candidate" : "listed without arb",
    };
  });
}

function arbWatchRows() {
  const routeRows = routeConsoleData();
  const pnetRouteRows = routeRows.filter(routeTouchesPnet);
  const rows = [...pnetRouteRows, ...pnetWatchlistRows()];
  const selectedRows = rows.length ? rows : routeRows;
  return selectedRows
    .slice(0, 6)
    .map((route) => {
      const action = route.action || arbActionForRoute(route);
      const path = route.path || [];
      const fromAsset = path[0] || route.pair.split("/")[0] || "asset";
      const toAsset = path[path.length - 1] || route.pair.split("/")[1] || "asset";
      return {
        ...route,
        action,
        actionTone: route.actionTone || arbActionTone(action, route.status),
        fromAsset: route.fromAsset || fromAsset,
        toAsset: route.toAsset || toAsset,
        ageLabel: route.ageLabel || (route.source === "stored" ? `${fmt.format(route.quoteAgeSeconds || 0)}s ago` : "preview"),
        sourceLabel: route.sourceLabel || (route.venues?.length ? route.venues.join(" / ") : "scanner"),
      };
    });
}

function tokenLogo(asset) {
  const symbol = String(asset || "").toUpperCase();
  const labels = {
    ALGO: "A",
    PNET: "P",
    USDC: "$",
    VOTE: "V",
    HOG: "H",
    PAW: "P",
  };
  return labels[symbol] || symbol.slice(0, 1) || "?";
}

function recentPnetSwapRows(routes) {
  const liveRows = (state.recentPnetSwaps?.swaps || []).slice(0, 5).map((swap) => ({
    routeHash: swap.routeHash || swap.id,
    pair: swap.pair,
    fromAsset: swap.fromAsset,
    toAsset: swap.toAsset,
    inputAmount: Number(swap.inputAmount || 0),
    expectedOutput: Number(swap.expectedOutput || 0),
    ageLabel: swap.ageLabel || "live",
    notionalLabel: swap.notionalLabel || `$${fmt.format(Number(swap.notionalUsd || 0))}`,
    venueIcon: "pool",
    source: swap.source || "live",
    sourceLabel: `${swap.protocolLabel || "Vestige"} / ${swap.sourceLabel || "Vestige swaps API"}`,
    sample: false,
    block: swap.block,
  }));
  const pnetRows = routes.filter(routeTouchesPnet);
  const sampleRows = [
    {
      routeHash: "sample-pnet-algo-swap",
      pair: "PNET/ALGO",
      fromAsset: "PNET",
      toAsset: "ALGO",
      inputAmount: 4777,
      expectedOutput: 0.32,
      ageLabel: "sample",
      notionalLabel: "$0.03",
      venueIcon: "pool",
      sample: true,
    },
    {
      routeHash: "sample-algo-pnet-swap",
      pair: "ALGO/PNET",
      fromAsset: "ALGO",
      toAsset: "PNET",
      inputAmount: 0.32,
      expectedOutput: 4777,
      ageLabel: "sample",
      notionalLabel: "$0.03",
      venueIcon: "route",
      sample: true,
    },
    {
      routeHash: "sample-usdc-pnet-swap",
      pair: "USDC/PNET",
      fromAsset: "USDC",
      toAsset: "PNET",
      inputAmount: 0.19,
      expectedOutput: 532,
      ageLabel: "sample",
      notionalLabel: "$0.19",
      venueIcon: "pool",
      sample: true,
    },
  ];
  const rows = [...liveRows, ...pnetRows, ...sampleRows].slice(0, 5);
  return rows.slice(0, 5).map((row, index) => ({
    ...row,
    ageLabel: row.ageLabel || (row.source === "stored" ? `${fmt.format(row.quoteAgeSeconds || 0)}s ago` : "delayed"),
    notionalLabel: row.notionalLabel || `$${fmt.format(Math.max(0.01, Math.abs(Number(row.netProfit || row.expectedOutput || 0)) / 100))}`,
    venueIcon: row.venueIcon || (index % 2 === 0 ? "pool" : "route"),
  }));
}

function RecentPnetSwapsPanel(routes) {
  const swaps = recentPnetSwapRows(routes);
  return `
    <div class="recent-swaps-panel" aria-label="Recent PNET swap watch">
      <div class="recent-swaps-head">
        <h3>Recent PNET swaps</h3>
        <span>${escapeHtml(state.recentPnetSwaps?.sourceLabel || "Delayed watch feed")}</span>
      </div>
      ${
        state.recentPnetSwapsError
          ? `<p class="muted">Real swap feed unavailable; showing delayed route examples.</p>`
          : state.recentPnetSwaps?.source === "live"
            ? `<p class="muted">Read-only Vestige market data. No wallet, signer, transaction submission, or executable route payload is exposed.</p>`
            : ""
      }
      ${swaps
        .map(
          (swap) => `
        <article class="recent-swap-row ${swap.sample ? "sample" : ""}">
          <span class="swap-venue ${escapeHtml(swap.venueIcon)}" aria-hidden="true">${swap.venueIcon === "pool" ? "LP" : "R"}</span>
          <div class="swap-meta">
            <strong>Swap</strong>
            <span>${escapeHtml(swap.sample ? "example" : swap.ageLabel)}</span>
            ${swap.sourceLabel ? `<em>${escapeHtml(swap.sourceLabel)}</em>` : ""}
          </div>
          <div class="swap-token-pill">
            <strong>${fmt.format(swap.inputAmount)}</strong>
            <span class="token-logo ${escapeHtml(String(swap.fromAsset || "").toLowerCase())}">${escapeHtml(tokenLogo(swap.fromAsset))}</span>
            <em>${escapeHtml(swap.fromAsset || "asset")}</em>
            <small>${escapeHtml(swap.notionalLabel)}</small>
          </div>
          <span class="swap-arrow">-&gt;</span>
          <div class="swap-token-pill">
            <strong>${fmt.format(swap.expectedOutput)}</strong>
            <span class="token-logo ${escapeHtml(String(swap.toAsset || "").toLowerCase())}">${escapeHtml(tokenLogo(swap.toAsset))}</span>
            <em>${escapeHtml(swap.toAsset || "asset")}</em>
            <small>${escapeHtml(swap.notionalLabel)}</small>
          </div>
          <button type="button" data-route-action="inspect" data-route-hash="${escapeHtml(swap.routeHash)}">Inspect</button>
        </article>`
        )
        .join("")}
    </div>`;
}

function ArbBotWatchPanel() {
  const readiness = state.latestReadiness || {};
  const scan = readiness.scan || {};
  const routes = arbWatchRows();
  const liveArmed = readiness.execution_flags?.enable_live_execution && readiness.execution_flags?.execute_approved;
  const target = readiness.target_asset?.discovery?.target_asset?.ticker || "PNET";
  const lastScan = scan.last_scan_age_seconds === null || scan.last_scan_age_seconds === undefined ? "waiting" : `${fmt.format(scan.last_scan_age_seconds)}s ago`;
  return `
    <section class="cockpit-card span-3 arb-watch-card">
      <div class="arb-watch-head">
        <div>
          <p class="eyebrow">Arbitrage bot watch</p>
          <h2>PNET Arb Scanner</h2>
          <p>The bot is constantly looking for PNET price gaps across supported Algorand venues. Public mode shows delayed/read-only candidates; it does not sign, submit, custody, or trade.</p>
        </div>
        <div class="arb-watch-status">
          <span>${liveArmed ? "Live armed" : "Watching only"}</span>
          <strong>${escapeHtml(target)}</strong>
          <em>Refreshes every 15s</em>
        </div>
      </div>
      <div class="arb-watch-metrics">
        <div><span>Pools watched</span><strong>${fmt.format(scan.pools_monitored || state.latestPools.length || 0)}</strong></div>
        <div><span>Candidates</span><strong>${fmt.format(readiness.scan?.opportunities_24h || state.latestOpportunities.length || 0)}</strong></div>
        <div><span>Approved</span><strong>${fmt.format(readiness.scan?.approved_24h || 0)}</strong></div>
        <div><span>Last scan</span><strong>${escapeHtml(lastScan)}</strong></div>
      </div>
      <div class="arb-feed" aria-label="PNET arbitrage watch feed">
        ${routes
          .map(
            (route) => `
          <article class="arb-feed-row ${escapeHtml(route.status)}">
            <span class="arb-action ${escapeHtml(route.actionTone)}">${escapeHtml(route.action)}</span>
            <div class="arb-route-source">
              <strong>${escapeHtml(route.pair)}</strong>
              <em>${escapeHtml(route.sourceLabel)}</em>
            </div>
            <div class="arb-swap-pill">
              <strong>${fmt.format(route.inputAmount)}</strong>
              <span>${escapeHtml(route.fromAsset)}</span>
            </div>
            <span class="arb-arrow">-&gt;</span>
            <div class="arb-swap-pill">
              <strong>${fmt.format(route.expectedOutput)}</strong>
              <span>${escapeHtml(route.toAsset)}</span>
            </div>
            <div class="arb-net">
              <strong>${escapeHtml(route.netValueLabel || fmt.format(route.netProfit))}</strong>
              <span>${escapeHtml(route.statusLabel || (route.skipReason ? gateLabel(route.skipReason) : `${fmt.format(route.profitBps)} bps`))}</span>
            </div>
            <span class="arb-age">${escapeHtml(route.ageLabel)}</span>
            <button type="button" data-route-action="inspect" data-route-hash="${escapeHtml(route.routeHash)}">Inspect</button>
          </article>`
          )
          .join("")}
      </div>
      ${RecentPnetSwapsPanel(routes)}
      <div class="arb-watch-flow">
        <span>1. Scan pools</span>
        <span>2. Compare venue quotes</span>
        <span>3. Flag price gap</span>
        <span>4. Risk/paper review</span>
        <span>5. Trading stays gated</span>
      </div>
    </section>`;
}

function renderWalletProviderSwitch({ compact = false } = {}) {
  const provider = currentWalletProvider();
  const network = currentWalletNetwork();
  const backendNetwork = APP_CONFIG.NETWORK || "testnet";
  const mismatch = network.key !== backendNetwork;
  const live = state.walletConnection || {};
  return `
    <div class="wallet-provider-panel ${compact ? "compact" : ""}" aria-label="Wallet provider and network selector">
      <div class="wallet-control-grid">
        <div>
          <span>Wallet</span>
          <div class="mode-switch wallet-provider-switch" role="group" aria-label="Wallet provider">
            ${Object.values(walletProviders)
              .map(
                (item) => `
              <button type="button" data-wallet-provider="${escapeHtml(item.key)}" class="${item.key === provider.key ? "active" : ""}">
                ${escapeHtml(item.label)}
              </button>`
              )
              .join("")}
          </div>
        </div>
        <div>
          <span>Network</span>
          <div class="mode-switch wallet-network-switch" role="group" aria-label="Network selector">
            ${Object.values(walletNetworks)
              .map(
                (item) => `
              <button type="button" data-wallet-network="${escapeHtml(item.key)}" class="${item.key === network.key ? "active" : ""} ${item.key !== backendNetwork ? "mismatch" : ""}">
                ${escapeHtml(item.label)}
              </button>`
              )
              .join("")}
          </div>
        </div>
      </div>
      <div class="wallet-provider-note ${mismatch || live.status === "wrong_network" ? "warn" : ""} ${live.status === "loading" ? "loading" : ""}">
        <span>${escapeHtml(provider.label)} / ${escapeHtml(network.label)} / ${escapeHtml(provider.status)}</span>
        <strong>${escapeHtml(provider.method)}</strong>
        <p>${escapeHtml(provider.capability)}</p>
        <p>${escapeHtml(provider.boundary)} ${escapeHtml(network.boundary)}</p>
        <p><strong>Backend network:</strong> ${escapeHtml(backendNetwork)} (authority). Chain id ${escapeHtml(String(backendChainId()))}.</p>
        ${
          mismatch
            ? `<p class="wallet-mismatch-msg">MainNet mismatch: backend is ${escapeHtml(backendNetwork)}. Connection will be rejected until the selector matches.</p>`
            : ""
        }
        ${live.status === "rejected" || live.status === "unavailable" ? `<p class="wallet-error-msg">${escapeHtml(live.error || "Wallet connection failed.")}</p>` : ""}
        ${live.status === "connected" && live.address ? `<p class="wallet-live-msg">Connected ${escapeHtml(shortAddress(live.address))} · ${escapeHtml(live.algoBalance != null ? `${fmt.format(Number(live.algoBalance))} ALGO` : "ALGO n/a")}</p>` : ""}
        <a class="wallet-provider-docs" href="${escapeHtml(provider.docsUrl)}" target="_blank" rel="noreferrer">
          Review ${escapeHtml(provider.label)} integration docs
        </a>
      </div>
    </div>`;
}

function renderPnetAccessGate() {
  const session = currentSession();
  const provider = currentWalletProvider();
  const providerSwitch = renderWalletProviderSwitch();
  const pnetConfigured = APP_CONFIG.PNET_ASA_CONFIGURED !== false && Number(APP_CONFIG.PNET_ASA_ID || 0) > 0;
  if (session.state === "loading") {
    return `
      <div class="access-gate wait-gate">
        ${providerSwitch}
        <strong>Connecting ${escapeHtml(provider.label)}…</strong>
        <p>Waiting for wallet approval. Connect-only — no signing or submission requests are sent.</p>
      </div>`;
  }
  if (session.state === "wrong_network") {
    return `
      <div class="access-gate blocked-gate">
        ${providerSwitch}
        <strong>Wrong network</strong>
        <p>Backend network is ${escapeHtml(APP_CONFIG.NETWORK === "testnet" ? "TestNet" : "MainNet")}. MainNet wallet/network mismatches are rejected. Select the backend network and reconnect.</p>
      </div>`;
  }
  if (session.role === "guest") {
    return `
      <div class="access-gate guest-gate">
        ${providerSwitch}
        <strong>Connect ${escapeHtml(provider.label)} Wallet</strong>
        <p>Connect Pera or Defly on TestNet to read your address and ALGO balance. Signing, opt-in transactions, and submission stay disabled.</p>
        <button type="button" data-wallet-connect="1">Connect ${escapeHtml(provider.label)}</button>
      </div>`;
  }
  if (session.network !== APP_CONFIG.NETWORK || session.state === "wrong_network") {
    return `
      <div class="access-gate blocked-gate">
        ${providerSwitch}
        <strong>Wrong network</strong>
        <p>Backend network is ${escapeHtml(APP_CONFIG.NETWORK === "testnet" ? "TestNet" : "MainNet")}. MainNet wallet/network mismatches are rejected. Disconnect and reconnect on the backend network.</p>
        <button type="button" data-wallet-disconnect="1">Disconnect</button>
      </div>`;
  }
  if (!pnetConfigured) {
    return `
      <div class="access-gate wait-gate">
        ${providerSwitch}
        <strong>PNET TestNet asset not configured</strong>
        <p>ALGO account verification still works. Address ${escapeHtml(shortAddress(session.address))} · ${escapeHtml(session.algoBalance != null ? `${fmt.format(Number(session.algoBalance))} ALGO` : "ALGO n/a")}. Configure a TestNet PNET ASA id before fee-gated features.</p>
        <button type="button" data-wallet-disconnect="1">Disconnect</button>
      </div>`;
  }
  if (!session.optedIn) {
    return `
      <div class="access-gate wait-gate">
        ${providerSwitch}
        <strong>PNET not opted in</strong>
        <p>${escapeHtml(session.pnetMessage || "Wallet is not opted into the configured TestNet PNET ASA.")} Opt-in transactions are not offered from this app (connect/read only).</p>
        <button type="button" data-wallet-disconnect="1">Disconnect</button>
      </div>`;
  }
  if (session.pnetBalance < 12) {
    return `
      <div class="access-gate wait-gate">
        ${providerSwitch}
        <strong>PNET balance too low</strong>
        <p>Required fee starts at 12 PNET. Current balance: ${fmt.format(session.pnetBalance)} PNET.</p>
      </div>`;
  }
  return `
    <div class="access-gate ok-gate">
      ${providerSwitch}
      <strong>PNET fee ready</strong>
      <p>Request market intelligence, route simulations, or pool monitoring. These are data fees, not deposits into the bot.</p>
      <div class="access-actions">
        ${Object.entries(pnetActions)
          .map(
            ([key, action]) => `
          <button type="button" data-pnet-action="${escapeHtml(key)}">${escapeHtml(action.label)} / ${fmt.format(action.fee)} PNET</button>`
          )
          .join("")}
      </div>
    </div>`;
}

function renderPnetNoGateBuilds() {
  const safeItems = [
    ["Live PNET liquidity watchlist", "Lists observed PNET pools from read-only Tinyman/Pact/Vestige data even when no arb route is approved.", "Research", "research"],
    ["Read-only market summary refresh", "Pulls fresh scanner evidence into delayed reports without signing, submitting, or exposing executable routes.", "Refresh in Research", "research"],
    ["LP education lane", "Explains how someone can review PNET pools externally and why liquidity provision carries risk.", "Review below", "access"],
    ["Unsigned utility tools", "Payment URI builder, IL calculator, and node status stay local/read-only and do not connect a wallet.", "Utility", "utility"],
    ["Premium report access boundary", "x402/PNET access unlocks delayed report data only, not live trading signals or bot execution.", "PNET Access", "access"],
    ["Contribution Protocol beta", "Lets users submit reviewed contributions and spend local credits on bounded access surfaces without token rewards or governance control.", "Review dashboard", "access"],
    ["Community growth beta", "Referral receipts, onboarding, contributor leaderboard, and reputation badges can run as local-review evidence without automatic rewards.", "Review community", "access"],
    ["Content system", "30-day calendar, X threads, blog templates, website copy, and diagrams can be drafted around verified utility and contribution evidence.", "Review copy", "access"],
    ["Documentation and audit readiness", "Tokenomics facts, use-case docs, roadmap language, audit-scope inventory, and image evidence can be drafted before external publication.", "Docs packet", "access"],
  ];
  const gatedItems = [
    "Smart-contract or atomic-group dry-run expansion",
    "Signer, wallet custody, private keys, or transaction submission",
    "Mainnet deploy, public challenge eligibility claims, or production trading",
    "LP incentives, rewards, staking, ROI, buy/sell, or price claims",
    "External publication, CEX/listing outreach, or audited/production-ready claims",
    "On-chain credit contract deployment or binding governance",
    "Automatic referral rewards, self-payment loops, or production leaderboard claims",
  ];
  return `
    <section class="cockpit-card span-3 no-gate-build-card">
      <div class="panel-head">
        <h2>No-Gate Builds Available Now</h2>
        <span>Public-safe</span>
      </div>
      <p class="deck-note">These are safe product surfaces we can build and iterate without crossing signer, trading, Mainnet, deploy, or public-claim gates.</p>
      <div class="no-gate-build-grid">
        ${safeItems
          .map(
            ([title, detail, cta, view]) => `
          <article>
            ${statusChip("SAFE", "ok")}
            <strong>${escapeHtml(title)}</strong>
            <p>${escapeHtml(detail)}</p>
            <button type="button" data-journey-view="${escapeHtml(view)}">${escapeHtml(cta)}</button>
          </article>`
          )
          .join("")}
      </div>
      <div class="no-gate-blocked-list">
        <strong>Still gated</strong>
        ${gatedItems.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
      </div>
    </section>`;
}

function renderPnetLiquidityEducation() {
  const steps = [
    ["1", "Inspect PNET pool visibility", "Use the Research watchlist to see which PNET pairs and venues were observed by the read-only scanner."],
    ["2", "Review LP risk externally", "Liquidity provision can lose value through price movement, fees, thin pools, and impermanent loss."],
    ["3", "Use your own wallet outside AlgoPulse", "AlgoPulse does not custody funds, sign transactions, submit transactions, or provide wallet instructions."],
    ["4", "Refresh the watchlist later", "After external LP changes, refresh Research to see whether public pool visibility changed."],
  ];
  return `
    <section class="cockpit-card span-3 pnet-lp-education-card">
      <div class="panel-head">
        <h2>PNET LP Visibility Lane</h2>
        <span>Education only</span>
      </div>
      <p class="deck-note">This can encourage healthier PNET liquidity by making pool visibility easy to inspect, without promising returns or handling funds.</p>
      <div class="pnet-lp-step-grid">
        ${steps
          .map(
            ([step, title, detail]) => `
          <article>
            <span>${escapeHtml(step)}</span>
            <strong>${escapeHtml(title)}</strong>
            <p>${escapeHtml(detail)}</p>
          </article>`
          )
          .join("")}
      </div>
      <div class="utility-status-line wait"><span></span><strong>Not financial advice. No ROI, rewards, staking, or price claims are made here.</strong></div>
    </section>`;
}

function ContributionProtocolDashboard() {
  const session = currentSession();
  const data = state.contributionProtocol;
  const catalog = data?.catalog || {};
  const contributionActions = catalog.contributionActions || [];
  const creditUnlocks = catalog.creditUnlocks || [];
  const activity = data?.activityHistory || [];
  const connected = session.role !== "guest";
  const disabled = connected ? "" : "disabled";
  return `
    <section class="cockpit-card span-3 contribution-protocol-card">
      <div class="panel-head">
        <h2>Contribution Protocol Beta</h2>
        <span>${escapeHtml(catalog.smartContractStatus || "local-review")}</span>
      </div>
      <p class="deck-note">PNET credits unlock bounded tool access, delayed reports, non-binding governance signals, and beta previews. They are not token rewards, yield, revenue share, treasury control, or trading permission.</p>
      ${
        state.contributionProtocolLoading
          ? `<div class="loading-row">Loading contribution protocol...</div>`
          : state.contributionProtocolError
          ? `<div class="verification-banner fail"><strong>Contribution protocol unavailable</strong><span>${escapeHtml(
              state.contributionProtocolError
            )}</span></div>`
          : ""
      }
      <div class="contribution-summary-grid">
        <div><span>Wallet</span><strong>${escapeHtml(shortAddress(session.address))}</strong></div>
        <div><span>Credit balance</span><strong>${fmt.format(data?.creditBalance ?? session.credits ?? 0)}</strong></div>
        <div><span>Pending review</span><strong>${fmt.format(data?.pendingContributions ?? 0)}</strong></div>
        <div><span>Auth mode</span><strong>${escapeHtml(data?.authMode || "local-review-mock")}</strong></div>
      </div>
      <div class="contribution-flow-grid">
        <article>
          <h3>Submit contribution</h3>
          <p>Send docs fixes, pool observations, beta feedback, data-source ideas, or safety reports for manual review.</p>
          <div class="contribution-action-list">
            ${contributionActions
              .map(
                (item) => `
              <button type="button" data-contribution-submit="${escapeHtml(item.code)}" ${disabled}>
                <strong>${escapeHtml(item.label)}</strong>
                <span>Pending review / ${fmt.format(item.credits || 0)} credit${Number(item.credits) === 1 ? "" : "s"}</span>
              </button>`
              )
              .join("")}
          </div>
        </article>
        <article>
          <h3>Spend credits</h3>
          <p>Use approved credits for access boundaries only. Governance is a non-binding signal until a separate review gate says otherwise.</p>
          <div class="contribution-action-list">
            ${creditUnlocks
              .map(
                (item) => `
              <button type="button" data-credit-spend="${escapeHtml(item.code)}" ${disabled}>
                <strong>${escapeHtml(item.label)}</strong>
                <span>${fmt.format(item.creditsCost || 0)} credit${Number(item.creditsCost) === 1 ? "" : "s"} / ${escapeHtml(
                  item.category || "access"
                )}</span>
              </button>`
              )
              .join("")}
          </div>
        </article>
      </div>
      <div class="contribution-activity">
        <div class="panel-head mini">
          <h3>Activity history</h3>
          <span>${fmt.format(activity.length)} events</span>
        </div>
        ${
          activity.length
            ? activity
                .slice(0, 6)
                .map(
                  (item) => `
            <div class="contribution-event">
              <strong>${escapeHtml(item.label || item.title || item.kind)}</strong>
              <span>${escapeHtml(item.status || "recorded")}</span>
              <p>${escapeHtml(item.title || item.unlockCode || item.contributionType || item.kind)}</p>
            </div>`
                )
                .join("")
            : `<p class="muted">No contribution events yet. Connect a review wallet and submit a beta contribution to start the local ledger.</p>`
        }
      </div>
      <div class="integration-boundary">
        <strong>AlgoFlow integration boundary</strong>
        <p>${escapeHtml(
          data?.integrationBoundary ||
            "AlgoFlow can consume contribution receipts and credit-spend receipts later, but it must not receive signer secrets, custody funds, or execute trades."
        )}</p>
      </div>
    </section>`;
}

function PnetContentSystemPanel() {
  const cards = [
    [
      "Tokenomics, documented as facts",
      "PNET is referenced by Algorand ASA ID 3169177585. Public copy should use verified facts only and avoid price, ROI, listing, or buy/sell claims.",
    ],
    [
      "Verified contribution",
      "Docs fixes, pool observations, bug reports, demo feedback, and data-source suggestions can enter manual review before credits are granted.",
    ],
    [
      "Real-world utility with receipts",
      "Earning or operating experiments should use redacted receipts, source labels, and methodology notes; past receipts do not imply future income.",
    ],
    [
      "Visual evidence pipeline",
      "Diagrams, screenshots, and GIFs must pass redaction review before publication and must label mock, local, delayed, TestNet, or verified sources.",
    ],
  ];
  return `
    <section class="cockpit-card span-3 pnet-content-system-card">
      <div class="panel-head">
        <h2>PNET Content System</h2>
        <span>No hype</span>
      </div>
      <p class="deck-note">Use this copy direction for tokenomics, contribution, real-world utility, and transparency pages. Publishing still requires exact wording approval.</p>
      <div class="pnet-content-grid">
        ${cards
          .map(
            ([title, detail]) => `
          <article>
            <strong>${escapeHtml(title)}</strong>
            <p>${escapeHtml(detail)}</p>
          </article>`
          )
          .join("")}
      </div>
      <div class="utility-status-line wait"><span></span><strong>No financial advice, no guaranteed earnings, no CEX/listing claim, no production-readiness claim.</strong></div>
    </section>`;
}

function CommunityGrowthDashboard() {
  const session = currentSession();
  const data = state.communityGrowth;
  const connected = session.role !== "guest";
  const disabled = connected ? "" : "disabled";
  const leaderboard = data?.leaderboard || [];
  const onboarding = data?.onboardingSteps || [];
  const reputation = data?.reputation || {};
  return `
    <section class="cockpit-card span-3 community-growth-card">
      <div class="panel-head">
        <h2>Community Growth Beta</h2>
        <span>${escapeHtml(reputation.tier || "observer")}</span>
      </div>
      <p class="deck-note">Referral, leaderboard, onboarding, and reputation are based on verified contribution activity. Mining and bandwidth entries are evidence submissions only, not earnings claims.</p>
      ${
        state.communityGrowthLoading
          ? `<div class="loading-row">Loading community growth model...</div>`
          : state.communityGrowthError
          ? `<div class="verification-banner fail"><strong>Community model unavailable</strong><span>${escapeHtml(state.communityGrowthError)}</span></div>`
          : ""
      }
      <div class="community-growth-grid">
        <article>
          <h3>Referral receipt</h3>
          <p>Share the local-review code after public wording is approved. Referral receipts require review before recognition.</p>
          <strong>${escapeHtml(data?.referral?.code || "PNET-GUEST")}</strong>
          <button type="button" data-community-referral="record" ${disabled}>Record referral receipt</button>
        </article>
        <article>
          <h3>Reputation</h3>
          <p>Meaning comes from useful evidence and review activity, not token holdings or spending.</p>
          <div class="community-reputation-stack">
            <span>Score ${fmt.format(reputation.reputationScore || 0)}</span>
            <span>${escapeHtml((reputation.badges || ["Observer"]).join(" / "))}</span>
            <span>${fmt.format(reputation.verifiedEvidenceCount || 0)} evidence receipts</span>
          </div>
        </article>
        <article>
          <h3>Evidence submissions</h3>
          <p>Submit redacted operating receipts or verification reports for manual review. No income projection is created.</p>
          <div class="community-evidence-actions">
            <button type="button" data-contribution-submit="mining_evidence" ${disabled}>Mining evidence</button>
            <button type="button" data-contribution-submit="bandwidth_evidence" ${disabled}>Bandwidth evidence</button>
            <button type="button" data-contribution-submit="verification_report" ${disabled}>Verification report</button>
          </div>
        </article>
      </div>
      <div class="onboarding-strip">
        ${onboarding
          .map(
            (item, index) => `
          <div>
            <span>${index + 1}</span>
            <strong>${escapeHtml(item.label)}</strong>
            <p>${escapeHtml(item.detail)}</p>
          </div>`
          )
          .join("")}
      </div>
      <div class="leaderboard-panel">
        <div class="panel-head mini">
          <h3>Contributor leaderboard</h3>
          <span>local-review</span>
        </div>
        ${leaderboard
          .slice(0, 5)
          .map(
            (item, index) => `
          <div class="leaderboard-row">
            <span>${index + 1}</span>
            <strong>${escapeHtml(item.displayName || shortAddress(item.wallet))}</strong>
            <em>${escapeHtml(item.category || "community")}</em>
            <b>${fmt.format(item.reputationScore || 0)}</b>
          </div>`
          )
          .join("")}
      </div>
      <div class="utility-status-line wait"><span></span><strong>Leaderboard rank is not yield, not income, not governance power, and not a token reward.</strong></div>
    </section>`;
}

function TransparencyDashboard() {
  const data = state.transparencySystem || {};
  const proofs = data.proofMatrix || [];
  const ledger = data.publicLedger || {};
  const entries = ledger.entries || [];
  const summary = ledger.summary || {};
  const snapshot = data.githubSnapshot || {};
  const audit = data.auditReadiness || {};
  const checklist = audit.checklist || [];
  const threats = audit.threatModel || [];
  const boundaries = data.safetyBoundaries || [];
  return `
    <section class="cockpit-card span-3 transparency-hero-card">
      <div>
        <p class="eyebrow">Public Proof System</p>
        <h2>Transparency Ledger</h2>
        <p>Review on-chain activity references, contribution reviews, x402 proof gates, and audit readiness without exposing secrets, full payment payloads, or fresh executable route data.</p>
      </div>
      <button type="button" data-transparency-action="refresh" ${state.transparencyLoading ? "disabled" : ""}>
        ${state.transparencyLoading ? "Refreshing..." : "Refresh transparency"}
      </button>
      ${
        state.transparencyError
          ? `<div class="verification-banner fail"><strong>Transparency unavailable</strong><span>${escapeHtml(
              state.transparencyError
            )}</span></div>`
          : ""
      }
    </section>
    <section class="cockpit-card span-3 transparency-proof-card">
      <div class="panel-head">
        <h2>Automated Proof Checks</h2>
        <span>${fmt.format(proofs.length)} checks</span>
      </div>
      <div class="transparency-proof-grid">
        ${proofs
          .map(
            (item) => `
          <article>
            ${statusChip(item.status || "waiting", item.status === "complete" || item.status === "active" ? "ok" : item.status === "blocked" ? "blocked" : "wait")}
            <strong>${escapeHtml(item.label || item.code)}</strong>
            <span>${fmt.format(item.evidenceCount || 0)} evidence item${Number(item.evidenceCount || 0) === 1 ? "" : "s"}</span>
            <p>${escapeHtml(item.detail || "Evidence detail pending.")}</p>
          </article>`
          )
          .join("")}
      </div>
    </section>
    <section class="cockpit-card span-2 transparency-ledger-card">
      <div class="panel-head">
        <h2>Public Activity Ledger</h2>
        <span>${fmt.format(entries.length)} redacted rows</span>
      </div>
      <div class="transparency-summary-grid">
        <div><span>Payments</span><strong>${fmt.format(summary.paymentVerificationCount || 0)}</strong></div>
        <div><span>Reviews</span><strong>${fmt.format(summary.reviewEventCount || 0)}</strong></div>
        <div><span>Raw txids</span><strong>${summary.rawTxidsExposed ? "exposed" : "redacted"}</strong></div>
        <div><span>Payloads</span><strong>${summary.paymentPayloadsExposed ? "exposed" : "omitted"}</strong></div>
      </div>
      <div class="transparency-ledger-list">
        ${
          entries.length
            ? entries
                .slice(0, 8)
                .map(
                  (item) => `
          <article>
            <div>
              <strong>${escapeHtml(item.label || item.kind || "ledger row")}</strong>
              <span>${escapeHtml(item.status || "recorded")} / ${escapeHtml(item.source || "stored")}</span>
            </div>
            <p>${escapeHtml(item.txReference?.hash || item.walletReference?.hash || "redacted reference")}</p>
            <em>${escapeHtml(item.createdAt || "time unavailable")}</em>
          </article>`
                )
                .join("")
            : `<p class="muted">No local proof rows yet. The ledger will fill as payment verifications, reviews, referrals, and credit receipts are recorded.</p>`
        }
      </div>
    </section>
    <section class="cockpit-card transparency-snapshot-card">
      <div class="panel-head">
        <h2>GitHub Dossier Snapshot</h2>
        <span>${escapeHtml(snapshot.generatedAt || "not generated")}</span>
      </div>
      <div class="transparency-summary-grid single">
        <div><span>Checks</span><strong>${fmt.format(snapshot.proofSummary?.checks || 0)}</strong></div>
        <div><span>Active/complete</span><strong>${fmt.format(snapshot.proofSummary?.activeOrComplete || 0)}</strong></div>
        <div><span>Blocked/limited</span><strong>${fmt.format(snapshot.proofSummary?.blockedOrLimited || 0)}</strong></div>
      </div>
      <p class="muted">${escapeHtml(snapshot.recommendedSnapshotCadence || "Generate before external demos and public claims.")}</p>
      <div class="transparency-doc-list">
        ${(snapshot.docs || []).map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
      </div>
    </section>
    <section class="cockpit-card span-3 transparency-audit-card">
      <div class="panel-head">
        <h2>Audit Readiness Package</h2>
        <span>Threat model + checklist</span>
      </div>
      <div class="transparency-audit-grid">
        <article>
          <h3>Checklist</h3>
          ${checklist
            .map(
              (item) => `
            <div class="transparency-check-row">
              ${statusChip(item.status || "waiting", item.status === "active" ? "ok" : "wait")}
              <strong>${escapeHtml(item.label)}</strong>
              <p>${escapeHtml(item.evidence)}</p>
            </div>`
            )
            .join("")}
        </article>
        <article>
          <h3>Threat Model</h3>
          ${threats
            .map(
              (item) => `
            <div class="transparency-threat-row">
              <strong>${escapeHtml(item.threat)}</strong>
              <p>${escapeHtml(item.control)}</p>
              <span>${escapeHtml(item.residualRisk)}</span>
            </div>`
            )
            .join("")}
        </article>
      </div>
      <div class="utility-status-line wait"><span></span><strong>${escapeHtml(
        boundaries[0] || "No secrets, payment payloads, Mainnet, deploy, signing, trading, or public eligibility claim is approved."
      )}</strong></div>
    </section>`;
}

function renderRoleGateNotice() {
  const view = dashboardViews[state.activeView] || dashboardViews.pulse;
  if (!view.adminOnly) return "";
  return `
    <section class="cockpit-card span-2 role-lock-card">
      <div>
        ${statusChip("ADMIN ONLY", "blocked")}
        <h2>${escapeHtml(view.label)} is locked</h2>
        <p>Connect a verified admin wallet to review this cockpit surface. Non-admin wallets can access delayed market intelligence, PNET scan credits, public receipts, and route simulations only.</p>
      </div>
      <div class="role-lock-list">
        <span>Production status: NOT LIVE READY</span>
        <span>Current safe mode: Scanner / Paper / Dry Run only</span>
        <span>Hidden from this role: platform hot-wallet controls</span>
        <span>Hidden from this role: signer and kill-switch policy</span>
        <span>Hidden from this role: live execution settings</span>
        <span>Still available: delayed routes and PNET access requests</span>
      </div>
    </section>`;
}

function renderVisibilityRules() {
  return `
    <section class="cockpit-card">
      <div class="panel-head">
        <h2>Data Visibility</h2>
        <span>Public-safe</span>
      </div>
      <div class="visibility-rules">
        <span>Delayed route intelligence</span>
        <span>No live raw opportunities</span>
        <span>No platform execution control</span>
        <span>No user deposits</span>
      </div>
    </section>`;
}

function renderUserRunHistory() {
  return `
    <section class="cockpit-card">
      <div class="panel-head">
        <h2>User Run History</h2>
        <span>PNET receipts</span>
      </div>
      <div class="queue-list">
        <div class="queue-row"><span>today</span><strong>pair scan</strong><span>12 PNET</span><span>mock-tx-01</span><span>report unlocked</span></div>
        <div class="queue-row"><span>yesterday</span><strong>route simulation</strong><span>24 PNET</span><span>mock-tx-00</span><span>paper result</span></div>
      </div>
    </section>`;
}

function utilityNumber(value, fallback = 0) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function utilityPaymentUri() {
  const data = state.utilityHub;
  const address = String(data.qrAddress || "").trim();
  if (!address) return "";
  const params = [];
  const amount = utilityNumber(data.qrAmount, 0);
  if (amount > 0) params.push(`amount=${encodeURIComponent(String(Math.round(amount * 1_000_000)))}`);
  if (data.qrNote) params.push(`note=${encodeURIComponent(String(data.qrNote).slice(0, 120))}`);
  return `algorand://${encodeURIComponent(address)}${params.length ? `?${params.join("&")}` : ""}`;
}

function utilityImpermanentLoss() {
  const data = state.utilityHub;
  const aInitial = Math.max(utilityNumber(data.tokenAInitial, 1), 0.000001);
  const bInitial = Math.max(utilityNumber(data.tokenBInitial, 1), 0.000001);
  const aCurrent = Math.max(utilityNumber(data.tokenACurrent, 1), 0.000001);
  const bCurrent = Math.max(utilityNumber(data.tokenBCurrent, 1), 0.000001);
  const investment = Math.max(utilityNumber(data.investment, 0), 0);
  const relativePriceRatio = (aCurrent / aInitial) / (bCurrent / bInitial);
  const ilRatio = 2 * Math.sqrt(relativePriceRatio) / (1 + relativePriceRatio) - 1;
  const hodl = (investment / 2) * (aCurrent / aInitial) + (investment / 2) * (bCurrent / bInitial);
  const lp = hodl * (1 + ilRatio);
  return {
    percent: ilRatio * 100,
    hodl,
    lp,
    difference: lp - hodl,
  };
}

function renderUtilityNodeStatus() {
  const data = state.opsControlRoom || {};
  const connectors = connectorDisplayRecords(data.connectors || {});
  const rollup = connectorDisplayRollup(connectors);
  const algod = connectors.find((item) => item.connectorType === "algod") || unavailableConnector("algod");
  const indexer = connectors.find((item) => item.connectorType === "indexer") || unavailableConnector("indexer");
  const status = rollup.blockedReasons.length ? "blocked" : rollup.waitReasons.length ? "wait" : "ok";
  const latestRound = Math.max(Number(algod.latestRound || 0), Number(indexer.latestRound || 0));
  return `
    <section class="cockpit-card utility-card span-2">
      <div class="panel-head">
        <h2>Node Status</h2>
        <span>${escapeHtml(status === "ok" ? "Operational" : status === "wait" ? "Review" : "Blocked")}</span>
      </div>
      <p class="deck-note">Read-only connector health from AlgoPulse evidence. This does not submit transactions or prove Mainnet readiness.</p>
      <div class="utility-stat-grid">
        <div><span>Latest round</span><strong>${latestRound ? fmt.format(latestRound) : "unavailable"}</strong></div>
        <div><span>Algod</span><strong>${escapeHtml(algod.status || "unavailable")}</strong></div>
        <div><span>Indexer</span><strong>${escapeHtml(indexer.status || "unavailable")}</strong></div>
        <div><span>Source</span><strong>${escapeHtml(data.connectors?.source || "stored/mock")}</strong></div>
      </div>
      <div class="utility-status-line ${escapeHtml(status)}">
        <span></span>
        <strong>${escapeHtml(status === "ok" ? "Network telemetry usable" : status === "wait" ? "Evidence needs review" : "Connector evidence blocks readiness")}</strong>
      </div>
      <button type="button" data-utility-action="refresh-status">Refresh Status</button>
    </section>`;
}

function renderUtilityQrBuilder() {
  const data = state.utilityHub;
  const uri = utilityPaymentUri();
  return `
    <section class="cockpit-card utility-card">
      <div class="panel-head">
        <h2>QR Pay URI</h2>
        <span>Unsigned</span>
      </div>
      <p class="deck-note">Builds a copyable Algorand payment URI only. No wallet connection, signing, or submission happens here.</p>
      <div class="utility-form">
        <label>
          <span>Receiver address</span>
          <input type="text" data-utility-input="qrAddress" value="${escapeHtml(data.qrAddress)}" placeholder="Algorand address" />
        </label>
        <label>
          <span>Amount (ALGO)</span>
          <input type="number" min="0" step="0.000001" data-utility-input="qrAmount" value="${escapeHtml(data.qrAmount)}" />
        </label>
        <label>
          <span>Note</span>
          <input type="text" data-utility-input="qrNote" value="${escapeHtml(data.qrNote)}" />
        </label>
      </div>
      <div id="utility-payment-uri" class="utility-output ${uri ? "" : "empty"}">
        <span>Payment URI</span>
        <strong>${uri ? escapeHtml(uri) : "Enter a receiver address to generate a URI."}</strong>
      </div>
      <button id="utility-copy-uri" type="button" data-utility-action="copy-payment-uri" ${uri ? "" : "disabled"}>
        ${state.utilityHub.copied ? "Copied" : "Copy URI"}
      </button>
    </section>`;
}

function renderUtilityIlCalculator() {
  const data = state.utilityHub;
  const result = utilityImpermanentLoss();
  const tone = result.percent < -1 ? "blocked" : result.percent < -0.1 ? "wait" : "ok";
  return `
    <section class="cockpit-card utility-card">
      <div class="panel-head">
        <h2>IL Visualizer</h2>
        <span>Calculator</span>
      </div>
      <p class="deck-note">Estimates impermanent loss versus holding. This is educational math, not trading advice.</p>
      <div class="utility-form two-col">
        <label><span>Token A initial</span><input type="number" min="0.000001" step="0.000001" data-utility-input="tokenAInitial" value="${escapeHtml(data.tokenAInitial)}" /></label>
        <label><span>Token B initial</span><input type="number" min="0.000001" step="0.000001" data-utility-input="tokenBInitial" value="${escapeHtml(data.tokenBInitial)}" /></label>
        <label><span>Token A current</span><input type="number" min="0.000001" step="0.000001" data-utility-input="tokenACurrent" value="${escapeHtml(data.tokenACurrent)}" /></label>
        <label><span>Token B current</span><input type="number" min="0.000001" step="0.000001" data-utility-input="tokenBCurrent" value="${escapeHtml(data.tokenBCurrent)}" /></label>
        <label class="wide"><span>Total position value</span><input type="number" min="0" step="1" data-utility-input="investment" value="${escapeHtml(data.investment)}" /></label>
      </div>
      <div class="utility-stat-grid">
        <div><span>IL estimate</span><strong id="utility-il-percent" class="${escapeHtml(tone)}">${result.percent.toFixed(2)}%</strong></div>
        <div><span>HODL value</span><strong id="utility-il-hodl">$${result.hodl.toFixed(2)}</strong></div>
        <div><span>LP value</span><strong id="utility-il-lp">$${result.lp.toFixed(2)}</strong></div>
        <div><span>Difference</span><strong id="utility-il-difference" class="${escapeHtml(tone)}">$${result.difference.toFixed(2)}</strong></div>
      </div>
    </section>`;
}

function refreshUtilityDynamicPanels() {
  const uri = utilityPaymentUri();
  const uriBox = document.getElementById("utility-payment-uri");
  const copyButton = document.getElementById("utility-copy-uri");
  if (uriBox) {
    uriBox.classList.toggle("empty", !uri);
    const value = uriBox.querySelector("strong");
    if (value) value.textContent = uri || "Enter a receiver address to generate a URI.";
  }
  if (copyButton) {
    copyButton.disabled = !uri;
    copyButton.textContent = state.utilityHub.copied ? "Copied" : "Copy URI";
  }

  const result = utilityImpermanentLoss();
  const tone = result.percent < -1 ? "blocked" : result.percent < -0.1 ? "wait" : "ok";
  const percent = document.getElementById("utility-il-percent");
  const hodl = document.getElementById("utility-il-hodl");
  const lp = document.getElementById("utility-il-lp");
  const difference = document.getElementById("utility-il-difference");
  if (percent) {
    percent.textContent = `${result.percent.toFixed(2)}%`;
    percent.className = tone;
  }
  if (hodl) hodl.textContent = `$${result.hodl.toFixed(2)}`;
  if (lp) lp.textContent = `$${result.lp.toFixed(2)}`;
  if (difference) {
    difference.textContent = `$${result.difference.toFixed(2)}`;
    difference.className = tone;
  }
}

function renderUtilityRiskRadar() {
  const rows = [
    ["Wallet cleaner", "blocked", "Requires opt-out transactions and wallet signing; not implemented in AlgoPulse."],
    ["Quick opt-in", "blocked", "Requires asset opt-in transactions; keep outside this safe dashboard."],
    ["MultiSender", "blocked", "Batch payments would submit transactions and need a separate audited tool."],
    ["Risk radar", "ok", "Use existing route, redaction, signer, and production-readiness checks."],
    ["NFD scout", "wait", "Useful later as read-only lookup; avoid adding an external dependency in this PR."],
  ];
  return `
    <section class="cockpit-card utility-card span-3">
      <div class="panel-head">
        <h2>Tool Boundary Radar</h2>
        <span>Safe imports only</span>
      </div>
      <div class="utility-tool-grid">
        ${rows
          .map(
            ([label, status, detail]) => `
          <article class="utility-tool ${escapeHtml(status)}">
            ${statusChip(status.toUpperCase(), status)}
            <strong>${escapeHtml(label)}</strong>
            <p>${escapeHtml(detail)}</p>
          </article>`
          )
          .join("")}
      </div>
    </section>`;
}

function renderUtilityHub() {
  return `
    <section class="cockpit-card span-3 user-header utility-header">
      <div>
        <p class="eyebrow">ProfitNet Utility Hub</p>
        <h2>Safe Algorand tools</h2>
        <p>Borrowed from the standalone utility concept, narrowed for this repo: read-only status, calculators, URI generation, and explicit transaction boundaries.</p>
      </div>
      ${renderMetricCards([
        ["Mode", "No signing", "ok"],
        ["Route", "Public tools", "ok"],
        ["Mainnet", "Not activated", "warn"],
        ["Wallet", "Not connected", "ok"],
        ["Live execution", "Blocked", "danger"],
      ])}
    </section>
    ${renderUtilityNodeStatus()}
    ${renderUtilityQrBuilder()}
    ${renderUtilityIlCalculator()}
    ${renderUtilityRiskRadar()}`;
}

function TestnetReadinessPanel() {
  if (state.testnetReadinessError) {
    return `
      <section class="cockpit-card span-3 testnet-readiness-card blocked">
        <div class="panel-head"><h2>Phase 3 / TestNet Access</h2><span>Unavailable</span></div>
        <p class="deck-note">Backend readiness evidence could not be loaded: ${escapeHtml(state.testnetReadinessError)}</p>
      </section>`;
  }

  const data = state.testnetReadiness;
  if (!data) {
    return `
      <section class="cockpit-card span-3 testnet-readiness-card wait">
        <div class="panel-head"><h2>Phase 3 / TestNet Access</h2><span>Loading</span></div>
        <p class="deck-note">Checking network, live algod/Indexer health, connectors, wallet boundary, and execution locks.</p>
      </section>`;
  }

  const accessReady = Boolean(data.walletConnectionReady);
  const tone = accessReady ? "ok" : data.readOnlyStatus === "blocked" || data.walletAccessStatus === "blocked" ? "blocked" : "wait";
  const priorityKeys = new Set([
    "network",
    "execution_boundary",
    "public_delay",
    "asset_configuration",
    "connectors",
    "wallet_boundary",
    "algod_live",
    "indexer_live",
  ]);
  const checks = (data.checks || []).filter((item) => priorityKeys.has(item.key));
  const activeReasons = [...(data.blockedReasons || []), ...(data.waitReasons || [])].slice(0, 3);
  const health = data.networkHealth || state.networkHealth || {};
  const algod = health.algod || {};
  const indexer = health.indexer || {};
  const live = state.walletConnection || {};
  const connectorNote = (data.checks || []).find((item) => item.key === "connectors");
  return `
    <section class="cockpit-card span-3 testnet-readiness-card ${escapeHtml(tone)}">
      <div class="testnet-readiness-head">
        <div>
          <p class="eyebrow">Phase 3 · TestNet Access</p>
          <h2>TestNet Access &amp; Readiness</h2>
          <p>Backend is the network authority (${escapeHtml(data.network || APP_CONFIG.NETWORK || "testnet")}).
          Pera and Defly are connect-only. Signing and submission stay disarmed.
          ${data.pnetAsaConfigured ? "" : " PNET TestNet asset not configured — ALGO account reads still work."}</p>
        </div>
        <div class="testnet-readiness-score ${escapeHtml(tone)}">
          <span>Access evidence</span>
          <strong>${fmt.format(data.passedCount || 0)}/${fmt.format(data.totalCount || 0)}</strong>
          <em>${escapeHtml(data.status || data.walletAccessStatus || data.readOnlyStatus || "in_progress")}</em>
        </div>
      </div>
      <div class="testnet-health-row">
        <article class="${algod.healthy ? "ok" : "blocked"}">
          <span>algod</span>
          <strong>${escapeHtml(algod.status || (algod.healthy ? "ok" : "down"))}</strong>
          <p>round ${escapeHtml(String(algod.lastRound ?? "—"))} · ${escapeHtml(String(algod.latencyMs ?? "—"))} ms</p>
        </article>
        <article class="${indexer.healthy ? "ok" : "blocked"}">
          <span>Indexer</span>
          <strong>${escapeHtml(indexer.status || (indexer.healthy ? "ok" : "down"))}</strong>
          <p>round ${escapeHtml(String(indexer.lastRound ?? "—"))} · ${escapeHtml(String(indexer.latencyMs ?? "—"))} ms</p>
        </article>
        <article class="${connectorNote?.status === "pass" ? "ok" : "wait"}">
          <span>DEX connectors</span>
          <strong>${escapeHtml(connectorNote?.status || "wait")}</strong>
          <p>${escapeHtml(gateLabel(connectorNote?.reason || "connector_state_unknown"))}</p>
        </article>
        <article class="${accessReady ? "ok" : "wait"}">
          <span>Wallet access</span>
          <strong>${escapeHtml(accessReady ? "connect-only ready" : data.walletStatus || "wait")}</strong>
          <p>${escapeHtml((data.supportedWallets || ["pera", "defly"]).join(" · "))} · ${escapeHtml(live.status || "disconnected")}</p>
        </article>
      </div>
      <div class="testnet-check-grid">
        ${checks
          .map((item) => {
            const itemTone = item.status === "pass" ? "ok" : item.status === "blocked" ? "blocked" : "wait";
            return `
              <article class="${escapeHtml(itemTone)}">
                ${statusChip(item.status, itemTone)}
                <strong>${escapeHtml(item.label)}</strong>
                <p>${escapeHtml(gateLabel(item.reason))}</p>
              </article>`;
          })
          .join("")}
      </div>
      <div class="testnet-next-row">
        <div>
          <span>Next safe action</span>
          <strong>${escapeHtml(data.nextAction || "Connect Pera or Defly on TestNet.")}</strong>
        </div>
        <div>
          <span>Current blockers</span>
          <strong>${escapeHtml(activeReasons.length ? activeReasons.map(gateLabel).join(" / ") : accessReady ? "Wallet connect-only ready" : "Review remaining checks")}</strong>
        </div>
        <div class="testnet-lock-badge">
          <span>Execution</span>
          <strong>Locked</strong>
        </div>
      </div>
    </section>`;
}

function Phase2CompletionPanel() {
  const items = [
    ["PNET-first default routes", "Default route view starts with PNET surfaces."],
    ["Other ALGO behind click", "ALGO-only routes require intentional filter click."],
    ["Real route filters", "Venue, status, and min-net controls filter visible rows."],
    ["Route inspection", "Inspect opens route evidence and public-safe detail."],
    ["Public-safe JSON", "JSON snapshots are explicitly non-executable."],
    ["Paper simulation", "T0, T+5s, and T+30s evidence is visible per route."],
    ["Recent swaps watch", "PNET swap/pool activity is source-labeled."],
    ["Role-gated UX", "Admin controls stay hidden from guest/user mode."],
    ["Execution lock clarity", "Dry-run, queue, signer, contract, and live execution stay blocked."],
  ];
  return `
    <section class="cockpit-card span-3 phase2-completion-card">
      <div class="phase2-completion-head">
        <div>
          <p class="eyebrow">Phase 2 Completion</p>
          <h2>User Experience Layer</h2>
          <p>Frontend interaction is complete enough for review: users can navigate, filter, inspect, simulate, and understand exactly what remains locked.</p>
        </div>
        <div class="phase2-score">
          <span>UX gate</span>
          <strong>${items.length}/${items.length}</strong>
          <em>Ready for review</em>
        </div>
      </div>
      <div class="phase2-check-grid">
        ${items
          .map(
            ([title, detail]) => `
          <article>
            ${statusChip("done", "ok")}
            <strong>${escapeHtml(title)}</strong>
            <p>${escapeHtml(detail)}</p>
          </article>`
          )
          .join("")}
      </div>
      <div class="utility-status-line wait"><span></span><strong>Next phase is TestNet readiness: Pera/Defly connect-only, TestNet config, payment/credit spec, and human review before any contract or transaction flow.</strong></div>
    </section>`;
}

function renderUserPortal() {
  const session = currentSession();
  const view = state.activeView;
  const lockNotice = renderRoleGateNotice();
  const notice = state.operatorNotice
    ? `
    <section class="cockpit-card span-3 notice-card">
      <span>${session.role === "admin" ? "Operator Notice" : "Access Notice"}</span>
      <strong>${escapeHtml(state.operatorNotice)}</strong>
    </section>`
    : "";
  const accessPanel = `
    <section class="cockpit-card">
      <div class="panel-head">
        <h2>PNET Access Gate</h2>
        <span>Wallet-gated</span>
      </div>
      ${renderPnetAccessGate()}
    </section>`;
  let content = `${TestnetReadinessPanel()}${ArbBotWatchPanel()}${renderPublicJourneyPanel()}${renderRouteConsole({ admin: false, compact: true })}${accessPanel}${renderUserRunHistory()}`;
  if (view === "routes") content = `${TestnetReadinessPanel()}${renderRouteConsole({ admin: false })}${renderVisibilityRules()}`;
  if (view === "research") content = ResearchArchive();
  if (view === "utility") content = renderUtilityHub();
  if (view === "transparency") content = TransparencyDashboard();
  if (view === "access")
    content = `${accessPanel}${ContributionProtocolDashboard()}${CommunityGrowthDashboard()}${PnetContentSystemPanel()}${renderPnetNoGateBuilds()}${renderPnetLiquidityEducation()}${renderUserRunHistory()}`;
  if (view === "receipts") content = `${renderReceiptFeed()}${renderUserRunHistory()}`;
  if (dashboardViews[view]?.adminOnly) content = `${lockNotice}${accessPanel}${renderVisibilityRules()}`;

  return `
    <section class="cockpit-card span-3 user-header">
      <div>
        <p class="eyebrow">${session.role === "guest" ? "Public Guest" : "Connected User"}</p>
        <h2>PNET Arbitrage Watch</h2>
        <p>AlgoPulse watches Algorand pools for PNET price gaps, shows delayed candidates, and keeps trading/signing locked behind human gates.</p>
      </div>
      ${renderMetricCards([
        ["Mode", "Scanner watch", "ok"],
        ["Target", "PNET", "ok"],
        ["Wallet", shortAddress(session.address)],
        ["Live trading", "Blocked", "warn"],
        ["Access tier", session.role === "guest" ? "Public delayed" : "PNET user"],
      ])}
    </section>
    ${notice}
    ${content}`;
}

function renderAdminDashboard() {
  const view = state.activeView;
  if (view === "routes") return `${TestnetReadinessPanel()}${renderRouteConsole({ admin: true })}`;
  if (view === "research") return ResearchArchive();
  if (view === "utility") return renderUtilityHub();
  if (view === "transparency") return TransparencyDashboard();
  if (view === "pipeline") return ProductionControlRoom();
  if (view === "heatmap") return MarketPulseHeatmap();
  if (view === "readiness") return ProductionReadinessPage();
  if (view === "replay") return ReplayLab();
  if (view === "forensics") return RouteForensicsPanel();
  if (view === "confidence") return ConfidenceAnalysisPanel();
  if (view === "decay") return OpportunityHalfLifeDashboard();
  if (view === "failure") return FailureLab();
  if (view === "provenance") return DataProvenanceViewer();
  if (view === "evidence") return ProductionEvidenceSystem();
  if (view === "validation") return ProductValidationDashboard();
  if (view === "bot") return `${renderBotControlPanel()}${renderRiskPolicyPanel()}${renderSignerPolicyCatalog()}${renderExecutionQueue()}`;
  if (view === "access") return `${renderPnetAccessGate()}${ContributionProtocolDashboard()}${CommunityGrowthDashboard()}${PnetContentSystemPanel()}${renderPnetNoGateBuilds()}${renderPnetLiquidityEducation()}${renderUserRunHistory()}`;
  if (view === "receipts") return `${renderReceiptFeed()}${renderExecutionQueue()}`;
  if (view === "logs") return `${renderLogPanel()}${renderPreflightChecklist()}`;
  return `${TestnetReadinessPanel()}${renderAdminCommandHeader()}${renderPreflightChecklist()}${renderBotControlPanel()}${renderRouteConsole({ admin: true, compact: true })}`;
}

function renderRoleDashboard() {
  const target = document.getElementById("role-dashboard");
  if (!target) return;
  const session = currentSession();
  const adminReady = session.role === "admin" && session.network === APP_CONFIG.NETWORK;
  target.className = `control-deck ${session.role}`;
  target.innerHTML = adminReady ? renderAdminDashboard() : renderUserPortal();
}

function renderPnetFeeModalBody(action, quote, session) {
  const provider = currentWalletProvider();
  const feeLabel = quote ? `${fmt.format(Number(quote.feeAmount || action.fee))} PNET` : `${fmt.format(action.fee)} PNET`;
  const receiver = quote?.receiver || APP_CONFIG.PLATFORM_FEE_RECEIVER;
  const appId = quote?.feeAppId || APP_CONFIG.PLATFORM_APP_ID;
  const note = quote?.note || "quote pending";
  const intent = quote?.paymentIntent || {};
  const accessChecks = quote?.accessCheck?.checks || [];
  document.getElementById("pnet-fee-body").innerHTML = `
    <div class="fee-summary">
      <div><span>Action</span><strong>${escapeHtml(action.label)}</strong></div>
      <div><span>PNET fee</span><strong>${escapeHtml(feeLabel)}</strong></div>
      <div><span>Recipient / app</span><strong>${escapeHtml(receiver)} / ${escapeHtml(appId)}</strong></div>
      <div><span>Network</span><strong>${escapeHtml(quote?.network || APP_CONFIG.NETWORK)}</strong></div>
      <div><span>Wallet</span><strong>${escapeHtml(shortAddress(session.address))}</strong></div>
      <div><span>Receives</span><strong>${escapeHtml(action.receives)}</strong></div>
      <div><span>Quote ID</span><strong>${escapeHtml(quote?.feeQuoteId || "requesting")}</strong></div>
      <div><span>Payment note</span><strong>${escapeHtml(note)}</strong></div>
    </div>
    <div class="payment-flow">
      <div class="flow-step done"><span>1</span><strong>Backend access check</strong><em>${accessChecks.filter((check) => check.ok).length}/${accessChecks.length || 4} checks passed</em></div>
      <div class="flow-step done"><span>2</span><strong>Fee quote issued</strong><em>${escapeHtml(quote?.verificationMode || "pending")}</em></div>
      <div class="flow-step wait"><span>3</span><strong>Frontend builds PNET transfer</strong><em>ASA ${escapeHtml(intent.assetId || APP_CONFIG.PNET_ASA_ID)} / ${escapeHtml(intent.amountAtomic || "0")} atomic</em></div>
      <div class="flow-step wait"><span>4</span><strong>User reviews in ${escapeHtml(provider.label)}</strong><em>user wallet only / review mode</em></div>
      <div class="flow-step wait"><span>5</span><strong>Backend verifies txid</strong><em>receipt unlocks delayed report</em></div>
    </div>
    <div class="intent-box">
      <span>Payment intent</span>
      <strong>${escapeHtml(intent.transactionType || "asset_transfer")} / ${escapeHtml(intent.signer || provider.intentSigner)}</strong>
      <p>${escapeHtml(quote?.nextStep || "Submit a user-signed PNET payment txid for backend verification.")}</p>
    </div>
    <p class="modal-disclaimer">This is a market-data or route-intelligence fee. It does not guarantee profit, does not deposit funds into the bot, and does not grant control over platform execution.</p>`;
}

async function openPnetFeeModal(actionKey) {
  const action = pnetActions[actionKey];
  if (!action) return;
  const session = currentSession();
  state.activeFeeAction = actionKey;
  state.activeFeeQuote = null;
  setWalletPreset("paymentPending");
  document.getElementById("pnet-fee-title").textContent = action.label;
  document.getElementById("pnet-fee-body").innerHTML = `<p class="muted">Checking wallet, network, PNET opt-in, and balance...</p>`;
  showModal("pnet-fee-modal", true);
  try {
    const accessCheck = await fetchApiData("/api/user/pnet/access-check", {
      method: "POST",
      headers: apiHeaders({ json: true }),
      body: JSON.stringify({
        wallet: session.address,
        network: session.network,
        action: actionKey,
      }),
    });
    if (!accessCheck.ok) {
      document.getElementById("pnet-fee-body").innerHTML = `
        <div class="verification-banner fail">
          <strong>Access check failed</strong>
          ${accessCheck.checks
            .map((check) => `<span>${check.ok ? "OK" : "WAIT"}: ${escapeHtml(check.label)} - ${escapeHtml(check.detail)}</span>`)
            .join("")}
        </div>`;
      return;
    }
    document.getElementById("pnet-fee-body").innerHTML = `<p class="muted">Access check passed. Requesting backend fee quote...</p>`;
    const quote = await fetchApiData("/api/user/pnet/fee-quote", {
      method: "POST",
      headers: apiHeaders({ json: true }),
      body: JSON.stringify({
        wallet: session.address,
        network: session.network,
        action: actionKey,
        pair: state.latestOpportunities[0]?.route_hash || null,
      }),
    });
    state.activeFeeQuote = quote;
    renderPnetFeeModalBody(action, quote, session);
  } catch (error) {
    document.getElementById("pnet-fee-body").innerHTML = `
      <div class="verification-banner fail">
        <strong>Quote rejected</strong>
        <span>${escapeHtml(error.message)}</span>
        <span>No credit was created.</span>
      </div>`;
  }
}

function closePnetFeeModal() {
  showModal("pnet-fee-modal", false);
  state.activeFeeQuote = null;
  if (state.walletPreset === "paymentPending") setWalletPreset("feeReady");
}

async function confirmPnetFee() {
  const quote = state.activeFeeQuote;
  if (!quote) {
    state.operatorNotice = "No backend PNET fee quote is active.";
    renderRoleDashboard();
    return;
  }
  try {
    document.getElementById("pnet-fee-body").innerHTML += `<p class="muted">Review mode: confirming with a mock submitted txid. Production would use a user-wallet-submitted txid after separate review.</p>`;
    const confirmation = await fetchApiData("/api/user/pnet/fee-confirm", {
      method: "POST",
      headers: apiHeaders({ json: true }),
      body: JSON.stringify({
        wallet: quote.wallet,
        fee_quote_id: quote.feeQuoteId,
        txid: `mock-${quote.feeQuoteId}`,
        action: state.activeFeeAction,
        pair: quote.pair,
      }),
    });
    showModal("pnet-fee-modal", false);
    state.activeFeeQuote = null;
    setWalletPreset("paymentConfirmed");
    state.operatorNotice = confirmation.message;
  } catch (error) {
    state.operatorNotice = `PNET confirmation rejected: ${error.message}`;
  }
  renderRoleDashboard();
}

function listValue(value) {
  if (Array.isArray(value)) return value.filter((item) => item !== null && item !== undefined);
  if (value === null || value === undefined || value === "") return [];
  return [value];
}

function listLabel(value, fallback = "not public") {
  const items = listValue(value);
  return items.length ? items.join(" / ") : fallback;
}

function recentSwapRouteRecord(swap) {
  const fromAsset = swap.fromAsset || String(swap.pair || "").split("/")[0] || "asset";
  const toAsset = swap.toAsset || String(swap.pair || "").split("/")[1] || "asset";
  return {
    routeHash: swap.routeHash || swap.id || "recent-pnet-swap",
    pair: swap.pair || `${fromAsset}/${toAsset}`,
    path: [fromAsset, toAsset],
    venues: [swap.sourceLabel || "recent PNET swap feed"],
    poolIds: [],
    appIds: [],
    assetIds: [],
    inputAmount: Number(swap.inputAmount || 0),
    expectedOutput: Number(swap.expectedOutput || 0),
    networkFees: 0,
    dexFees: 0,
    safetyBuffer: 0,
    netProfit: 0,
    profitBps: 0,
    priceImpactBps: 0,
    confidenceScore: 0,
    quoteAgeSeconds: 0,
    status: swap.sample ? "example" : "observed",
    source: swap.source || "live",
    skipReason: swap.sample ? "sample_swap" : "recent_swap_observation",
    block: swap.block || null,
    publicSafe: true,
  };
}

function routeDetailRecords() {
  const routes = routeConsoleData();
  const pnetRows = pnetWatchlistRows();
  const swaps = recentPnetSwapRows([...routes, ...pnetRows]).map(recentSwapRouteRecord);
  return [...routes, ...pnetRows, ...swaps];
}

function routeDetailRecordForHash(routeHash) {
  return routeDetailRecords().find((item) => String(item.routeHash) === String(routeHash));
}

function publicRouteSnapshot(route) {
  return {
    routeHash: route.routeHash,
    pair: route.pair,
    path: listValue(route.path),
    venues: listValue(route.venues),
    source: route.source || "unavailable",
    status: route.status || "review",
    inputAmount: Number(route.inputAmount || 0),
    expectedOutput: Number(route.expectedOutput || 0),
    netProfit: Number(route.netProfit || 0),
    profitBps: Number(route.profitBps || 0),
    priceImpactBps: Number(route.priceImpactBps || 0),
    confidenceScore: Number(route.confidenceScore || 0),
    rejectionReason: route.skipReason || null,
    publicSafe: true,
    executable: false,
    redaction: "No raw executable route JSON, signer state, hot-wallet data, signed transactions, or submission payloads.",
  };
}

function routePaperSimulation(route) {
  const quoteAgeSeconds = Number(route.quoteAgeSeconds || 0);
  const priceImpactBps = Number(route.priceImpactBps || 0);
  const confidenceScore = Math.max(0, Math.min(1, Number(route.confidenceScore || 0)));
  const status = String(route.status || "review");
  const routeIsObservation = ["watch", "observed", "example"].includes(status) || route.skipReason === "listed_without_arb";
  const expectedProfit = routeIsObservation ? 0 : Number(route.netProfit || route.grossProfit || 0);
  const expectedOutput = Number(route.expectedOutput || 0);
  const stale = quoteAgeSeconds > 5 || route.skipReason === "quote_stale";
  const impactDrag = Math.max(0, priceImpactBps) / 10000;
  const confidenceDrag = (1 - confidenceScore) * 0.08;
  const ageDrag = Math.max(0, quoteAgeSeconds - 2) * 0.015;
  const baseDecay = Math.max(0.0001, Math.abs(expectedProfit) * (0.08 + impactDrag + confidenceDrag + ageDrag));
  const quoteDecay5s = Number((baseDecay * (stale ? 1.8 : 0.65)).toFixed(6));
  const quoteDecay30s = Number((baseDecay * (stale ? 4.4 : 2.2)).toFixed(6));
  const simulatedProfit5s = Number((expectedProfit - quoteDecay5s).toFixed(6));
  const simulatedProfit30s = Number((expectedProfit - quoteDecay30s).toFixed(6));
  const simulatedOutput5s = Number(Math.max(0, expectedOutput - quoteDecay5s).toFixed(6));
  const simulatedOutput30s = Number(Math.max(0, expectedOutput - quoteDecay30s).toFixed(6));
  let verdict = "would_skip";
  let reason = route.skipReason || "below_minimum_evidence";
  if (routeIsObservation) {
    verdict = "would_skip";
    reason = route.skipReason || "observation_only";
  } else if (stale) {
    verdict = "stale";
    reason = "quote_stale";
  } else if (simulatedProfit30s > 0 && confidenceScore >= 0.6 && priceImpactBps <= 50) {
    verdict = "would_execute";
    reason = "paper_positive_after_30s";
  } else if (status === "rejected") {
    verdict = "unsafe";
    reason = route.skipReason || "risk_rejected";
  }
  return {
    routeHash: route.routeHash,
    pair: route.pair,
    source: route.source || "unavailable",
    inputAmount: Number(route.inputAmount || 0),
    expectedOutput,
    expectedProfit,
    simulatedOutput5s,
    simulatedOutput30s,
    simulatedProfit5s,
    simulatedProfit30s,
    quoteDecay5s,
    quoteDecay30s,
    priceImpactBps,
    confidenceScore,
    quoteAgeSeconds,
    wouldExecute: verdict === "would_execute",
    verdict,
    reason,
    publicSafe: true,
    simulationOnly: true,
    executionLocked: true,
  };
}

function paperSimulationTone(verdict) {
  if (verdict === "would_execute") return "ok";
  if (verdict === "stale" || verdict === "unsafe") return "blocked";
  return "wait";
}

async function copyTextToClipboard(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return true;
  }
  return false;
}

function openRouteJsonSnapshot(routeHash) {
  const route = routeDetailRecordForHash(routeHash);
  document.getElementById("route-detail-title").textContent = routeHash || "Route snapshot";
  document.getElementById("route-detail-body").innerHTML = route
    ? `
    <p class="deck-note">Public-safe route snapshot only. This is not an executable route payload and cannot be signed or submitted.</p>
    <pre class="json-preview">${escapeHtml(JSON.stringify(publicRouteSnapshot(route), null, 2))}</pre>
    <div class="modal-actions">
      <button type="button" data-route-action="inspect" data-route-hash="${escapeHtml(route.routeHash)}">Back to detail</button>
      <button type="button" data-route-action="copy" data-route-hash="${escapeHtml(route.routeHash)}">Copy route hash</button>
    </div>`
    : `<p class="deck-note">This route is not available in the current delayed/public-safe route cache.</p>`;
  showModal("route-detail-modal", true);
}

function openPaperSimulationModal(routeHash) {
  const route = routeDetailRecordForHash(routeHash);
  document.getElementById("route-detail-title").textContent = routeHash || "Paper simulation";
  if (!route) {
    document.getElementById("route-detail-body").innerHTML = `
      <p class="deck-note">Paper simulation unavailable because this route is not present in the current delayed/public-safe cache.</p>`;
    showModal("route-detail-modal", true);
    return;
  }
  const simulation = routePaperSimulation(route);
  const tone = paperSimulationTone(simulation.verdict);
  document.getElementById("route-detail-body").innerHTML = `
    <div class="paper-simulation-panel ${escapeHtml(tone)}">
      <div class="paper-simulation-head">
        <div>
          <p class="eyebrow">Paper Simulation</p>
          <h3>${escapeHtml(simulation.pair || "route")}</h3>
          <p>Simulation-only evidence for whether a delayed route would still look usable after quote decay. No smart contract, wallet signature, signer, hot-wallet, or transaction submission is touched.</p>
        </div>
        <div>
          ${statusChip(simulation.verdict.replaceAll("_", " "), tone)}
          ${SourceBadge(simulation.source || "unavailable")}
        </div>
      </div>
      <div class="paper-sim-timeline">
        <article>
          <span>T0 detected</span>
          <strong>${fmt.format(simulation.expectedOutput)}</strong>
          <em>Expected profit ${fmt.format(simulation.expectedProfit)}</em>
        </article>
        <article>
          <span>T+5s recheck</span>
          <strong>${fmt.format(simulation.simulatedOutput5s)}</strong>
          <em>Decay ${fmt.format(simulation.quoteDecay5s)} / profit ${fmt.format(simulation.simulatedProfit5s)}</em>
        </article>
        <article>
          <span>T+30s recheck</span>
          <strong>${fmt.format(simulation.simulatedOutput30s)}</strong>
          <em>Decay ${fmt.format(simulation.quoteDecay30s)} / profit ${fmt.format(simulation.simulatedProfit30s)}</em>
        </article>
      </div>
      <div class="policy-grid">
        <div><span>Input amount</span><strong>${fmt.format(simulation.inputAmount)}</strong></div>
        <div><span>Quote age</span><strong>${fmt.format(simulation.quoteAgeSeconds)}s</strong></div>
        <div><span>Price impact</span><strong>${fmt.format(simulation.priceImpactBps)} bps</strong></div>
        <div><span>Confidence</span><strong>${fmt.format(simulation.confidenceScore * 100)}%</strong></div>
        <div><span>Would execute</span><strong>${simulation.wouldExecute ? "paper yes" : "paper no"}</strong></div>
        <div><span>Reason</span><strong>${escapeHtml(gateLabel(simulation.reason))}</strong></div>
      </div>
      <div class="utility-status-line blocked"><span></span><strong>Execution remains locked. This output is not an executable route, signed transaction, submission payload, or contract call.</strong></div>
    </div>
    <div class="modal-actions">
      <button type="button" data-route-action="inspect" data-route-hash="${escapeHtml(route.routeHash)}">Back to detail</button>
      <button type="button" data-route-action="copy" data-route-hash="${escapeHtml(route.routeHash)}">Copy route hash</button>
      <button type="button" data-route-action="json" data-route-hash="${escapeHtml(route.routeHash)}">View JSON</button>
    </div>`;
  showModal("route-detail-modal", true);
}

function openRouteDetailModal(routeHash) {
  const route = routeDetailRecordForHash(routeHash);
  if (!route) {
    document.getElementById("route-detail-title").textContent = routeHash || "Route unavailable";
    document.getElementById("route-detail-body").innerHTML = `
      <p class="deck-note">This row is not available in the current delayed/public-safe cache. Try refreshing the scanner or opening a listed route.</p>`;
    showModal("route-detail-modal", true);
    return;
  }
  const path = listValue(route.path).length ? listValue(route.path) : [route.fromAsset, route.toAsset].filter(Boolean);
  document.getElementById("route-detail-title").textContent = route.routeHash;
  document.getElementById("route-detail-body").innerHTML = `
    <div class="route-detail-grid">
      <div class="route-timeline">
        ${path.map((step, index) => `<span>${index + 1}. ${escapeHtml(step)}</span>`).join("")}
      </div>
      <div class="policy-grid">
        <div><span>Pair</span><strong>${escapeHtml(route.pair)}</strong></div>
        <div><span>Venues</span><strong>${escapeHtml(listValue(route.venues).join(" -> ") || "observed feed")}</strong></div>
        <div><span>Pool IDs</span><strong>${escapeHtml(listLabel(route.poolIds))}</strong></div>
        <div><span>App IDs</span><strong>${escapeHtml(listLabel(route.appIds))}</strong></div>
        <div><span>Asset IDs</span><strong>${escapeHtml(listLabel(route.assetIds))}</strong></div>
        <div><span>Pre-trade quote</span><strong>${fmt.format(route.inputAmount)} -> ${fmt.format(route.expectedOutput)}</strong></div>
        <div><span>Fee breakdown</span><strong>${fmt.format(route.networkFees || 0)} network / ${fmt.format(route.dexFees || 0)} DEX</strong></div>
        <div><span>Safety buffer</span><strong>${fmt.format(route.safetyBuffer || 0)}</strong></div>
        <div><span>Risk status</span><strong>${escapeHtml(route.status || "review")}</strong></div>
        <div><span>Reconciliation</span><strong>${route.status === "approved" ? "pending dry-run" : "not executed"}</strong></div>
      </div>
    </div>
    <div class="modal-actions">
      <button type="button" data-route-action="copy" data-route-hash="${escapeHtml(route.routeHash)}">Copy route hash</button>
      <button type="button" data-route-action="json" data-route-hash="${escapeHtml(route.routeHash)}">View JSON</button>
      <button type="button" data-route-action="paper" data-route-hash="${escapeHtml(route.routeHash)}">Run paper simulation</button>
      <button type="button" data-route-action="dry-run" data-route-hash="${escapeHtml(route.routeHash)}" ${currentSession().role === "admin" ? "" : "disabled"}>Build dry run</button>
      <button type="button" data-route-action="queue" data-route-hash="${escapeHtml(route.routeHash)}" ${currentSession().role === "admin" && route.status === "approved" ? "" : "disabled"}>Approve for execution</button>
    </div>`;
  showModal("route-detail-modal", true);
}

function openLiveArmModal() {
  const risk = state.latestReadiness?.risk || {};
  const limits = [
    ["Max trade size", `${fmt.format(risk.max_live_trade_size || 10)} ALGO`],
    ["Daily loss limit", "20 ALGO"],
    ["Max daily trades", `${fmt.format(risk.max_daily_trades || 20)}`],
    ["Route length limit", `${fmt.format(risk.max_route_legs || 3)} swaps`],
    ["Allowed assets", "ALGO, USDC, PNET, reviewed ASAs"],
    ["Allowed app IDs", `${fmt.format(risk.allowed_app_ids_count || 0)} loaded`],
    ["Signer state", "locked by default"],
  ];
  document.getElementById("live-arm-limits").innerHTML = limits
    .map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`)
    .join("");
  showModal("live-arm-modal", true);
}

function showModal(id, visible) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.toggle("hidden", !visible);
  modal.setAttribute("aria-hidden", visible ? "false" : "true");
}

const adminActionEndpoints = {
  scan: "/api/admin/scan-now",
  "start-scanner": "/api/admin/scanner/start",
  "pause-scanner": "/api/admin/scanner/pause",
  "route-engine": "/api/admin/routes/run",
  paper: "/api/admin/paper/start",
  "dry-run": "/api/admin/dry-run/build",
  "arm-live": "/api/admin/live/arm",
  disarm: "/api/admin/live/disarm",
  kill: "/api/admin/kill-switch/trigger",
  "clear-kill": "/api/admin/kill-switch/clear",
};

function botModeNotice(mode) {
  return {
    scanner: "Bot mode set to scanner-only. This is read-only market evidence collection.",
    paper: "Bot mode set to paper trading. Candidates can be simulated, but no signing or submission is enabled.",
    "dry-run": "Bot mode set to dry-run review. Future groups must remain unsigned and policy-validated.",
    "live-micro": "Live micro mode is still locked. Arming live execution requires completed gates and human approval.",
  }[mode] || "Bot mode updated.";
}

async function runAdminAction(action) {
  const endpoint = adminActionEndpoints[action];
  if (!endpoint) return;
  if (currentSession().role !== "admin") {
    state.operatorNotice = "Admin control requires a backend-verified admin wallet session.";
    renderRoleDashboard();
    return;
  }
  state.operatorNotice = "Submitting control-plane request to backend...";
  renderRoleDashboard();
  try {
    const result = await fetchApiData(endpoint, {
      method: "POST",
      headers: apiHeaders(),
    });
    state.operatorNotice = result.message || `${result.action || action} queued by backend policy.`;
    await loadAdminPreflight({ render: false });
    await loadAdminAlertCatalog({ render: false });
    await loadAdminPolicyCatalog({ render: false });
    await loadOpsControlRoom({ render: false });
    await loadProductionReadiness({ render: false });
    await loadReplayLab({ render: false });
    await loadRouteForensics({ render: false });
    await loadConfidenceCalibration({ render: false });
    await loadOpportunityDecay({ render: false });
    await loadMarketHeatmap({ render: false });
    await loadDataProvenance({ render: false });
    await loadEvidenceSystem({ render: false });
  } catch (error) {
    state.operatorNotice = `Backend rejected ${action}: ${error.message}`;
  }
  renderRoleDashboard();
}

async function runRouteAction(action, routeHash) {
  if (action === "inspect") {
    await recordProductAction("opened_route", {
      page: "routes",
      route_hash: routeHash || null,
      evidence_source: "route_details",
    });
    openRouteDetailModal(routeHash);
    return;
  }
  if (action === "copy") {
    const copied = await copyTextToClipboard(routeHash || "");
    state.operatorNotice = copied
      ? `${routeHash || "route"} copied to clipboard.`
      : `${routeHash || "route"} is ready to copy; browser clipboard permission was unavailable.`;
    renderRoleDashboard();
    return;
  }
  if (action === "json") {
    await recordProductAction("opened_route", {
      page: "routes",
      route_hash: routeHash || null,
      evidence_source: "public_safe_route_json",
    });
    openRouteJsonSnapshot(routeHash);
    return;
  }
  if (["dry-run", "queue"].includes(action) && currentSession().role !== "admin") {
    state.operatorNotice = "That route action is admin-only. Non-admin wallets can request delayed intelligence and paper simulations.";
    renderRoleDashboard();
    return;
  }
  if (action === "dry-run") {
    await runAdminAction("dry-run");
    return;
  }
  if (action === "queue") {
    await runAdminAction("route-engine");
    return;
  }
  if (action === "paper") {
    await recordProductAction("generated_simulation", {
      page: "routes",
      route_hash: routeHash || null,
      evidence_source: "paper_simulation_modal",
    });
    state.operatorNotice = `${routeHash || "route"} paper simulation opened. This is simulation-only and cannot sign or submit.`;
    openPaperSimulationModal(routeHash);
    return;
  }
  state.operatorNotice = `${routeHash || "route"} ${action} requested in UI review mode. Backend policy must approve production actions.`;
  renderRoleDashboard();
}

async function handleRoleDashboardClick(event) {
  const button = event.target.closest("button");
  if (!button) return;
  if (button.dataset.journeyView) {
    const view = button.dataset.journeyView;
    setActiveView(view);
    await recordProductAction(productActionForView(view), {
      page: view,
      evidence_source: dashboardViews[view]?.userScope || view,
    });
    return;
  }
  if (button.dataset.researchAction === "refresh-live") {
    await recordProductAction("requested_scan", {
      page: "research",
      evidence_source: "read_only_live_api_refresh",
    });
    await refreshResearchFromLiveApi();
    return;
  }
  if (button.dataset.routeScope) {
    state.routeScope = button.dataset.routeScope;
    renderRoleDashboard();
    recordProductAction("opened_route", {
      page: state.activeView || "routes",
      route_scope: state.routeScope,
      evidence_source: "route_scope_filter",
    });
    return;
  }
  if (button.dataset.routeFilterReset) {
    state.routeFilters = { venue: "all", status: "all", minProfit: "" };
    state.operatorNotice = "Route filters reset. PNET-first route view remains active.";
    renderRoleDashboard();
    return;
  }
  if (button.dataset.botMode) {
    state.botMode = button.dataset.botMode;
    state.operatorNotice = botModeNotice(state.botMode);
    if (state.botMode === "live-micro") {
      openLiveArmModal();
    }
    renderRoleDashboard();
    return;
  }
  if (button.dataset.walletProvider) {
    state.walletProvider = walletProviders[button.dataset.walletProvider] ? button.dataset.walletProvider : "pera";
    try {
      localStorage.setItem(WALLET_PROVIDER_STORAGE_KEY, state.walletProvider);
    } catch (_e) {
      /* optional preference only */
    }
    const provider = currentWalletProvider();
    state.operatorNotice = `${provider.label} selected. Connect-only on the backend network (${APP_CONFIG.NETWORK}); no signing or transaction submission.`;
    renderWalletSession();
    renderRoleDashboard();
    return;
  }
  if (button.dataset.walletNetwork) {
    const next = walletNetworks[button.dataset.walletNetwork] ? button.dataset.walletNetwork : APP_CONFIG.NETWORK;
    state.walletNetwork = next;
    const network = currentWalletNetwork();
    if (next !== APP_CONFIG.NETWORK) {
      state.operatorNotice = `${network.label} selected, but backend is ${APP_CONFIG.NETWORK}. MainNet mismatch will be rejected until the selector matches the backend.`;
      if (state.walletConnection?.address) {
        state.walletConnection = {
          ...state.walletConnection,
          status: "wrong_network",
          error: `UI network ${next} does not match backend ${APP_CONFIG.NETWORK}`,
        };
      }
    } else {
      state.operatorNotice = `${network.label} selected (matches backend). Connect-only; no live trading.`;
      if (state.walletConnection?.status === "wrong_network") {
        state.walletConnection = state.walletConnection.address
          ? { ...state.walletConnection, status: "connected", network: APP_CONFIG.NETWORK, error: null }
          : {
              ...state.walletConnection,
              status: "disconnected",
              network: APP_CONFIG.NETWORK,
              chainId: backendChainId(),
              error: null,
            };
      }
    }
    renderWalletSession();
    renderRoleDashboard();
    return;
  }
  if (button.dataset.walletConnect) {
    await connectSelectedWallet();
    return;
  }
  if (button.dataset.walletDisconnect) {
    await disconnectWallet();
    return;
  }
  if (button.dataset.walletPreset) {
    setWalletPreset(button.dataset.walletPreset);
    if (currentSession().role === "admin") {
      await loadAdminPreflight({ render: false });
      await loadAdminAlertCatalog({ render: false });
      await loadAdminPolicyCatalog({ render: false });
      await loadOpsControlRoom({ render: false });
      await loadProductionReadiness({ render: false });
      await loadReplayLab({ render: false });
      await loadRouteForensics({ render: false });
      await loadMarketHeatmap({ render: false });
      await loadFailureLab({ render: false });
      await loadDataProvenance({ render: false });
      await loadEvidenceSystem({ render: false });
      await loadProductValidation({ render: false });
    } else {
      await loadResearchArchive({ render: false });
    }
    if (state.activeView === "access") {
      await loadContributionProtocol({ render: false });
      await loadCommunityGrowth({ render: false });
    }
    if (state.activeView === "transparency") {
      await loadTransparencySystem({ render: false });
    }
    renderRoleDashboard();
    return;
  }
  if (button.dataset.pnetAction) {
    const actionMap = {
      public_scan: "requested_scan",
      pair_scan: "requested_scan",
      route_unlock: "opened_route",
      run_simulation: "generated_simulation",
      pool_monitor_request: "created_alert",
    };
    await recordProductAction(actionMap[button.dataset.pnetAction] || "requested_scan", {
      page: "access",
      pnet_action: button.dataset.pnetAction,
      evidence_source: "pnet_access_request",
    });
    await openPnetFeeModal(button.dataset.pnetAction);
    return;
  }
  if (button.dataset.contributionSubmit) {
    await recordProductAction("requested_scan", {
      page: "access",
      contribution_type: button.dataset.contributionSubmit,
      evidence_source: "contribution_protocol_beta",
    });
    await submitContributionProtocol(button.dataset.contributionSubmit);
    return;
  }
  if (button.dataset.creditSpend) {
    await recordProductAction("opened_route", {
      page: "access",
      unlock_code: button.dataset.creditSpend,
      evidence_source: "contribution_credit_spend",
    });
    await spendContributionCredits(button.dataset.creditSpend);
    return;
  }
  if (button.dataset.communityReferral) {
    await recordProductAction("requested_scan", {
      page: "access",
      evidence_source: "community_referral_receipt",
    });
    await recordCommunityReferral();
    return;
  }
  if (button.dataset.transparencyAction === "refresh") {
    await recordProductAction("viewed_receipt", {
      page: "transparency",
      evidence_source: "public_proof_ledger",
    });
    await loadTransparencySystem({ render: true });
    return;
  }
  if (button.dataset.utilityAction) {
    if (button.dataset.utilityAction === "refresh-status") {
      if (currentSession().role === "admin") {
        await loadOpsControlRoom({ render: false });
        await loadAdminPreflight({ render: false });
        state.operatorNotice = "Admin connector/status evidence refreshed.";
      } else {
        await refresh();
        state.operatorNotice = "Public scanner/readiness status refreshed. Admin connector internals remain hidden.";
      }
      renderRoleDashboard();
      return;
    }
    if (button.dataset.utilityAction === "copy-payment-uri") {
      const uri = utilityPaymentUri();
      if (uri && navigator.clipboard) {
        await navigator.clipboard.writeText(uri);
        state.utilityHub.copied = true;
        renderRoleDashboard();
        setTimeout(() => {
          state.utilityHub.copied = false;
          if (state.activeView === "utility") renderRoleDashboard();
        }, 1400);
      }
      return;
    }
  }
  if (button.dataset.provenanceMetric) {
    await recordProductAction("exported_data", {
      page: "provenance",
      metric: button.dataset.provenanceMetric,
      evidence_source: "data_provenance",
    });
    await openDataProvenance(button.dataset.provenanceMetric, button.dataset.provenanceRouteHash || null);
    return;
  }
  if (button.dataset.evidenceFilter) {
    state.evidenceFilters[button.dataset.evidenceFilter] = button.dataset.evidenceValue || "all";
    state.selectedEvidenceId = null;
    await loadEvidenceSystem({ render: true });
    return;
  }
  if (button.dataset.evidenceId) {
    state.selectedEvidenceId = button.dataset.evidenceId;
    renderRoleDashboard();
    return;
  }
  if (button.dataset.routeAction) {
    await runRouteAction(button.dataset.routeAction, button.dataset.routeHash);
    return;
  }
  if (button.dataset.serviceKey) {
    openEvidenceDrawer(button.dataset.serviceKey);
    return;
  }
  if (button.dataset.replayId) {
    await recordProductAction("opened_opportunity_replay", {
      page: "replay",
      replay_id: button.dataset.replayId,
      evidence_source: "opportunity_replay",
    });
    state.selectedReplayId = button.dataset.replayId;
    state.replayStep = 0;
    stopReplayPlayback();
    renderRoleDashboard();
    return;
  }
  if (button.dataset.compareReplayId) {
    const id = button.dataset.compareReplayId;
    if (state.compareReplayIds.includes(id)) {
      state.compareReplayIds = state.compareReplayIds.filter((item) => item !== id);
    } else {
      state.compareReplayIds = [...state.compareReplayIds, id].slice(-3);
    }
    renderRoleDashboard();
    return;
  }
  if (button.dataset.replayStep !== undefined) {
    state.replayStep = Number(button.dataset.replayStep || 0);
    stopReplayPlayback();
    renderRoleDashboard();
    return;
  }
  if (button.dataset.replayAction) {
    if (button.dataset.replayAction === "play") {
      startReplayPlayback();
    } else {
      stopReplayPlayback();
      renderRoleDashboard();
    }
    return;
  }
  if (button.dataset.forensicsId) {
    await recordProductAction("inspected_route_forensics", {
      page: "forensics",
      forensics_id: button.dataset.forensicsId,
      evidence_source: "route_forensics",
    });
    state.selectedForensicsId = button.dataset.forensicsId;
    renderRoleDashboard();
    return;
  }
  if (button.dataset.compareForensicsId) {
    const id = button.dataset.compareForensicsId;
    if (state.compareForensicsIds.some((item) => String(item) === String(id))) {
      state.compareForensicsIds = state.compareForensicsIds.filter((item) => String(item) !== String(id));
    } else {
      state.compareForensicsIds = [...state.compareForensicsIds, id].slice(-3);
    }
    renderRoleDashboard();
    return;
  }
  if (button.dataset.heatmapView) {
    state.heatmapView = button.dataset.heatmapView;
    state.selectedHeatmapCellKey = null;
    await loadMarketHeatmap({ render: true });
    return;
  }
  if (button.dataset.heatmapCellKey) {
    await recordProductAction("viewed_liquidity_health", {
      page: "heatmap",
      heatmap_cell: button.dataset.heatmapCellKey,
      evidence_source: "liquidity_heatmap_cell",
    });
    state.selectedHeatmapCellKey = button.dataset.heatmapCellKey;
    renderRoleDashboard();
    return;
  }
  if (button.dataset.decayView) {
    state.decayView = button.dataset.decayView;
    await loadOpportunityDecay({ render: true });
    return;
  }
  if (button.dataset.failureKey) {
    state.selectedFailureKey = button.dataset.failureKey;
    renderRoleDashboard();
    return;
  }
  if (button.dataset.reportDate) {
    await recordProductAction("opened_daily_report", {
      page: "research",
      report_date: button.dataset.reportDate,
      evidence_source: "daily_market_report",
    });
    state.selectedReportDate = button.dataset.reportDate;
    renderRoleDashboard();
    return;
  }
  if (button.dataset.adminAction) {
    if (button.dataset.adminAction === "arm-live") {
      openLiveArmModal();
      return;
    }
    await runAdminAction(button.dataset.adminAction);
  }
}

function pairKeyFromIds(left, right) {
  return [Number(left), Number(right)].sort((a, b) => a - b).join("-");
}

function lpOpeningsFor(readiness, pools) {
  const pairs = readiness?.target_asset?.discovery?.pairs || [];
  if (!pairs.length) return [];
  const poolsByPair = new Map();
  (pools || []).forEach((pool) => {
    const key = pairKeyFromIds(pool.asset_a_id, pool.asset_b_id);
    const entry = poolsByPair.get(key) || { pools: [], venues: new Set() };
    entry.pools.push(pool);
    entry.venues.add(pool.venue_id);
    poolsByPair.set(key, entry);
  });

  return pairs
    .map((pair) => {
      const key = pairKeyFromIds(pair.target_asset_id, pair.other_asset_id);
      const entry = poolsByPair.get(key) || { pools: [], venues: new Set() };
      const venueCount = entry.venues.size;
      const livePoolCount = entry.pools.length;
      const reason = livePoolCount === 0 ? "seed pool" : venueCount < 2 ? "second venue" : "deeper liquidity";
      return {
        ...pair,
        key,
        livePoolCount,
        venueCount,
        reason,
      };
    })
    .filter((pair) => pair.livePoolCount === 0 || pair.venueCount < 2);
}

function renderLiveReadiness(report) {
  const panel = document.getElementById("live-readiness");
  const status = document.getElementById("execution-status");
  const mode = document.getElementById("readiness-mode");
  const wallet = report.wallet || {};
  const execution = report.execution_preflight || {};
  const risk = report.risk || {};
  const signer = {
    enabled: false,
    kill_switch: true,
    route_hash_allowlist_count: 0,
    main_executor_can_sign: false,
    ...(report.signer || {}),
  };
  const tinyLive = {
    enabled: false,
    allow_automation: false,
    scope_ok: false,
    limits_ok: false,
    funding_range: { detail: "wallet lookup required" },
    manual_first_route_ok: false,
    post_first_trade_proof_ok: false,
    automation_gate_ok: true,
    ...(report.tiny_live || {}),
  };
  const route = report.best_approved_route || report.best_observed_route;
  const routeGate = report.route_gate || {};
  const targetAsset = report.target_asset || {};
  const discoveredPairs = targetAsset.discovery?.pairs || [];
  const pinnedPairCount = targetAsset.discovery?.pinned_pair_asset_ids?.length || 0;
  const pairCountLabel = pinnedPairCount
    ? `${pinnedPairCount} pinned pairs`
    : discoveredPairs.length
      ? `${discoveredPairs.length} large pools`
      : `${targetAsset.asset_pairs?.length || 0} pairs`;
  const checks = report.checks || [];
  const coreChecks = checks.slice(0, 15);
  const statusText = report.execution_flags?.enable_live_execution && report.execution_flags?.execute_approved
    ? "Live execution armed"
    : "Live execution disarmed";

  status.textContent = statusText;
  status.className = report.execution_flags?.enable_live_execution && report.execution_flags?.execute_approved
    ? "status armed"
    : "status";
  mode.textContent = report.scan?.ran_now ? "Fresh scan" : "Stored scan";
  setOptionalText("radar-target", targetAsset.discovery?.target_asset?.ticker || `ASA ${targetAsset.asset_id}`);
  setOptionalText("radar-source", targetAsset.vestige_discovery_enabled ? "Vestige discovery" : "Configured pairs");
  setOptionalText("radar-venues", report.connectors?.observed_venues?.join(" / ") || "No venues");
  setOptionalText("radar-pairs", discoveredPairs.length || targetAsset.asset_pairs?.length || 0);
  setOptionalText("radar-pools", report.scan?.pools_monitored || 0);
  setOptionalText("radar-routes", report.scan?.opportunities_24h || 0);
  setOptionalText("radar-lp-slots", lpOpeningsFor(report, state.latestPools).length || 0);
  setOptionalText("ops-verdict", report.verdict_label || "checking");
  setOptionalText("ops-route", report.best_approved_route ? "approved spread" : routeGate.best_observed_skip_reason ? `blocked: ${shortGateLabel(routeGate.best_observed_skip_reason)}` : "waiting");
  setOptionalText(
    "ops-wallet",
    wallet.configured ? wallet.address_masked || "configured" : "No wallet required — read-only"
  );
  setOptionalText("ops-scan", report.scan?.last_scan_age_seconds === null ? "not scanned" : `${Math.round(report.scan?.last_scan_age_seconds || 0)}s ago`);
  setOptionalText(
    "ops-profit-gate",
    `${fmt.format(risk.min_net_profit_input_units || risk.min_net_profit_algos || 0)} min units / ${fmt.format(risk.min_profit_bps || 0)} bps / ${fmt.format(risk.max_route_age_seconds || 0)}s quote`
  );
  setOptionalText("ops-exec-state", statusText);

  panel.innerHTML = `
    <div class="readiness-summary">
      <div>
        <span>Verdict</span>
        <strong>${report.verdict_label}</strong>
      </div>
      <div>
        <span>Score</span>
        <strong>${report.readiness_score}%</strong>
      </div>
      <div>
        <span>Network</span>
        <strong>${report.network}</strong>
      </div>
      <div>
        <span>Target</span>
        <strong>${targetAsset.discovery?.target_asset?.ticker || `ASA ${targetAsset.asset_id}`}</strong>
      </div>
    </div>
    <p class="readiness-detail">${report.verdict_detail}</p>
    <div class="readiness-grid">
      <div class="readiness-card">
        <h3>Source</h3>
        <span>${targetAsset.vestige_discovery_enabled ? "Vestige discovery" : "Configured pairs"}</span>
        <span>${pairCountLabel}</span>
        <span>${targetAsset.execution_note || "scanner and executor aligned"}</span>
      </div>
      <div class="readiness-card">
        <h3>Market</h3>
        <span>${report.scan.pools_monitored} pools</span>
        <span>${report.connectors.observed_venues.join(", ") || "no venues"}</span>
        <span>${report.scan.last_scan_age_seconds === null ? "not scanned" : `${Math.round(report.scan.last_scan_age_seconds)}s old`}</span>
      </div>
      <div class="readiness-card">
        <h3>Wallet</h3>
        <span>${wallet.address_masked || "No wallet required — read-only"}</span>
        <span>${wallet.balance_detail || wallet.detail || "read-only scanning active"}</span>
        <span>${wallet.opt_in_detail || "signing disabled"}</span>
      </div>
      <div class="readiness-card">
        <h3>${report.best_approved_route ? "Approved Route" : "Observed Route"}</h3>
        <span>${route ? `${assetLabel(route.input_asset_id)} ${fmt.format(route.input_amount)} in` : "no route"}</span>
        <span>${route ? `${fmt.format(route.expected_net_profit)} ${assetLabel(route.profit_asset_id || route.input_asset_id)} net` : "waiting"}</span>
        <span>${route?.skip_reason ? `blocked: ${gateLabel(route.skip_reason)}` : route ? route.venues.join(" -> ") : "market-dependent"}</span>
      </div>
      <div class="readiness-card">
        <h3>Profit Gate</h3>
        <span>${risk.requires_positive_net_after_fees === false ? "profit guard disabled" : "Positive net after fees only"}</span>
        <span>${fmt.format(risk.min_net_profit_input_units || risk.min_net_profit_algos || 0)} start-asset units minimum</span>
        <span>${fmt.format(risk.min_profit_bps || 0)} bps minimum</span>
        <span>${fmt.format(risk.min_fee_buffer_multiplier || 0)}x fee buffer</span>
        <span>${fmt.format(risk.max_route_age_seconds || 0)}s max quote age</span>
      </div>
      <div class="readiness-card">
        <h3>Risk Limits</h3>
        <span>${risk.own_funds_only === false ? "own-funds guard off" : "own funds only"}</span>
        <span>${fmt.format(risk.max_live_trade_size || 0)} max trade / ${fmt.format(risk.max_price_impact_bps || 0)} bps impact</span>
        <span>${fmt.format(risk.max_route_legs || 0)} swaps / ${fmt.format(risk.max_concurrent_execution || 0)} concurrent</span>
        <span>${fmt.format(risk.submitted_live_trades_24h || 0)} / ${fmt.format(risk.max_daily_trades || 0)} trades today</span>
        <span>${
          Number(risk.paper_verified_app_ids_count || (risk.paper_verified_app_ids || []).length || 0) > 0
            ? `${fmt.format(risk.paper_verified_app_ids_count || (risk.paper_verified_app_ids || []).length)} paper verified apps`
            : risk.app_id_allowlist_required
              ? `${fmt.format(risk.allowed_app_ids_count || 0)} execution app IDs (paper registry separate)`
              : "app ID allowlist optional"
        }</span>
      </div>
      <div class="readiness-card">
        <h3>Dry Run</h3>
        <span>${execution.group_build_ok ? "atomic group built" : execution.detail || "not attempted"}</span>
        <span>${execution.result?.unsigned_group ? "unsigned group only" : report.execution_flags?.unsigned_executor_only ? "unsigned executor only" : "signing path gated"}</span>
        <span>${execution.result?.tx_count ? `${execution.result.tx_count}/${execution.result.max_tx_group_size || risk.max_tx_group_size || 16} txns` : `0/${risk.max_tx_group_size || 16} txns`}</span>
        <span>${execution.result?.fee_algos ? `${fmt.format(execution.result.fee_algos)} ALGO fee` : "fees pending"}</span>
      </div>
      <div class="readiness-card">
        <h3>Signer</h3>
        <span>${signer.enabled ? "service enabled" : "service disabled"}</span>
        <span>${signer.kill_switch ? "kill switch active" : "kill switch open"}</span>
        <span>${fmt.format(signer.route_hash_allowlist_count || 0)} reviewed route hashes</span>
        <span>${signer.main_executor_can_sign === false ? "executor cannot sign" : "review signing path"}</span>
      </div>
      <div class="readiness-card">
        <h3>Tiny Live</h3>
        <span>${tinyLive.enabled ? "mode enabled" : "mode locked"}</span>
        <span>${tinyLive.scope_ok ? "ALGO/USDC only" : "scope not tiny-live"}</span>
        <span>${tinyLive.enabled ? tinyLive.limits_ok ? "10 ALGO / 20 loss / 20 trades" : "limits need review" : "template ready"}</span>
        <span>${tinyLive.enabled ? tinyLive.manual_first_route_ok ? "manual route approved" : "manual route needed" : "manual gate off"}</span>
        <span>${tinyLive.enabled ? tinyLive.post_first_trade_proof_ok ? "Lora + reconciliation recorded" : "Lora + reconciliation pending" : "proof gate off"}</span>
      </div>
      <div class="readiness-card">
        <h3>Route Gate</h3>
        <span>${report.best_approved_route ? "approved spread available" : "waiting for spread"}</span>
        <span>${routeGate.best_observed_skip_reason ? gateLabel(routeGate.best_observed_skip_reason) : "no rejection"}</span>
        <span>${Object.entries(routeGate.rejection_summary || {}).slice(0, 2).map(([key, count]) => `${count} ${gateLabel(key)}`).join(" / ") || "clean"}</span>
      </div>
    </div>
    <div class="check-list">
      ${coreChecks
        .map(
          (check) => `
        <div class="check ${checkClass(check)}">
          <span>${check.name.replaceAll("_", " ")}</span>
          <strong>${checkLabel(check)}</strong>
        </div>`
        )
        .join("")}
    </div>
  `;
}

function renderMarketRadar(readiness, pools, opportunities) {
  state.latestReadiness = readiness;
  // Only real stored pools — never fabricate client-side market data.
  state.latestPools = (pools || []).filter((pool) => pool && (pool.pool_id || pool.poolId) && (pool.venue_id || pool.venue));
  state.latestOpportunities = opportunities || [];
  state.latestLpOpenings = lpOpeningsFor(readiness, state.latestPools);
  setOptionalText("radar-lp-slots", state.latestLpOpenings.length || 0);
  setOptionalText("radar-pools", state.latestPools.length || readiness?.scan?.pools_monitored || 0);
  setOptionalText("radar-routes", readiness?.scan?.opportunities_24h || state.latestOpportunities.length || 0);
  renderLpCta(readiness, state.latestLpOpenings);
  drawMarketRadar();
  bindRadarPoolClicks();
  if (!state.radarAnimation) {
    const animate = () => {
      state.radarPhase += 0.018;
      drawMarketRadar();
      state.radarAnimation = requestAnimationFrame(animate);
    };
    state.radarAnimation = requestAnimationFrame(animate);
  }
}

function bindRadarPoolClicks() {
  const canvas = document.getElementById("market-radar");
  if (!canvas || canvas.dataset.radarClickBound === "1") return;
  canvas.dataset.radarClickBound = "1";
  canvas.style.cursor = "pointer";
  canvas.addEventListener("click", (event) => {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const hits = state.radarHits || [];
    let best = null;
    let bestDist = Infinity;
    hits.forEach((hit) => {
      const dist = Math.hypot(hit.x - x, hit.y - y);
      if (dist <= hit.radius + 8 && dist < bestDist) {
        best = hit;
        bestDist = dist;
      }
    });
    if (best?.pool) {
      state.radarSelectedPoolId = best.pool.pool_id || best.pool.poolId;
      renderRadarPoolDetail(best.pool);
      drawMarketRadar();
    }
  });
}

function renderRadarPoolDetail(pool) {
  const el = document.getElementById("radar-pool-detail");
  if (!el || !pool) return;
  const venue = pool.venue_id || pool.venue || "unknown";
  const appId = pool.app_id ?? pool.appId ?? "—";
  const poolId = pool.pool_id || pool.poolId || "—";
  const assetA = assetLabel(pool.asset_a_id ?? pool.assets?.[0]);
  const assetB = assetLabel(pool.asset_b_id ?? pool.assets?.[1]);
  const reserveA = money.format(pool.reserve_a ?? pool.reserves?.a ?? 0);
  const reserveB = money.format(pool.reserve_b ?? pool.reserves?.b ?? 0);
  const liquidity = money.format(pool.liquidity_estimate ?? pool.liquidity ?? 0);
  const round = pool.block_round ?? pool.blockRound ?? "—";
  const freshness = secondsLabel(pool.snapshot_age_seconds ?? pool.freshnessSeconds ?? pool.freshness ?? 0);
  const source = pool.source || "connector";
  const connector = pool.connectorStatus || "unknown";
  el.classList.remove("muted");
  el.innerHTML = `
    <strong>${escapeHtml(String(venue))}</strong>
    · ${escapeHtml(String(assetA))}/${escapeHtml(String(assetB))}
    · app ${escapeHtml(String(appId))}
    · reserves ${reserveA} / ${reserveB}
    · liq ${liquidity}
    · round ${escapeHtml(String(round))}
    · age ${escapeHtml(String(freshness))}
    · ${escapeHtml(String(source))} (${escapeHtml(String(connector))})
    <span class="muted"> · ${escapeHtml(String(poolId))}</span>
  `;
}

function renderLpCta(readiness, openings) {
  const cta = document.getElementById("radar-cta");
  if (!cta) return;
  if (!openings.length) {
    cta.classList.add("hidden");
    return;
  }

  cta.classList.remove("hidden");
  const target = readiness?.target_asset?.discovery?.target_asset?.ticker || "PNET";
  const featured = openings
    .slice()
    .sort((a, b) => Number(b.target_reserve || 0) - Number(a.target_reserve || 0))[0];
  const pair = `${target} / ${assetLabel(featured.other_asset_id)}`;
  setOptionalText("radar-cta-kicker", `${openings.length} LP slots open`);
  setOptionalText("radar-cta-main", "Could be you");
  setOptionalText("radar-cta-sub", `${pair} needs depth`);
}

function drawMarketRadar() {
  const canvas = document.getElementById("market-radar");
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return;

  const dpr = window.devicePixelRatio || 1;
  const width = Math.max(1, Math.floor(rect.width * dpr));
  const height = Math.max(1, Math.floor(rect.height * dpr));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }

  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, rect.width, rect.height);

  const cx = rect.width * 0.5;
  const cy = rect.height * 0.52;
  const radius = Math.min(rect.width, rect.height) * 0.36;
  const pools = state.latestPools.slice(0, 28);
  const opportunities = state.latestOpportunities || [];
  const lpOpenings = state.latestLpOpenings || [];
  const target = state.latestReadiness?.target_asset?.discovery?.target_asset?.ticker || "PNET";
  state.radarHits = [];

  if (!pools.length) {
    ctx.fillStyle = "#050b09";
    ctx.fillRect(0, 0, rect.width, rect.height);
    ctx.fillStyle = "rgba(234, 255, 247, 0.72)";
    ctx.font = "600 16px Inter, system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Scanner unavailable or no live pools stored", cx, cy);
    ctx.textAlign = "start";
    return;
  }

  ctx.fillStyle = "#050b09";
  ctx.fillRect(0, 0, rect.width, rect.height);

  const backgroundGlow = ctx.createRadialGradient(cx, cy, radius * 0.08, cx, cy, radius * 1.08);
  backgroundGlow.addColorStop(0, "rgba(72, 255, 175, 0.09)");
  backgroundGlow.addColorStop(0.46, "rgba(73, 215, 255, 0.025)");
  backgroundGlow.addColorStop(1, "rgba(6, 8, 6, 0)");
  ctx.fillStyle = backgroundGlow;
  ctx.fillRect(0, 0, rect.width, rect.height);

  ctx.strokeStyle = "rgba(72, 255, 175, 0.12)";
  ctx.lineWidth = 1;
  for (let ring = 1; ring <= 4; ring += 1) {
    ctx.beginPath();
    ctx.arc(cx, cy, (radius * ring) / 4, 0, Math.PI * 2);
    ctx.stroke();
  }

  for (let spoke = 0; spoke < 12; spoke += 1) {
    const angle = (Math.PI * 2 * spoke) / 12;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
    ctx.stroke();
  }

  const sweep = state.radarPhase % (Math.PI * 2);
  const sweepGradient = ctx.createLinearGradient(cx, cy, cx + Math.cos(sweep) * radius, cy + Math.sin(sweep) * radius);
  sweepGradient.addColorStop(0, "rgba(72, 255, 175, 0.72)");
  sweepGradient.addColorStop(1, "rgba(72, 255, 175, 0)");
  ctx.strokeStyle = sweepGradient;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(cx + Math.cos(sweep) * radius, cy + Math.sin(sweep) * radius);
  ctx.stroke();

  drawLpOpenings(ctx, {
    cx,
    cy,
    radius,
    phase: state.radarPhase,
    openings: lpOpenings,
  });

  pools.forEach((pool, index) => {
    const angle = (Math.PI * 2 * index) / Math.max(1, pools.length) + state.radarPhase * 0.12;
    const reserve = Math.max(Number(pool.reserve_a || pool.reserves?.a || 0), Number(pool.reserve_b || pool.reserves?.b || 0));
    const depth = Math.min(1, Math.log10(reserve + 10) / 8);
    const distance = radius * (0.22 + depth * 0.72);
    const x = cx + Math.cos(angle) * distance;
    const y = cy + Math.sin(angle) * distance;
    const venueId = pool.venue_id || pool.venue;
    const venueColor = venueId === "pact" ? "#49d7ff" : "#48ffaf";
    const dotRadius = 2.8 + depth * 5.8;
    const selected = state.radarSelectedPoolId && state.radarSelectedPoolId === (pool.pool_id || pool.poolId);

    ctx.beginPath();
    ctx.fillStyle = venueColor;
    ctx.shadowColor = venueColor;
    ctx.shadowBlur = selected ? 16 : 10;
    ctx.arc(x, y, selected ? dotRadius + 1.5 : dotRadius, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;

    ctx.beginPath();
    ctx.strokeStyle = selected
      ? "rgba(255, 255, 255, 0.75)"
      : venueId === "pact"
        ? "rgba(73, 215, 255, 0.24)"
        : "rgba(72, 255, 175, 0.24)";
    ctx.lineWidth = selected ? 2 : 1;
    ctx.arc(x, y, dotRadius + 4, 0, Math.PI * 2);
    ctx.stroke();

    state.radarHits.push({ x, y, radius: dotRadius, pool });
  });

  ctx.beginPath();
  ctx.fillStyle = "rgba(6, 8, 6, 0.56)";
  ctx.arc(cx, cy, radius * 0.22, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.strokeStyle = "rgba(72, 255, 175, 0.18)";
  ctx.lineWidth = 1.5;
  ctx.arc(cx, cy, radius * 0.22, 0, Math.PI * 2);
  ctx.stroke();

  ctx.fillStyle = "#eafff7";
  ctx.font = "900 33px Inter, system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(target, cx, cy + 10);
  ctx.textAlign = "start";
}

function drawLpOpenings(ctx, { cx, cy, radius, phase, openings }) {
  if (!openings.length) return;
  const maxGhosts = Math.min(openings.length, 8);
  const highlightedIndex = Math.floor(phase / 1.4) % maxGhosts;

  ctx.save();
  ctx.setLineDash([5, 5]);
  openings.slice(0, maxGhosts).forEach((opening, index) => {
    const angle = (Math.PI * 2 * index) / maxGhosts - phase * 0.08;
    const orbit = radius * (0.78 + (index % 2) * 0.1);
    const x = cx + Math.cos(angle) * orbit;
    const y = cy + Math.sin(angle) * orbit;
    const pulse = 0.5 + Math.sin(phase * 3 + index) * 0.18;
    const ring = opening.livePoolCount === 0 ? 13 : 9;
    const highlighted = index === highlightedIndex;

    ctx.beginPath();
    ctx.strokeStyle = highlighted ? "rgba(255, 204, 102, 0.72)" : `rgba(255, 204, 102, ${pulse * 0.42})`;
    ctx.lineWidth = highlighted ? 2 : 1.1;
    ctx.arc(x, y, highlighted ? ring + 3 : ring, 0, Math.PI * 2);
    ctx.stroke();

    ctx.beginPath();
    ctx.fillStyle = highlighted ? "rgba(255, 204, 102, 0.11)" : "rgba(255, 204, 102, 0.045)";
    ctx.arc(x, y, ring - 2, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.restore();
}

function renderPulse(pulse) {
  setText("pools-count", pulse.pools_monitored);
  setText("opportunity-count", pulse.opportunities_24h);
  setText("approved-count", pulse.approved_24h);
  setText("paper-net", `${fmt.format(pulse.paper_net_profit_24h)} ALGO`);
  setText("last-scan", pulse.last_scan_at ? ago(pulse.last_scan_at) : "not scanned");
  setText("market-health", pulse.market_health);

  const best = document.getElementById("best-route");
  if (!pulse.best_opportunity) {
    best.innerHTML = `<p class="muted">No approved public route yet. Run a scan to seed the engine.</p>`;
    return;
  }
  const route = pulse.best_opportunity.route || [];
  best.innerHTML = `
    <div class="route-line">
      <span>${assetLabel(pulse.best_opportunity.input_asset_id)}</span>
      <strong>${fmt.format(pulse.best_opportunity.expected_net_profit)} ${assetLabel(pulse.best_opportunity.input_asset_id)} net</strong>
    </div>
    <div class="route-legs">
      ${route
        .map(
          (leg) => `
        <div class="leg">
          <span class="venue">${leg.venue}</span>
          <span>${assetLabel(leg.input_asset_id)} to ${assetLabel(leg.output_asset_id)}</span>
          <span>${fmt.format(leg.input_amount)} in</span>
        </div>`
        )
        .join("")}
    </div>
  `;
}

function renderPools(pools) {
  const body = document.getElementById("pools-body");
  body.innerHTML = pools
    .map((pool) => {
      const freshness = pool.snapshot_age_seconds ?? pool.data_freshness_seconds ?? 0;
      return `
      <tr>
        <td>${pool.venue_id}</td>
        <td>${escapeHtml(pool.pool_id)} / ${pool.app_id}</td>
        <td>${assetLabel(pool.asset_a_id)} / ${assetLabel(pool.asset_b_id)}</td>
        <td>${money.format(pool.reserve_a)}</td>
        <td>${money.format(pool.reserve_b)}</td>
        <td>${money.format(pool.liquidity_estimate || 0)}</td>
        <td>${fmt.format(pool.price_a_in_b)}</td>
        <td>${pool.block_round}</td>
        <td>${secondsLabel(freshness)}</td>
      </tr>`;
    })
    .join("");
}

function renderOpportunities(opportunities) {
  const list = document.getElementById("opportunity-list");
  if (!opportunities.length) {
    list.innerHTML = `<p class="muted">No public opportunities yet. The dashboard delays sensitive route data.</p>`;
    return;
  }
  list.innerHTML = opportunities
    .slice(0, 8)
    .map(
      (item) => `
      <article class="opportunity ${item.status}">
        <div class="opportunity-main">
          <h3>${assetLabel(item.input_asset_id)} route</h3>
          <p>${item.route.map((leg) => leg.venue).join(" -> ")}</p>
          <div class="opportunity-breakdown">
            <span><em>Gross</em><strong>${signedAmount(item.gross_profit, item.input_asset_id)}</strong></span>
            <span><em>Network</em><strong>${fmt.format(item.estimated_network_fee || 0)}</strong></span>
            <span><em>DEX fees</em><strong>${fmt.format(item.total_dex_fees || 0)}</strong></span>
            <span><em>Impact</em><strong>${fmt.format(item.total_price_impact_bps || item.max_price_impact_bps || 0)} bps</strong></span>
            <span><em>Slippage</em><strong>${fmt.format(item.slippage_buffer || 0)}</strong></span>
            <span><em>Confidence</em><strong>${fmt.format(item.confidence_score || 0)}%</strong></span>
          </div>
        </div>
        <div class="opportunity-metrics">
          <strong>${signedAmount(item.expected_net_profit, item.input_asset_id)}</strong>
          <span>${fmt.format(item.expected_profit_bps)} bps</span>
          <span>${item.status}${item.skip_reason ? `: ${gateLabel(item.skip_reason)}` : ""}</span>
        </div>
      </article>`
    )
    .join("");
}

function renderTrades(trades) {
  const list = document.getElementById("paper-trades");
  if (!trades.length) {
    list.innerHTML = `<p class="muted">Paper candidates will appear after scans. Delayed checks update when later scans refresh pool state.</p>`;
    return;
  }
  const checkpoint = (trade, suffix) => {
    const checked = trade[`checked_${suffix}_at`];
    if (!checked) return `${suffix}: pending`;
    const profit = trade[`simulated_profit_${suffix}`];
    const decay = trade[`quote_decay_${suffix}`];
    const delta = trade[`expected_vs_simulated_profit_${suffix}`];
    return `${suffix}: ${signedAmount(profit, trade.input_asset_id)} / decay ${fmt.format(decay || 0)} / delta ${fmt.format(delta || 0)}`;
  };
  list.innerHTML = trades
    .slice(0, 6)
    .map(
      (trade) => `
      <div class="trade-row paper-row">
        <span>${trade.route_hash}</span>
        <strong>${trade.would_execute ? "would execute" : `skip: ${gateLabel(trade.skip_reason || "unknown")}`}</strong>
        <span>expected ${signedAmount(trade.expected_net_profit || trade.expected_profit, trade.input_asset_id)}</span>
        <span>${checkpoint(trade, "5s")}</span>
        <span>${checkpoint(trade, "30s")}</span>
        <span>${trade.last_error ? escapeHtml(trade.last_error) : escapeHtml(trade.notes || "")}</span>
      </div>`
    )
    .join("");
}

function renderPaperDailyReport(report) {
  const target = document.getElementById("paper-daily-report");
  if (!target) return;
  if (!report) {
    target.innerHTML = `<p class="muted">Daily paper report is loading.</p>`;
    return;
  }
  const skipReasons = report.skipReasons || [];
  target.innerHTML = `
    <div class="paper-report-grid">
      <div><span>Candidates</span><strong>${fmt.format(report.candidates || 0)}</strong></div>
      <div><span>Would execute</span><strong>${fmt.format(report.wouldExecute || 0)}</strong></div>
      <div><span>30s complete</span><strong>${fmt.format((report.completionRate30s || 0) * 100)}%</strong></div>
      <div><span>Expected net</span><strong>${fmt.format(report.expectedNetProfit || 0)}</strong></div>
      <div><span>Simulated 30s</span><strong>${fmt.format(report.simulatedProfit30s || 0)}</strong></div>
      <div><span>Avg quote decay</span><strong>${fmt.format(report.averageQuoteDecay30s || 0)}</strong></div>
    </div>
    <div class="skip-reason-list">
      ${
        skipReasons.length
          ? skipReasons
              .slice(0, 4)
              .map(
                (item) => `
          <div class="skip-reason-row">
            <span>${escapeHtml(gateLabel(item.reason))}</span>
            <strong>${fmt.format(item.count || 0)} candidates</strong>
          </div>`
              )
              .join("")
          : `<p class="muted">No skip reasons recorded in the current window.</p>`
      }
    </div>
  `;
}

function renderLiveTrades(trades) {
  const list = document.getElementById("live-trades");
  if (!trades.length) {
    list.innerHTML = `<p class="muted">No execution dry-runs or submitted trades have been recorded yet.</p>`;
    return;
  }
  list.innerHTML = trades
    .slice(0, 6)
    .map((trade) => {
      const result = JSON.parse(trade.result_json || "{}");
      const label = trade.submitted ? "submitted" : "dry-run";
      const detail = result.txid || result.reason || result.group_id_hex || "recorded";
      return `
        <div class="trade-row">
          <span>${trade.route_hash || "route"}</span>
          <strong>${label}</strong>
          <span>${detail}</span>
        </div>`;
    })
    .join("");
}

function deltaSummary(deltas) {
  const entries = Object.entries(deltas || {});
  if (!entries.length) return "no deltas";
  return entries
    .map(([assetId, value]) => `${Number(value) >= 0 ? "+" : ""}${fmt.format(Number(value))} ${assetLabel(assetId)}`)
    .join(" / ");
}

function renderReconciliations(reconciliations) {
  const list = document.getElementById("reconciliations");
  if (!list) return;
  if (!reconciliations.length) {
    list.innerHTML = `<p class="muted">No reconciliation receipts yet. Dry-run plans will show expected deltas; submitted trades add actual balance deltas.</p>`;
    return;
  }

  list.innerHTML = reconciliations
    .slice(0, 6)
    .map((item) => {
      const status = item.status || "unknown";
      const okLabel = item.ok === null || item.ok === undefined ? "planned" : item.ok ? "ok" : "variance";
      const actual = item.actual_deltas ? deltaSummary(item.actual_deltas) : "awaiting submitted trade";
      return `
        <div class="trade-row reconciliation-row ${okLabel}">
          <span>${item.route_hash || "route"}</span>
          <strong>${status}</strong>
          <span>${deltaSummary(item.expected_deltas)} expected</span>
          <span>${actual}</span>
        </div>`;
    })
    .join("");
}

function renderPaymentVerificationResult(result) {
  const target = document.getElementById("payment-verification-result");
  if (!target) return;
  if (!result) {
    target.innerHTML = "";
    return;
  }

  const label = result.ok ? "verified" : result.status || "not verified";
  const reason = result.reason ? `: ${result.reason}` : "";
  const observed = result.observed || {};
  target.innerHTML = `
    <div class="verification-banner ${result.ok ? "ok" : "fail"}">
      <strong>${escapeHtml(label)}${escapeHtml(reason)}</strong>
      <span>${escapeHtml(result.txid)}</span>
      <span>${escapeHtml(observed.receiver || "no receiver")} / ${fmt.format(Number(observed.amount_display || 0))} ${assetLabel(result.asset_id || 0)}</span>
    </div>
  `;
}

function renderPaymentVerifications(verifications) {
  const list = document.getElementById("payment-verifications");
  if (!list) return;
  if (!verifications.length) {
    list.innerHTML = `<p class="muted">No payment receipts checked yet.</p>`;
    return;
  }

  list.innerHTML = verifications
    .slice(0, 6)
    .map((item) => {
      const result = item.result || {};
      const observed = result.observed || {};
      return `
        <div class="trade-row payment-row ${item.ok ? "ok" : "fail"}">
          <span>#${item.id} ${escapeHtml(item.txid)}</span>
          <strong>${escapeHtml(item.status)}${item.reason ? `: ${escapeHtml(item.reason)}` : ""}</strong>
          <span>${fmt.format(Number(observed.amount_display || 0))} ${assetLabel(item.asset_id || 0)} / ${escapeHtml(observed.receiver || "no receiver")}</span>
        </div>`;
    })
    .join("");
}

function renderRefundCaseResult(result) {
  const target = document.getElementById("refund-case-result");
  if (!target) return;
  if (!result) {
    target.innerHTML = "";
    return;
  }

  target.innerHTML = `
    <div class="verification-banner ${result.status === "refund_ready" ? "ok" : "fail"}">
      <strong>${escapeHtml(result.status)}: ${escapeHtml(result.operator_action || "recorded")}</strong>
      <span>#${result.id} ${escapeHtml(result.source_txid || "no source tx")}</span>
      <span>${fmt.format(Number(result.amount_display || 0))} ${assetLabel(result.asset_id || 0)} / ${escapeHtml(result.refund_address || "no refund address")}</span>
    </div>
  `;
}

function renderRefundCases(cases) {
  const list = document.getElementById("refund-cases");
  if (!list) return;
  if (!cases.length) {
    list.innerHTML = `<p class="muted">No failure or refund cases recorded yet.</p>`;
    return;
  }

  list.innerHTML = cases
    .slice(0, 8)
    .map((item) => {
      const canResolve = ["refund_ready", "needs_review"].includes(item.status);
      const amount = `${fmt.format(Number(item.amount_display || 0))} ${assetLabel(item.asset_id || 0)}`;
      return `
        <div class="refund-row ${escapeHtml(item.status)}">
          <div class="refund-main">
            <span>#${item.id} ${escapeHtml(item.failure_type)} / ${escapeHtml(item.status)}</span>
            <strong>${escapeHtml(item.operator_action || "recorded")}</strong>
            <span>${escapeHtml(item.reason)}</span>
          </div>
          <div class="refund-detail">
            <span>${escapeHtml(item.source_txid || "no source tx")}</span>
            <span>${amount} -> ${escapeHtml(item.refund_address || "not refundable")}</span>
            <span>${escapeHtml(item.resolution_txid || item.resolution_note || "unresolved")}</span>
          </div>
          <div class="refund-actions">
            ${
              canResolve
                ? `<button type="button" data-refund-action="resolve" data-case-id="${item.id}">Resolve</button>
                   <button type="button" data-refund-action="cancel" data-case-id="${item.id}">Cancel</button>`
                : `<span>${item.resolved_at ? "closed" : "tracked"}</span>`
            }
          </div>
        </div>`;
    })
    .join("");
}

function renderDemoRun(demo) {
  const target = document.getElementById("demo-run");
  target.innerHTML = `
    <div class="demo-main">
      <div>
        <span class="demo-label">Input</span>
        <strong>${fmt.format(demo.input_amount)} ${demo.input_asset}</strong>
      </div>
      <div>
        <span class="demo-arrow">→</span>
      </div>
      <div>
        <span class="demo-label">Output</span>
        <strong>${fmt.format(demo.output_amount)} ${demo.output_asset}</strong>
      </div>
      <div>
        <span class="demo-label">Net</span>
        <strong>${fmt.format(demo.net_profit_algo)} ALGO</strong>
      </div>
    </div>
    <div class="route-legs">
      ${demo.route
        .map(
          (leg) => `
        <div class="leg">
          <span class="venue">${leg.venue}</span>
          <span>${leg.pair}</span>
          <span>${leg.output}</span>
        </div>`
        )
        .join("")}
    </div>
    <p class="demo-warning">${demo.warning}</p>
  `;
}

async function refresh() {
  try {
    const [
      publicConfig,
      pulse,
      pools,
      opportunities,
      trades,
      liveTrades,
      reconciliations,
      paymentVerifications,
      refundCases,
      demoRun,
      readiness,
      paperReport,
      recentPnetSwaps,
      testnetReadiness,
    ] = await Promise.all([
      fetchApiData("/api/config/public"),
      fetchJson("/api/pulse"),
      fetchJson("/api/pools"),
      fetchJson("/api/opportunities"),
      fetchJson("/api/paper-trades"),
      fetchJson("/api/live-trades"),
      fetchJson("/api/reconciliations"),
      fetchJson("/api/payment-verifications"),
      fetchJson("/api/refund-cases"),
      fetchJson("/api/demo-run"),
      fetchJson("/api/live-readiness"),
      fetchApiData("/api/reports/paper/daily"),
      fetchApiData("/api/market/pnet/recent-swaps?limit=5").catch((error) => {
        state.recentPnetSwapsError = error.message;
        return null;
      }),
      fetchApiData("/api/testnet/readiness").catch((error) => {
        state.testnetReadinessError = error.message;
        return null;
      }),
    ]);
    applyPublicConfig(publicConfig);
    await restoreWalletSession();
    renderPhaseGates();
    renderDeploymentModes();
    state.latestPaperReport = paperReport;
    state.recentPnetSwaps = recentPnetSwaps;
    if (recentPnetSwaps) state.recentPnetSwapsError = null;
    state.testnetReadiness = testnetReadiness;
    if (testnetReadiness) {
      state.testnetReadinessError = null;
      if (testnetReadiness.networkHealth) state.networkHealth = testnetReadiness.networkHealth;
    }
    renderLiveReadiness(readiness);
    renderMarketRadar(readiness, pools, opportunities);
    renderDemoRun(demoRun);
    renderPulse(pulse);
    renderPools(pools);
    renderOpportunities(opportunities);
    renderTrades(trades);
    renderLiveTrades(liveTrades);
    renderReconciliations(reconciliations);
    renderPaymentVerifications(paymentVerifications);
    renderRefundCases(refundCases);
    renderPaperDailyReport(paperReport);
    await loadAdminPreflight({ render: false });
    await loadAdminAlertCatalog({ render: false });
    await loadAdminPolicyCatalog({ render: false });
    await loadOpsControlRoom({ render: false });
    await loadProductionReadiness({ render: false });
    if (state.activeView === "replay" && currentSession().role === "admin") {
      await loadReplayLab({ render: false });
    }
    if (state.activeView === "forensics" && currentSession().role === "admin") {
      await loadRouteForensics({ render: false });
    }
    if (state.activeView === "confidence" && currentSession().role === "admin") {
      await loadConfidenceCalibration({ render: false });
    }
    if (state.activeView === "decay" && currentSession().role === "admin") {
      await loadOpportunityDecay({ render: false });
    }
    if (state.activeView === "heatmap" && currentSession().role === "admin") {
      await loadMarketHeatmap({ render: false });
    }
    if (state.activeView === "failure" && currentSession().role === "admin") {
      await loadFailureLab({ render: false });
    }
    if (state.activeView === "provenance" && currentSession().role === "admin") {
      await loadDataProvenance({ render: false });
    }
    if (state.activeView === "evidence" && currentSession().role === "admin") {
      await loadEvidenceSystem({ render: false });
    }
    if (state.activeView === "validation" && currentSession().role === "admin") {
      await loadProductValidation({ render: false });
    }
    if (state.activeView === "research") {
      await loadResearchArchive({ render: false });
    }
    renderRoleDashboard();
  } catch (error) {
    document.getElementById("live-readiness").innerHTML = `<p class="muted">Refresh failed: ${error.message}</p>`;
    renderRoleDashboard();
  }
}

async function scanNow() {
  const button = document.getElementById("scan-now");
  button.disabled = true;
  button.textContent = "Scanning";
  try {
    await fetchJson("/api/scan", { method: "POST" });
    await refresh();
  } finally {
    button.disabled = false;
    button.textContent = "Scan now";
  }
}

async function pollOpsControlRoom() {
  if (state.activeView !== "pipeline" || currentSession().role !== "admin" || state.opsLoading) {
    return;
  }
  await loadOpsControlRoom({ render: true, quiet: true });
}

async function preflightNow() {
  const button = document.getElementById("readiness-check");
  button.disabled = true;
  button.textContent = "Checking";
  try {
    if (currentSession().role === "admin") {
      await loadAdminPreflight({ render: false });
      state.operatorNotice = "Backend admin preflight refreshed.";
    } else {
      const readiness = await fetchJson("/api/live-readiness?run_scan=true");
      renderLiveReadiness(readiness);
    }
    await refresh();
  } finally {
    button.disabled = false;
    button.textContent = "Preflight";
  }
}

async function verifyPaymentNow(event) {
  event.preventDefault();
  const button = document.getElementById("verify-payment");
  const txid = document.getElementById("verify-txid").value.trim();
  const expectedReceiver = document.getElementById("verify-receiver").value.trim();
  const expectedAmount = Number(document.getElementById("verify-amount").value);
  const assetId = Number(document.getElementById("verify-asset-id").value || "0");
  const minConfirmations = Number(document.getElementById("verify-confirmations").value || "1");
  const notePrefix = document.getElementById("verify-note-prefix").value.trim();

  if (!txid || !expectedReceiver || !expectedAmount) {
    renderPaymentVerificationResult({
      ok: false,
      status: "missing_input",
      reason: "txid_receiver_amount_required",
      txid: txid || "no txid",
      asset_id: assetId,
      observed: {},
    });
    return;
  }

  button.disabled = true;
  button.textContent = "Verifying";
  try {
    const result = await fetchJson("/api/verify-payment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        txid,
        expected_receiver: expectedReceiver,
        expected_amount: expectedAmount,
        asset_id: assetId,
        asset_decimals: 6,
        amount_unit: "display",
        min_confirmations: minConfirmations,
        note_prefix: notePrefix || null,
      }),
    });
    renderPaymentVerificationResult(result);
    renderPaymentVerifications(await fetchJson("/api/payment-verifications"));
  } catch (error) {
    renderPaymentVerificationResult({
      ok: false,
      status: "request_failed",
      reason: error.message,
      txid,
      asset_id: assetId,
      observed: {},
    });
  } finally {
    button.disabled = false;
    button.textContent = "Verify";
  }
}

async function createRefundCaseNow(event) {
  event.preventDefault();
  const button = document.getElementById("create-refund-case");
  const verificationId = document.getElementById("refund-verification-id").value.trim();
  const failureType = document.getElementById("refund-failure-type").value;
  const reason = document.getElementById("refund-reason").value.trim();
  const operatorNote = document.getElementById("refund-note").value.trim();

  if (!reason) {
    renderRefundCaseResult({
      id: "new",
      status: "missing_input",
      operator_action: "reason_required",
      source_txid: null,
      amount_display: 0,
      asset_id: 0,
      refund_address: null,
    });
    return;
  }

  button.disabled = true;
  button.textContent = "Creating";
  try {
    const result = await fetchJson("/api/refund-cases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        payment_verification_id: verificationId ? Number(verificationId) : null,
        failure_type: failureType,
        reason,
        operator_note: operatorNote || null,
      }),
    });
    renderRefundCaseResult(result);
    renderRefundCases(await fetchJson("/api/refund-cases"));
    document.getElementById("refund-reason").value = "";
    document.getElementById("refund-note").value = "";
  } catch (error) {
    renderRefundCaseResult({
      id: "new",
      status: "request_failed",
      operator_action: error.message,
      source_txid: null,
      amount_display: 0,
      asset_id: 0,
      refund_address: null,
    });
  } finally {
    button.disabled = false;
    button.textContent = "Create case";
  }
}

async function updateRefundCaseStatus(event) {
  const button = event.target.closest("[data-refund-action]");
  if (!button) return;

  const caseId = button.dataset.caseId;
  const action = button.dataset.refundAction;
  const resolutionTxid = action === "resolve" ? window.prompt("Refund txid or resolution reference:") : null;
  if (action === "resolve" && !resolutionTxid) return;
  const resolutionNote = window.prompt("Resolution note:") || null;
  const status = action === "resolve" ? "resolved" : "cancelled";

  button.disabled = true;
  try {
    const result = await fetchJson(`/api/refund-cases/${caseId}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        status,
        resolution_txid: resolutionTxid,
        resolution_note: resolutionNote,
      }),
    });
    renderRefundCaseResult(result);
    renderRefundCases(await fetchJson("/api/refund-cases"));
  } catch (error) {
    renderRefundCaseResult({
      id: caseId,
      status: "request_failed",
      operator_action: error.message,
      source_txid: null,
      amount_display: 0,
      asset_id: 0,
      refund_address: null,
    });
  } finally {
    button.disabled = false;
  }
}

document.getElementById("scan-now").addEventListener("click", async () => {
  await recordProductAction("requested_scan", {
    page: state.activeView || "pulse",
    evidence_source: "scanner_request",
  });
  await scanNow();
});
document.getElementById("readiness-check").addEventListener("click", preflightNow);
document.getElementById("payment-verification-form").addEventListener("submit", verifyPaymentNow);
document.getElementById("refund-case-form").addEventListener("submit", createRefundCaseNow);
document.getElementById("refund-cases").addEventListener("click", updateRefundCaseStatus);
document.getElementById("role-dashboard").addEventListener("click", handleRoleDashboardClick);
document.getElementById("role-dashboard").addEventListener("input", (event) => {
  const routeFilter = event.target.closest("[data-route-filter]");
  if (routeFilter) {
    state.routeFilters[routeFilter.dataset.routeFilter] = routeFilter.value;
    renderRoleDashboard();
    return;
  }
  const utilityInput = event.target.closest("[data-utility-input]");
  if (utilityInput) {
    const key = utilityInput.dataset.utilityInput;
    if (Object.prototype.hasOwnProperty.call(state.utilityHub, key)) {
      state.utilityHub[key] = utilityInput.value;
      state.utilityHub.copied = false;
      refreshUtilityDynamicPanels();
    }
    return;
  }
  const input = event.target.closest("[data-replay-scrub]");
  if (!input) return;
  state.replayStep = Number(input.value || 0);
  stopReplayPlayback();
  renderRoleDashboard();
});
document.getElementById("role-dashboard").addEventListener("change", (event) => {
  const routeFilter = event.target.closest("[data-route-filter]");
  if (!routeFilter) return;
  state.routeFilters[routeFilter.dataset.routeFilter] = routeFilter.value;
  renderRoleDashboard();
});
document.getElementById("route-detail-modal").addEventListener("click", handleRoleDashboardClick);
document.querySelector(".wallet-strip").addEventListener("click", handleRoleDashboardClick);
document.querySelector(".nav-tabs").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-dashboard-view]");
  if (!button) return;
  const view = button.dataset.dashboardView;
  setActiveView(view);
  await recordProductAction(productActionForView(view), {
    page: view,
    evidence_source: dashboardViews[view]?.userScope || view,
  });
  if (view === "validation" && currentSession().role === "admin") {
    await loadProductValidation({ render: true });
  }
});
document.getElementById("pera-wallet-button").addEventListener("click", () => {
  toggleWalletConnection();
});
document.getElementById("close-pnet-fee-modal").addEventListener("click", closePnetFeeModal);
document.getElementById("cancel-pnet-fee").addEventListener("click", closePnetFeeModal);
document.getElementById("confirm-pnet-fee").addEventListener("click", confirmPnetFee);
document.getElementById("close-route-detail-modal").addEventListener("click", () => showModal("route-detail-modal", false));
document.getElementById("close-evidence-drawer").addEventListener("click", () => showModal("evidence-drawer", false));
document.getElementById("close-live-arm-modal").addEventListener("click", () => showModal("live-arm-modal", false));
document.getElementById("cancel-live-arm").addEventListener("click", () => showModal("live-arm-modal", false));
document.getElementById("confirm-live-arm").addEventListener("click", async () => {
  showModal("live-arm-modal", false);
  await runAdminAction("arm-live");
});
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    showModal("pnet-fee-modal", false);
    showModal("route-detail-modal", false);
    showModal("evidence-drawer", false);
    showModal("live-arm-modal", false);
  }
});
window.addEventListener("hashchange", () => setActiveView(dashboardViewFromHash()));
state.activeView = canAccessDashboardView(dashboardViewFromHash()) ? dashboardViewFromHash() : "pulse";
renderAppPhaseLabel();
renderWalletSession();
renderNavState();
renderRoleDashboard();
renderProductThesis();
renderVersionLadder();
renderPhaseGates();
renderDeploymentModes();
renderRepoRedFlags();
if (state.activeView === "access") {
  loadContributionProtocol({ render: true });
  loadCommunityGrowth({ render: true });
}
if (state.activeView === "transparency") {
  loadTransparencySystem({ render: true });
}
refresh();
state.refreshTimer = setInterval(refresh, 15000);
state.opsHeartbeatTimer = setInterval(pollOpsControlRoom, 5000);
