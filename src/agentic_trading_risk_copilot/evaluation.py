from __future__ import annotations

import json
from pathlib import Path

from .models import AgentState


def evaluate_findings(state: AgentState, expected_path: Path) -> dict[str, float]:
    expected = set(json.loads(expected_path.read_text())["expected_finding_ids"])
    observed = {finding.finding_id for finding in state.findings}

    true_positive = len(expected & observed)
    false_positive = len(observed - expected)
    false_negative = len(expected - observed)

    precision = true_positive / (true_positive + false_positive) if observed else 0.0
    recall = true_positive / (true_positive + false_negative) if expected else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    metrics = {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "true_positive": float(true_positive),
        "false_positive": float(false_positive),
        "false_negative": float(false_negative),
    }
    state.metrics.update(metrics)
    state.trace(
        "evaluate_findings",
        {"expected_path": str(expected_path)},
        {"metrics": metrics, "observed": sorted(observed), "expected": sorted(expected)},
    )
    return metrics
