from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskIntent(str, Enum):
    FULL_RISK_SCAN = "full_risk_scan"
    TRADE_RISK_REVIEW = "trade_risk_review"
    TRADE_NOTIONAL_REVIEW = "trade_notional_review"
    INVENTORY_RISK_REVIEW = "inventory_risk_review"
    RECONCILIATION_REVIEW = "reconciliation_review"
    FEE_ANOMALY_REVIEW = "fee_anomaly_review"
    POLICY_QA = "policy_qa"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class Trade:
    trade_id: str
    timestamp: datetime
    venue: str
    symbol: str
    side: str
    quantity: float
    price: float
    fee: float
    order_type: str
    strategy: str

    @property
    def notional(self) -> float:
        return self.quantity * self.price


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: float
    mark_price: float
    limit_quantity: float
    limit_notional: float

    @property
    def notional(self) -> float:
        return abs(self.quantity * self.mark_price)


@dataclass(frozen=True)
class LedgerEntry:
    trade_id: str
    expected_quantity: float
    settled_quantity: float
    status: str
    reason: str

    @property
    def break_quantity(self) -> float:
        return self.settled_quantity - self.expected_quantity


@dataclass(frozen=True)
class PolicyRule:
    rule_id: str
    description: str
    threshold: float
    unit: str
    severity: Severity
    action_type: str


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    document_id: str
    title: str
    section: str
    score: float


@dataclass
class GroundedAnalysis:
    answer: str
    grounded: bool = True
    root_cause_hypotheses: list[str] = field(default_factory=list)
    recommended_next_steps: list[str] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)


@dataclass
class Finding:
    finding_id: str
    severity: Severity
    category: str
    symbol: str
    evidence: str
    policy_rule_id: str
    root_cause: str = "unassigned"
    recommended_action: str = "triage"
    approval_required: bool = False
    rag_analysis: GroundedAnalysis | None = None


@dataclass
class Action:
    action_id: str
    finding_id: str
    action_type: str
    description: str
    approval_required: bool
    status: str = "proposed"


@dataclass
class ToolCall:
    tool_name: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]


@dataclass(frozen=True)
class RoutingDecision:
    intent: RiskIntent
    symbol: str | None
    requested_action: str
    confidence: float
    rationale: str


@dataclass
class AgentState:
    trades: list[Trade]
    positions: list[Position]
    ledger: list[LedgerEntry]
    policies: dict[str, PolicyRule]
    findings: list[Finding] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
    tool_trace: list[ToolCall] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    routing_decision: RoutingDecision | None = None
    user_request: str | None = None
    knowledge_answer: GroundedAnalysis | None = None

    def trace(self, tool_name: str, inputs: dict[str, Any], outputs: dict[str, Any]) -> None:
        self.tool_trace.append(ToolCall(tool_name=tool_name, inputs=inputs, outputs=outputs))
