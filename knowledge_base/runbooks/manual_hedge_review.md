---
document_id: RUN-HEDGE-001
document_type: runbook
title: Manual Hedge Review Runbook
risk_domain: inventory_limit
version: 1.3
effective_from: 2026-01-01
status: active
jurisdiction: global
owner: market-risk
synthetic: true
---

# Manual Hedge Review Runbook

## Triage

Confirm the position snapshot, signed quantity, mark price, mark timestamp, notional limit, and utilization. Stop the investigation and label data quality if the mark or position is stale.

## Diagnose

Inspect recent fills, rejected hedge orders, outstanding orders, funding events, transfers, and strategy configuration. Compare inventory across correlated instruments before assuming that the single-symbol position is unhedged.

## Prepare a Proposal

If remediation is required, calculate a proposed hedge quantity, venue, order type, maximum notional, expected fees, expected slippage, and residual basis risk. The proposal must reference the originating finding and policy version.

## Approval

Obtain approval from an authorized trader and risk reviewer. The approval must expire and cannot be reused after material price, position, or order-book changes.

## Verify

After execution, reconcile fills and recalculate inventory utilization. Close the case only when post-action evidence is attached and the position is within the approved limit.
