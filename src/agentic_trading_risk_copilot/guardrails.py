from __future__ import annotations

from .models import Action


HUMAN_APPROVAL_ACTION_TYPES = {
    "quote_size_reduction",
    "manual_hedge_review",
    "limit_override_request",
    "strategy_pause",
}


def apply_action_guardrails(actions: list[Action]) -> list[Action]:
    """Mark market-impacting actions as awaiting human approval.

    The copilot is intentionally not allowed to auto-change trading limits,
    pause strategies, or place hedges. It can propose and document actions.
    """

    guarded: list[Action] = []
    for action in actions:
        if action.action_type in HUMAN_APPROVAL_ACTION_TYPES:
            action.approval_required = True
            action.status = "awaiting_human_approval"
        else:
            action.status = "ready_for_ops_queue"
        guarded.append(action)
    return guarded
