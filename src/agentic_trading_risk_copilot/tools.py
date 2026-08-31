from __future__ import annotations

from statistics import mean, pstdev

from .models import AgentState, Finding, Severity


def retrieve_policy(state: AgentState, rule_id: str):
    policy = state.policies[rule_id]
    state.trace(
        "retrieve_policy",
        {"rule_id": rule_id},
        {
            "description": policy.description,
            "threshold": policy.threshold,
            "unit": policy.unit,
            "severity": policy.severity.value,
        },
    )
    return policy


def detect_single_trade_notional_breaches(state: AgentState, symbol: str | None = None) -> list[Finding]:
    policy = retrieve_policy(state, "TRADE_NOTIONAL_LIMIT")
    findings: list[Finding] = []
    for trade in state.trades:
        if symbol is not None and trade.symbol != symbol:
            continue
        if trade.notional > policy.threshold:
            findings.append(
                Finding(
                    finding_id=f"F-TRADE-{trade.trade_id}",
                    severity=policy.severity,
                    category="single_trade_notional",
                    symbol=trade.symbol,
                    evidence=(
                        f"{trade.trade_id} notional ${trade.notional:,.2f} exceeds "
                        f"${policy.threshold:,.2f} threshold on {trade.venue}."
                    ),
                    policy_rule_id=policy.rule_id,
                )
            )
    state.trace(
        "detect_single_trade_notional_breaches",
        {"threshold": policy.threshold, "symbol": symbol},
        {"finding_ids": [finding.finding_id for finding in findings]},
    )
    return findings


def detect_inventory_limit_breaches(state: AgentState, symbol: str | None = None) -> list[Finding]:
    policy = retrieve_policy(state, "INVENTORY_LIMIT")
    findings: list[Finding] = []
    for position in state.positions:
        if symbol is not None and position.symbol != symbol:
            continue
        utilization = position.notional / position.limit_notional if position.limit_notional else 0.0
        if position.notional > position.limit_notional:
            findings.append(
                Finding(
                    finding_id=f"F-INV-{position.symbol}",
                    severity=policy.severity,
                    category="inventory_limit",
                    symbol=position.symbol,
                    evidence=(
                        f"{position.symbol} inventory notional ${position.notional:,.2f} "
                        f"is {utilization:.1%} of limit ${position.limit_notional:,.2f}."
                    ),
                    policy_rule_id=policy.rule_id,
                )
            )
    state.trace(
        "detect_inventory_limit_breaches",
        {"rule_id": policy.rule_id, "symbol": symbol},
        {"finding_ids": [finding.finding_id for finding in findings]},
    )
    return findings


def detect_reconciliation_breaks(state: AgentState, symbol: str | None = None) -> list[Finding]:
    policy = retrieve_policy(state, "RECON_BREAK_QTY")
    findings: list[Finding] = []
    for entry in state.ledger:
        trade = next((trade for trade in state.trades if trade.trade_id == entry.trade_id), None)
        if symbol is not None and (trade is None or trade.symbol != symbol):
            continue
        if abs(entry.break_quantity) > policy.threshold or entry.status.lower() != "matched":
            finding_symbol = trade.symbol if trade else "UNKNOWN"
            findings.append(
                Finding(
                    finding_id=f"F-RECON-{entry.trade_id}",
                    severity=policy.severity,
                    category="reconciliation_break",
                    symbol=finding_symbol,
                    evidence=(
                        f"{entry.trade_id} expected {entry.expected_quantity:g}, settled "
                        f"{entry.settled_quantity:g}, break {entry.break_quantity:+g}; reason={entry.reason}."
                    ),
                    policy_rule_id=policy.rule_id,
                )
            )
    state.trace(
        "detect_reconciliation_breaks",
        {"threshold": policy.threshold, "symbol": symbol},
        {"finding_ids": [finding.finding_id for finding in findings]},
    )
    return findings


def detect_fee_bps_outliers(state: AgentState, symbol: str | None = None) -> list[Finding]:
    policy = retrieve_policy(state, "FEE_BPS_OUTLIER")
    scoped_trades = [trade for trade in state.trades if symbol is None or trade.symbol == symbol]
    bps_by_trade = {trade.trade_id: trade.fee / trade.notional * 10_000 for trade in state.trades if trade.notional}
    values = list(bps_by_trade.values())
    baseline = mean(values) if values else 0.0
    sigma = pstdev(values) if len(values) > 1 else 0.0
    cutoff = max(policy.threshold, baseline + 2.0 * sigma)
    findings: list[Finding] = []
    for trade in scoped_trades:
        fee_bps = bps_by_trade.get(trade.trade_id, 0.0)
        if fee_bps > cutoff:
            findings.append(
                Finding(
                    finding_id=f"F-FEE-{trade.trade_id}",
                    severity=policy.severity,
                    category="fee_bps_outlier",
                    symbol=trade.symbol,
                    evidence=(
                        f"{trade.trade_id} fee {fee_bps:.2f} bps exceeds dynamic cutoff "
                        f"{cutoff:.2f} bps; venue={trade.venue}, order_type={trade.order_type}."
                    ),
                    policy_rule_id=policy.rule_id,
                )
            )
    state.trace(
        "detect_fee_bps_outliers",
        {"static_threshold_bps": policy.threshold, "baseline_bps": round(baseline, 4), "symbol": symbol},
        {"dynamic_cutoff_bps": round(cutoff, 4), "finding_ids": [finding.finding_id for finding in findings]},
    )
    return findings


def dedupe_findings(findings: list[Finding]) -> list[Finding]:
    seen: set[str] = set()
    unique: list[Finding] = []
    for finding in findings:
        if finding.finding_id not in seen:
            seen.add(finding.finding_id)
            unique.append(finding)
    return unique


def severity_rank(severity: Severity) -> int:
    return {
        Severity.LOW: 1,
        Severity.MEDIUM: 2,
        Severity.HIGH: 3,
        Severity.CRITICAL: 4,
    }[severity]
