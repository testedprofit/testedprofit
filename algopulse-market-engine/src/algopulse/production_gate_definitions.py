from __future__ import annotations


PHASE_DEFINITIONS = [
    ("phase_0a_inventory", "Phase 0A Inventory"),
    ("phase_0b_scanner", "Phase 0B Scanner"),
    ("phase_0c_route_engine", "Phase 0C Route Engine"),
    ("phase_0d_paper_trading", "Phase 0D Paper Trading"),
    ("phase_0e_risk_engine", "Phase 0E Risk Engine"),
    ("phase_0f_live_micro", "Phase 0F Live Micro"),
    ("phase_0g_public_dash", "Phase 0G Public Dash"),
]


PRODUCTION_GATE_DEFINITIONS = [
    {
        "key": "inventory_scope",
        "phaseKey": "phase_0a_inventory",
        "label": "Inventory / Safe Scope",
        "sortOrder": 10,
        "description": "Repo, environment, and control-plane boundaries are defined before runtime gates matter.",
        "requiredEvidence": ["Safe-scope docs exist", "Production gate table seeded"],
    },
    {
        "key": "scanner_reliability",
        "phaseKey": "phase_0b_scanner",
        "label": "Scanner Reliability",
        "sortOrder": 20,
        "description": "The scanner proves read-only uptime and freshness without private key material.",
        "requiredEvidence": ["scanner uptime 24h", "scanner uptime 7d", "scanner requires no keys"],
    },
    {
        "key": "quote_engine_quality",
        "phaseKey": "phase_0c_route_engine",
        "label": "Quote Engine Quality",
        "sortOrder": 30,
        "description": "Quote rows are comparable across venues and fresh enough to be useful.",
        "requiredEvidence": ["comparable Tinyman/Pact quotes", "quote freshness under threshold"],
    },
    {
        "key": "route_risk_explainability",
        "phaseKey": "phase_0e_risk_engine",
        "label": "Route / Risk Explainability",
        "sortOrder": 40,
        "description": "Every rejected route has an explanation and a stored risk decision.",
        "requiredEvidence": ["route rejection explanations", "risk decisions recorded"],
    },
    {
        "key": "paper_trading_window",
        "phaseKey": "phase_0d_paper_trading",
        "label": "Paper Trading Window",
        "sortOrder": 50,
        "description": "Paper trading captures enough replay evidence before any production promotion.",
        "requiredEvidence": ["paper trades collected", "5s/30s rechecks complete"],
    },
    {
        "key": "dry_run_validation",
        "phaseKey": "phase_0f_live_micro",
        "label": "Unsigned Dry-Run Validation",
        "sortOrder": 60,
        "description": "Dry-run transaction groups are unsigned-only and stay within Algorand group limits.",
        "requiredEvidence": ["dry-run validation", "transaction group size guard"],
    },
    {
        "key": "signer_isolation",
        "phaseKey": "phase_0f_live_micro",
        "label": "Signer Isolation Review",
        "sortOrder": 70,
        "description": "Signer remains isolated, disabled unless explicitly reviewed, and protected by a kill switch.",
        "requiredEvidence": ["signer isolation review", "kill switch active"],
    },
    {
        "key": "manual_reconciliation",
        "phaseKey": "phase_0f_live_micro",
        "label": "Manual Trade Reconciliation",
        "sortOrder": 80,
        "description": "The first tiny manual trade must reconcile expected and actual outputs.",
        "requiredEvidence": ["manual trade reconciliation"],
    },
    {
        "key": "public_dashboard_safety",
        "phaseKey": "phase_0g_public_dash",
        "label": "Public Dashboard Safety",
        "sortOrder": 90,
        "description": "Public surfaces use delayed, source-labeled data and never expose signing authority.",
        "requiredEvidence": ["delayed public data", "source-labeled evidence"],
    },
]
