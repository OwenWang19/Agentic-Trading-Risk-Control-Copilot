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

    def trace(self, tool_name: str, inputs: dict[str, Any], outputs: dict[str, Any]) -> None:
        self.tool_trace.append(ToolCall(tool_name=tool_name, inputs=inputs, outputs=outputs))
