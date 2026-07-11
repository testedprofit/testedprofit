# Capability Catalog

AlgoPulse should be understood as a market engine, not just an arbitrage script. These are the eight product capabilities exposed in `GET /api/config/public` and rendered in the dashboard.

| Capability | Audience | Phase 0 Boundary |
| --- | --- | --- |
| `market_intelligence` | public, PNET users, admins | Read-only market data, quote history, freshness, route context, and paper results. |
| `scanner` | admins now; delayed public and PNET users later | Read-only Tinyman, Pact, and later Vestige/Folks market-state collection with no private key required. |
| `route_engine` | PNET users, admins | Route candidate generation with fee math, impact, confidence, and skip reasons; no execution. |
| `paper_trading` | admins, PNET report users | 5s/30s route rechecks, quote decay, simulated results, and daily reports with no real funds. |
| `risk_engine` | admins | Reject-first policy for freshness, allowlists, trade size, price impact, fees, loss limits, and route length. |
| `execution_controls` | admins only | Arm/disarm, kill switch, unsigned dry-run, signer-lock, and future tiny own-funds controls; never user deposits. |
| `public_dashboard` | public | Delayed market intelligence, source labels, receipts, and public-safe status without fresh executable routes. |
| `pnet_access_layer` | PNET users, admins | Pera wallet checks, PNET fee quotes, tx verification, credits, receipts, and delayed reports only. |

## Product Rule

The user-facing product is useful intelligence and proof, not custody. PNET user flows can buy scans, simulations, delayed route intelligence, reports, and credits. They must never be framed as deposits into the bot or permission to trade user funds.
