from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import Action, AgentState, Finding, RoutingDecision, Severity, ToolCall


def _severity_label(severity: Severity) -> str:
    return severity.value.upper()


def finding_to_dict(finding: Finding) -> dict[str, object]:
    data = asdict(finding)
    data["severity"] = finding.severity.value
    return data


def action_to_dict(action: Action) -> dict[str, object]:
    return asdict(action)


def trace_to_dict(call: ToolCall) -> dict[str, object]:
    return asdict(call)


def routing_to_dict(decision: RoutingDecision) -> dict[str, object]:
    return {
        "intent": decision.intent.value,
        "symbol": decision.symbol,
        "requested_action": decision.requested_action,
        "confidence": decision.confidence,
        "rationale": decision.rationale,
    }


def write_json_audit(state: AgentState, output_path: Path) -> None:
    payload = {
        "metrics": state.metrics,
        "routing_decision": routing_to_dict(state.routing_decision) if state.routing_decision else None,
        "knowledge_answer": asdict(state.knowledge_answer) if state.knowledge_answer else None,
        "findings": [finding_to_dict(finding) for finding in state.findings],
        "actions": [action_to_dict(action) for action in state.actions],
        "tool_trace": [trace_to_dict(call) for call in state.tool_trace],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def write_markdown_report(state: AgentState, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    approval_required = [action for action in state.actions if action.approval_required]
    ready_for_ops = [action for action in state.actions if not action.approval_required]

    lines = [
        "# Trading Risk Control Copilot Report",
        "",
        "## Executive Summary",
        "",
        (
            f"The copilot identified {len(state.findings)} control findings, "
            f"with {len(approval_required)} market-impacting actions held for human approval."
        ),
        "",
    ]

    if state.routing_decision:
        decision = state.routing_decision
        lines.extend(
            [
                "## Request Routing",
                "",
                f"- Intent: `{decision.intent.value}`",
                f"- Symbol scope: `{decision.symbol or 'ALL'}`",
                f"- Requested action: `{decision.requested_action}`",
                f"- Confidence: `{decision.confidence:.2f}`",
                f"- Rationale: {decision.rationale}",
                "- Execution boundary: The current copilot analyzes and recommends only; it never places trades.",
                "",
            ]
        )

    if state.knowledge_answer:
        answer = state.knowledge_answer
        heading = "Grounded Policy Answer" if answer.grounded else "Policy Answer — Insufficient Context"
        lines.extend([f"## {heading}", "", answer.answer, ""])
        if answer.root_cause_hypotheses:
            lines.extend(["### Hypotheses", ""])
            lines.extend(f"- {item}" for item in answer.root_cause_hypotheses)
            lines.append("")
        if answer.recommended_next_steps:
            lines.extend(["### Recommended Next Steps", ""])
            lines.extend(f"- {item}" for item in answer.recommended_next_steps)
            lines.append("")
        lines.extend(["### Citations", ""])
        lines.extend(
            f"- `{citation.chunk_id}` — {citation.title}, {citation.section} (score `{citation.score:.4f}`)"
            for citation in answer.citations
        )
        if not answer.citations:
            lines.append("- No sufficiently relevant source was retrieved; the agent abstained.")
        lines.append("")

    lines.extend(["## Findings", ""])

    for finding in state.findings:
        lines.extend(
            [
                f"### {finding.finding_id} - {_severity_label(finding.severity)} - {finding.category}",
                "",
                f"- Symbol: `{finding.symbol}`",
                f"- Evidence: {finding.evidence}",
                f"- Policy: `{finding.policy_rule_id}`",
                f"- Root cause: {finding.root_cause}",
                f"- Recommended action: {finding.recommended_action}",
                f"- Human approval required: `{str(finding.approval_required).lower()}`",
                "",
            ]
        )
        if finding.rag_analysis:
            analysis = finding.rag_analysis
            heading = "Retrieved Policy Context" if analysis.grounded else "Policy Context — Insufficient Evidence"
            lines.extend([f"#### {heading}", "", analysis.answer, ""])
            if analysis.root_cause_hypotheses:
                lines.extend(["Hypotheses (not confirmed):", ""])
                lines.extend(f"- {item}" for item in analysis.root_cause_hypotheses)
                lines.append("")
            if analysis.recommended_next_steps:
                lines.extend(["Evidence-based next steps:", ""])
                lines.extend(f"- {item}" for item in analysis.recommended_next_steps)
                lines.append("")
            lines.extend(["Citations:", ""])
            lines.extend(
                f"- `{citation.chunk_id}` — {citation.title}, {citation.section} (score `{citation.score:.4f}`)"
                for citation in analysis.citations
            )
            if not analysis.citations:
                lines.append("- The agent abstained because no sufficiently relevant source was retrieved.")
            lines.append("")

    lines.extend(["## Action Queue", ""])
    for action in state.actions:
        lines.extend(
            [
                f"- `{action.action_id}` / `{action.status}` / `{action.action_type}`: "
                f"{action.description} ({action.finding_id})"
            ]
        )

    lines.extend(["", "## Evaluation", ""])
    if "precision" in state.metrics:
        lines.extend(
            [
                f"- Precision: `{state.metrics['precision']:.4f}`",
                f"- Recall: `{state.metrics['recall']:.4f}`",
                f"- F1: `{state.metrics['f1']:.4f}`",
            ]
        )
    else:
        lines.append("- No ground-truth evaluation file supplied.")

    lines.extend(["", "## Tool Trace", ""])
    for index, call in enumerate(state.tool_trace, start=1):
        lines.append(f"{index}. `{call.tool_name}`")

    output_path.write_text("\n".join(lines) + "\n")
