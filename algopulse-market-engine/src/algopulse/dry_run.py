from __future__ import annotations

from dataclasses import dataclass

from algopulse.models import Opportunity


@dataclass(frozen=True)
class DryRunExecutionPlan:
    route_hash: str
    route: list[dict]
    expected_net_profit: float
    policy_note: str


class DryRunExecutor:
    def build_plan(self, opportunity: Opportunity) -> DryRunExecutionPlan:
        return DryRunExecutionPlan(
            route_hash=opportunity.route_hash,
            route=opportunity.route,
            expected_net_profit=opportunity.expected_net_profit,
            policy_note="Dry run only. Live signing is intentionally disabled in Phase 0 starter.",
        )
