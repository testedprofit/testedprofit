from __future__ import annotations

import json
import math
import sqlite3
import time
from datetime import datetime
from datetime import timezone
from pathlib import Path

from algopulse.confidence_calibration import build_confidence_calibration_report
from algopulse.data_provenance import build_data_provenance_report
from algopulse.evidence_system import build_evidence_records
from algopulse.evidence_system import summarize_evidence_records
from algopulse.market_heatmap import HEATMAP_VIEWS
from algopulse.market_heatmap import build_market_pulse_heatmap
from algopulse.market_report import build_daily_market_intelligence_report
from algopulse.market_report import render_market_intelligence_markdown
from algopulse.models import Asset, Opportunity, Pool, Venue
from algopulse.opportunity_decay import build_opportunity_decay_report
from algopulse.product_validation import build_product_validation_report
from algopulse.product_validation import default_evidence_source
from algopulse.product_validation import is_decision_action
from algopulse.production_gate_definitions import PRODUCTION_GATE_DEFINITIONS
from algopulse.route_forensics import build_route_forensics


DEFAULT_BACKFILL_NETWORK_FEE = 0.006


def _average_values(values) -> float:
    numbers = [float(value) for value in values if value is not None]
    return 0.0 if not numbers else sum(numbers) / len(numbers)


def _paper_route_class(route: list[dict]) -> str:
    venues = {str(leg.get("venue") or leg.get("venue_id") or "unknown") for leg in route}
    if len(route) >= 3:
        return "triangle"
    if {"tinyman", "pact"}.issubset(venues):
        return "cross_venue_tinyman_pact"
    if len(venues) == 1:
        return "same_venue"
    return "cross_venue_other"


class MarketStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def initialize(self, *, run_backfills: bool = True) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.executescript(
                """
                create table if not exists assets (
                    asset_id integer primary key,
                    symbol text not null,
                    name text not null,
                    decimals integer not null,
                    is_verified integer not null,
                    is_allowlisted integer not null,
                    has_freeze integer not null,
                    has_clawback integer not null
                );

                create table if not exists venues (
                    venue_id text primary key,
                    name text not null,
                    kind text not null
                );

                create table if not exists pools (
                    pool_id text primary key,
                    venue_id text not null,
                    app_id integer not null,
                    asset_a_id integer not null,
                    asset_b_id integer not null,
                    fee_bps integer not null,
                    status text not null,
                    source text not null,
                    first_seen_at real not null,
                    last_seen_at real not null
                );

                create table if not exists pool_snapshots (
                    id integer primary key autoincrement,
                    pool_id text not null,
                    venue_id text not null,
                    app_id integer not null,
                    asset_a_id integer not null,
                    asset_b_id integer not null,
                    reserve_a real not null,
                    reserve_b real not null,
                    fee_bps integer not null,
                    price_a_in_b real not null,
                    price_b_in_a real not null,
                    liquidity_estimate real not null default 0,
                    block_round integer not null,
                    data_freshness_seconds real not null default 0,
                    captured_at real not null
                );

                create table if not exists opportunities (
                    id integer primary key autoincrement,
                    route_hash text not null,
                    route_json text not null,
                    input_asset_id integer not null,
                    input_amount real not null,
                    expected_final_amount real not null,
                    gross_profit real not null default 0,
                    estimated_network_fee real not null default 0,
                    total_dex_fees real not null default 0,
                    total_price_impact_bps real not null default 0,
                    slippage_buffer real not null default 0,
                    expected_net_profit real not null,
                    expected_profit_bps real not null,
                    max_price_impact_bps real not null,
                    involved_pool_ids_json text not null,
                    involved_asset_ids_json text not null,
                    status text not null,
                    skip_reason text,
                    confidence_score real not null,
                    risk_rules_json text not null,
                    created_at real not null
                );

                create table if not exists quotes (
                    id integer primary key autoincrement,
                    route_hash text,
                    opportunity_id integer,
                    leg_index integer not null,
                    pool_id text not null,
                    venue_id text not null,
                    input_asset_id integer not null,
                    output_asset_id integer not null,
                    input_amount real not null,
                    output_amount real not null,
                    fee_amount real,
                    price_impact_bps real,
                    block_round integer not null default 0,
                    captured_at real not null,
                    expires_at real not null default 0
                );

                create table if not exists risk_decisions (
                    id integer primary key autoincrement,
                    route_hash text not null,
                    opportunity_id integer,
                    approved integer not null,
                    reason text,
                    rules_json text not null,
                    policy_json text,
                    created_at real not null
                );

                create table if not exists route_forensics (
                    id integer primary key autoincrement,
                    route_hash text not null,
                    opportunity_id integer,
                    route_path_json text not null,
                    route_path_label text not null,
                    profitability_json text not null,
                    quote_freshness_json text not null,
                    price_impact_json text not null,
                    liquidity_score_json text not null,
                    risk_result_json text not null,
                    approval_decision_json text not null,
                    rejection_reason text not null,
                    confidence_calculation_json text not null,
                    decision_tree_json text not null,
                    completeness_json text not null,
                    source text not null,
                    created_at real not null
                );

                create table if not exists paper_trades (
                    id integer primary key autoincrement,
                    opportunity_hash text not null,
                    route_hash text not null,
                    opportunity_status text not null default '',
                    skip_reason text,
                    input_asset_id integer not null default 0,
                    input_amount real not null default 0,
                    expected_final_amount real not null default 0,
                    expected_net_profit real not null default 0,
                    estimated_network_fee real not null default 0,
                    slippage_buffer real not null default 0,
                    route_json text not null default '[]',
                    route_class text not null default 'unknown',
                    quote_captured_at real not null default 0,
                    check_5s_due_at real not null default 0,
                    check_30s_due_at real not null default 0,
                    check_60s_due_at real not null default 0,
                    checked_5s_at real,
                    checked_30s_at real,
                    checked_60s_at real,
                    simulated_final_amount_5s real,
                    simulated_final_amount_30s real,
                    simulated_final_amount_60s real,
                    quote_decay_5s real,
                    quote_decay_30s real,
                    quote_decay_60s real,
                    expected_vs_simulated_profit_5s real,
                    expected_vs_simulated_profit_30s real,
                    expected_vs_simulated_profit_60s real,
                    survived_5s integer,
                    survived_30s integer,
                    survived_60s integer,
                    failure_reason_5s text,
                    failure_reason_30s text,
                    failure_reason_60s text,
                    last_error text,
                    expected_profit real not null,
                    simulated_profit_5s real not null,
                    simulated_profit_30s real not null,
                    simulated_profit_60s real not null default 0,
                    confidence_score real not null default 0,
                    success integer,
                    would_execute integer not null,
                    notes text not null,
                    created_at real not null
                );

                create table if not exists opportunity_decay (
                    id integer primary key autoincrement,
                    opportunity_hash text not null,
                    detected_at real not null,
                    route_hash text not null,
                    expected_profit real not null,
                    expected_profit_5s real,
                    expected_profit_30s real,
                    expected_profit_60s real,
                    checked_5s_at real,
                    checked_30s_at real,
                    checked_60s_at real,
                    pair_key text not null,
                    pair_label text not null,
                    venues_json text not null,
                    route_type text not null,
                    route_json text not null,
                    source text not null,
                    created_at real not null
                );

                create table if not exists live_trades (
                    id integer primary key autoincrement,
                    route_hash text,
                    submitted integer not null,
                    dry_run integer not null,
                    txid text,
                    group_id_hex text,
                    tx_count integer,
                    fee_algos real,
                    conservative_profit real,
                    reason text,
                    result_json text not null,
                    created_at real not null
                );

                create table if not exists balance_reconciliations (
                    id integer primary key autoincrement,
                    live_trade_id integer,
                    route_hash text,
                    status text not null,
                    ok integer,
                    submitted integer not null,
                    dry_run integer not null,
                    expected_deltas_json text not null,
                    actual_deltas_json text,
                    variance_json text,
                    before_json text,
                    after_json text,
                    detail text,
                    created_at real not null
                );

                create table if not exists payment_verifications (
                    id integer primary key autoincrement,
                    txid text not null,
                    ok integer not null,
                    status text not null,
                    reason text,
                    asset_id integer not null,
                    expected_receiver text not null,
                    expected_amount_raw integer not null,
                    observed_sender text,
                    observed_receiver text,
                    observed_amount_raw integer,
                    confirmed_round integer,
                    confirmations integer,
                    result_json text not null,
                    created_at real not null
                );

                create table if not exists refund_cases (
                    id integer primary key autoincrement,
                    payment_verification_id integer,
                    source_txid text,
                    status text not null,
                    failure_type text not null,
                    reason text not null,
                    refund_address text,
                    asset_id integer not null,
                    asset_decimals integer not null,
                    amount_raw integer not null,
                    amount_display real not null,
                    operator_action text not null,
                    operator_note text,
                    guardrails_json text not null,
                    decision_json text not null,
                    resolution_txid text,
                    resolution_note text,
                    resolved_at real,
                    created_at real not null
                );

                create table if not exists service_health (
                    id integer primary key autoincrement,
                    service_name text not null,
                    status text not null,
                    detail text,
                    metrics_json text not null,
                    checked_at real not null
                );

                create table if not exists testnet_soak_observations (
                    id integer primary key autoincrement,
                    observation_id text not null unique,
                    run_id text not null,
                    sequence_number integer not null,
                    started_at real not null,
                    completed_at real not null,
                    network text not null,
                    source text not null,
                    payload_json text not null
                );

                create table if not exists verified_pool_registry (
                    app_id integer not null,
                    network text not null,
                    venue_id text not null,
                    asset_a_id integer not null,
                    asset_b_id integer not null,
                    fee_bps integer not null,
                    reserve_a real not null,
                    reserve_b real not null,
                    latest_round integer not null,
                    status text not null,
                    reason text not null,
                    verification_source text not null,
                    pool_id text not null default '',
                    verified_at real not null,
                    primary key (network, app_id)
                );

                create table if not exists alerts (
                    id integer primary key autoincrement,
                    severity text not null,
                    source text not null,
                    title text not null,
                    detail text,
                    status text not null,
                    route_hash text,
                    created_at real not null,
                    resolved_at real
                );

                create table if not exists production_gates (
                    gate_key text primary key,
                    phase_key text not null,
                    label text not null,
                    sort_order integer not null,
                    description text not null,
                    required_evidence_json text not null,
                    created_at real not null,
                    updated_at real not null
                );

                create table if not exists production_evidence (
                    id integer primary key autoincrement,
                    gate_key text not null,
                    evidence_key text not null,
                    label text not null,
                    status text not null,
                    value text not null,
                    detail text not null,
                    source text not null,
                    evidence_url text,
                    observed_at real not null,
                    metadata_json text not null
                );

                create table if not exists evidence_records (
                    evidence_id text primary key,
                    service text not null,
                    category text not null,
                    title text not null,
                    summary text not null,
                    status text not null,
                    created_at real not null,
                    metadata_json text not null
                );

                create table if not exists market_intelligence_reports (
                    id integer primary key autoincrement,
                    report_date text not null,
                    window_start real not null,
                    window_end real not null,
                    source text not null,
                    report_json text not null,
                    markdown text not null,
                    generated_at real not null
                );

                create table if not exists user_actions (
                    id integer primary key autoincrement,
                    action_type text not null,
                    timestamp real not null,
                    user_role text not null,
                    wallet_connected integer not null,
                    source_page text not null,
                    metadata_json text not null
                );

                create table if not exists decision_events (
                    decision_id text primary key,
                    action_type text not null,
                    user_role text not null,
                    page text not null,
                    evidence_source text not null,
                    created_at real not null
                );

                create index if not exists idx_pools_pair on pools(asset_a_id, asset_b_id);
                create index if not exists idx_pool_snapshots_pool_time on pool_snapshots(pool_id, captured_at);
                create index if not exists idx_quotes_route_hash on quotes(route_hash);
                create index if not exists idx_risk_decisions_route_hash on risk_decisions(route_hash);
                create index if not exists idx_route_forensics_route_hash on route_forensics(route_hash);
                create unique index if not exists idx_route_forensics_opportunity_id
                    on route_forensics(opportunity_id);
                create index if not exists idx_service_health_name_time on service_health(service_name, checked_at);
                create index if not exists idx_testnet_soak_run_seq on testnet_soak_observations(run_id, sequence_number);
                create index if not exists idx_testnet_soak_completed on testnet_soak_observations(completed_at);
                create index if not exists idx_verified_pool_registry_status
                    on verified_pool_registry(network, status);
                create index if not exists idx_alerts_status_severity on alerts(status, severity);
                create index if not exists idx_production_evidence_gate_time on production_evidence(gate_key, observed_at);
                create unique index if not exists idx_production_evidence_latest on production_evidence(gate_key, evidence_key);
                create index if not exists idx_evidence_records_category_status
                    on evidence_records(category, status);
                create index if not exists idx_evidence_records_service_status
                    on evidence_records(service, status);
                create unique index if not exists idx_market_intelligence_reports_date on market_intelligence_reports(report_date);
                create unique index if not exists idx_opportunity_decay_hash on opportunity_decay(opportunity_hash);
                create index if not exists idx_opportunity_decay_detected_at on opportunity_decay(detected_at);
                create index if not exists idx_opportunity_decay_pair on opportunity_decay(pair_key, detected_at);
                create index if not exists idx_user_actions_type_time on user_actions(action_type, timestamp);
                create index if not exists idx_user_actions_role_time on user_actions(user_role, timestamp);
                create index if not exists idx_decision_events_type_time on decision_events(action_type, created_at);
                create index if not exists idx_decision_events_page_time on decision_events(page, created_at);
                """
            )
            self._ensure_column(con, "pool_snapshots", "liquidity_estimate", "real not null default 0")
            self._ensure_column(con, "pool_snapshots", "data_freshness_seconds", "real not null default 0")
            self._ensure_column(con, "quotes", "block_round", "integer not null default 0")
            self._ensure_column(con, "quotes", "expires_at", "real not null default 0")
            self._ensure_column(con, "opportunities", "gross_profit", "real not null default 0")
            self._ensure_column(con, "opportunities", "estimated_network_fee", "real not null default 0")
            self._ensure_column(con, "opportunities", "total_dex_fees", "real not null default 0")
            self._ensure_column(con, "opportunities", "total_price_impact_bps", "real not null default 0")
            self._ensure_column(con, "opportunities", "slippage_buffer", "real not null default 0")
            if run_backfills:
                self._backfill_opportunity_breakdowns(con)
            self._ensure_column(con, "paper_trades", "opportunity_status", "text not null default ''")
            self._ensure_column(con, "paper_trades", "skip_reason", "text")
            self._ensure_column(con, "paper_trades", "input_asset_id", "integer not null default 0")
            self._ensure_column(con, "paper_trades", "input_amount", "real not null default 0")
            self._ensure_column(con, "paper_trades", "expected_final_amount", "real not null default 0")
            self._ensure_column(con, "paper_trades", "expected_net_profit", "real not null default 0")
            self._ensure_column(con, "paper_trades", "estimated_network_fee", "real not null default 0")
            self._ensure_column(con, "paper_trades", "slippage_buffer", "real not null default 0")
            self._ensure_column(con, "paper_trades", "route_json", "text not null default '[]'")
            self._ensure_column(con, "paper_trades", "route_class", "text not null default 'unknown'")
            self._ensure_column(con, "paper_trades", "quote_captured_at", "real not null default 0")
            self._ensure_column(con, "paper_trades", "check_5s_due_at", "real not null default 0")
            self._ensure_column(con, "paper_trades", "check_30s_due_at", "real not null default 0")
            self._ensure_column(con, "paper_trades", "check_60s_due_at", "real not null default 0")
            self._ensure_column(con, "paper_trades", "checked_5s_at", "real")
            self._ensure_column(con, "paper_trades", "checked_30s_at", "real")
            self._ensure_column(con, "paper_trades", "checked_60s_at", "real")
            self._ensure_column(con, "paper_trades", "simulated_final_amount_5s", "real")
            self._ensure_column(con, "paper_trades", "simulated_final_amount_30s", "real")
            self._ensure_column(con, "paper_trades", "simulated_final_amount_60s", "real")
            self._ensure_column(con, "paper_trades", "quote_decay_5s", "real")
            self._ensure_column(con, "paper_trades", "quote_decay_30s", "real")
            self._ensure_column(con, "paper_trades", "quote_decay_60s", "real")
            self._ensure_column(con, "paper_trades", "expected_vs_simulated_profit_5s", "real")
            self._ensure_column(con, "paper_trades", "expected_vs_simulated_profit_30s", "real")
            self._ensure_column(con, "paper_trades", "expected_vs_simulated_profit_60s", "real")
            self._ensure_column(con, "paper_trades", "survived_5s", "integer")
            self._ensure_column(con, "paper_trades", "survived_30s", "integer")
            self._ensure_column(con, "paper_trades", "survived_60s", "integer")
            self._ensure_column(con, "paper_trades", "failure_reason_5s", "text")
            self._ensure_column(con, "paper_trades", "failure_reason_30s", "text")
            self._ensure_column(con, "paper_trades", "failure_reason_60s", "text")
            self._ensure_column(con, "paper_trades", "last_error", "text")
            self._ensure_column(con, "paper_trades", "simulated_profit_60s", "real not null default 0")
            self._ensure_column(con, "paper_trades", "confidence_score", "real not null default 0")
            self._ensure_column(con, "paper_trades", "success", "integer")
            if run_backfills:
                self._backfill_paper_calibration(con)
                self._backfill_opportunity_decay(con)
            self._seed_production_gates(con)
            if run_backfills:
                self._backfill_route_forensics(con)

    def has_market_data(self) -> bool:
        with self._connect() as con:
            row = con.execute("select count(*) as count from pool_snapshots").fetchone()
            return bool(row["count"])

    def list_production_gates(self) -> list[dict]:
        with self._connect() as con:
            rows = con.execute(
                """
                select *
                from production_gates
                order by sort_order asc
                """
            ).fetchall()
        return [
            {
                "key": row["gate_key"],
                "phaseKey": row["phase_key"],
                "label": row["label"],
                "sortOrder": int(row["sort_order"]),
                "description": row["description"],
                "requiredEvidence": json.loads(row["required_evidence_json"]),
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"],
            }
            for row in rows
        ]

    def record_production_evidence(self, evidence: list[dict]) -> None:
        if not evidence:
            return
        with self._connect() as con:
            con.executemany(
                """
                insert into production_evidence (
                    gate_key, evidence_key, label, status, value, detail,
                    source, evidence_url, observed_at, metadata_json
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(gate_key, evidence_key) do update set
                    label=excluded.label,
                    status=excluded.status,
                    value=excluded.value,
                    detail=excluded.detail,
                    source=excluded.source,
                    evidence_url=excluded.evidence_url,
                    observed_at=excluded.observed_at,
                    metadata_json=excluded.metadata_json
                """,
                [
                    (
                        item["gateKey"],
                        item["evidenceKey"],
                        item["label"],
                        item["status"],
                        str(item.get("value", "")),
                        item.get("detail", ""),
                        item.get("source", "unavailable"),
                        item.get("evidenceUrl"),
                        float(item.get("observedAt") or time.time()),
                        json.dumps(item.get("metadata") or {}, sort_keys=True),
                    )
                    for item in evidence
                ],
            )

    def list_production_evidence(self) -> list[dict]:
        with self._connect() as con:
            rows = con.execute(
                """
                select *
                from production_evidence
                order by gate_key asc, evidence_key asc
                """
            ).fetchall()
        return [
            {
                "gateKey": row["gate_key"],
                "evidenceKey": row["evidence_key"],
                "label": row["label"],
                "status": row["status"],
                "value": row["value"],
                "detail": row["detail"],
                "source": row["source"],
                "evidenceUrl": row["evidence_url"],
                "observedAt": float(row["observed_at"]),
                "metadata": json.loads(row["metadata_json"] or "{}"),
            }
            for row in rows
        ]

    def evidence_records_report(
        self,
        settings,
        *,
        category: str | None = None,
        service: str | None = None,
        status: str | None = None,
        now: float | None = None,
    ) -> dict:
        generated_at = float(now or time.time())
        metrics = self.production_readiness_metrics(now=generated_at)
        system_state = self._evidence_system_state(settings)
        generated_records = build_evidence_records(metrics=metrics, system_state=system_state, now=generated_at)
        self.record_evidence_records(generated_records)
        all_records = self.list_evidence_records()
        filtered_records = self.list_evidence_records(category=category, service=service, status=status)
        return {
            "records": filtered_records,
            "count": len(filtered_records),
            "summary": summarize_evidence_records(all_records),
            "filteredSummary": summarize_evidence_records(filtered_records),
            "filters": {
                "category": category or "all",
                "service": service or "all",
                "status": status or "all",
            },
            "services": sorted({item["service"] for item in all_records}),
            "categories": sorted({item["category"] for item in all_records}),
            "statuses": sorted({item["status"] for item in all_records}),
            "generatedAt": generated_at,
            "source": "stored" if all_records else "unavailable",
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
        }

    def record_user_action(
        self,
        *,
        action_type: str,
        user_role: str,
        wallet_connected: bool,
        source_page: str,
        metadata: dict | None = None,
        timestamp: float | None = None,
    ) -> dict:
        observed_at = float(timestamp or time.time())
        metadata_payload = metadata or {}
        metadata_json = json.dumps(metadata_payload, sort_keys=True)
        with self._connect() as con:
            cursor = con.execute(
                """
                insert into user_actions (
                    action_type, timestamp, user_role, wallet_connected, source_page, metadata_json
                )
                values (?, ?, ?, ?, ?, ?)
                """,
                (
                    action_type,
                    observed_at,
                    user_role,
                    int(bool(wallet_connected)),
                    source_page,
                    metadata_json,
                ),
            )
            action_id = int(cursor.lastrowid)
            decision_id = None
            if is_decision_action(action_type):
                evidence_source = str(
                    metadata_payload.get("evidence_source")
                    or metadata_payload.get("evidenceSource")
                    or default_evidence_source(action_type)
                )
                decision_id = f"decision_{int(observed_at * 1000)}_{action_id}"
                con.execute(
                    """
                    insert into decision_events (
                        decision_id, action_type, user_role, page, evidence_source, created_at
                    )
                    values (?, ?, ?, ?, ?, ?)
                    """,
                    (decision_id, action_type, user_role, source_page, evidence_source, observed_at),
                )
        return {
            "actionId": action_id,
            "actionType": action_type,
            "decisionRecorded": decision_id is not None,
            "decisionId": decision_id,
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
        }

    def product_validation_report(self, window_days: int = 30, now: float | None = None) -> dict:
        with self._connect() as con:
            actions = con.execute(
                """
                select *
                from user_actions
                order by timestamp desc, id desc
                """
            ).fetchall()
            decisions = con.execute(
                """
                select *
                from decision_events
                order by created_at desc
                """
            ).fetchall()
        return build_product_validation_report(
            [dict(row) for row in actions],
            [dict(row) for row in decisions],
            window_days=window_days,
            now=now,
        )

    def record_evidence_records(self, records: list[dict]) -> None:
        if not records:
            return
        with self._connect() as con:
            con.executemany(
                """
                insert into evidence_records (
                    evidence_id, service, category, title, summary,
                    status, created_at, metadata_json
                )
                values (?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(evidence_id) do update set
                    service=excluded.service,
                    category=excluded.category,
                    title=excluded.title,
                    summary=excluded.summary,
                    status=excluded.status,
                    created_at=excluded.created_at,
                    metadata_json=excluded.metadata_json
                """,
                [
                    (
                        item["evidenceId"],
                        item["service"],
                        item["category"],
                        item["title"],
                        item["summary"],
                        item["status"],
                        float(item["createdAt"]),
                        json.dumps(item.get("metadata") or {}, sort_keys=True),
                    )
                    for item in records
                ],
            )

    def list_evidence_records(
        self,
        *,
        category: str | None = None,
        service: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[str] = []
        if category and category != "all":
            clauses.append("category = ?")
            params.append(category)
        if service and service != "all":
            clauses.append("service = ?")
            params.append(service)
        if status and status != "all":
            clauses.append("status = ?")
            params.append(status)
        where = f"where {' and '.join(clauses)}" if clauses else ""
        with self._connect() as con:
            rows = con.execute(
                f"""
                select *
                from evidence_records
                {where}
                order by
                    case status
                        when 'fail' then 0
                        when 'warn' then 1
                        when 'pending' then 2
                        when 'pass' then 3
                        else 4
                    end,
                    category asc,
                    service asc,
                    title asc
                """,
                params,
            ).fetchall()
        return [self._row_to_evidence_record(row) for row in rows]

    def production_readiness_metrics(self, now: float | None = None) -> dict:
        current_time = float(now or time.time())
        with self._connect() as con:
            scanner = con.execute(
                """
                select
                    count(*) as snapshot_count,
                    count(distinct pool_id) as pool_count,
                    min(captured_at) as first_seen_at,
                    max(captured_at) as last_seen_at,
                    count(distinct date(captured_at, 'unixepoch')) as days_seen
                from pool_snapshots
                """
            ).fetchone()
            quotes = con.execute(
                """
                select
                    count(*) as quote_count,
                    count(distinct venue_id) as venue_count,
                    max(captured_at) as last_quote_at,
                    coalesce(sum(case when expires_at >= ? then 1 else 0 end), 0) as fresh_count,
                    coalesce(avg(price_impact_bps), 0) as avg_price_impact_bps
                from quotes
                """,
                (current_time,),
            ).fetchone()
            opportunities = con.execute(
                """
                select
                    count(*) as opportunity_count,
                    coalesce(sum(case when status != 'approved' then 1 else 0 end), 0) as rejected_count,
                    coalesce(sum(case when status != 'approved' and skip_reason is not null and skip_reason != '' then 1 else 0 end), 0)
                        as rejected_with_reason_count,
                    coalesce(sum(case when status = 'approved' then 1 else 0 end), 0) as approved_count
                from opportunities
                """
            ).fetchone()
            risk = con.execute(
                """
                select
                    count(*) as risk_decision_count,
                    coalesce(sum(case when approved = 0 then 1 else 0 end), 0) as rejected_decision_count
                from risk_decisions
                """
            ).fetchone()
            paper = con.execute(
                """
                select
                    count(*) as paper_count,
                    count(distinct date(created_at, 'unixepoch')) as days_collected,
                    coalesce(sum(case when checked_5s_at is not null then 1 else 0 end), 0) as checked_5s_count,
                    coalesce(sum(case when checked_30s_at is not null then 1 else 0 end), 0) as checked_30s_count
                from paper_trades
                """
            ).fetchone()
            live = con.execute(
                """
                select
                    coalesce(sum(case when dry_run = 1 then 1 else 0 end), 0) as dry_run_count,
                    coalesce(sum(case when dry_run = 1 and coalesce(tx_count, 0) <= 16 then 1 else 0 end), 0) as dry_run_group_size_ok_count,
                    coalesce(sum(case when submitted = 1 then 1 else 0 end), 0) as submitted_count
                from live_trades
                """
            ).fetchone()
            reconciliations = con.execute(
                """
                select
                    count(*) as reconciliation_count,
                    coalesce(sum(case when submitted = 1 and ok = 1 then 1 else 0 end), 0) as manual_ok_count,
                    coalesce(sum(case when ok = 0 then 1 else 0 end), 0) as mismatch_count
                from balance_reconciliations
                """
            ).fetchone()

        first_seen = scanner["first_seen_at"]
        last_seen = scanner["last_seen_at"]
        last_quote_at = quotes["last_quote_at"]
        scanner_span = max(0.0, float(last_seen or 0.0) - float(first_seen or 0.0)) if first_seen and last_seen else 0.0
        latest_scan_age = max(0.0, current_time - float(last_seen)) if last_seen else None
        latest_quote_age = max(0.0, current_time - float(last_quote_at)) if last_quote_at else None
        paper_count = int(paper["paper_count"] or 0)
        checked_30s = int(paper["checked_30s_count"] or 0)
        return {
            "now": current_time,
            "scanner": {
                "snapshotCount": int(scanner["snapshot_count"] or 0),
                "poolCount": int(scanner["pool_count"] or 0),
                "firstSeenAt": float(first_seen) if first_seen else None,
                "lastSeenAt": float(last_seen) if last_seen else None,
                "spanSeconds": scanner_span,
                "latestAgeSeconds": latest_scan_age,
                "daysSeen": int(scanner["days_seen"] or 0),
            },
            "quotes": {
                "quoteCount": int(quotes["quote_count"] or 0),
                "venueCount": int(quotes["venue_count"] or 0),
                "freshCount": int(quotes["fresh_count"] or 0),
                "lastQuoteAt": float(last_quote_at) if last_quote_at else None,
                "latestAgeSeconds": latest_quote_age,
                "avgPriceImpactBps": float(quotes["avg_price_impact_bps"] or 0.0),
            },
            "opportunities": {
                "opportunityCount": int(opportunities["opportunity_count"] or 0),
                "approvedCount": int(opportunities["approved_count"] or 0),
                "rejectedCount": int(opportunities["rejected_count"] or 0),
                "rejectedWithReasonCount": int(opportunities["rejected_with_reason_count"] or 0),
            },
            "risk": {
                "riskDecisionCount": int(risk["risk_decision_count"] or 0),
                "rejectedDecisionCount": int(risk["rejected_decision_count"] or 0),
            },
            "paper": {
                "paperCount": paper_count,
                "daysCollected": int(paper["days_collected"] or 0),
                "checked5sCount": int(paper["checked_5s_count"] or 0),
                "checked30sCount": checked_30s,
                "completionRate30s": (checked_30s / paper_count) if paper_count else 0.0,
            },
            "dryRun": {
                "dryRunCount": int(live["dry_run_count"] or 0),
                "dryRunGroupSizeOkCount": int(live["dry_run_group_size_ok_count"] or 0),
                "submittedCount": int(live["submitted_count"] or 0),
            },
            "reconciliation": {
                "reconciliationCount": int(reconciliations["reconciliation_count"] or 0),
                "manualOkCount": int(reconciliations["manual_ok_count"] or 0),
                "mismatchCount": int(reconciliations["mismatch_count"] or 0),
            },
        }

    def read_only_staging_report(
        self,
        *,
        now: float | None = None,
        window_seconds: int = 24 * 60 * 60,
        max_quote_age_seconds: float = 5.0,
    ) -> dict:
        current_time = float(now or time.time())
        safe_window = max(60, int(window_seconds))
        cutoff = current_time - safe_window
        with self._connect() as con:
            scanner = con.execute(
                """
                select
                    count(*) as snapshot_count,
                    count(distinct pool_id) as pool_count,
                    min(captured_at) as first_snapshot_at,
                    max(captured_at) as latest_snapshot_at
                from pool_snapshots
                where captured_at >= ?
                """,
                (cutoff,),
            ).fetchone()
            routes = con.execute(
                """
                select
                    count(*) as candidate_count,
                    coalesce(sum(case when status = 'approved' then 1 else 0 end), 0) as approved_count,
                    coalesce(sum(case when status != 'approved' then 1 else 0 end), 0) as rejected_count
                from opportunities
                where created_at >= ?
                """,
                (cutoff,),
            ).fetchone()
            rejection_rows = con.execute(
                """
                select coalesce(skip_reason, 'unknown') as reason, count(*) as count
                from opportunities
                where created_at >= ? and status != 'approved'
                group by coalesce(skip_reason, 'unknown')
                order by count desc, reason asc
                """,
                (cutoff,),
            ).fetchall()
            risk = con.execute(
                """
                select
                    count(*) as decision_count,
                    coalesce(sum(case when approved = 1 then 1 else 0 end), 0) as approved_count,
                    coalesce(sum(case when approved = 0 then 1 else 0 end), 0) as rejected_count
                from risk_decisions
                where created_at >= ?
                """,
                (cutoff,),
            ).fetchone()

        first_snapshot = scanner["first_snapshot_at"]
        latest_snapshot = scanner["latest_snapshot_at"]
        uptime_seconds = (
            max(0.0, float(latest_snapshot) - float(first_snapshot))
            if first_snapshot and latest_snapshot
            else 0.0
        )
        quote_freshness = self.quote_freshness_evidence(
            max_age_seconds=max_quote_age_seconds,
            now=current_time,
            limit=100,
        )
        connectors = self.connector_reliability_evidence(
            lookback_seconds=safe_window,
            now=current_time,
            max_quote_age_seconds=max_quote_age_seconds,
        )
        paper = self.paper_trading_evidence_summary(limit=25, lookback_seconds=safe_window)
        decay = self.opportunity_decay_dashboard(view="24h", now=current_time)
        connector_rollup = connectors.get("readinessRollup") or {}
        blockers = self._read_only_staging_blockers(
            scanner_pool_count=int(scanner["pool_count"] or 0),
            quote_freshness=quote_freshness,
            connectors=connectors,
            routes=routes,
            paper=paper,
            risk=risk,
        )
        evidence_samples = self._read_only_staging_evidence_samples(
            cutoff=cutoff,
            quote_freshness=quote_freshness,
            connectors=connectors,
            paper=paper,
        )
        return {
            "source": "stored" if int(scanner["snapshot_count"] or 0) or quote_freshness["quoteCount"] else "unavailable",
            "mode": "read_only_staging",
            "windowSeconds": safe_window,
            "generatedAt": current_time,
            "status": "blocked" if blockers else "ready_for_staging_review",
            "scanner": {
                "uptimeSeconds": uptime_seconds,
                "uptimePercent": min(100.0, (uptime_seconds / safe_window) * 100.0),
                "snapshotCount": int(scanner["snapshot_count"] or 0),
                "poolsMonitored": int(scanner["pool_count"] or 0),
                "firstSnapshotAt": float(first_snapshot) if first_snapshot else None,
                "latestSnapshotAt": float(latest_snapshot) if latest_snapshot else None,
            },
            "quotes": {
                "recorded": int(quote_freshness["quoteCount"]),
                "fresh": int(quote_freshness["freshQuoteCount"]),
                "aging": int(quote_freshness["agingQuoteCount"]),
                "stale": int(quote_freshness["staleQuoteCount"]),
                "unavailable": int(quote_freshness["unavailableQuoteCount"]),
                "rejectedReasons": quote_freshness["rejectedReasons"],
            },
            "connectors": {
                "okCount": int(connector_rollup.get("okCount") or 0),
                "degradedCount": int(connector_rollup.get("degradedCount") or 0),
                "downCount": int(connector_rollup.get("downCount") or 0),
                "staleCount": int(connector_rollup.get("staleCount") or 0),
                "mockCount": int(connector_rollup.get("mockCount") or 0),
                "overallReadiness": connector_rollup.get("overallReadiness", "blocked"),
                "blockedReasons": connector_rollup.get("blockedReasons", []),
                "waitReasons": connector_rollup.get("waitReasons", []),
            },
            "routes": {
                "candidateCount": int(routes["candidate_count"] or 0),
                "approvedCount": int(routes["approved_count"] or 0),
                "rejectedCount": int(routes["rejected_count"] or 0),
                "rejectedByReason": [
                    {"reason": row["reason"], "count": int(row["count"] or 0)}
                    for row in rejection_rows
                ],
            },
            "risk": {
                "decisionCount": int(risk["decision_count"] or 0),
                "approvedCount": int(risk["approved_count"] or 0),
                "rejectedCount": int(risk["rejected_count"] or 0),
            },
            "paper": {
                "tradeCount": int(paper["candidateCount"]),
                "checked5sCount": int(paper["checked5sCount"]),
                "checked30sCount": int(paper["checked30sCount"]),
                "survivedT5Count": int(decay["summary"].get("survivedT5Count") or 0),
                "survivedT30Count": int(decay["summary"].get("survivedT30Count") or 0),
                "averageQuoteDecay5s": float(paper["averageQuoteDecay5s"]),
                "averageQuoteDecay30s": float(paper["averageQuoteDecay30s"]),
                "complete": bool(paper["candidateCount"] and paper["checked30sCount"]),
            },
            "evidenceSamples": evidence_samples,
            "blockers": blockers,
            "nextRequiredGate": self._read_only_staging_next_gate(blockers),
            "liveExecutionRequired": False,
            "dryRunRequired": False,
        }

    def _read_only_staging_evidence_samples(
        self,
        *,
        cutoff: float,
        quote_freshness: dict,
        connectors: dict,
        paper: dict,
        limit: int = 5,
    ) -> dict:
        safe_limit = max(1, min(10, int(limit)))
        with self._connect() as con:
            scanner_rows = con.execute(
                """
                select
                    pool_id, venue_id, app_id, asset_a_id, asset_b_id,
                    liquidity_estimate, block_round, data_freshness_seconds,
                    captured_at
                from pool_snapshots
                where captured_at >= ?
                order by captured_at desc, id desc
                limit ?
                """,
                (cutoff, safe_limit),
            ).fetchall()
            route_rows = con.execute(
                """
                select
                    route_hash, input_asset_id, input_amount,
                    expected_final_amount, expected_net_profit,
                    expected_profit_bps, status, skip_reason,
                    confidence_score, created_at
                from opportunities
                where created_at >= ?
                order by created_at desc, id desc
                limit ?
                """,
                (cutoff, safe_limit),
            ).fetchall()
            risk_rows = con.execute(
                """
                select
                    route_hash, opportunity_id, approved, reason,
                    rules_json, created_at
                from risk_decisions
                where created_at >= ?
                order by created_at desc, id desc
                limit ?
                """,
                (cutoff, safe_limit),
            ).fetchall()

        scanner_samples = [
            {
                "poolId": row["pool_id"],
                "venueId": row["venue_id"],
                "appId": int(row["app_id"] or 0),
                "assetAId": int(row["asset_a_id"] or 0),
                "assetBId": int(row["asset_b_id"] or 0),
                "liquidityEstimate": float(row["liquidity_estimate"] or 0.0),
                "blockRound": int(row["block_round"] or 0),
                "dataFreshnessSeconds": float(row["data_freshness_seconds"] or 0.0),
                "capturedAt": float(row["captured_at"] or 0.0),
                "source": "stored",
            }
            for row in scanner_rows
        ]
        route_samples = [
            {
                "routeHash": row["route_hash"],
                "inputAssetId": int(row["input_asset_id"] or 0),
                "inputAmount": float(row["input_amount"] or 0.0),
                "expectedFinalAmount": float(row["expected_final_amount"] or 0.0),
                "expectedNetProfit": float(row["expected_net_profit"] or 0.0),
                "expectedProfitBps": float(row["expected_profit_bps"] or 0.0),
                "status": row["status"],
                "skipReason": row["skip_reason"],
                "confidenceScore": float(row["confidence_score"] or 0.0),
                "createdAt": float(row["created_at"] or 0.0),
                "source": "stored",
            }
            for row in route_rows
        ]
        risk_samples = []
        for row in risk_rows:
            approved = bool(row["approved"])
            rules = self._safe_json_loads(row["rules_json"], {})
            failed_rules = [key for key, value in sorted(rules.items()) if value is False]
            risk_samples.append(
                {
                    "routeHash": row["route_hash"],
                    "opportunityId": row["opportunity_id"],
                    "approved": approved,
                    "decision": "approved" if approved else "rejected",
                    "reason": "approved" if approved else (row["reason"] or "missing_rejection_reason"),
                    "failedRuleKeys": failed_rules,
                    "createdAt": float(row["created_at"] or 0.0),
                    "source": "stored",
                }
            )
        paper_samples = [
            {
                "paperTradeId": item["paperTradeId"],
                "routeHash": item["routeHash"],
                "detectedAt": item["detectedAt"],
                "inputAmount": item["inputAmount"],
                "expectedProfit": item["expectedProfit"],
                "t5SimulatedProfit": item["t5SimulatedProfit"],
                "t30SimulatedProfit": item["t30SimulatedProfit"],
                "quoteDecay5s": item["quoteDecay5s"],
                "quoteDecay30s": item["quoteDecay30s"],
                "survivedT5": None if item["t5SimulatedProfit"] is None else item["t5SimulatedProfit"] > 0,
                "survivedT30": None if item["t30SimulatedProfit"] is None else item["t30SimulatedProfit"] > 0,
                "wouldExecute": item["wouldExecute"],
                "skipOrFailureReason": item["skipOrFailureReason"],
                "source": item["source"],
            }
            for item in paper.get("recentEvidence", [])[:safe_limit]
        ]
        has_samples = any(
            (
                scanner_samples,
                quote_freshness.get("quotes"),
                connectors.get("connectors"),
                route_samples,
                risk_samples,
                paper_samples,
            )
        )
        samples = {
            "source": "stored" if has_samples else "unavailable",
            "maxSamplesPerType": safe_limit,
            "scannerUptime": scanner_samples,
            "quoteFreshness": list(quote_freshness.get("quotes", []))[:safe_limit],
            "connectorState": [
                {
                    "connectorName": item.get("connectorName"),
                    "connectorType": item.get("connectorType"),
                    "status": item.get("status"),
                    "readinessImpact": item.get("readinessImpact"),
                    "productionReady": item.get("productionReady"),
                    "degradationReason": item.get("degradationReason"),
                    "freshCount24h": int(item.get("freshCount24h") or 0),
                    "staleCount24h": int(item.get("staleCount24h") or 0),
                    "errorCount24h": int(item.get("errorCount24h") or 0),
                    "lastSuccessAt": item.get("lastSuccessAt"),
                    "lastFailureAt": item.get("lastFailureAt"),
                    "source": "stored",
                }
                for item in connectors.get("connectors", [])[:safe_limit]
            ],
            "routeDecisions": route_samples,
            "riskDecisions": risk_samples,
            "paperTradeSurvival": paper_samples,
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
        }
        return samples

    def _read_only_staging_blockers(
        self,
        *,
        scanner_pool_count: int,
        quote_freshness: dict,
        connectors: dict,
        routes: sqlite3.Row,
        paper: dict,
        risk: sqlite3.Row,
    ) -> list[dict]:
        blockers: list[dict] = []
        if scanner_pool_count <= 0:
            blockers.append({"code": "scanner_no_pools", "detail": "No pool snapshots are stored in the report window."})
        if int(quote_freshness["staleQuoteCount"]) > 0:
            blockers.append({"code": "stale_quotes_present", "detail": "Stale quotes must be rejected before staging readiness."})
        if int(quote_freshness["unavailableQuoteCount"]) > 0:
            blockers.append({"code": "unavailable_quotes_present", "detail": "Quotes with missing capture metadata are not readiness evidence."})
        connector_rollup = connectors.get("readinessRollup") or {}
        if int(connector_rollup.get("downCount") or 0) > 0:
            blockers.append({"code": "connector_down", "detail": "At least one connector is down."})
        if connectors.get("blocksReadiness"):
            blockers.append({"code": "connector_blocks_readiness", "detail": "Connector evidence blocks staging readiness."})
        if int(routes["candidate_count"] or 0) <= 0:
            blockers.append({"code": "no_route_candidates", "detail": "No route candidates are stored in the report window."})
        if int(risk["decision_count"] or 0) <= 0:
            blockers.append({"code": "no_risk_decisions", "detail": "No risk decisions are stored in the report window."})
        if int(paper["candidateCount"] or 0) <= 0:
            blockers.append({"code": "missing_paper_evidence", "detail": "No paper-trading candidates are stored in the report window."})
        elif int(paper["checked30sCount"] or 0) <= 0:
            blockers.append({"code": "missing_t30_paper_evidence", "detail": "Paper trades need T+30s checks before staging review."})
        return blockers

    def _read_only_staging_next_gate(self, blockers: list[dict]) -> str:
        if not blockers:
            return "24h read-only staging review"
        priority = [
            "scanner_no_pools",
            "connector_down",
            "connector_blocks_readiness",
            "stale_quotes_present",
            "unavailable_quotes_present",
            "no_route_candidates",
            "no_risk_decisions",
            "missing_paper_evidence",
            "missing_t30_paper_evidence",
        ]
        labels = {
            "scanner_no_pools": "collect scanner pool snapshots",
            "connector_down": "restore connector reliability",
            "connector_blocks_readiness": "clear connector readiness blockers",
            "stale_quotes_present": "stabilize fresh quote capture",
            "unavailable_quotes_present": "fix quote capture metadata",
            "no_route_candidates": "generate route candidates",
            "no_risk_decisions": "record risk decisions",
            "missing_paper_evidence": "collect paper-trading evidence",
            "missing_t30_paper_evidence": "complete T+30 paper checks",
        }
        blocker_codes = {item["code"] for item in blockers}
        for code in priority:
            if code in blocker_codes:
                return labels[code]
        return "review read-only blockers"

    def _evidence_system_state(self, settings) -> dict:
        with self._connect() as con:
            forensics_rows = con.execute("select completeness_json from route_forensics").fetchall()
            payment = con.execute("select count(*) as count from payment_verifications").fetchone()
            reports = con.execute(
                """
                select count(*) as count, max(report_date) as latest_report_date
                from market_intelligence_reports
                """
            ).fetchone()
        complete_count = 0
        for row in forensics_rows:
            try:
                if json.loads(row["completeness_json"] or "{}").get("complete"):
                    complete_count += 1
            except json.JSONDecodeError:
                continue
        return {
            "routeForensicsCount": len(forensics_rows),
            "routeForensicsCompleteCount": complete_count,
            "paymentVerificationCount": int(payment["count"] or 0),
            "marketReportCount": int(reports["count"] or 0),
            "latestMarketReportDate": reports["latest_report_date"],
            "maxRouteAgeSeconds": float(settings.max_route_age_seconds),
            "allowedAssetCount": len(settings.allowed_asset_ids),
            "allowedAppCount": len(settings.allowed_app_ids),
            "requireAppIdAllowlist": bool(settings.require_app_id_allowlist),
            "enableLiveExecution": bool(settings.enable_live_execution),
            "executeApproved": bool(settings.execute_approved),
            "signerEnabled": bool(settings.signer_enabled),
            "signerKillSwitch": bool(settings.signer_kill_switch),
        }

    def _row_to_evidence_record(self, row: sqlite3.Row) -> dict:
        return {
            "evidenceId": row["evidence_id"],
            "service": row["service"],
            "category": row["category"],
            "title": row["title"],
            "summary": row["summary"],
            "status": row["status"],
            "createdAt": float(row["created_at"]),
            "metadata": json.loads(row["metadata_json"] or "{}"),
        }

    def upsert_assets(self, assets: list[Asset]) -> None:
        with self._connect() as con:
            con.executemany(
                """
                insert into assets values (?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(asset_id) do update set
                    symbol=excluded.symbol,
                    name=excluded.name,
                    decimals=excluded.decimals,
                    is_verified=excluded.is_verified,
                    is_allowlisted=excluded.is_allowlisted,
                    has_freeze=excluded.has_freeze,
                    has_clawback=excluded.has_clawback
                """,
                [
                    (
                        asset.asset_id,
                        asset.symbol,
                        asset.name,
                        asset.decimals,
                        int(asset.is_verified),
                        int(asset.is_allowlisted),
                        int(asset.has_freeze),
                        int(asset.has_clawback),
                    )
                    for asset in assets
                ],
            )

    def upsert_venues(self, venues: list[Venue]) -> None:
        with self._connect() as con:
            con.executemany(
                """
                insert into venues values (?, ?, ?)
                on conflict(venue_id) do update set
                    name=excluded.name,
                    kind=excluded.kind
                """,
                [(venue.venue_id, venue.name, venue.kind) for venue in venues],
            )

    def record_pool_snapshots(self, pools: list[Pool]) -> None:
        now = time.time()
        with self._connect() as con:
            con.executemany(
                """
                insert into pools (
                    pool_id, venue_id, app_id, asset_a_id, asset_b_id,
                    fee_bps, status, source, first_seen_at, last_seen_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(pool_id) do update set
                    venue_id=excluded.venue_id,
                    app_id=excluded.app_id,
                    asset_a_id=excluded.asset_a_id,
                    asset_b_id=excluded.asset_b_id,
                    fee_bps=excluded.fee_bps,
                    status=excluded.status,
                    source=excluded.source,
                    last_seen_at=excluded.last_seen_at
                """,
                [
                    (
                        pool.pool_id,
                        pool.venue_id,
                        pool.app_id,
                        pool.asset_a_id,
                        pool.asset_b_id,
                        pool.fee_bps,
                        "active",
                        "connector",
                        now,
                        pool.captured_at,
                    )
                    for pool in pools
                ],
            )
            con.executemany(
                """
                insert into pool_snapshots (
                    pool_id, venue_id, app_id, asset_a_id, asset_b_id, reserve_a,
                    reserve_b, fee_bps, price_a_in_b, price_b_in_a, liquidity_estimate,
                    block_round, data_freshness_seconds, captured_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        pool.pool_id,
                        pool.venue_id,
                        pool.app_id,
                        pool.asset_a_id,
                        pool.asset_b_id,
                        pool.reserve_a,
                        pool.reserve_b,
                        pool.fee_bps,
                        pool.to_dict()["price_a_in_b"],
                        pool.to_dict()["price_b_in_a"],
                        self._liquidity_estimate(pool),
                        pool.block_round,
                        max(0.0, now - pool.captured_at),
                        pool.captured_at,
                    )
                    for pool in pools
                ],
            )

    def record_opportunities(self, opportunities: list[Opportunity]) -> None:
        with self._connect() as con:
            for item in opportunities:
                cursor = con.execute(
                    """
                    insert into opportunities (
                        route_hash, route_json, input_asset_id, input_amount,
                        expected_final_amount, gross_profit, estimated_network_fee,
                        total_dex_fees, total_price_impact_bps, slippage_buffer,
                        expected_net_profit, expected_profit_bps,
                        max_price_impact_bps, involved_pool_ids_json, involved_asset_ids_json,
                        status, skip_reason, confidence_score, risk_rules_json, created_at
                    )
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.route_hash,
                        json.dumps(item.route),
                        item.input_asset_id,
                        item.input_amount,
                        item.expected_final_amount,
                        item.gross_profit,
                        item.estimated_network_fee,
                        item.total_dex_fees,
                        item.total_price_impact_bps,
                        item.slippage_buffer,
                        item.expected_net_profit,
                        item.expected_profit_bps,
                        item.max_price_impact_bps,
                        json.dumps(item.involved_pool_ids),
                        json.dumps(item.involved_asset_ids),
                        item.status,
                        item.skip_reason,
                        item.confidence_score,
                        json.dumps(item.risk_rules),
                        item.created_at,
                    ),
                )
                opportunity_id = cursor.lastrowid
                self._record_route_quotes(con, opportunity_id, item)
                self._record_risk_decision(con, opportunity_id, item)
                self._record_route_forensics(con, opportunity_id, item)

    def record_service_health(
        self,
        service_name: str,
        status: str,
        *,
        detail: str | None = None,
        metrics: dict | None = None,
    ) -> None:
        with self._connect() as con:
            con.execute(
                """
                insert into service_health (
                    service_name, status, detail, metrics_json, checked_at
                )
                values (?, ?, ?, ?, ?)
                """,
                (service_name, status, detail, json.dumps(metrics or {}, sort_keys=True), time.time()),
            )

    def replace_verified_pool_registry(
        self,
        records: list[dict],
        *,
        network: str,
        generated_at: float | None = None,
    ) -> None:
        """Replace the paper-only verified pool registry for a network."""
        verified_at = float(generated_at if generated_at is not None else time.time())
        network_key = (network or "").strip().lower() or "unknown"
        with self._connect() as con:
            con.execute(
                """
                create table if not exists verified_pool_registry (
                    app_id integer not null,
                    network text not null,
                    venue_id text not null,
                    asset_a_id integer not null,
                    asset_b_id integer not null,
                    fee_bps integer not null,
                    reserve_a real not null,
                    reserve_b real not null,
                    latest_round integer not null,
                    status text not null,
                    reason text not null,
                    verification_source text not null,
                    pool_id text not null default '',
                    verified_at real not null,
                    primary key (network, app_id)
                )
                """
            )
            con.execute("delete from verified_pool_registry where network = ?", (network_key,))
            for item in records:
                con.execute(
                    """
                    insert into verified_pool_registry (
                        app_id, network, venue_id, asset_a_id, asset_b_id, fee_bps,
                        reserve_a, reserve_b, latest_round, status, reason,
                        verification_source, pool_id, verified_at
                    ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(item.get("app_id") or 0),
                        network_key,
                        str(item.get("venue_id") or ""),
                        int(item.get("asset_a_id") or 0),
                        int(item.get("asset_b_id") or 0),
                        int(item.get("fee_bps") or 0),
                        float(item.get("reserve_a") or 0.0),
                        float(item.get("reserve_b") or 0.0),
                        int(item.get("latest_round") or 0),
                        str(item.get("status") or "rejected"),
                        str(item.get("reason") or ""),
                        str(item.get("verification_source") or ""),
                        str(item.get("pool_id") or ""),
                        float(item.get("verified_at") or verified_at),
                    ),
                )

    def list_verified_pool_registry(
        self,
        *,
        network: str,
        status: str | None = None,
    ) -> list[dict]:
        network_key = (network or "").strip().lower() or "unknown"
        with self._connect() as con:
            con.execute(
                """
                create table if not exists verified_pool_registry (
                    app_id integer not null,
                    network text not null,
                    venue_id text not null,
                    asset_a_id integer not null,
                    asset_b_id integer not null,
                    fee_bps integer not null,
                    reserve_a real not null,
                    reserve_b real not null,
                    latest_round integer not null,
                    status text not null,
                    reason text not null,
                    verification_source text not null,
                    pool_id text not null default '',
                    verified_at real not null,
                    primary key (network, app_id)
                )
                """
            )
            if status:
                rows = con.execute(
                    """
                    select * from verified_pool_registry
                    where network = ? and status = ?
                    order by app_id asc
                    """,
                    (network_key, status),
                ).fetchall()
            else:
                rows = con.execute(
                    """
                    select * from verified_pool_registry
                    where network = ?
                    order by status asc, app_id asc
                    """,
                    (network_key,),
                ).fetchall()
        return [dict(row) for row in rows]

    def record_testnet_soak_observation(self, observation: dict) -> None:
        """Persist one public-safe TestNet soak observation. Restart-safe append only."""
        observation_id = str(observation.get("observationId") or "").strip()
        run_id = str(observation.get("runId") or "").strip()
        if not observation_id or not run_id:
            raise ValueError("testnet soak observation requires observationId and runId")
        payload = dict(observation)
        payload["productionReady"] = False
        payload["liveExecutionLocked"] = True
        with self._connect() as con:
            # Ensure table exists for databases initialized before this schema was added.
            con.execute(
                """
                create table if not exists testnet_soak_observations (
                    id integer primary key autoincrement,
                    observation_id text not null unique,
                    run_id text not null,
                    sequence_number integer not null,
                    started_at real not null,
                    completed_at real not null,
                    network text not null,
                    source text not null,
                    payload_json text not null
                )
                """
            )
            con.execute(
                """
                insert into testnet_soak_observations (
                    observation_id, run_id, sequence_number, started_at, completed_at,
                    network, source, payload_json
                )
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation_id,
                    run_id,
                    int(observation.get("sequenceNumber") or 0),
                    float(observation.get("startedAt") or time.time()),
                    float(observation.get("completedAt") or time.time()),
                    str(observation.get("network") or ""),
                    str(observation.get("source") or "unavailable"),
                    json.dumps(payload, sort_keys=True),
                ),
            )

    def next_testnet_soak_sequence(self, run_id: str) -> int:
        with self._connect() as con:
            con.execute(
                """
                create table if not exists testnet_soak_observations (
                    id integer primary key autoincrement,
                    observation_id text not null unique,
                    run_id text not null,
                    sequence_number integer not null,
                    started_at real not null,
                    completed_at real not null,
                    network text not null,
                    source text not null,
                    payload_json text not null
                )
                """
            )
            row = con.execute(
                """
                select coalesce(max(sequence_number), 0) as max_seq
                from testnet_soak_observations
                where run_id = ?
                """,
                (run_id,),
            ).fetchone()
        return int(row["max_seq"] or 0) + 1

    def list_testnet_soak_observations(
        self,
        limit: int = 50,
        *,
        newest_first: bool = False,
    ) -> list[dict]:
        """Return public-safe soak observations. Defaults to newest-first for ops panels."""
        safe_limit = max(1, min(10_000, int(limit)))
        with self._connect() as con:
            con.execute(
                """
                create table if not exists testnet_soak_observations (
                    id integer primary key autoincrement,
                    observation_id text not null unique,
                    run_id text not null,
                    sequence_number integer not null,
                    started_at real not null,
                    completed_at real not null,
                    network text not null,
                    source text not null,
                    payload_json text not null
                )
                """
            )
            rows = con.execute(
                """
                select payload_json
                from testnet_soak_observations
                order by completed_at desc, id desc
                limit ?
                """,
                (safe_limit,),
            ).fetchall()
        observations: list[dict] = []
        for row in rows:
            payload = self._safe_json_loads(row["payload_json"], {})
            if isinstance(payload, dict):
                payload["productionReady"] = False
                payload["liveExecutionLocked"] = True
                observations.append(payload)
        if newest_first:
            return observations
        # Chronological order for rollups and gap math.
        return list(reversed(observations))

    def record_paper_trade(
        self,
        opportunity: Opportunity,
        would_execute: bool,
        notes: str,
        *,
        decision_round: int | None = None,
    ) -> bool:
        """Persist a paper candidate. Returns False if a pending recheck already exists.

        When ``decision_round`` is set, opportunity_hash is keyed by route+round so the
        same route cannot enqueue duplicate T+5/T+30 work for that round.
        """
        created_at = time.time()
        route_payload = json.dumps(opportunity.route, sort_keys=True)
        route_class = _paper_route_class(opportunity.route)
        if decision_round is not None:
            opportunity_hash = f"{opportunity.route_hash}:round:{int(decision_round)}"
        else:
            opportunity_hash = f"{opportunity.route_hash}:{round(opportunity.created_at, 3)}"
        # Prefer source leg capture times over opportunity wall-clock create.
        leg_captures = [
            float(leg.get("captured_at"))
            for leg in opportunity.route
            if leg.get("captured_at") is not None
        ]
        quote_captured_at = min(leg_captures) if leg_captures else float(opportunity.created_at or created_at)
        with self._connect() as con:
            if decision_round is not None:
                existing = con.execute(
                    """
                    select id from paper_trades
                    where opportunity_hash = ?
                       or (
                         route_hash = ?
                         and notes like ?
                         and checked_30s_at is null
                       )
                    limit 1
                    """,
                    (
                        opportunity_hash,
                        opportunity.route_hash,
                        f"%round={int(decision_round)}%",
                    ),
                ).fetchone()
                if existing:
                    return False
            con.execute(
                """
                insert into paper_trades (
                    opportunity_hash, route_hash, opportunity_status, skip_reason,
                    input_asset_id, input_amount, expected_final_amount, expected_net_profit,
                    estimated_network_fee, slippage_buffer, route_json, route_class, quote_captured_at,
                    check_5s_due_at, check_30s_due_at, check_60s_due_at, expected_profit,
                    simulated_profit_5s, simulated_profit_30s, simulated_profit_60s, confidence_score,
                    success, would_execute, notes, created_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    opportunity_hash,
                    opportunity.route_hash,
                    opportunity.status,
                    opportunity.skip_reason,
                    opportunity.input_asset_id,
                    opportunity.input_amount,
                    opportunity.expected_final_amount,
                    opportunity.expected_net_profit,
                    opportunity.estimated_network_fee,
                    opportunity.slippage_buffer,
                    route_payload,
                    route_class,
                    quote_captured_at,
                    created_at + 5,
                    created_at + 30,
                    created_at + 60,
                    opportunity.expected_net_profit,
                    opportunity.expected_net_profit,
                    opportunity.expected_net_profit,
                    opportunity.expected_net_profit,
                    opportunity.confidence_score,
                    None,
                    int(would_execute),
                    notes,
                    created_at,
                ),
            )
            self._record_opportunity_decay(
                con,
                opportunity=opportunity,
                opportunity_hash=opportunity_hash,
                route_payload=route_payload,
                created_at=created_at,
            )
        return True

    def update_due_paper_trades(
        self,
        pools: list[Pool],
        now: float | None = None,
        *,
        created_at_min: float | None = None,
        run_id: str | None = None,
    ) -> dict:
        checked_at = now or time.time()
        pool_by_id = {pool.pool_id: pool for pool in pools}
        updated_5s = 0
        updated_30s = 0
        updated_60s = 0
        errors = 0
        filters: list[str] = []
        filter_params: list[object] = []
        if created_at_min is not None:
            filters.append("created_at >= ?")
            filter_params.append(float(created_at_min))
        if run_id:
            filters.append("notes like ?")
            filter_params.append(f"%runId={run_id}%")
        extra_filter = "" if not filters else " and " + " and ".join(filters)
        with self._connect() as con:
            rows = con.execute(
                f"""
                select *
                from paper_trades
                where route_json != '[]'
                  {extra_filter}
                  and (
                    (checked_5s_at is null and check_5s_due_at <= ?)
                    or
                    (checked_30s_at is null and check_30s_due_at <= ?)
                    or
                    (checked_60s_at is null and check_60s_due_at <= ?)
                  )
                """,
                (*filter_params, checked_at, checked_at, checked_at),
            ).fetchall()
            for row in rows:
                if row["checked_5s_at"] is None and float(row["check_5s_due_at"] or 0.0) <= checked_at:
                    if self._update_paper_trade_checkpoint(con, row, pool_by_id, checked_at, "5s"):
                        updated_5s += 1
                    else:
                        errors += 1
                if row["checked_30s_at"] is None and float(row["check_30s_due_at"] or 0.0) <= checked_at:
                    if self._update_paper_trade_checkpoint(con, row, pool_by_id, checked_at, "30s"):
                        updated_30s += 1
                    else:
                        errors += 1
                if row["checked_60s_at"] is None and float(row["check_60s_due_at"] or 0.0) <= checked_at:
                    if self._update_paper_trade_checkpoint(con, row, pool_by_id, checked_at, "60s"):
                        updated_60s += 1
                    else:
                        errors += 1
        return {
            "checked_5s": updated_5s,
            "checked_30s": updated_30s,
            "checked_60s": updated_60s,
            "errors": errors,
        }

    def record_live_trade(self, opportunity: Opportunity | dict, result: dict) -> None:
        route_hash = result.get("route_hash")
        if not route_hash and isinstance(opportunity, Opportunity):
            route_hash = opportunity.route_hash
        elif not route_hash and isinstance(opportunity, dict):
            route_hash = opportunity.get("route_hash")
        conservative_profit_algos = result.get("conservative_profit_algos")
        if conservative_profit_algos is None and int(result.get("profit_asset_id", 0) or 0) == 0:
            conservative_profit_algos = result.get("conservative_profit")
        created_at = time.time()
        with self._connect() as con:
            cursor = con.execute(
                """
                insert into live_trades (
                    route_hash, submitted, dry_run, txid, group_id_hex, tx_count,
                    fee_algos, conservative_profit, reason, result_json, created_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    route_hash,
                    int(bool(result.get("submitted"))),
                    int(bool(result.get("dry_run", True))),
                    result.get("txid"),
                    result.get("group_id_hex"),
                    result.get("tx_count"),
                    result.get("fee_algos"),
                    conservative_profit_algos,
                    result.get("reason"),
                    json.dumps(result),
                    created_at,
                ),
            )
            self._record_balance_reconciliation(
                con=con,
                live_trade_id=cursor.lastrowid,
                route_hash=route_hash,
                result=result,
                created_at=created_at,
            )

    def get_pulse(self, public_delay_seconds: int, required_asset_id: int | None = None) -> dict:
        cutoff = time.time() - 86_400
        pool_filter = ""
        pool_params: list[object] = []
        opportunity_filter = ""
        opportunity_params: list[object] = []
        if required_asset_id is not None:
            pool_filter = "where asset_a_id = ? or asset_b_id = ?"
            pool_params = [required_asset_id, required_asset_id]
            opportunity_filter = """
                and exists (
                    select 1
                    from json_each(opportunities.involved_asset_ids_json) asset
                    where asset.value = ?
                )
            """
            opportunity_params = [required_asset_id]
        with self._connect() as con:
            pools_monitored = con.execute(
                f"select count(distinct pool_id) as count from pool_snapshots {pool_filter}",
                pool_params,
            ).fetchone()["count"]
            last_scan_row = con.execute(
                f"select max(captured_at) as last_scan_at from pool_snapshots {pool_filter}",
                pool_params,
            ).fetchone()
            opportunity_count = con.execute(
                f"""
                select count(*) as count
                from opportunities
                where created_at >= ?
                {opportunity_filter}
                """,
                [cutoff, *opportunity_params],
            ).fetchone()["count"]
            approved_count = con.execute(
                f"""
                select count(*) as count
                from opportunities
                where created_at >= ? and status = 'approved'
                {opportunity_filter}
                """,
                [cutoff, *opportunity_params],
            ).fetchone()["count"]
            paper_net = con.execute(
                """
                select coalesce(sum(simulated_profit_30s), 0) as total
                from paper_trades
                where created_at >= ?
                  and would_execute = 1
                  and checked_30s_at is not null
                """,
                (cutoff,),
            ).fetchone()["total"]
            best = con.execute(
                f"""
                select * from opportunities
                where status = 'approved' and created_at >= ? and created_at <= ?
                {opportunity_filter}
                order by expected_net_profit desc
                limit 1
                """,
                [cutoff, time.time() - public_delay_seconds, *opportunity_params],
            ).fetchone()

        market_health = "warming up"
        if pools_monitored >= 6 and approved_count > 0:
            market_health = "active"
        elif pools_monitored >= 6:
            market_health = "watching"

        return {
            "pools_monitored": pools_monitored,
            "opportunities_24h": opportunity_count,
            "approved_24h": approved_count,
            "paper_net_profit_24h": paper_net,
            "last_scan_at": last_scan_row["last_scan_at"],
            "market_health": market_health,
            "best_opportunity": self._row_to_opportunity(best) if best else None,
        }

    def list_latest_pools(self, limit: int = 50, required_asset_id: int | None = None) -> list[dict]:
        filter_clause = ""
        filter_params: list[object] = []
        if required_asset_id is not None:
            filter_clause = "where asset_a_id = ? or asset_b_id = ?"
            filter_params = [required_asset_id, required_asset_id]
        with self._connect() as con:
            rows = con.execute(
                f"""
                select ps.*
                from pool_snapshots ps
                join (
                    select pool_id, max(captured_at) as captured_at
                    from pool_snapshots
                    {filter_clause}
                    group by pool_id
                ) latest
                on latest.pool_id = ps.pool_id and latest.captured_at = ps.captured_at
                order by ps.venue_id, ps.pool_id
                limit ?
                """,
                [*filter_params, limit],
            ).fetchall()
            health_rows = con.execute(
                """
                select service_name, status, detail, metrics_json, checked_at
                from service_health
                where service_name like 'connector:%'
                order by checked_at desc
                limit 40
                """
            ).fetchall()
        connector_status: dict[str, str] = {}
        for health in health_rows:
            name = str(health["service_name"] or "")
            if not name.startswith("connector:"):
                continue
            venue = name.split(":", 1)[-1]
            if venue not in connector_status:
                connector_status[venue] = str(health["status"] or "unavailable")
        now = time.time()
        latest = [dict(row) for row in rows]
        for row in latest:
            age = max(0.0, now - float(row["captured_at"] or 0.0))
            row["snapshot_age_seconds"] = age
            # Public evidence contract for radar / Control Room (real stored rows only).
            row["venue"] = row.get("venue_id")
            row["appId"] = row.get("app_id")
            row["poolId"] = row.get("pool_id")
            row["assets"] = [row.get("asset_a_id"), row.get("asset_b_id")]
            row["reserves"] = {"a": row.get("reserve_a"), "b": row.get("reserve_b")}
            row["feeTier"] = row.get("fee_bps")
            row["liquidity"] = row.get("liquidity_estimate")
            row["spotPrice"] = row.get("price_a_in_b")
            row["blockRound"] = row.get("block_round")
            row["capturedAt"] = row.get("captured_at")
            row["freshness"] = age
            row["freshnessSeconds"] = age
            row["source"] = "connector"
            row["connectorStatus"] = connector_status.get(str(row.get("venue_id") or ""), "unknown")
        return latest

    def list_opportunities(
        self,
        limit: int = 50,
        public_delay_seconds: int = 0,
        min_created_at: float | None = None,
        required_asset_id: int | None = None,
    ) -> list[dict]:
        clauses = ["created_at <= ?"]
        params: list[object] = [time.time() - public_delay_seconds]
        if min_created_at is not None:
            clauses.append("created_at >= ?")
            params.append(min_created_at)
        if required_asset_id is not None:
            clauses.append(
                """
                exists (
                    select 1
                    from json_each(opportunities.involved_asset_ids_json) asset
                    where asset.value = ?
                )
                """
            )
            params.append(required_asset_id)
        params.append(limit)
        with self._connect() as con:
            rows = con.execute(
                f"""
                select * from opportunities
                where {" and ".join(clauses)}
                order by expected_net_profit desc, created_at desc
                limit ?
                """,
                params,
            ).fetchall()
        return [self._row_to_opportunity(row) for row in rows]

    def list_paper_trades(self, limit: int = 50) -> list[dict]:
        with self._connect() as con:
            rows = con.execute(
                """
                select *
                from paper_trades
                order by
                    case
                        when checked_30s_at is not null or checked_5s_at is not null then 0
                        else 1
                    end,
                    coalesce(checked_30s_at, checked_5s_at, created_at) desc,
                    created_at desc
                limit ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_paper_trades_since(self, created_at_min: float, *, limit: int = 10_000) -> list[dict]:
        """Paper trades created at/after ``created_at_min`` (session-scoped canaries)."""
        with self._connect() as con:
            rows = con.execute(
                """
                select *
                from paper_trades
                where created_at >= ?
                order by created_at desc, id desc
                limit ?
                """,
                (float(created_at_min), max(1, int(limit))),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_opportunity_replays(self, limit: int = 30) -> list[dict]:
        with self._connect() as con:
            rows = con.execute(
                """
                select *
                from paper_trades
                order by
                    case
                        when checked_30s_at is not null or checked_5s_at is not null then 0
                        else 1
                    end,
                    coalesce(checked_30s_at, checked_5s_at, created_at) desc,
                    created_at desc
                limit ?
                """,
                (limit,),
            ).fetchall()
            return [self._row_to_opportunity_replay(con, row) for row in rows]

    def paper_trading_evidence_summary(self, limit: int = 10, lookback_seconds: int = 7 * 86_400) -> dict:
        cutoff = time.time() - lookback_seconds
        safe_limit = max(1, min(100, int(limit)))
        with self._connect() as con:
            rows = con.execute(
                """
                select *
                from paper_trades
                where created_at >= ?
                order by
                    coalesce(checked_30s_at, checked_5s_at, created_at) desc,
                    id desc
                """,
                (cutoff,),
            ).fetchall()
        evidence = [self._row_to_paper_evidence(row) for row in rows]
        recent = evidence[:safe_limit]
        candidate_count = len(evidence)
        checked_5s = sum(1 for item in evidence if item["t5SimulatedOutput"] is not None)
        checked_30s = sum(1 for item in evidence if item["t30SimulatedOutput"] is not None)
        survived_5s = sum(1 for item in evidence if item["t5SimulatedProfit"] is not None and item["t5SimulatedProfit"] > 0)
        survived_30s = sum(1 for item in evidence if item["t30SimulatedProfit"] is not None and item["t30SimulatedProfit"] > 0)
        would_execute = sum(1 for item in evidence if item["wouldExecute"])
        failures = sum(1 for item in evidence if item["skipOrFailureReason"] not in {"none", "would_execute"})
        expected_total = sum(float(item["expectedProfit"] or 0.0) for item in evidence)
        simulated_5s_total = sum(float(item["t5SimulatedProfit"] or 0.0) for item in evidence)
        simulated_30s_total = sum(float(item["t30SimulatedProfit"] or 0.0) for item in evidence)
        return {
            "source": "stored" if candidate_count else "unavailable",
            "windowSeconds": lookback_seconds,
            "sampleSize": len(recent),
            "candidateCount": candidate_count,
            "checked5sCount": checked_5s,
            "checked30sCount": checked_30s,
            "survived5sCount": survived_5s,
            "survived30sCount": survived_30s,
            "survivalRate5s": 0.0 if checked_5s <= 0 else survived_5s / checked_5s,
            "survivalRate30s": 0.0 if checked_30s <= 0 else survived_30s / checked_30s,
            "wouldExecuteCount": would_execute,
            "skipOrFailureCount": failures,
            "expectedNetAlgo": expected_total,
            "simulatedNetAlgo5s": simulated_5s_total,
            "simulatedNetAlgo30s": simulated_30s_total,
            "averageQuoteDecay5s": _average_values(item["quoteDecay5s"] for item in evidence),
            "averageQuoteDecay30s": _average_values(item["quoteDecay30s"] for item in evidence),
            "recentEvidence": recent,
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
        }

    def quote_freshness_evidence(
        self,
        *,
        max_age_seconds: float = 5.0,
        now: float | None = None,
        limit: int = 10,
    ) -> dict:
        current_time = float(now or time.time())
        safe_limit = max(1, min(100, int(limit)))
        with self._connect() as con:
            rows = con.execute(
                """
                select
                    route_hash, opportunity_id, leg_index, pool_id, venue_id,
                    input_asset_id, output_asset_id, input_amount, output_amount,
                    block_round, captured_at, expires_at
                from quotes
                order by captured_at desc, id desc
                """
            ).fetchall()

        quote_count = len(rows)
        fresh_rows = []
        aging_rows = []
        stale_rows = []
        unavailable_rows = []
        venues: dict[str, dict] = {}
        latest_quote_at = None
        for row in rows:
            venue_id = str(row["venue_id"] or "unknown")
            captured_at = float(row["captured_at"] or 0.0)
            expires_at = float(row["expires_at"] or 0.0)
            age_seconds = max(0.0, current_time - captured_at) if captured_at else None
            freshness_status = self._quote_freshness_status(row, current_time=current_time, max_age_seconds=max_age_seconds)
            is_usable = freshness_status in {"fresh", "aging"}
            latest_quote_at = captured_at if latest_quote_at is None else max(latest_quote_at, captured_at)
            if freshness_status == "fresh":
                fresh_rows.append(row)
            elif freshness_status == "aging":
                aging_rows.append(row)
            elif freshness_status == "unavailable":
                unavailable_rows.append(row)
            else:
                stale_rows.append(row)
            venue = venues.setdefault(
                venue_id,
                {
                    "venueId": venue_id,
                    "venueName": venue_id,
                    "quoteCount": 0,
                    "freshCount": 0,
                    "agingCount": 0,
                    "staleCount": 0,
                    "unavailableCount": 0,
                    "readinessEligibleQuoteCount": 0,
                    "latestQuoteAt": None,
                    "latestAgeSeconds": None,
                    "status": "unavailable",
                },
            )
            venue["quoteCount"] += 1
            if freshness_status == "fresh":
                venue["freshCount"] += 1
            elif freshness_status == "aging":
                venue["agingCount"] += 1
            elif freshness_status == "unavailable":
                venue["unavailableCount"] += 1
            else:
                venue["staleCount"] += 1
            if is_usable:
                venue["readinessEligibleQuoteCount"] += 1
            venue["latestQuoteAt"] = captured_at if venue["latestQuoteAt"] is None else max(venue["latestQuoteAt"], captured_at)

        for venue in venues.values():
            latest = venue["latestQuoteAt"]
            venue["latestAgeSeconds"] = max(0.0, current_time - float(latest)) if latest else None
            if venue["readinessEligibleQuoteCount"] > 0 and venue["staleCount"] == 0 and venue["unavailableCount"] == 0:
                venue["status"] = "ok"
            elif venue["readinessEligibleQuoteCount"] > 0:
                venue["status"] = "degraded"
            elif venue["quoteCount"] > 0:
                venue["status"] = "blocked"

        fresh_count = len(fresh_rows)
        aging_count = len(aging_rows)
        stale_count = len(stale_rows)
        unavailable_count = len(unavailable_rows)
        usable_count = fresh_count + aging_count
        if quote_count <= 0:
            freshness_status = "unavailable"
        elif usable_count <= 0:
            freshness_status = "blocked"
        elif stale_count > 0 or unavailable_count > 0:
            freshness_status = "degraded"
        else:
            freshness_status = "ok"
        rejected_rows = stale_rows + unavailable_rows
        rejected_reasons = self._quote_rejection_reasons(
            rejected_rows,
            current_time=current_time,
            max_age_seconds=max_age_seconds,
        )
        quote_records = [
            self._row_to_quote_freshness_record(
                row,
                current_time=current_time,
                max_age_seconds=max_age_seconds,
            )
            for row in rows[:safe_limit]
        ]
        return {
            "source": "stored" if quote_count else "unavailable",
            "maxAgeSeconds": float(max_age_seconds),
            "quoteCount": quote_count,
            "freshCount": fresh_count,
            "agingCount": aging_count,
            "staleCount": stale_count,
            "unavailableCount": unavailable_count,
            "freshQuoteCount": fresh_count,
            "agingQuoteCount": aging_count,
            "staleQuoteCount": stale_count,
            "unavailableQuoteCount": unavailable_count,
            "readinessEligibleQuoteCount": usable_count,
            "readinessExcludedQuoteCount": stale_count + unavailable_count,
            "rejectedQuoteCount": stale_count + unavailable_count,
            "rejectedReasons": rejected_reasons,
            "freshnessStatus": freshness_status,
            "blocksReadiness": bool(quote_count > 0 and usable_count <= 0),
            "latestQuoteAt": latest_quote_at,
            "latestAgeSeconds": max(0.0, current_time - float(latest_quote_at)) if latest_quote_at else None,
            "venues": sorted(venues.values(), key=lambda item: item["venueId"]),
            "venuesRepresented": sorted({record["venue"] for record in quote_records if record["venue"]}),
            "pairsRepresented": sorted({record["pair"] for record in quote_records if record["pair"]}),
            "quotes": quote_records,
            "staleSamples": [
                self._row_to_stale_quote_sample(
                    row,
                    current_time=current_time,
                    max_age_seconds=max_age_seconds,
                )
                for row in sorted(rejected_rows, key=lambda item: float(item["captured_at"] or 0.0), reverse=True)[:safe_limit]
            ],
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
        }

    def connector_reliability_evidence(
        self,
        *,
        lookback_seconds: int = 24 * 60 * 60,
        now: float | None = None,
        max_quote_age_seconds: float = 5.0,
    ) -> dict:
        current_time = float(now or time.time())
        cutoff = current_time - float(lookback_seconds)
        with self._connect() as con:
            health_rows = con.execute(
                """
                select service_name, status, detail, metrics_json, checked_at
                from service_health
                where checked_at >= ?
                order by checked_at desc, id desc
                """,
                (cutoff,),
            ).fetchall()
            pool_rows = con.execute(
                """
                select venue_id, count(*) as pool_snapshot_count, max(captured_at) as latest_pool_at
                from pool_snapshots
                where captured_at >= ?
                group by venue_id
                order by venue_id
                """,
                (cutoff,),
            ).fetchall()
            quote_rows = con.execute(
                """
                select venue_id, count(*) as quote_count, max(captured_at) as latest_quote_at
                from quotes
                where captured_at >= ?
                group by venue_id
                order by venue_id
                """,
                (cutoff,),
            ).fetchall()
            quote_detail_rows = con.execute(
                """
                select
                    venue_id, captured_at, expires_at
                from quotes
                where captured_at >= ?
                order by captured_at desc, id desc
                """,
                (cutoff,),
            ).fetchall()

        connectors: dict[str, dict] = {}
        for row in health_rows:
            metrics = self._safe_json_loads(row["metrics_json"], {})
            if row["service_name"] == "market_scanner" and not metrics.get("connectors"):
                continue
            names = metrics.get("connectors") if row["service_name"] == "market_scanner" else None
            if not names:
                connector_name = str(metrics.get("connector") or row["service_name"]).removeprefix("connector:")
                names = [connector_name]
            for name in names:
                connector_id = str(name or "unknown")
                item = connectors.setdefault(
                    connector_id,
                    {
                        "connector": connector_id,
                        "connectorName": connector_id,
                        "connectorType": self._connector_type(connector_id, metrics),
                        "scanCount": 0,
                        "successCount": 0,
                        "errorCount": 0,
                        "errorCount24h": 0,
                        "lastRunAt": None,
                        "lastSuccessAt": None,
                        "lastFailureAt": None,
                        "lastError": None,
                        "latencyMs": None,
                        "latestRound": None,
                        "expectedMinRound": None,
                        "degradationReason": None,
                        "readinessImpact": "blocked",
                        "productionReady": False,
                        "freshQuoteCount24h": 0,
                        "staleQuoteCount24h": 0,
                        "freshCount24h": 0,
                        "staleCount24h": 0,
                        "status": "unavailable",
                        "successRate": 0.0,
                    },
                )
                item["scanCount"] += 1
                checked_at = float(row["checked_at"] or 0.0)
                latency_ms = metrics.get("latency_ms", metrics.get("latencyMs"))
                if latency_ms is not None:
                    item["latencyMs"] = float(latency_ms)
                item["connectorType"] = self._connector_type(connector_id, metrics)
                latest_round = self._metric_number(metrics, "latestRound", "latest_round")
                expected_min_round = self._metric_number(metrics, "expectedMinRound", "expected_min_round")
                if latest_round is not None:
                    item["latestRound"] = latest_round
                if expected_min_round is not None:
                    item["expectedMinRound"] = expected_min_round
                fresh_count = self._metric_number(metrics, "freshCount24h", "fresh_count_24h", "freshQuoteCount24h")
                stale_count = self._metric_number(metrics, "staleCount24h", "stale_count_24h", "staleQuoteCount24h")
                if fresh_count is not None:
                    item["freshQuoteCount24h"] = max(item["freshQuoteCount24h"], int(fresh_count))
                    item["freshCount24h"] = item["freshQuoteCount24h"]
                if stale_count is not None:
                    item["staleQuoteCount24h"] = max(item["staleQuoteCount24h"], int(stale_count))
                    item["staleCount24h"] = item["staleQuoteCount24h"]
                item["lastRunAt"] = checked_at if item["lastRunAt"] is None else max(item["lastRunAt"], checked_at)
                if row["status"] == "ok":
                    item["successCount"] += 1
                    item["lastSuccessAt"] = (
                        checked_at if item["lastSuccessAt"] is None else max(item["lastSuccessAt"], checked_at)
                    )
                elif row["status"] == "degraded":
                    item["successCount"] += 1
                    item["errorCount"] += 1
                    item["errorCount24h"] = item["errorCount"]
                    item["lastSuccessAt"] = (
                        checked_at if item["lastSuccessAt"] is None else max(item["lastSuccessAt"], checked_at)
                    )
                    item["lastFailureAt"] = (
                        checked_at if item["lastFailureAt"] is None else max(item["lastFailureAt"], checked_at)
                    )
                    item["lastError"] = row["detail"] or "connector_degraded"
                else:
                    item["errorCount"] += 1
                    item["errorCount24h"] = item["errorCount"]
                    item["lastFailureAt"] = (
                        checked_at if item["lastFailureAt"] is None else max(item["lastFailureAt"], checked_at)
                    )
                    item["lastError"] = row["detail"] or row["status"]

        for item in connectors.values():
            item["successRate"] = 0.0 if item["scanCount"] <= 0 else item["successCount"] / item["scanCount"]
            self._apply_connector_degradation_rules(item)

        venue_coverage = {}
        for row in pool_rows:
            venue_id = str(row["venue_id"] or "unknown")
            latest = row["latest_pool_at"]
            venue_coverage[venue_id] = {
                "venueId": venue_id,
                "venueName": venue_id,
                "poolSnapshotCount": int(row["pool_snapshot_count"] or 0),
                "quoteCount": 0,
                "latestPoolAt": float(latest) if latest else None,
                "latestQuoteAt": None,
                "latestPoolAgeSeconds": max(0.0, current_time - float(latest)) if latest else None,
                "latestQuoteAgeSeconds": None,
                "lastSuccessAt": None,
                "lastFailureAt": None,
                "latencyMs": None,
                "freshQuoteCount24h": 0,
                "staleQuoteCount24h": 0,
                "freshCount24h": 0,
                "staleCount24h": 0,
                "errorCount24h": 0,
                "status": "down",
                "source": "stored",
            }
        for row in quote_rows:
            venue_id = str(row["venue_id"] or "unknown")
            latest = row["latest_quote_at"]
            item = venue_coverage.setdefault(
                venue_id,
                {
                    "venueId": venue_id,
                    "venueName": venue_id,
                    "poolSnapshotCount": 0,
                    "quoteCount": 0,
                    "latestPoolAt": None,
                    "latestQuoteAt": None,
                    "latestPoolAgeSeconds": None,
                    "latestQuoteAgeSeconds": None,
                    "lastSuccessAt": None,
                    "lastFailureAt": None,
                    "latencyMs": None,
                    "freshQuoteCount24h": 0,
                    "staleQuoteCount24h": 0,
                    "freshCount24h": 0,
                    "staleCount24h": 0,
                    "errorCount24h": 0,
                    "status": "down",
                    "source": "stored",
                },
            )
            item["quoteCount"] = int(row["quote_count"] or 0)
            item["latestQuoteAt"] = float(latest) if latest else None
            item["latestQuoteAgeSeconds"] = max(0.0, current_time - float(latest)) if latest else None
        for row in quote_detail_rows:
            venue_id = str(row["venue_id"] or "unknown")
            item = venue_coverage.setdefault(
                venue_id,
                {
                    "venueId": venue_id,
                    "venueName": venue_id,
                    "poolSnapshotCount": 0,
                    "quoteCount": 0,
                    "latestPoolAt": None,
                    "latestQuoteAt": None,
                    "latestPoolAgeSeconds": None,
                    "latestQuoteAgeSeconds": None,
                    "lastSuccessAt": None,
                    "lastFailureAt": None,
                    "latencyMs": None,
                    "freshQuoteCount24h": 0,
                    "staleQuoteCount24h": 0,
                    "freshCount24h": 0,
                    "staleCount24h": 0,
                    "errorCount24h": 0,
                    "status": "down",
                    "source": "stored",
                },
            )
            status = self._quote_freshness_status(
                row,
                current_time=current_time,
                max_age_seconds=max_quote_age_seconds,
            )
            captured_at = float(row["captured_at"] or 0.0)
            if status in {"fresh", "aging"}:
                item["freshQuoteCount24h"] += 1
                item["freshCount24h"] = item["freshQuoteCount24h"]
                item["lastSuccessAt"] = (
                    captured_at if item["lastSuccessAt"] is None else max(item["lastSuccessAt"], captured_at)
                )
            else:
                item["staleQuoteCount24h"] += 1
                item["staleCount24h"] = item["staleQuoteCount24h"]
                item["lastFailureAt"] = (
                    captured_at if item["lastFailureAt"] is None else max(item["lastFailureAt"], captured_at)
                )
            matched_connector = connectors.get(venue_id)
            if matched_connector:
                matched_connector["freshQuoteCount24h"] = item["freshQuoteCount24h"]
                matched_connector["staleQuoteCount24h"] = item["staleQuoteCount24h"]
                matched_connector["freshCount24h"] = item["freshCount24h"]
                matched_connector["staleCount24h"] = item["staleCount24h"]

        for item in venue_coverage.values():
            matched_connector = connectors.get(item["venueId"])
            if matched_connector:
                item["errorCount24h"] = matched_connector["errorCount"]
                item["freshQuoteCount24h"] = max(item["freshQuoteCount24h"], matched_connector["freshQuoteCount24h"])
                item["staleQuoteCount24h"] = max(item["staleQuoteCount24h"], matched_connector["staleQuoteCount24h"])
                item["freshCount24h"] = item["freshQuoteCount24h"]
                item["staleCount24h"] = item["staleQuoteCount24h"]
                item["latencyMs"] = matched_connector["latencyMs"]
                if matched_connector["lastFailureAt"] is not None:
                    item["lastFailureAt"] = max(
                        float(item["lastFailureAt"] or 0.0),
                        float(matched_connector["lastFailureAt"]),
                    )
            if item["venueId"] == "mock":
                item["status"] = "mock"
            elif item["freshQuoteCount24h"] > 0 and item["staleQuoteCount24h"] == 0 and item["errorCount24h"] == 0:
                item["status"] = "ok"
            elif item["freshQuoteCount24h"] > 0:
                item["status"] = "degraded"
            else:
                item["status"] = "down"

        for item in connectors.values():
            self._apply_connector_degradation_rules(item)

        connector_count = len(connectors)
        healthy_count = sum(1 for item in connectors.values() if item["status"] == "ok")
        error_count = sum(1 for item in connectors.values() if item["status"] == "down")
        wait_count = sum(1 for item in connectors.values() if item["readinessImpact"] == "wait")
        blocked_count = sum(1 for item in connectors.values() if item["readinessImpact"] == "blocked")
        venue_values = sorted(venue_coverage.values(), key=lambda item: item["venueId"])
        connector_values = sorted(connectors.values(), key=lambda item: item["connector"])
        readiness_rollup = self._connector_readiness_rollup(connector_values)
        down_venue_count = sum(1 for item in venue_values if item["status"] == "down")
        degraded_venue_count = sum(1 for item in venue_values if item["status"] == "degraded")
        if not health_rows and not venue_values:
            status = "unavailable"
        elif not venue_values and blocked_count > 0 and healthy_count <= 0:
            status = "down"
        elif not venue_values and blocked_count > 0:
            status = "degraded"
        elif not venue_values and healthy_count <= 0 and error_count > 0:
            status = "down"
        elif not venue_values and healthy_count > 0 and error_count > 0:
            status = "degraded"
        elif not venue_values and healthy_count > 0:
            status = "degraded" if wait_count > 0 else "ok"
        elif not venue_values and wait_count > 0:
            status = "mock" if all(item["status"] == "mock" for item in connectors.values()) else "degraded"
        elif down_venue_count > 0 and all(item["freshQuoteCount24h"] <= 0 for item in venue_values):
            status = "down"
        elif down_venue_count > 0 or degraded_venue_count > 0 or error_count > 0:
            status = "degraded"
        else:
            status = "ok"
        return {
            "source": "stored" if health_rows or venue_coverage else "unavailable",
            "windowSeconds": int(lookback_seconds),
            "status": status,
            "connectorCount": connector_count,
            "healthyConnectorCount": healthy_count,
            "errorConnectorCount": error_count,
            "waitingConnectorCount": wait_count,
            "blockedConnectorCount": blocked_count,
            "readinessRollup": readiness_rollup,
            "connectors": connector_values,
            "venues": venue_values,
            "venueCoverage": venue_values,
            "hasRecentScannerHealth": any(row["service_name"] == "market_scanner" for row in health_rows),
            "blocksReadiness": status in {"down", "unavailable"} or blocked_count > 0,
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
        }

    def route_readiness_evidence(
        self,
        *,
        limit: int = 50,
        max_quote_age_seconds: float = 5.0,
        now: float | None = None,
    ) -> dict:
        current_time = float(now or time.time())
        safe_limit = max(1, min(100, int(limit)))
        with self._connect() as con:
            route_rows = con.execute(
                """
                select
                    id, route_hash, route_json, involved_asset_ids_json,
                    status, skip_reason, created_at
                from opportunities
                order by created_at desc, id desc
                limit ?
                """,
                (safe_limit,),
            ).fetchall()
            quote_rows = con.execute(
                """
                select
                    route_hash, opportunity_id, leg_index, pool_id, venue_id,
                    input_asset_id, output_asset_id, input_amount, output_amount,
                    fee_amount, price_impact_bps, block_round, captured_at, expires_at
                from quotes
                order by route_hash, leg_index, id
                """
            ).fetchall()
            risk_rows = con.execute(
                """
                select route_hash, approved, reason, created_at
                from risk_decisions
                order by created_at desc, id desc
                """
            ).fetchall()

        quotes_by_route: dict[str, list[sqlite3.Row]] = {}
        for row in quote_rows:
            quotes_by_route.setdefault(str(row["route_hash"] or ""), []).append(row)
        risk_by_route: dict[str, sqlite3.Row] = {}
        for row in risk_rows:
            route_hash = str(row["route_hash"] or "")
            if route_hash and route_hash not in risk_by_route:
                risk_by_route[route_hash] = row

        connector_evidence = self.connector_reliability_evidence(
            lookback_seconds=24 * 60 * 60,
            now=current_time,
            max_quote_age_seconds=max_quote_age_seconds,
        )
        connector_by_name = self._connector_records_by_name(connector_evidence)
        routes = [
            self._route_readiness_record(
                route,
                quotes=quotes_by_route.get(str(route["route_hash"] or ""), []),
                risk=risk_by_route.get(str(route["route_hash"] or "")),
                connector_by_name=connector_by_name,
                current_time=current_time,
                max_quote_age_seconds=max_quote_age_seconds,
            )
            for route in route_rows
        ]
        ready_count = sum(1 for route in routes if route["readinessStatus"] == "ready")
        wait_count = sum(1 for route in routes if route["readinessStatus"] == "wait")
        blocked_count = sum(1 for route in routes if route["readinessStatus"] == "blocked")
        reason_counts: dict[str, int] = {}
        for route in routes:
            for reason in route["reasons"]:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        return {
            "source": "stored" if routes else "unavailable",
            "routeCount": len(routes),
            "readyCount": ready_count,
            "waitCount": wait_count,
            "blockedCount": blocked_count,
            "productionReadyCount": sum(1 for route in routes if route["productionReady"]),
            "overallReadiness": "blocked" if blocked_count else "wait" if wait_count else "ready" if ready_count else "blocked",
            "reasonCounts": [
                {"reason": reason, "count": count}
                for reason, count in sorted(reason_counts.items())
            ],
            "routes": routes,
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
        }

    def scanner_to_paper_pipeline_evidence(
        self,
        limit: int = 10,
        lookback_seconds: int = 7 * 86_400,
        max_quote_age_seconds: float = 5.0,
    ) -> dict:
        safe_limit = max(1, min(100, int(limit)))
        with self._connect() as con:
            scanner = con.execute(
                """
                select
                    count(*) as snapshot_count,
                    count(distinct pool_id) as pool_count,
                    count(distinct venue_id) as venue_count,
                    min(captured_at) as first_snapshot_at,
                    max(captured_at) as latest_snapshot_at
                from pool_snapshots
                """
            ).fetchone()
            scanner_venues = [
                str(row["venue_id"])
                for row in con.execute(
                    """
                    select distinct venue_id
                    from pool_snapshots
                    order by venue_id
                    """
                ).fetchall()
            ]
            quote_rows = con.execute(
                """
                select
                    route_hash, opportunity_id, leg_index, pool_id, venue_id,
                    input_asset_id, output_asset_id, input_amount, output_amount,
                    fee_amount, price_impact_bps, block_round, captured_at, expires_at
                from quotes
                order by input_asset_id, output_asset_id, input_amount, venue_id, route_hash
                """
            ).fetchall()
            route_summary = con.execute(
                """
                select
                    count(*) as candidate_count,
                    coalesce(sum(case when status = 'approved' then 1 else 0 end), 0) as approved_count,
                    coalesce(sum(case when status != 'approved' then 1 else 0 end), 0) as rejected_count,
                    coalesce(sum(case when status != 'approved' and coalesce(skip_reason, '') != '' then 1 else 0 end), 0)
                        as rejected_with_reason_count,
                    count(distinct route_hash) as route_count
                from opportunities
                """
            ).fetchone()
            route_quote_links = con.execute(
                """
                select count(*) as linked_count
                from opportunities o
                where exists (
                    select 1
                    from quotes q
                    where q.route_hash = o.route_hash
                )
                """
            ).fetchone()
            rejected_rows = con.execute(
                """
                select route_hash, status, skip_reason
                from opportunities
                where status != 'approved'
                order by created_at desc, id desc
                limit ?
                """,
                (safe_limit,),
            ).fetchall()
            risk = con.execute(
                """
                select
                    count(*) as decision_count,
                    coalesce(sum(case when approved = 1 then 1 else 0 end), 0) as approved_count,
                    coalesce(sum(case when approved = 0 then 1 else 0 end), 0) as rejected_count
                from risk_decisions
                """
            ).fetchone()

        comparable_quotes = self._comparable_quote_groups(quote_rows, safe_limit)
        quote_freshness = self.quote_freshness_evidence(max_age_seconds=max_quote_age_seconds, limit=safe_limit)
        connector_reliability = self.connector_reliability_evidence(lookback_seconds=24 * 60 * 60)
        route_readiness = self.route_readiness_evidence(
            limit=safe_limit,
            max_quote_age_seconds=max_quote_age_seconds,
        )
        paper = self.paper_trading_evidence_summary(limit=safe_limit, lookback_seconds=lookback_seconds)
        scanner_has_evidence = int(scanner["snapshot_count"] or 0) > 0 and int(scanner["pool_count"] or 0) > 0
        quotes_have_comparable_evidence = len(comparable_quotes) > 0
        quotes_have_fresh_evidence = quote_freshness["freshCount"] > 0
        connectors_have_health_evidence = connector_reliability["healthyConnectorCount"] > 0
        routes_have_candidates = int(route_summary["candidate_count"] or 0) > 0
        routes_have_rejection_reasons = int(route_summary["rejected_with_reason_count"] or 0) > 0
        risk_has_decisions = int(risk["decision_count"] or 0) > 0
        paper_has_rechecks = bool(
            paper["candidateCount"] > 0
            and paper["checked5sCount"] > 0
            and paper["checked30sCount"] > 0
            and any(
                item["t5SimulatedOutput"] is not None
                and item["t30SimulatedOutput"] is not None
                and item["quoteDecay5s"] is not None
                and item["quoteDecay30s"] is not None
                and item["expectedVsSimulatedProfit5s"] is not None
                and item["expectedVsSimulatedProfit30s"] is not None
                for item in paper["recentEvidence"]
            )
        )
        risk_to_paper = bool(paper["wouldExecuteCount"] > 0 and int(risk["approved_count"] or 0) > 0)
        quotes_to_routes = bool(routes_have_candidates and int(route_quote_links["linked_count"] or 0) > 0)
        return {
            "source": "stored" if scanner_has_evidence and quotes_have_comparable_evidence else "unavailable",
            "windowSeconds": lookback_seconds,
            "scanner": {
                "hasEvidence": scanner_has_evidence,
                "poolSnapshotCount": int(scanner["snapshot_count"] or 0),
                "poolCount": int(scanner["pool_count"] or 0),
                "venueCount": int(scanner["venue_count"] or 0),
                "venues": scanner_venues,
                "firstSnapshotAt": scanner["first_snapshot_at"],
                "latestSnapshotAt": scanner["latest_snapshot_at"],
            },
            "quotes": {
                "hasComparableQuotes": quotes_have_comparable_evidence,
                "hasFreshQuotes": quotes_have_fresh_evidence,
                "quoteCount": len(quote_rows),
                "comparableGroupCount": len(comparable_quotes),
                "comparableGroups": comparable_quotes,
            },
            "quoteFreshness": quote_freshness,
            "connectorReliability": connector_reliability,
            "routeReadiness": route_readiness,
            "routes": {
                "hasCandidates": routes_have_candidates,
                "candidateCount": int(route_summary["candidate_count"] or 0),
                "routeCount": int(route_summary["route_count"] or 0),
                "approvedCount": int(route_summary["approved_count"] or 0),
                "rejectedCount": int(route_summary["rejected_count"] or 0),
                "rejectedWithReasonCount": int(route_summary["rejected_with_reason_count"] or 0),
                "routesLinkedToQuotes": int(route_quote_links["linked_count"] or 0),
                "hasRejectedReasons": routes_have_rejection_reasons,
                "rejections": [
                    {
                        "routeHash": row["route_hash"],
                        "status": row["status"],
                        "reason": row["skip_reason"] or "unknown",
                    }
                    for row in rejected_rows
                ],
            },
            "risk": {
                "hasDecisions": risk_has_decisions,
                "decisionCount": int(risk["decision_count"] or 0),
                "approvedCount": int(risk["approved_count"] or 0),
                "rejectedCount": int(risk["rejected_count"] or 0),
            },
            "paper": paper,
            "proof": {
                "scannerToQuotes": bool(scanner_has_evidence and quotes_have_comparable_evidence),
                "quoteFreshness": quotes_have_fresh_evidence,
                "connectorReliability": connectors_have_health_evidence,
                "routeReadiness": route_readiness["readyCount"] > 0,
                "quotesToRoutes": quotes_to_routes,
                "routesToRisk": bool(routes_have_candidates and risk_has_decisions),
                "riskToPaper": risk_to_paper,
                "paperRechecks": paper_has_rechecks,
                "endToEnd": bool(
                    scanner_has_evidence
                    and quotes_have_comparable_evidence
                    and quotes_have_fresh_evidence
                    and connectors_have_health_evidence
                    and route_readiness["readyCount"] > 0
                    and quotes_to_routes
                    and routes_have_rejection_reasons
                    and risk_has_decisions
                    and risk_to_paper
                    and paper_has_rechecks
                ),
            },
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
        }

    def list_route_forensics(self, limit: int = 50) -> list[dict]:
        with self._connect() as con:
            rows = con.execute(
                """
                select *
                from route_forensics
                order by created_at desc, id desc
                limit ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_route_forensics(row) for row in rows]

    def list_route_decision_forensics(
        self,
        limit: int = 50,
        *,
        max_quote_age_seconds: float = 5.0,
        now: float | None = None,
    ) -> list[dict]:
        current_time = float(now or time.time())
        safe_limit = max(1, min(100, int(limit)))
        readiness = self.route_readiness_evidence(
            limit=safe_limit,
            max_quote_age_seconds=max_quote_age_seconds,
            now=current_time,
        )
        readiness_by_route = {item["routeHash"]: item for item in readiness["routes"]}
        with self._connect() as con:
            opportunity_rows = con.execute(
                """
                select *
                from opportunities
                order by created_at desc, id desc
                limit ?
                """,
                (safe_limit,),
            ).fetchall()
            route_hashes = [str(row["route_hash"] or "") for row in opportunity_rows if row["route_hash"]]
            route_forensics_by_hash = self._route_forensics_by_hash(con, route_hashes)
            paper_by_route = self._paper_evidence_by_route(con, route_hashes)
        return [
            self._route_decision_forensics_record(
                opportunity_row,
                route_forensics=route_forensics_by_hash.get(str(opportunity_row["route_hash"] or "")),
                readiness=readiness_by_route.get(str(opportunity_row["route_hash"] or "")),
                paper=paper_by_route.get(str(opportunity_row["route_hash"] or "")),
            )
            for opportunity_row in opportunity_rows
        ]

    def route_forensics_summary(self) -> dict:
        with self._connect() as con:
            summary = con.execute(
                """
                select
                    count(*) as route_count,
                    coalesce(sum(case when json_extract(completeness_json, '$.complete') = 1 then 1 else 0 end), 0)
                        as complete_count,
                    coalesce(sum(case when rejection_reason != 'none' then 1 else 0 end), 0) as rejected_count,
                    coalesce(sum(case when json_extract(approval_decision_json, '$.approved') = 1 then 1 else 0 end), 0)
                        as approved_count
                from route_forensics
                """
            ).fetchone()
            rejection_rows = con.execute(
                """
                select rejection_reason as reason, count(*) as count
                from route_forensics
                group by rejection_reason
                order by count desc, rejection_reason asc
                """
            ).fetchall()
        return {
            "routeCount": int(summary["route_count"] or 0),
            "completeCount": int(summary["complete_count"] or 0),
            "approvedCount": int(summary["approved_count"] or 0),
            "rejectedCount": int(summary["rejected_count"] or 0),
            "rejectionReasons": [
                {"reason": row["reason"], "count": int(row["count"] or 0)}
                for row in rejection_rows
                if row["reason"] != "none"
            ],
        }

    def data_provenance_report(self, metric_key: str | None = None, route_hash: str | None = None) -> dict:
        metrics = self.production_readiness_metrics()
        with self._connect() as con:
            opportunity_row = self._select_provenance_opportunity(con, route_hash)
            opportunity = self._row_to_opportunity(opportunity_row) if opportunity_row else None
            quotes: list[dict] = []
            pool_snapshots: list[dict] = []
            risk_decisions: list[dict] = []
            route_forensics = None
            if opportunity:
                quotes = [
                    dict(row)
                    for row in con.execute(
                        """
                        select *
                        from quotes
                        where opportunity_id = ? or route_hash = ?
                        order by leg_index asc, id asc
                        """,
                        (opportunity["id"], opportunity["route_hash"]),
                    ).fetchall()
                ]
                pool_snapshots = self._provenance_pool_snapshots(con, quotes)
                risk_decisions = [
                    {**dict(row), "rules": json.loads(row["rules_json"] or "{}"), "policy": json.loads(row["policy_json"] or "{}")}
                    for row in con.execute(
                        """
                        select *
                        from risk_decisions
                        where opportunity_id = ? or route_hash = ?
                        order by created_at desc, id desc
                        """,
                        (opportunity["id"], opportunity["route_hash"]),
                    ).fetchall()
                ]
                forensics_row = con.execute(
                    """
                    select *
                    from route_forensics
                    where opportunity_id = ? or route_hash = ?
                    order by created_at desc, id desc
                    limit 1
                    """,
                    (opportunity["id"], opportunity["route_hash"]),
                ).fetchone()
                if forensics_row:
                    route_forensics = self._row_to_route_forensics(forensics_row)

        return build_data_provenance_report(
            metric_key=metric_key,
            metrics=metrics,
            opportunity=opportunity,
            quotes=quotes,
            pool_snapshots=pool_snapshots,
            risk_decisions=risk_decisions,
            route_forensics=route_forensics,
        )

    def confidence_calibration_report(self) -> dict:
        with self._connect() as con:
            rows = con.execute(
                """
                select *
                from paper_trades
                order by created_at desc, id desc
                """
            ).fetchall()
        return build_confidence_calibration_report([dict(row) for row in rows])

    def opportunity_decay_dashboard(self, view: str = "24h", now: float | None = None) -> dict:
        with self._connect() as con:
            paper_rows = con.execute(
                """
                select
                    id,
                    opportunity_hash,
                    coalesce(quote_captured_at, created_at) as detected_at,
                    route_hash,
                    expected_net_profit as expected_profit,
                    case when checked_5s_at is not null then simulated_profit_5s else null end as expected_profit_5s,
                    case when checked_30s_at is not null then simulated_profit_30s else null end as expected_profit_30s,
                    case when checked_60s_at is not null then simulated_profit_60s else null end as expected_profit_60s,
                    quote_decay_5s,
                    quote_decay_30s,
                    quote_decay_60s,
                    checked_5s_at,
                    checked_30s_at,
                    checked_60s_at,
                    input_asset_id,
                    route_json,
                    'stored' as source,
                    created_at
                from paper_trades
                order by coalesce(quote_captured_at, created_at) desc, id desc
                """
            ).fetchall()
            fallback_rows = con.execute(
                """
                select *
                from opportunity_decay
                order by detected_at desc, id desc
                """
            ).fetchall()
        rows = [self._paper_trade_decay_row(row) for row in paper_rows] if paper_rows else [dict(row) for row in fallback_rows]
        return build_opportunity_decay_report(rows, view=view, now=now)

    def market_pulse_heatmap(self, view: str = "24h", now: float | None = None) -> dict:
        selected_view = view if view in HEATMAP_VIEWS else "24h"
        current_time = float(now or time.time())
        start_at = current_time - int(HEATMAP_VIEWS[selected_view]["seconds"])
        with self._connect() as con:
            opportunities = con.execute(
                """
                select *
                from opportunities
                where created_at >= ? and created_at <= ?
                order by created_at asc
                """,
                (start_at, current_time),
            ).fetchall()
            paper_trades = con.execute(
                """
                select *
                from paper_trades
                where created_at >= ? and created_at <= ?
                order by created_at asc
                """,
                (start_at, current_time),
            ).fetchall()
        return build_market_pulse_heatmap(
            [self._row_to_opportunity(row) for row in opportunities],
            [dict(row) for row in paper_trades],
            view=selected_view,
            now=current_time,
        )

    def generate_market_intelligence_report(
        self,
        report_date: str | None = None,
        now: float | None = None,
        cached_market_context: dict | None = None,
    ) -> dict:
        selected_date, window_start, window_end = self._daily_report_window(report_date=report_date, now=now)
        generated_at = float(now or time.time())
        with self._connect() as con:
            opportunities = con.execute(
                """
                select *
                from opportunities
                where created_at >= ? and created_at < ?
                order by expected_profit_bps desc, created_at desc
                """,
                (window_start, window_end),
            ).fetchall()
            pool_snapshots = con.execute(
                """
                select *
                from pool_snapshots
                where captured_at >= ? and captured_at < ?
                order by captured_at asc
                """,
                (window_start, window_end),
            ).fetchall()
            paper_trades = con.execute(
                """
                select *
                from paper_trades
                where created_at >= ? and created_at < ?
                order by created_at asc
                """,
                (window_start, window_end),
            ).fetchall()
            risk_decisions = con.execute(
                """
                select *
                from risk_decisions
                where created_at >= ? and created_at < ?
                order by created_at asc
                """,
                (window_start, window_end),
            ).fetchall()
            service_health = con.execute(
                """
                select *
                from service_health
                where checked_at >= ? and checked_at < ?
                order by checked_at asc
                """,
                (window_start, window_end),
            ).fetchall()
            assets = con.execute("select * from assets").fetchall()

            report = build_daily_market_intelligence_report(
                report_date=selected_date,
                window_start=window_start,
                window_end=window_end,
                generated_at=generated_at,
                opportunities=[self._row_to_opportunity(row) for row in opportunities],
                pool_snapshots=[dict(row) for row in pool_snapshots],
                paper_trades=[dict(row) for row in paper_trades],
                risk_decisions=[dict(row) for row in risk_decisions],
                service_health=[dict(row) for row in service_health],
                assets=[dict(row) for row in assets],
                cached_market_context=cached_market_context,
            )
            markdown = render_market_intelligence_markdown(report)
            con.execute(
                """
                insert into market_intelligence_reports (
                    report_date, window_start, window_end, source,
                    report_json, markdown, generated_at
                )
                values (?, ?, ?, ?, ?, ?, ?)
                on conflict(report_date) do update set
                    window_start=excluded.window_start,
                    window_end=excluded.window_end,
                    source=excluded.source,
                    report_json=excluded.report_json,
                    markdown=excluded.markdown,
                    generated_at=excluded.generated_at
                """,
                (
                    selected_date,
                    window_start,
                    window_end,
                    report["source"],
                    json.dumps(report, sort_keys=True),
                    markdown,
                    generated_at,
                ),
            )
        return {**report, "markdown": markdown}

    def get_market_intelligence_report(self, report_date: str | None = None, generate_if_missing: bool = True) -> dict | None:
        selected_date, _, _ = self._daily_report_window(report_date=report_date)
        with self._connect() as con:
            row = con.execute(
                """
                select *
                from market_intelligence_reports
                where report_date = ?
                """,
                (selected_date,),
            ).fetchone()
        if row is None and generate_if_missing:
            return self.generate_market_intelligence_report(report_date=selected_date)
        return self._row_to_market_intelligence_report(row, include_markdown=True) if row else None

    def list_market_intelligence_reports(self, limit: int = 30) -> list[dict]:
        with self._connect() as con:
            rows = con.execute(
                """
                select *
                from market_intelligence_reports
                order by report_date desc, generated_at desc
                limit ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_market_intelligence_report(row, include_markdown=False) for row in rows]

    def generate_recent_market_intelligence_reports(self, limit_days: int = 7) -> list[dict]:
        report_dates = self._market_intelligence_evidence_dates(limit_days=limit_days)
        if not report_dates:
            return [self.generate_market_intelligence_report()]
        return [self.generate_market_intelligence_report(report_date=report_date) for report_date in report_dates]

    def paper_daily_report(self, lookback_seconds: int = 86_400) -> dict:
        cutoff = time.time() - lookback_seconds
        with self._connect() as con:
            con.row_factory = sqlite3.Row
            summary = con.execute(
                """
                select
                    count(*) as candidates,
                    coalesce(sum(would_execute), 0) as would_execute,
                    coalesce(sum(case when would_execute = 0 then 1 else 0 end), 0) as skipped,
                    coalesce(sum(case when checked_5s_at is not null then 1 else 0 end), 0) as checked_5s,
                    coalesce(sum(case when checked_30s_at is not null then 1 else 0 end), 0) as checked_30s,
                    coalesce(sum(expected_net_profit), 0) as expected_net_profit,
                    coalesce(sum(case when checked_30s_at is not null then simulated_profit_30s else 0 end), 0)
                        as simulated_profit_30s,
                    coalesce(avg(case when checked_30s_at is not null then quote_decay_30s end), 0)
                        as average_quote_decay_30s,
                    coalesce(avg(case when checked_30s_at is not null then expected_vs_simulated_profit_30s end), 0)
                        as average_profit_delta_30s,
                    count(distinct date(created_at, 'unixepoch')) as days_collected
                from paper_trades
                where created_at >= ?
                """,
                (cutoff,),
            ).fetchone()
            skip_rows = con.execute(
                """
                select coalesce(skip_reason, 'none') as reason, count(*) as count
                from paper_trades
                where created_at >= ?
                group by coalesce(skip_reason, 'none')
                order by count desc, reason asc
                limit 8
                """,
                (cutoff,),
            ).fetchall()
            best = con.execute(
                """
                select route_hash, input_asset_id, input_amount, expected_net_profit,
                       simulated_profit_30s, checked_30s_at, skip_reason, would_execute
                from paper_trades
                where created_at >= ?
                order by coalesce(simulated_profit_30s, expected_net_profit) desc, created_at desc
                limit 1
                """,
                (cutoff,),
            ).fetchone()

        candidates = int(summary["candidates"] or 0)
        checked_30s = int(summary["checked_30s"] or 0)
        return {
            "windowSeconds": lookback_seconds,
            "candidates": candidates,
            "wouldExecute": int(summary["would_execute"] or 0),
            "skipped": int(summary["skipped"] or 0),
            "checked5s": int(summary["checked_5s"] or 0),
            "checked30s": checked_30s,
            "completionRate30s": (checked_30s / candidates) if candidates else 0.0,
            "daysCollected": int(summary["days_collected"] or 0),
            "expectedNetProfit": float(summary["expected_net_profit"] or 0.0),
            "simulatedProfit30s": float(summary["simulated_profit_30s"] or 0.0),
            "averageQuoteDecay30s": float(summary["average_quote_decay_30s"] or 0.0),
            "averageProfitDelta30s": float(summary["average_profit_delta_30s"] or 0.0),
            "skipReasons": [{"reason": row["reason"], "count": int(row["count"])} for row in skip_rows],
            "bestRoute": dict(best) if best else None,
        }

    def list_live_trades(self, limit: int = 50) -> list[dict]:
        with self._connect() as con:
            rows = con.execute(
                "select * from live_trades order by created_at desc limit ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_reconciliations(self, limit: int = 50) -> list[dict]:
        with self._connect() as con:
            rows = con.execute(
                "select * from balance_reconciliations order by created_at desc limit ?",
                (limit,),
            ).fetchall()
        return [self._row_to_reconciliation(row) for row in rows]

    def record_payment_verification(self, result: dict) -> None:
        expected = result.get("expected") or {}
        observed = result.get("observed") or {}
        with self._connect() as con:
            con.execute(
                """
                insert into payment_verifications (
                    txid, ok, status, reason, asset_id, expected_receiver,
                    expected_amount_raw, observed_sender, observed_receiver,
                    observed_amount_raw, confirmed_round, confirmations, result_json, created_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.get("txid"),
                    int(bool(result.get("ok"))),
                    result.get("status"),
                    result.get("reason"),
                    int(result.get("asset_id") or 0),
                    expected.get("receiver") or "",
                    int(expected.get("amount_raw") or 0),
                    observed.get("sender"),
                    observed.get("receiver"),
                    observed.get("amount_raw"),
                    observed.get("confirmed_round"),
                    observed.get("confirmations"),
                    json.dumps(result, sort_keys=True),
                    time.time(),
                ),
            )

    def list_payment_verifications(self, limit: int = 50) -> list[dict]:
        with self._connect() as con:
            rows = con.execute(
                """
                select *
                from payment_verifications
                order by created_at desc
                limit ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_payment_verification(row) for row in rows]

    def get_payment_verification(self, verification_id: int) -> dict | None:
        with self._connect() as con:
            row = con.execute(
                "select * from payment_verifications where id = ?",
                (verification_id,),
            ).fetchone()
        return self._row_to_payment_verification(row) if row else None

    def record_refund_case(self, decision: dict) -> dict:
        created_at = time.time()
        with self._connect() as con:
            cursor = con.execute(
                """
                insert into refund_cases (
                    payment_verification_id, source_txid, status, failure_type, reason,
                    refund_address, asset_id, asset_decimals, amount_raw, amount_display,
                    operator_action, operator_note, guardrails_json, decision_json, created_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.get("payment_verification_id"),
                    decision.get("source_txid"),
                    decision.get("status"),
                    decision.get("failure_type"),
                    decision.get("reason"),
                    decision.get("refund_address"),
                    int(decision.get("asset_id") or 0),
                    int(decision.get("asset_decimals") or 6),
                    int(decision.get("amount_raw") or 0),
                    float(decision.get("amount_display") or 0.0),
                    decision.get("operator_action"),
                    decision.get("operator_note"),
                    json.dumps(decision.get("guardrails") or []),
                    json.dumps(decision, sort_keys=True),
                    created_at,
                ),
            )
            row = con.execute("select * from refund_cases where id = ?", (cursor.lastrowid,)).fetchone()
        return self._row_to_refund_case(row)

    def list_refund_cases(self, limit: int = 50) -> list[dict]:
        with self._connect() as con:
            rows = con.execute(
                """
                select *
                from refund_cases
                order by created_at desc
                limit ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_refund_case(row) for row in rows]

    def update_refund_case_status(
        self,
        case_id: int,
        *,
        status: str,
        resolution_txid: str | None = None,
        resolution_note: str | None = None,
    ) -> dict | None:
        resolved_at = time.time() if status in {"resolved", "failed", "cancelled"} else None
        with self._connect() as con:
            con.execute(
                """
                update refund_cases
                set status = ?,
                    resolution_txid = ?,
                    resolution_note = ?,
                    resolved_at = ?
                where id = ?
                """,
                (status, resolution_txid, resolution_note, resolved_at, case_id),
            )
            row = con.execute("select * from refund_cases where id = ?", (case_id,)).fetchone()
        return self._row_to_refund_case(row) if row else None

    def get_submitted_live_profit_24h(self) -> float:
        cutoff = time.time() - 86_400
        with self._connect() as con:
            row = con.execute(
                """
                select coalesce(sum(conservative_profit), 0) as total
                from live_trades
                where submitted = 1 and created_at >= ?
                """,
                (cutoff,),
            ).fetchone()
        return float(row["total"] or 0.0)

    def get_submitted_live_trade_count_24h(self) -> int:
        cutoff = time.time() - 86_400
        with self._connect() as con:
            row = con.execute(
                """
                select count(*) as count
                from live_trades
                where submitted = 1 and created_at >= ?
                """,
                (cutoff,),
            ).fetchone()
        return int(row["count"] or 0)

    def get_best_approved_opportunity(
        self,
        max_input_amount: float | None = None,
        min_created_at: float | None = None,
        required_asset_id: int | None = None,
    ) -> dict | None:
        clauses = ["status = 'approved'"]
        params: list[object] = []
        if max_input_amount is not None:
            clauses.append("input_amount <= ?")
            params.append(max_input_amount)
        if min_created_at is not None:
            clauses.append("created_at >= ?")
            params.append(min_created_at)
        if required_asset_id is not None:
            clauses.append(
                """
                exists (
                    select 1
                    from json_each(opportunities.involved_asset_ids_json) asset
                    where asset.value = ?
                )
                """
            )
            params.append(required_asset_id)
        with self._connect() as con:
            row = con.execute(
                f"""
                select * from opportunities
                where {" and ".join(clauses)}
                order by expected_net_profit desc, created_at desc
                limit 1
                """,
                params,
            ).fetchone()
        return self._row_to_opportunity(row) if row else None

    def _row_to_opportunity(self, row: sqlite3.Row) -> dict:
        data = dict(row)
        data["route"] = json.loads(data.pop("route_json"))
        data["involved_pool_ids"] = json.loads(data.pop("involved_pool_ids_json"))
        data["involved_asset_ids"] = json.loads(data.pop("involved_asset_ids_json"))
        data["risk_rules"] = json.loads(data.pop("risk_rules_json"))
        if data["skip_reason"] == "absolute_profit_ok":
            data["skip_reason"] = "net_profit_after_fees_ok"
        if "absolute_profit_ok" in data["risk_rules"] and "net_profit_after_fees_ok" not in data["risk_rules"]:
            data["risk_rules"]["net_profit_after_fees_ok"] = data["risk_rules"].pop("absolute_profit_ok")
        return data

    def _select_provenance_opportunity(self, con: sqlite3.Connection, route_hash: str | None) -> sqlite3.Row | None:
        if route_hash:
            return con.execute(
                """
                select *
                from opportunities
                where route_hash = ?
                order by created_at desc, id desc
                limit 1
                """,
                (route_hash,),
            ).fetchone()
        return con.execute(
            """
            select *
            from opportunities
            order by expected_net_profit desc, created_at desc, id desc
            limit 1
            """
        ).fetchone()

    def _provenance_pool_snapshots(self, con: sqlite3.Connection, quotes: list[dict]) -> list[dict]:
        snapshots: list[dict] = []
        seen: set[int] = set()
        for quote in quotes:
            captured_at = float(quote.get("captured_at") or 0.0)
            row = con.execute(
                """
                select *
                from pool_snapshots
                where pool_id = ?
                order by
                    case when captured_at <= ? then 0 else 1 end,
                    abs(captured_at - ?) asc,
                    captured_at desc,
                    id desc
                limit 1
                """,
                (quote.get("pool_id"), captured_at, captured_at),
            ).fetchone()
            if row and int(row["id"]) not in seen:
                seen.add(int(row["id"]))
                snapshots.append(dict(row))
        return snapshots

    def _row_to_market_intelligence_report(self, row: sqlite3.Row, *, include_markdown: bool) -> dict:
        report = json.loads(row["report_json"])
        summary = report.get("marketSummary") or {}
        top_pairs = report.get("topPairs") or []
        opportunity_counts = report.get("opportunityCounts") or {}
        paper = report.get("paperTradePerformance") or {}
        scanner = report.get("scannerHealth") or {}
        data = {
            **report,
            "id": int(row["id"]),
            "reportDate": row["report_date"],
            "windowStart": float(row["window_start"]),
            "windowEnd": float(row["window_end"]),
            "generatedAt": float(row["generated_at"]),
            "source": row["source"],
            "summary": {
                "headline": summary.get("headline", "No market summary available."),
                "topPair": summary.get("topPair", top_pairs[0]["pairLabel"] if top_pairs else "none"),
                "opportunityCount": int(opportunity_counts.get("total", 0)),
                "paperWinRate30s": float(paper.get("winRate30s", 0.0)),
                "scannerStatus": scanner.get("status", "unavailable"),
            },
        }
        if include_markdown:
            data["markdown"] = row["markdown"]
        return data

    def _row_to_route_forensics(self, row: sqlite3.Row) -> dict:
        data = dict(row)
        return {
            "id": data["id"],
            "routeHash": data["route_hash"],
            "opportunityId": data["opportunity_id"],
            "routePath": json.loads(data["route_path_json"]),
            "routePathLabel": data["route_path_label"],
            "profitability": json.loads(data["profitability_json"]),
            "quoteFreshness": json.loads(data["quote_freshness_json"]),
            "priceImpact": json.loads(data["price_impact_json"]),
            "liquidityScore": json.loads(data["liquidity_score_json"]),
            "riskResult": json.loads(data["risk_result_json"]),
            "approvalDecision": json.loads(data["approval_decision_json"]),
            "rejectionReason": data["rejection_reason"],
            "confidenceCalculation": json.loads(data["confidence_calculation_json"]),
            "decisionTree": json.loads(data["decision_tree_json"]),
            "completeness": json.loads(data["completeness_json"]),
            "source": data["source"],
            "createdAt": float(data["created_at"]),
        }

    def _paper_trade_decay_row(self, row: sqlite3.Row) -> dict:
        data = dict(row)
        metadata = self._decay_route_metadata(data.get("route_json"), data.get("input_asset_id"), [])
        return {
            **data,
            "pair_key": metadata["pair_key"],
            "pair_label": metadata["pair_label"],
            "venues_json": json.dumps(metadata["venues"], sort_keys=True),
            "route_type": metadata["route_type"],
        }

    def _route_forensics_by_hash(self, con: sqlite3.Connection, route_hashes: list[str]) -> dict[str, dict]:
        records: dict[str, dict] = {}
        for route_hash in route_hashes:
            if not route_hash or route_hash in records:
                continue
            row = con.execute(
                """
                select *
                from route_forensics
                where route_hash = ?
                order by created_at desc, id desc
                limit 1
                """,
                (route_hash,),
            ).fetchone()
            if row:
                records[route_hash] = self._row_to_route_forensics(row)
        return records

    def _paper_evidence_by_route(self, con: sqlite3.Connection, route_hashes: list[str]) -> dict[str, dict]:
        records: dict[str, dict] = {}
        for route_hash in route_hashes:
            if not route_hash or route_hash in records:
                continue
            row = con.execute(
                """
                select *
                from paper_trades
                where route_hash = ?
                order by created_at desc, id desc
                limit 1
                """,
                (route_hash,),
            ).fetchone()
            if row:
                records[route_hash] = self._row_to_paper_evidence(row)
        return records

    def _route_decision_forensics_record(
        self,
        row: sqlite3.Row,
        *,
        route_forensics: dict | None,
        readiness: dict | None,
        paper: dict | None,
    ) -> dict:
        opportunity = self._row_to_opportunity(row)
        path = route_forensics.get("routePath", []) if route_forensics else opportunity["route"]
        venues = readiness.get("venues", []) if readiness else self._route_payload_venues(opportunity["route"])
        risk_decision = self._route_decision_risk_payload(opportunity, route_forensics)
        quote_freshness = self._route_decision_quote_payload(route_forensics, readiness)
        connector_readiness = self._route_decision_connector_payload(readiness)
        final_decision, final_reasons = self._route_final_decision(
            readiness=readiness,
            risk_decision=risk_decision,
            paper=paper,
        )
        record = {
            **(route_forensics or {}),
            "routeHash": opportunity["route_hash"],
            "pair": readiness.get("pair") if readiness else self._opportunity_pair_label(opportunity),
            "path": path,
            "venues": venues,
            "inputAmount": float(opportunity["input_amount"] or 0.0),
            "expectedOutput": float(opportunity["expected_final_amount"] or 0.0),
            "grossProfit": float(opportunity["gross_profit"] or 0.0),
            "fees": {
                "network": float(opportunity["estimated_network_fee"] or 0.0),
                "dex": float(opportunity["total_dex_fees"] or 0.0),
                "total": float(opportunity["estimated_network_fee"] or 0.0) + float(opportunity["total_dex_fees"] or 0.0),
            },
            "safetyBuffer": float(opportunity["slippage_buffer"] or 0.0),
            "netExpectedProfit": float(opportunity["expected_net_profit"] or 0.0),
            "quoteFreshness": quote_freshness,
            "connectorReadiness": connector_readiness,
            "riskDecision": risk_decision,
            "paperDecision": self._route_decision_paper_payload(paper),
            "finalDecision": final_decision,
            "finalReasons": final_reasons,
            "source": "stored",
            "liveExecutionTouched": False,
            "signerCodeTouched": False,
        }
        if not record["finalDecision"]:
            record["finalDecision"] = "rejected"
        if not record["finalReasons"]:
            record["finalReasons"] = ["decision_reason_missing"]
        return record

    def _route_decision_quote_payload(self, route_forensics: dict | None, readiness: dict | None) -> dict:
        existing = dict(route_forensics.get("quoteFreshness") or {}) if route_forensics else {}
        readiness_status = readiness.get("quoteFreshnessStatus") if readiness else None
        reasons = [reason for reason in (readiness or {}).get("reasons", []) if reason.startswith("quote_")]
        return {
            **existing,
            "status": readiness_status or existing.get("status") or "unavailable",
            "readinessStatus": readiness_status or "unavailable",
            "reasons": reasons,
        }

    def _route_decision_connector_payload(self, readiness: dict | None) -> dict:
        reasons = [
            reason
            for reason in (readiness or {}).get("reasons", [])
            if reason.startswith(("connector_", "algod_", "indexer_", "mock_connector"))
        ]
        return {
            "status": (readiness or {}).get("connectorReadinessStatus") or "unavailable",
            "reasons": reasons,
            "venues": (readiness or {}).get("venues", []),
        }

    def _route_decision_risk_payload(self, opportunity: dict, route_forensics: dict | None) -> dict:
        existing = dict(route_forensics.get("riskResult") or {}) if route_forensics else {}
        approved = opportunity["status"] == "approved" and not opportunity.get("skip_reason")
        reason = opportunity.get("skip_reason") or existing.get("reason")
        return {
            **existing,
            "approved": bool(existing.get("approved", approved)),
            "status": "approved" if existing.get("approved", approved) else "rejected",
            "reason": reason,
            "source": "stored",
        }

    def _route_decision_paper_payload(self, paper: dict | None) -> dict:
        if not paper:
            return {"status": "unavailable", "available": False, "source": "unavailable"}
        return {
            "status": "would_execute" if paper["wouldExecute"] else "would_skip",
            "available": True,
            "wouldExecute": paper["wouldExecute"],
            "skipOrFailureReason": paper["skipOrFailureReason"],
            "expectedProfit": paper["expectedProfit"],
            "simulatedProfit5s": paper["t5SimulatedProfit"],
            "simulatedProfit30s": paper["t30SimulatedProfit"],
            "quoteDecay5s": paper["quoteDecay5s"],
            "quoteDecay30s": paper["quoteDecay30s"],
            "source": paper["source"],
        }

    def _route_final_decision(
        self,
        *,
        readiness: dict | None,
        risk_decision: dict,
        paper: dict | None,
    ) -> tuple[str, list[str]]:
        reasons = list((readiness or {}).get("reasons", []))
        readiness_status = (readiness or {}).get("readinessStatus") or "blocked"
        if readiness_status == "wait":
            return "wait", reasons or ["readiness_wait"]
        if not risk_decision.get("approved"):
            reason = risk_decision.get("reason")
            reasons.append(f"risk_rejected:{reason}" if reason else "risk_rejection_reason_missing")
            return "rejected", list(dict.fromkeys(reasons))
        if readiness_status == "blocked":
            return "rejected", reasons or ["readiness_blocked"]
        if paper:
            paper_reason = paper.get("skipOrFailureReason") or ("would_execute" if paper.get("wouldExecute") else "would_skip")
            return "paper_only", list(dict.fromkeys(["paper_evidence_available", str(paper_reason)]))
        return "approved", ["route_ready_for_paper_or_dry_run"]

    def _route_payload_venues(self, route: list[dict]) -> list[str]:
        return sorted({str(leg.get("venue") or leg.get("venue_id")) for leg in route if leg.get("venue") or leg.get("venue_id")})

    def _opportunity_pair_label(self, opportunity: dict) -> str:
        assets = sorted(int(asset_id) for asset_id in opportunity.get("involved_asset_ids", []) if asset_id is not None)
        if len(assets) < 2:
            return "unknown"
        return f"{assets[0]}/{assets[1]}"

    def _comparable_quote_groups(self, rows: list[sqlite3.Row], limit: int) -> list[dict]:
        groups: dict[tuple[int, int, float], list[sqlite3.Row]] = {}
        for row in rows:
            if int(row["leg_index"] or 0) != 0:
                continue
            key = (
                int(row["input_asset_id"]),
                int(row["output_asset_id"]),
                round(float(row["input_amount"] or 0.0), 12),
            )
            groups.setdefault(key, []).append(row)

        comparable: list[dict] = []
        for (input_asset_id, output_asset_id, input_amount), group_rows in groups.items():
            venues = sorted({str(row["venue_id"]) for row in group_rows})
            if len(venues) < 2:
                continue
            comparable.append(
                {
                    "inputAssetId": input_asset_id,
                    "outputAssetId": output_asset_id,
                    "inputAmount": input_amount,
                    "venueCount": len(venues),
                    "venues": venues,
                    "quoteCount": len(group_rows),
                    "routeHashes": sorted({str(row["route_hash"]) for row in group_rows if row["route_hash"]})[:limit],
                    "minOutputAmount": min(float(row["output_amount"] or 0.0) for row in group_rows),
                    "maxOutputAmount": max(float(row["output_amount"] or 0.0) for row in group_rows),
                }
            )
        comparable.sort(key=lambda item: (-item["venueCount"], item["inputAssetId"], item["outputAssetId"], item["inputAmount"]))
        return comparable[:limit]

    def _connector_type(self, connector_name: str, metrics: dict | None = None) -> str:
        metrics = metrics or {}
        explicit = metrics.get("connectorType", metrics.get("connector_type"))
        if explicit in {"dex", "algod", "indexer"}:
            return str(explicit)
        normalized = connector_name.lower()
        if normalized == "algod":
            return "algod"
        if normalized == "indexer":
            return "indexer"
        return "dex"

    def _metric_number(self, metrics: dict, *keys: str) -> float | None:
        for key in keys:
            value = metrics.get(key)
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return None

    def _apply_connector_degradation_rules(self, item: dict) -> None:
        item["errorCount24h"] = int(item.get("errorCount") or item.get("errorCount24h") or 0)
        item["freshCount24h"] = int(item.get("freshQuoteCount24h") or item.get("freshCount24h") or 0)
        item["staleCount24h"] = int(item.get("staleQuoteCount24h") or item.get("staleCount24h") or 0)
        item["freshQuoteCount24h"] = item["freshCount24h"]
        item["staleQuoteCount24h"] = item["staleCount24h"]
        item["degradationReason"] = None
        item["readinessImpact"] = "blocked"
        item["productionReady"] = False

        latest_round = item.get("latestRound")
        expected_round = item.get("expectedMinRound")
        round_is_stale = latest_round is not None and expected_round is not None and float(latest_round) < float(expected_round)
        connector_type = item.get("connectorType")

        if item["connector"] == "mock":
            item["status"] = "mock"
            item["degradationReason"] = "mock_connector_not_production_ready"
            item["readinessImpact"] = "wait"
            return
        if item["errorCount24h"] > 0 and item.get("successCount", 0) <= 0:
            item["status"] = "down"
            item["degradationReason"] = item.get("lastError") or "connector_down"
            item["readinessImpact"] = "blocked"
            return
        if round_is_stale and connector_type == "algod":
            item["status"] = "stale"
            item["degradationReason"] = "algod_round_stale"
            item["readinessImpact"] = "blocked"
            return
        if round_is_stale and connector_type == "indexer":
            item["status"] = "degraded"
            item["degradationReason"] = "indexer_round_stale"
            item["readinessImpact"] = "wait"
            return
        if item["staleCount24h"] > 0 and item["freshCount24h"] <= 0:
            item["status"] = "stale"
            item["degradationReason"] = "connector_quotes_stale"
            item["readinessImpact"] = "wait"
            return
        if item["errorCount24h"] > 0 or item["staleCount24h"] > 0:
            item["status"] = "degraded"
            item["degradationReason"] = item.get("lastError") or "connector_degraded"
            item["readinessImpact"] = "wait"
            return
        if item.get("successCount", 0) > 0:
            item["status"] = "ok"
            item["readinessImpact"] = "ok"
            item["productionReady"] = True

    def _connector_readiness_rollup(self, connectors: list[dict]) -> dict:
        blocked_reasons = [
            {
                "connectorName": item["connectorName"],
                "status": item["status"],
                "reason": item.get("degradationReason") or item["status"],
            }
            for item in connectors
            if item["readinessImpact"] == "blocked"
        ]
        wait_reasons = [
            {
                "connectorName": item["connectorName"],
                "status": item["status"],
                "reason": item.get("degradationReason") or item["status"],
            }
            for item in connectors
            if item["readinessImpact"] == "wait"
        ]
        if blocked_reasons:
            overall_readiness = "blocked"
        elif wait_reasons:
            overall_readiness = "wait"
        else:
            overall_readiness = "ok"
        return {
            "totalConnectors": len(connectors),
            "okCount": sum(1 for item in connectors if item["status"] == "ok"),
            "degradedCount": sum(1 for item in connectors if item["status"] == "degraded"),
            "downCount": sum(1 for item in connectors if item["status"] == "down"),
            "staleCount": sum(1 for item in connectors if item["status"] == "stale"),
            "mockCount": sum(1 for item in connectors if item["status"] == "mock"),
            "productionReadyCount": sum(1 for item in connectors if item["productionReady"]),
            "blockedReasons": blocked_reasons,
            "waitReasons": wait_reasons,
            "overallReadiness": overall_readiness,
        }

    def _connector_records_by_name(self, connector_evidence: dict) -> dict[str, dict]:
        records: dict[str, dict] = {}
        for item in connector_evidence.get("connectors", []):
            name = str(item.get("connectorName") or item.get("connector") or "").lower()
            if name:
                records[name] = item
        for item in connector_evidence.get("venueCoverage", []):
            name = str(item.get("venueId") or item.get("venueName") or "").lower()
            if name and name not in records:
                status = str(item.get("status") or "unavailable")
                if status == "ok":
                    readiness_impact = "ok"
                    degradation_reason = None
                elif status == "mock":
                    readiness_impact = "wait"
                    degradation_reason = "mock_connector_not_production_ready"
                elif status == "degraded":
                    readiness_impact = "wait"
                    degradation_reason = "connector_degraded"
                else:
                    readiness_impact = "blocked"
                    degradation_reason = "connector_health_unavailable"
                records[name] = {
                    **item,
                    "connectorName": name,
                    "connector": name,
                    "connectorType": "dex",
                    "readinessImpact": readiness_impact,
                    "degradationReason": degradation_reason,
                    "productionReady": status == "ok",
                }
        return records

    def _route_readiness_record(
        self,
        route: sqlite3.Row,
        *,
        quotes: list[sqlite3.Row],
        risk: sqlite3.Row | None,
        connector_by_name: dict[str, dict],
        current_time: float,
        max_quote_age_seconds: float,
    ) -> dict:
        route_hash = str(route["route_hash"] or "")
        quote_status, quote_reasons = self._route_quote_readiness(
            quotes,
            current_time=current_time,
            max_age_seconds=max_quote_age_seconds,
        )
        venues = self._route_venues(route, quotes)
        connector_status, connector_reasons = self._route_connector_readiness(
            venues,
            connector_by_name=connector_by_name,
        )
        risk_status, risk_reasons = self._route_risk_readiness(route, risk)
        reasons = quote_reasons + connector_reasons + risk_reasons
        blocked = any(
            reason.startswith(("quote_", "connector_down", "connector_health_unavailable", "algod_round_stale", "risk_"))
            for reason in reasons
        )
        if blocked:
            readiness_status = "blocked"
        elif reasons or quote_status == "aging" or connector_status == "wait":
            readiness_status = "wait"
        else:
            readiness_status = "ready"
        if readiness_status != "ready" and not reasons:
            reasons.append("readiness_reason_missing")
            readiness_status = "blocked"
        return {
            "routeHash": route_hash,
            "pair": self._route_pair_label(route, quotes),
            "venues": venues,
            "readinessStatus": readiness_status,
            "quoteFreshnessStatus": quote_status,
            "connectorReadinessStatus": connector_status,
            "riskStatus": risk_status,
            "reasons": reasons,
            "productionReady": readiness_status == "ready",
            "source": "stored",
        }

    def _route_quote_readiness(
        self,
        quotes: list[sqlite3.Row],
        *,
        current_time: float,
        max_age_seconds: float,
    ) -> tuple[str, list[str]]:
        if not quotes:
            return "unavailable", ["quote_evidence_unavailable"]
        statuses = [
            self._quote_freshness_status(
                quote,
                current_time=current_time,
                max_age_seconds=max_age_seconds,
            )
            for quote in quotes
        ]
        reasons = [
            reason
            for quote in quotes
            if (
                reason := self._quote_rejection_reason(
                    quote,
                    current_time=current_time,
                    max_age_seconds=max_age_seconds,
                )
            )
        ]
        if any(status == "unavailable" for status in statuses):
            return "unavailable", reasons or ["quote_unavailable"]
        if any(status == "stale" for status in statuses):
            return "stale", reasons or ["quote_stale"]
        if any(status == "aging" for status in statuses):
            return "aging", ["quote_aging"]
        return "fresh", []

    def _route_connector_readiness(
        self,
        venues: list[str],
        *,
        connector_by_name: dict[str, dict],
    ) -> tuple[str, list[str]]:
        reasons: list[str] = []
        has_wait = False
        for name, connector in sorted(connector_by_name.items()):
            connector_type = str(connector.get("connectorType") or "")
            if connector_type not in {"algod", "indexer"}:
                continue
            impact = str(connector.get("readinessImpact") or "blocked")
            status = str(connector.get("status") or "unavailable")
            reason = str(connector.get("degradationReason") or status)
            if connector_type == "algod" and impact == "blocked":
                reasons.append(reason if reason == "algod_round_stale" else f"connector_down:{name}")
            elif connector_type == "indexer" and impact == "wait":
                reasons.append(reason if reason == "indexer_round_stale" else f"connector_degraded:{name}")
                has_wait = True
            elif impact == "wait":
                reasons.append(f"connector_degraded:{name}")
                has_wait = True

        for venue in venues:
            connector = connector_by_name.get(venue.lower())
            if connector is None:
                reasons.append(f"connector_health_unavailable:{venue}")
                continue
            impact = str(connector.get("readinessImpact") or "blocked")
            status = str(connector.get("status") or "unavailable")
            reason = str(connector.get("degradationReason") or status)
            if status == "mock":
                reasons.append("mock_connector_not_production_ready")
                has_wait = True
            elif impact == "blocked":
                reasons.append(
                    f"connector_down:{venue}"
                    if reason in {"down", "connector_down"}
                    else f"connector_down:{venue}:{reason}"
                )
            elif impact == "wait":
                reasons.append(reason if reason else f"connector_degraded:{venue}")
                has_wait = True

        unique_reasons = list(dict.fromkeys(reasons))
        if any(
            reason.startswith(("connector_down", "connector_health_unavailable", "algod_round_stale"))
            for reason in unique_reasons
        ):
            return "blocked", unique_reasons
        if has_wait or unique_reasons:
            return "wait", unique_reasons
        return "ok", []

    def _route_risk_readiness(self, route: sqlite3.Row, risk: sqlite3.Row | None) -> tuple[str, list[str]]:
        status = str(route["status"] or "unknown")
        skip_reason = route["skip_reason"]
        if risk is not None:
            if int(risk["approved"] or 0) == 1:
                return "approved", []
            reason = risk["reason"] or skip_reason
            return "rejected", [f"risk_rejected:{reason}" if reason else "risk_rejection_reason_missing"]
        if status == "approved":
            return "approved", []
        return "rejected", [f"risk_rejected:{skip_reason}" if skip_reason else "risk_rejection_reason_missing"]

    def _route_venues(self, route: sqlite3.Row, quotes: list[sqlite3.Row]) -> list[str]:
        venues = {str(quote["venue_id"]) for quote in quotes if quote["venue_id"]}
        if not venues:
            route_payload = self._safe_json_loads(route["route_json"], [])
            venues.update(str(leg.get("venue")) for leg in route_payload if leg.get("venue"))
        return sorted(venues)

    def _route_pair_label(self, route: sqlite3.Row, quotes: list[sqlite3.Row]) -> str:
        asset_ids: set[int] = set()
        for quote in quotes:
            asset_ids.add(int(quote["input_asset_id"] or 0))
            asset_ids.add(int(quote["output_asset_id"] or 0))
        if not asset_ids:
            asset_ids.update(int(asset_id) for asset_id in self._safe_json_loads(route["involved_asset_ids_json"], []))
        if len(asset_ids) < 2:
            return "unknown"
        first, second = sorted(asset_ids)[:2]
        return f"{first}/{second}"

    def _row_to_stale_quote_sample(
        self,
        row: sqlite3.Row,
        *,
        current_time: float,
        max_age_seconds: float,
    ) -> dict:
        captured_at = float(row["captured_at"] or 0.0)
        expires_at = float(row["expires_at"] or 0.0)
        rejection_reason = self._quote_rejection_reason(
            row,
            current_time=current_time,
            max_age_seconds=max_age_seconds,
        )
        return {
            "routeHash": row["route_hash"],
            "opportunityId": row["opportunity_id"],
            "venueId": row["venue_id"],
            "poolId": row["pool_id"],
            "legIndex": int(row["leg_index"] or 0),
            "inputAssetId": int(row["input_asset_id"] or 0),
            "outputAssetId": int(row["output_asset_id"] or 0),
            "inputAmount": float(row["input_amount"] or 0.0),
            "outputAmount": float(row["output_amount"] or 0.0),
            "capturedAt": captured_at,
            "expiresAt": expires_at,
            "ageSeconds": max(0.0, current_time - captured_at) if captured_at else None,
            "expiredBySeconds": max(0.0, current_time - expires_at) if expires_at else None,
            "reason": rejection_reason,
            "source": "stored",
        }

    def _row_to_quote_freshness_record(
        self,
        row: sqlite3.Row,
        *,
        current_time: float,
        max_age_seconds: float,
    ) -> dict:
        input_asset_id = int(row["input_asset_id"] or 0)
        output_asset_id = int(row["output_asset_id"] or 0)
        captured_at = float(row["captured_at"] or 0.0)
        expires_at = float(row["expires_at"] or 0.0)
        status = self._quote_freshness_status(row, current_time=current_time, max_age_seconds=max_age_seconds)
        rejection_reason = self._quote_rejection_reason(
            row,
            current_time=current_time,
            max_age_seconds=max_age_seconds,
        )
        return {
            "routeHash": row["route_hash"],
            "opportunityId": row["opportunity_id"],
            "legIndex": int(row["leg_index"] or 0),
            "venue": row["venue_id"],
            "venueName": row["venue_id"],
            "pair": f"{min(input_asset_id, output_asset_id)}/{max(input_asset_id, output_asset_id)}",
            "poolId": row["pool_id"],
            "appId": None,
            "inputAssetId": input_asset_id,
            "outputAssetId": output_asset_id,
            "inputAmount": float(row["input_amount"] or 0.0),
            "expectedOutput": float(row["output_amount"] or 0.0),
            "capturedAt": captured_at if captured_at else None,
            "expiresAt": expires_at if expires_at else None,
            "blockRound": int(row["block_round"] or 0),
            "quoteAgeSeconds": max(0.0, current_time - captured_at) if captured_at else None,
            "freshnessStatus": status,
            "reason": rejection_reason,
            "rejectionReason": rejection_reason,
            "readinessEligible": status in {"fresh", "aging"},
            "source": "stored",
        }

    def _quote_rejection_reasons(
        self,
        rows: list[sqlite3.Row],
        *,
        current_time: float,
        max_age_seconds: float,
    ) -> list[dict]:
        counts: dict[str, int] = {}
        for row in rows:
            reason = self._quote_rejection_reason(
                row,
                current_time=current_time,
                max_age_seconds=max_age_seconds,
            )
            if reason is None:
                continue
            counts[reason] = counts.get(reason, 0) + 1
        return [{"reason": reason, "count": count} for reason, count in sorted(counts.items())]

    def _quote_rejection_reason(
        self,
        row: sqlite3.Row,
        *,
        current_time: float,
        max_age_seconds: float,
    ) -> str | None:
        captured_at = float(row["captured_at"] or 0.0)
        expires_at = float(row["expires_at"] or 0.0)
        if captured_at <= 0:
            return "quote_unavailable"
        if expires_at > 0 and expires_at < current_time:
            return "quote_expired"
        if max(0.0, current_time - captured_at) > max_age_seconds:
            return "quote_stale"
        return None

    def _quote_freshness_status(
        self,
        row: sqlite3.Row,
        *,
        current_time: float,
        max_age_seconds: float,
    ) -> str:
        captured_at = float(row["captured_at"] or 0.0)
        expires_at = float(row["expires_at"] or 0.0)
        if captured_at <= 0:
            return "unavailable"
        age_seconds = max(0.0, current_time - captured_at)
        if expires_at > 0 and expires_at < current_time:
            return "stale"
        if age_seconds > max_age_seconds:
            return "stale"
        if age_seconds > max_age_seconds * 0.5:
            return "aging"
        return "fresh"

    def _safe_json_loads(self, payload: str | None, default):
        if not payload:
            return default
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return default

    def _row_to_paper_evidence(self, row: sqlite3.Row) -> dict:
        data = dict(row)

        def optional_float(key: str, checked_key: str | None = None) -> float | None:
            if checked_key and data.get(checked_key) is None:
                return None
            value = data.get(key)
            return None if value is None else float(value)

        expected_profit = float(data.get("expected_net_profit") or data.get("expected_profit") or 0.0)
        failure_reason = data.get("last_error") or data.get("skip_reason")
        if not failure_reason:
            failure_reason = "would_execute" if bool(data.get("would_execute")) else "none"
        return {
            "paperTradeId": data["id"],
            "detectedAt": float(data.get("quote_captured_at") or data.get("created_at") or 0.0),
            "routeHash": data["route_hash"],
            "inputAssetId": data.get("input_asset_id"),
            "inputAmount": float(data.get("input_amount") or 0.0),
            "expectedOutput": float(data.get("expected_final_amount") or 0.0),
            "expectedProfit": expected_profit,
            "t5SimulatedOutput": optional_float("simulated_final_amount_5s", "checked_5s_at"),
            "t30SimulatedOutput": optional_float("simulated_final_amount_30s", "checked_30s_at"),
            "t5SimulatedProfit": optional_float("simulated_profit_5s", "checked_5s_at"),
            "t30SimulatedProfit": optional_float("simulated_profit_30s", "checked_30s_at"),
            "quoteDecay5s": optional_float("quote_decay_5s", "checked_5s_at"),
            "quoteDecay30s": optional_float("quote_decay_30s", "checked_30s_at"),
            "expectedVsSimulatedProfit5s": optional_float("expected_vs_simulated_profit_5s", "checked_5s_at"),
            "expectedVsSimulatedProfit30s": optional_float("expected_vs_simulated_profit_30s", "checked_30s_at"),
            "wouldExecute": bool(data.get("would_execute")),
            "opportunityStatus": data.get("opportunity_status") or "unknown",
            "skipOrFailureReason": str(failure_reason),
            "checked5sAt": data.get("checked_5s_at"),
            "checked30sAt": data.get("checked_30s_at"),
            "source": "stored",
        }

    def _row_to_opportunity_replay(self, con: sqlite3.Connection, row: sqlite3.Row) -> dict:
        data = dict(row)
        try:
            route = json.loads(data.get("route_json") or "[]")
        except json.JSONDecodeError:
            route = []
        detected_at = float(data.get("quote_captured_at") or data.get("created_at") or 0.0)
        input_amount = float(data.get("input_amount") or 0.0)
        expected_profit = float(data.get("expected_net_profit") or data.get("expected_profit") or 0.0)
        simulated_5s = data.get("simulated_profit_5s") if data.get("checked_5s_at") is not None else None
        simulated_30s = data.get("simulated_profit_30s") if data.get("checked_30s_at") is not None else None
        pool_ids = sorted({str(leg.get("pool_id") or "") for leg in route if leg.get("pool_id")})
        start_liquidity = self._sum_pool_liquidity(con, pool_ids, detected_at)
        latest_liquidity = self._sum_pool_liquidity(con, pool_ids, None)
        price_impact_bps = sum(float(leg.get("price_impact_bps") or 0.0) for leg in route)
        route_confidence = float(data.get("confidence_score") or 0.0)
        if route_confidence <= 0:
            route_confidence = max(0.0, min(100.0, 100.0 - max((float(leg.get("price_impact_bps") or 0.0) for leg in route), default=0.0)))
        verdict, verdict_reason = self._replay_verdict(data, simulated_30s)

        def checkpoint(
            *,
            key: str,
            label: str,
            due_at: float | None,
            checked_at: float | None,
            simulated_profit: float | None,
            quote_decay: float | None,
            profit_delta: float | None,
        ) -> dict:
            impact_change = None
            if quote_decay is not None and input_amount > 0:
                impact_change = (float(quote_decay) / input_amount) * 10_000
            return {
                "key": key,
                "label": label,
                "dueAt": due_at,
                "checkedAt": checked_at,
                "status": "checked" if checked_at is not None else "missing",
                "expectedProfit": expected_profit,
                "simulatedProfit": simulated_profit,
                "quoteDecay": quote_decay,
                "expectedVsSimulatedProfit": profit_delta,
                "priceImpactBps": price_impact_bps + (impact_change or 0.0),
                "priceImpactChangeBps": impact_change,
                "poolLiquidity": latest_liquidity if checked_at is not None else start_liquidity,
                "poolLiquidityChange": None if start_liquidity is None or latest_liquidity is None else latest_liquidity - start_liquidity,
                "routeConfidence": route_confidence,
            }

        timeline = [
            {
                "key": "t0",
                "label": "T0 detected",
                "dueAt": detected_at,
                "checkedAt": detected_at,
                "status": "detected",
                "expectedProfit": expected_profit,
                "simulatedProfit": None,
                "quoteDecay": 0.0,
                "expectedVsSimulatedProfit": None,
                "priceImpactBps": price_impact_bps,
                "priceImpactChangeBps": 0.0,
                "poolLiquidity": start_liquidity,
                "poolLiquidityChange": 0.0,
                "routeConfidence": route_confidence,
            },
            checkpoint(
                key="t5",
                label="T+5s recheck",
                due_at=data.get("check_5s_due_at"),
                checked_at=data.get("checked_5s_at"),
                simulated_profit=simulated_5s,
                quote_decay=data.get("quote_decay_5s"),
                profit_delta=data.get("expected_vs_simulated_profit_5s"),
            ),
            checkpoint(
                key="t30",
                label="T+30s recheck",
                due_at=data.get("check_30s_due_at"),
                checked_at=data.get("checked_30s_at"),
                simulated_profit=simulated_30s,
                quote_decay=data.get("quote_decay_30s"),
                profit_delta=data.get("expected_vs_simulated_profit_30s"),
            ),
        ]
        return {
            "id": f"paper-{data['id']}",
            "paperTradeId": data["id"],
            "routeHash": data["route_hash"],
            "detectedAt": detected_at,
            "inputAssetId": data.get("input_asset_id"),
            "inputAmount": input_amount,
            "expectedFinalAmount": float(data.get("expected_final_amount") or 0.0),
            "expectedProfit": expected_profit,
            "simulatedProfit5s": simulated_5s,
            "simulatedProfit30s": simulated_30s,
            "quoteDecay5s": data.get("quote_decay_5s"),
            "quoteDecay30s": data.get("quote_decay_30s"),
            "priceImpactBps": price_impact_bps,
            "priceImpactChangeBps": timeline[-1]["priceImpactChangeBps"],
            "poolLiquidityStart": start_liquidity,
            "poolLiquidityLatest": latest_liquidity,
            "poolLiquidityChange": None if start_liquidity is None or latest_liquidity is None else latest_liquidity - start_liquidity,
            "routeConfidence": route_confidence,
            "wouldExecute": bool(data.get("would_execute")),
            "opportunityStatus": data.get("opportunity_status") or "unknown",
            "skipReason": data.get("skip_reason"),
            "lastError": data.get("last_error"),
            "verdict": verdict,
            "verdictReason": verdict_reason,
            "route": route,
            "timeline": timeline,
            "source": "stored",
        }

    def _sum_pool_liquidity(self, con: sqlite3.Connection, pool_ids: list[str], captured_before: float | None) -> float | None:
        if not pool_ids:
            return None
        total = 0.0
        found = False
        for pool_id in pool_ids:
            if captured_before is None:
                row = con.execute(
                    """
                    select liquidity_estimate
                    from pool_snapshots
                    where pool_id = ?
                    order by captured_at desc
                    limit 1
                    """,
                    (pool_id,),
                ).fetchone()
            else:
                row = con.execute(
                    """
                    select liquidity_estimate
                    from pool_snapshots
                    where pool_id = ? and captured_at <= ?
                    order by captured_at desc
                    limit 1
                    """,
                    (pool_id, captured_before),
                ).fetchone()
            if row:
                total += float(row["liquidity_estimate"] or 0.0)
                found = True
        return total if found else None

    def _route_liquidity_summary(
        self,
        con: sqlite3.Connection,
        *,
        pool_ids: list[str],
        captured_before: float | None,
    ) -> dict:
        if not pool_ids:
            return {
                "totalLiquidity": None,
                "minLiquidity": None,
                "poolCount": 0,
                "missingPoolIds": [],
            }
        values = []
        missing = []
        for pool_id in pool_ids:
            if captured_before is None:
                row = con.execute(
                    """
                    select liquidity_estimate
                    from pool_snapshots
                    where pool_id = ?
                    order by captured_at desc
                    limit 1
                    """,
                    (pool_id,),
                ).fetchone()
            else:
                row = con.execute(
                    """
                    select liquidity_estimate
                    from pool_snapshots
                    where pool_id = ? and captured_at <= ?
                    order by captured_at desc
                    limit 1
                    """,
                    (pool_id, captured_before),
                ).fetchone()
            if row:
                values.append(float(row["liquidity_estimate"] or 0.0))
            else:
                missing.append(pool_id)
        return {
            "totalLiquidity": sum(values) if values else None,
            "minLiquidity": min(values) if values else None,
            "poolCount": len(values),
            "missingPoolIds": missing,
        }

    def _replay_verdict(self, data: dict, simulated_30s: float | None) -> tuple[str, str]:
        if data.get("last_error"):
            return "unsafe", str(data["last_error"])
        skip_reason = data.get("skip_reason") or ""
        if skip_reason in {"app_ids_allowlisted", "asset_ids_allowlisted", "price_impact_ok", "trade_size_ok", "route_length_ok"}:
            return "unsafe", f"Risk policy blocked route: {skip_reason}"
        if data.get("checked_30s_at") is None and float(data.get("check_30s_due_at") or 0.0) < time.time():
            return "stale", "30s recheck is missing or overdue."
        if bool(data.get("would_execute")) and simulated_30s is not None and float(simulated_30s) > 0:
            return "would_execute", "Expected edge survived the 30s paper recheck."
        return "would_skip", skip_reason or "Expected edge did not clear paper/risk review."

    def _record_route_quotes(
        self,
        con: sqlite3.Connection,
        opportunity_id: int,
        opportunity: Opportunity,
    ) -> None:
        rows = []
        for index, leg in enumerate(opportunity.route):
            quote_captured_at = float(leg.get("captured_at") or opportunity.created_at)
            quote_expires_at = float(leg.get("expires_at") or quote_captured_at)
            rows.append(
                (
                    opportunity.route_hash,
                    opportunity_id,
                    index,
                    leg.get("pool_id") or "",
                    leg.get("venue") or "",
                    int(leg.get("input_asset_id") or 0),
                    int(leg.get("output_asset_id") or 0),
                    float(leg.get("input_amount") or 0.0),
                    float(leg.get("expected_output") or leg.get("output_amount") or 0.0),
                    None if leg.get("fee_amount") is None else float(leg.get("fee_amount")),
                    None if leg.get("price_impact_bps") is None else float(leg.get("price_impact_bps")),
                    int(leg.get("block_round") or 0),
                    quote_captured_at,
                    quote_expires_at,
                )
            )
        if not rows:
            return
        con.executemany(
            """
            insert into quotes (
                route_hash, opportunity_id, leg_index, pool_id, venue_id,
                input_asset_id, output_asset_id, input_amount, output_amount,
                fee_amount, price_impact_bps, block_round, captured_at, expires_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    def _record_risk_decision(
        self,
        con: sqlite3.Connection,
        opportunity_id: int,
        opportunity: Opportunity,
    ) -> None:
        con.execute(
            """
            insert into risk_decisions (
                route_hash, opportunity_id, approved, reason,
                rules_json, policy_json, created_at
            )
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                opportunity.route_hash,
                opportunity_id,
                int(opportunity.status == "approved"),
                opportunity.skip_reason,
                json.dumps(opportunity.risk_rules, sort_keys=True),
                None,
                opportunity.created_at,
            ),
        )

    def _record_route_forensics(
        self,
        con: sqlite3.Connection,
        opportunity_id: int,
        opportunity: Opportunity | dict,
    ) -> None:
        if isinstance(opportunity, Opportunity):
            opportunity_payload = opportunity.to_dict()
        else:
            opportunity_payload = dict(opportunity)
        pool_ids = [
            str(pool_id)
            for pool_id in opportunity_payload.get("involved_pool_ids", [])
            if pool_id is not None and str(pool_id)
        ]
        liquidity = self._route_liquidity_summary(
            con,
            pool_ids=pool_ids,
            captured_before=float(opportunity_payload.get("created_at") or time.time()),
        )
        explanation = build_route_forensics(
            opportunity_payload,
            opportunity_id=opportunity_id,
            liquidity=liquidity,
            now=float(opportunity_payload.get("created_at") or time.time()),
        )
        con.execute(
            """
            insert into route_forensics (
                route_hash, opportunity_id, route_path_json, route_path_label,
                profitability_json, quote_freshness_json, price_impact_json,
                liquidity_score_json, risk_result_json, approval_decision_json,
                rejection_reason, confidence_calculation_json, decision_tree_json,
                completeness_json, source, created_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(opportunity_id) do update set
                route_hash=excluded.route_hash,
                route_path_json=excluded.route_path_json,
                route_path_label=excluded.route_path_label,
                profitability_json=excluded.profitability_json,
                quote_freshness_json=excluded.quote_freshness_json,
                price_impact_json=excluded.price_impact_json,
                liquidity_score_json=excluded.liquidity_score_json,
                risk_result_json=excluded.risk_result_json,
                approval_decision_json=excluded.approval_decision_json,
                rejection_reason=excluded.rejection_reason,
                confidence_calculation_json=excluded.confidence_calculation_json,
                decision_tree_json=excluded.decision_tree_json,
                completeness_json=excluded.completeness_json,
                source=excluded.source,
                created_at=excluded.created_at
            """,
            (
                explanation["routeHash"],
                explanation["opportunityId"],
                json.dumps(explanation["routePath"], sort_keys=True),
                explanation["routePathLabel"],
                json.dumps(explanation["profitability"], sort_keys=True),
                json.dumps(explanation["quoteFreshness"], sort_keys=True),
                json.dumps(explanation["priceImpact"], sort_keys=True),
                json.dumps(explanation["liquidityScore"], sort_keys=True),
                json.dumps(explanation["riskResult"], sort_keys=True),
                json.dumps(explanation["approvalDecision"], sort_keys=True),
                explanation["rejectionReason"],
                json.dumps(explanation["confidenceCalculation"], sort_keys=True),
                json.dumps(explanation["decisionTree"], sort_keys=True),
                json.dumps(explanation["completeness"], sort_keys=True),
                explanation["source"],
                explanation["createdAt"],
            ),
        )

    def _liquidity_estimate(self, pool: Pool) -> float:
        reserve_product = max(0.0, float(pool.reserve_a)) * max(0.0, float(pool.reserve_b))
        return math.sqrt(reserve_product)

    def _seed_production_gates(self, con: sqlite3.Connection) -> None:
        now = time.time()
        con.executemany(
            """
            insert into production_gates (
                gate_key, phase_key, label, sort_order, description,
                required_evidence_json, created_at, updated_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(gate_key) do update set
                phase_key=excluded.phase_key,
                label=excluded.label,
                sort_order=excluded.sort_order,
                description=excluded.description,
                required_evidence_json=excluded.required_evidence_json,
                updated_at=excluded.updated_at
            """,
            [
                (
                    gate["key"],
                    gate["phaseKey"],
                    gate["label"],
                    int(gate["sortOrder"]),
                    gate["description"],
                    json.dumps(gate["requiredEvidence"], sort_keys=True),
                    now,
                    now,
                )
                for gate in PRODUCTION_GATE_DEFINITIONS
            ],
        )

    def _backfill_opportunity_breakdowns(self, con: sqlite3.Connection) -> None:
        rows = con.execute(
            """
            select id, route_json, input_amount, expected_final_amount, expected_net_profit
            from opportunities
            where route_json != '[]'
              and total_dex_fees = 0
              and total_price_impact_bps = 0
            """
        ).fetchall()
        for row in rows:
            try:
                route = json.loads(row["route_json"])
            except json.JSONDecodeError:
                continue
            if not route:
                continue
            gross_profit = float(row["expected_final_amount"] or 0.0) - float(row["input_amount"] or 0.0)
            leg_count = len(route)
            estimated_network_fee = DEFAULT_BACKFILL_NETWORK_FEE * max(1.0, leg_count / 2)
            total_dex_fees = sum(float(leg.get("fee_amount") or 0.0) for leg in route)
            total_price_impact_bps = sum(float(leg.get("price_impact_bps") or 0.0) for leg in route)
            slippage_buffer = max(
                0.0,
                gross_profit - estimated_network_fee - float(row["expected_net_profit"] or 0.0),
            )
            con.execute(
                """
                update opportunities
                set gross_profit = ?,
                    estimated_network_fee = ?,
                    total_dex_fees = ?,
                    total_price_impact_bps = ?,
                    slippage_buffer = ?
                where id = ?
                """,
                (
                    gross_profit,
                    estimated_network_fee,
                    total_dex_fees,
                    total_price_impact_bps,
                    slippage_buffer,
                    row["id"],
                ),
            )

    def _backfill_route_forensics(self, con: sqlite3.Connection) -> None:
        rows = con.execute(
            """
            select *
            from opportunities
            where not exists (
                select 1
                from route_forensics
                where route_forensics.opportunity_id = opportunities.id
            )
            order by id asc
            """
        ).fetchall()
        for row in rows:
            opportunity = self._row_to_opportunity(row)
            self._record_route_forensics(con, row["id"], opportunity)

    def _record_opportunity_decay(
        self,
        con: sqlite3.Connection,
        *,
        opportunity: Opportunity,
        opportunity_hash: str,
        route_payload: str,
        created_at: float,
    ) -> None:
        metadata = self._decay_route_metadata(route_payload, opportunity.input_asset_id, opportunity.involved_asset_ids)
        con.execute(
            """
            insert into opportunity_decay (
                opportunity_hash, detected_at, route_hash, expected_profit,
                expected_profit_5s, expected_profit_30s, expected_profit_60s,
                checked_5s_at, checked_30s_at, checked_60s_at,
                pair_key, pair_label, venues_json, route_type, route_json, source, created_at
            )
            values (?, ?, ?, ?, null, null, null, null, null, null, ?, ?, ?, ?, ?, ?, ?)
            on conflict(opportunity_hash) do update set
                detected_at = excluded.detected_at,
                route_hash = excluded.route_hash,
                expected_profit = excluded.expected_profit,
                pair_key = excluded.pair_key,
                pair_label = excluded.pair_label,
                venues_json = excluded.venues_json,
                route_type = excluded.route_type,
                route_json = excluded.route_json,
                source = excluded.source
            """,
            (
                opportunity_hash,
                opportunity.created_at,
                opportunity.route_hash,
                opportunity.expected_net_profit,
                metadata["pair_key"],
                metadata["pair_label"],
                json.dumps(metadata["venues"], sort_keys=True),
                metadata["route_type"],
                route_payload,
                "stored",
                created_at,
            ),
        )

    def _backfill_opportunity_decay(self, con: sqlite3.Connection) -> None:
        rows = con.execute(
            """
            select *
            from paper_trades
            order by id asc
            """
        ).fetchall()
        for row in rows:
            route_payload = row["route_json"] or "[]"
            metadata = self._decay_route_metadata(route_payload, row["input_asset_id"], [])
            detected_at = float(row["quote_captured_at"] or row["created_at"] or 0.0)
            expected_profit = float(row["expected_net_profit"] or row["expected_profit"] or 0.0)
            con.execute(
                """
                insert into opportunity_decay (
                    opportunity_hash, detected_at, route_hash, expected_profit,
                    expected_profit_5s, expected_profit_30s, expected_profit_60s,
                    checked_5s_at, checked_30s_at, checked_60s_at,
                    pair_key, pair_label, venues_json, route_type, route_json, source, created_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(opportunity_hash) do update set
                    expected_profit = excluded.expected_profit,
                    expected_profit_5s = excluded.expected_profit_5s,
                    expected_profit_30s = excluded.expected_profit_30s,
                    expected_profit_60s = excluded.expected_profit_60s,
                    checked_5s_at = excluded.checked_5s_at,
                    checked_30s_at = excluded.checked_30s_at,
                    checked_60s_at = excluded.checked_60s_at,
                    pair_key = excluded.pair_key,
                    pair_label = excluded.pair_label,
                    venues_json = excluded.venues_json,
                    route_type = excluded.route_type,
                    route_json = excluded.route_json
                """,
                (
                    row["opportunity_hash"],
                    detected_at,
                    row["route_hash"],
                    expected_profit,
                    row["simulated_profit_5s"] if row["checked_5s_at"] is not None else None,
                    row["simulated_profit_30s"] if row["checked_30s_at"] is not None else None,
                    row["simulated_profit_60s"] if row["checked_60s_at"] is not None else None,
                    row["checked_5s_at"],
                    row["checked_30s_at"],
                    row["checked_60s_at"],
                    metadata["pair_key"],
                    metadata["pair_label"],
                    json.dumps(metadata["venues"], sort_keys=True),
                    metadata["route_type"],
                    route_payload,
                    "stored",
                    row["created_at"],
                ),
            )

    def _decay_route_metadata(self, route_payload: str | None, input_asset_id: int | None, involved_asset_ids: list[int]) -> dict:
        try:
            route = json.loads(route_payload or "[]")
        except json.JSONDecodeError:
            route = []
        if not isinstance(route, list):
            route = []
        venues = []
        for leg in route:
            venue = str(leg.get("venue") or leg.get("venue_id") or "unknown")
            if venue not in venues:
                venues.append(venue)
        if route:
            left = self._safe_int(route[0].get("input_asset_id"), input_asset_id or 0)
            right = self._safe_int(route[0].get("output_asset_id"), left)
        else:
            left = int(input_asset_id or 0)
            right = next((int(asset_id) for asset_id in involved_asset_ids if int(asset_id) != left), left)
        assets = sorted({left, right})
        route_type = "triangle" if len(route) >= 3 else "venue_arbitrage" if len(set(venues)) >= 2 else "single_venue"
        return {
            "pair_key": "-".join(str(asset_id) for asset_id in assets),
            "pair_label": "/".join(str(asset_id) for asset_id in assets),
            "venues": venues or ["unknown"],
            "route_type": route_type,
        }

    def _safe_int(self, value: object, default: int) -> int:
        try:
            if value is None or value == "":
                return int(default)
            return int(value)
        except (TypeError, ValueError):
            return int(default)

    def _backfill_paper_calibration(self, con: sqlite3.Connection) -> None:
        rows = con.execute(
            """
            select *
            from paper_trades
            order by id asc
            """
        ).fetchall()
        for row in rows:
            opportunity = con.execute(
                """
                select confidence_score
                from opportunities
                where route_hash = ?
                order by created_at desc, id desc
                limit 1
                """,
                (row["route_hash"],),
            ).fetchone()
            confidence = (
                float(opportunity["confidence_score"])
                if opportunity and opportunity["confidence_score"] is not None
                else self._paper_confidence_from_route(row["route_json"])
            )
            success = row["success"]
            if success is None and row["checked_30s_at"] is not None:
                success = int(float(row["simulated_profit_30s"] or 0.0) > 0)
            elif success is None and row["checked_5s_at"] is not None:
                success = int(float(row["simulated_profit_5s"] or 0.0) > 0)
            con.execute(
                """
                update paper_trades
                set confidence_score = ?,
                    success = ?
                where id = ?
                """,
                (confidence, success, row["id"]),
            )

    def _paper_confidence_from_route(self, route_json: str | None) -> float:
        try:
            route = json.loads(route_json or "[]")
        except json.JSONDecodeError:
            route = []
        max_impact = max((float(leg.get("price_impact_bps") or 0.0) for leg in route), default=0.0)
        return max(0.0, min(100.0, 100.0 - max_impact))

    def _update_paper_trade_checkpoint(
        self,
        con: sqlite3.Connection,
        row: sqlite3.Row,
        pool_by_id: dict[str, Pool],
        checked_at: float,
        suffix: str,
    ) -> bool:
        simulation = self._simulate_paper_route(row, pool_by_id)
        if not simulation["ok"]:
            con.execute(
                f"""
                update paper_trades
                set checked_{suffix}_at = ?,
                    failure_reason_{suffix} = ?,
                    survived_{suffix} = 0,
                    last_error = ?
                where id = ?
                """,
                (checked_at, simulation["reason"], simulation["reason"], row["id"]),
            )
            con.execute(
                f"""
                update opportunity_decay
                set checked_{suffix}_at = ?
                where opportunity_hash = ?
                """,
                (checked_at, row["opportunity_hash"]),
            )
            return False

        final_amount = float(simulation["final_amount"])
        expected_final_amount = float(row["expected_final_amount"] or 0.0)
        input_amount = float(row["input_amount"] or 0.0)
        simulated_profit = (
            final_amount
            - input_amount
            - float(row["estimated_network_fee"] or 0.0)
            - float(row["slippage_buffer"] or 0.0)
        )
        expected_net_profit = float(row["expected_net_profit"] or row["expected_profit"] or 0.0)
        quote_decay = expected_final_amount - final_amount
        profit_delta = simulated_profit - expected_net_profit
        con.execute(
            f"""
            update paper_trades
            set checked_{suffix}_at = ?,
                simulated_final_amount_{suffix} = ?,
                simulated_profit_{suffix} = ?,
                quote_decay_{suffix} = ?,
                expected_vs_simulated_profit_{suffix} = ?,
                survived_{suffix} = ?,
                failure_reason_{suffix} = null,
                success = ?,
                last_error = null
            where id = ?
            """,
            (
                checked_at,
                final_amount,
                simulated_profit,
                quote_decay,
                profit_delta,
                int(simulated_profit > 0),
                int(simulated_profit > 0),
                row["id"],
            ),
        )
        con.execute(
            f"""
            update opportunity_decay
            set expected_profit_{suffix} = ?,
                checked_{suffix}_at = ?
            where opportunity_hash = ?
            """,
            (simulated_profit, checked_at, row["opportunity_hash"]),
        )
        return True

    def _simulate_paper_route(self, row: sqlite3.Row, pool_by_id: dict[str, Pool]) -> dict:
        try:
            route = json.loads(row["route_json"])
        except (TypeError, json.JSONDecodeError):
            return {"ok": False, "reason": "paper route JSON is invalid"}
        if not route:
            return {"ok": False, "reason": "paper route is empty"}

        amount = float(row["input_amount"] or route[0].get("input_amount") or 0.0)
        for leg in route:
            pool = pool_by_id.get(leg.get("pool_id") or "")
            if pool is None:
                return {"ok": False, "reason": f"missing pool for paper route: {leg.get('pool_id')}"}
            quote = pool.quote(input_asset_id=int(leg["input_asset_id"]), input_amount=amount)
            if quote is None:
                return {
                    "ok": False,
                    "reason": (
                        f"could not quote {leg.get('pool_id')} "
                        f"for asset {leg.get('input_asset_id')}"
                    ),
                }
            amount = quote.output_amount
        return {"ok": True, "final_amount": amount}

    def _ensure_column(
        self,
        con: sqlite3.Connection,
        table_name: str,
        column_name: str,
        column_definition: str,
    ) -> None:
        columns = {row["name"] for row in con.execute(f"pragma table_info({table_name})")}
        if column_name in columns:
            return
        con.execute(f"alter table {table_name} add column {column_name} {column_definition}")

    def _record_balance_reconciliation(
        self,
        *,
        con: sqlite3.Connection,
        live_trade_id: int,
        route_hash: str | None,
        result: dict,
        created_at: float,
    ) -> None:
        reconciliation = result.get("balance_reconciliation")
        if not isinstance(reconciliation, dict):
            return
        con.execute(
            """
            insert into balance_reconciliations (
                live_trade_id, route_hash, status, ok, submitted, dry_run,
                expected_deltas_json, actual_deltas_json, variance_json,
                before_json, after_json, detail, created_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                live_trade_id,
                route_hash,
                reconciliation.get("status", "unknown"),
                None if reconciliation.get("ok") is None else int(bool(reconciliation.get("ok"))),
                int(bool(result.get("submitted"))),
                int(bool(result.get("dry_run", True))),
                json.dumps(reconciliation.get("expected_deltas") or {}),
                json.dumps(reconciliation.get("actual_deltas")) if reconciliation.get("actual_deltas") is not None else None,
                json.dumps(reconciliation.get("variance")) if reconciliation.get("variance") is not None else None,
                json.dumps(reconciliation.get("before")) if reconciliation.get("before") is not None else None,
                json.dumps(reconciliation.get("after")) if reconciliation.get("after") is not None else None,
                reconciliation.get("detail"),
                created_at,
            ),
        )

    def _row_to_reconciliation(self, row: sqlite3.Row) -> dict:
        data = dict(row)
        for source, default in (
            ("expected_deltas_json", {}),
            ("actual_deltas_json", None),
            ("variance_json", None),
            ("before_json", None),
            ("after_json", None),
        ):
            target = source.removesuffix("_json")
            raw = data.pop(source)
            data[target] = json.loads(raw) if raw else default
        return data

    def _row_to_payment_verification(self, row: sqlite3.Row) -> dict:
        data = dict(row)
        data["ok"] = bool(data["ok"])
        data["result"] = json.loads(data.pop("result_json"))
        return data

    def _row_to_refund_case(self, row: sqlite3.Row) -> dict:
        data = dict(row)
        data["guardrails"] = json.loads(data.pop("guardrails_json"))
        data["decision"] = json.loads(data.pop("decision_json"))
        return data

    def _daily_report_window(self, report_date: str | None = None, now: float | None = None) -> tuple[str, float, float]:
        current_time = float(now or time.time())
        if report_date:
            report_day = datetime.strptime(report_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            current_day = datetime.fromtimestamp(current_time, tz=timezone.utc)
            report_day = current_day.replace(hour=0, minute=0, second=0, microsecond=0)
        start = report_day.timestamp()
        end = start + 86_400
        if start <= current_time < end:
            end = current_time
        return report_day.date().isoformat(), start, end

    def _market_intelligence_evidence_dates(self, limit_days: int = 7) -> list[str]:
        with self._connect() as con:
            rows = con.execute(
                """
                select day
                from (
                    select date(created_at, 'unixepoch') as day from opportunities
                    union
                    select date(captured_at, 'unixepoch') as day from pool_snapshots
                    union
                    select date(created_at, 'unixepoch') as day from paper_trades
                    union
                    select date(created_at, 'unixepoch') as day from risk_decisions
                    union
                    select date(checked_at, 'unixepoch') as day from service_health
                )
                where day is not null
                order by day desc
                limit ?
                """,
                (max(1, int(limit_days)),),
            ).fetchall()
        return [str(row["day"]) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.database_path)
        con.row_factory = sqlite3.Row
        return con
