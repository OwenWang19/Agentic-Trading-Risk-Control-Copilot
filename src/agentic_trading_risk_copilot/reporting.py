from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import Action, AgentState, Finding, Severity, ToolCall


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


def write_json_audit(state: AgentState, output_path: Path) -> None:
    payload = {
        "metrics": state.metrics,
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
        "## Findings",
        "",
    ]

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
