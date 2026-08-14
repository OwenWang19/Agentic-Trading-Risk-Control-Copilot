from __future__ import annotations

from .guardrails import apply_action_guardrails
from .models import Action, AgentState, Finding
from .tools import (
    dedupe_findings,
    detect_fee_bps_outliers,
    detect_inventory_limit_breaches,
    detect_reconciliation_breaks,
    detect_single_trade_notional_breaches,
    severity_rank,
)


class RiskMonitorAgent:
    name = "risk-monitor-agent"

    def run(self, state: AgentState) -> AgentState:
        findings = []
        findings.extend(detect_single_trade_notional_breaches(state))
        findings.extend(detect_inventory_limit_breaches(state))
        findings.extend(detect_fee_bps_outliers(state))
        state.findings = dedupe_findings(state.findings + findings)
        state.trace(self.name, {}, {"findings_after_agent": len(state.findings)})
        return state


class ReconciliationAgent:
    name = "reconciliation-agent"

    def run(self, state: AgentState) -> AgentState:
        findings = detect_reconciliation_breaks(state)
        state.findings = dedupe_findings(state.findings + findings)
        state.trace(self.name, {}, {"findings_after_agent": len(state.findings)})
        return state


class RootCauseAgent:
    name = "root-cause-agent"

    def run(self, state: AgentState) -> AgentState:
        for finding in state.findings:
            finding.root_cause = self._infer_root_cause(finding)
        state.trace(
            self.name,
            {"finding_ids": [finding.finding_id for finding in state.findings]},
            {"root_causes": {finding.finding_id: finding.root_cause for finding in state.findings}},
        )
        return state

    def _infer_root_cause(self, finding: Finding) -> str:
        if finding.category == "single_trade_notional":
            return "large RFQ/slippage-sensitive execution exceeded pre-trade notional control"
        if finding.category == "inventory_limit":
            return "post-trade inventory drift breached desk-level exposure limit"
        if finding.category == "reconciliation_break":
            return "venue settlement quantity differs from internal expected fill quantity"
        if finding.category == "fee_bps_outlier":
            return "fee schedule or order routing likely deviated from expected maker/taker economics"
        return "requires manual triage"


class ControlActionAgent:
    name = "control-action-agent"

    def run(self, state: AgentState) -> AgentState:
        actions = [self._propose_action(index, finding) for index, finding in enumerate(state.findings, start=1)]
        state.actions = apply_action_guardrails(actions)
        for action in state.actions:
            matching = next(finding for finding in state.findings if finding.finding_id == action.finding_id)
            matching.recommended_action = action.description
            matching.approval_required = action.approval_required
        state.trace(
            self.name,
            {"finding_ids": [finding.finding_id for finding in state.findings]},
            {"action_ids": [action.action_id for action in state.actions]},
        )
        return state

    def _propose_action(self, index: int, finding: Finding) -> Action:
        if finding.category == "single_trade_notional":
            return Action(
                action_id=f"A-{index:03d}",
                finding_id=finding.finding_id,
                action_type="quote_size_reduction",
                description="route to trader for quote-size review before next RFQ cycle",
                approval_required=True,
            )
        if finding.category == "inventory_limit":
            return Action(
                action_id=f"A-{index:03d}",
                finding_id=finding.finding_id,
                action_type="manual_hedge_review",
                description="request human review of inventory reduction or hedge plan",
                approval_required=True,
            )
        if finding.category == "reconciliation_break":
            return Action(
                action_id=f"A-{index:03d}",
                finding_id=finding.finding_id,
                action_type="ops_reconciliation_case",
                description="open reconciliation case with venue fill evidence attached",
                approval_required=False,
            )
        if finding.category == "fee_bps_outlier":
            return Action(
                action_id=f"A-{index:03d}",
                finding_id=finding.finding_id,
                action_type="fee_schedule_review",
                description="compare charged fee tier against expected venue maker/taker schedule",
                approval_required=False,
            )
        return Action(
            action_id=f"A-{index:03d}",
            finding_id=finding.finding_id,
            action_type="manual_triage",
            description="send to risk analyst for manual triage",
            approval_required=True,
        )


class SupervisorAgent:
    name = "supervisor-agent"

    def __init__(self) -> None:
        self.agents = [
            RiskMonitorAgent(),
            ReconciliationAgent(),
            RootCauseAgent(),
            ControlActionAgent(),
        ]

    def run(self, state: AgentState) -> AgentState:
        for agent in self.agents:
            state = agent.run(state)
        state.findings.sort(key=lambda finding: severity_rank(finding.severity), reverse=True)
        state.metrics["finding_count"] = float(len(state.findings))
        state.metrics["approval_required_count"] = float(sum(1 for action in state.actions if action.approval_required))
        state.trace(
            self.name,
            {"agents": [agent.name for agent in self.agents]},
            {
                "finding_count": len(state.findings),
                "approval_required_count": int(state.metrics["approval_required_count"]),
            },
        )
        return state
