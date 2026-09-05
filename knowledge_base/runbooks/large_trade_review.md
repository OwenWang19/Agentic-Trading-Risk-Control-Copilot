---
document_id: RUN-TRD-001
document_type: runbook
title: Large Trade and RFQ Review Runbook
risk_domain: single_trade_notional
version: 1.1
effective_from: 2026-02-01
status: active
jurisdiction: global
owner: trading-risk
synthetic: true
---

# Large Trade and RFQ Review Runbook

## Validate the Event

Verify trade ID, venue, symbol, side, filled quantity, execution price, contract multiplier, and USD conversion. Confirm that the event is not duplicated and that the threshold was effective at decision time.

## Identify the Source

Determine whether the trade came from an RFQ hedge, algorithmic strategy, manual order, liquidation flow, or approved block trade. Review order parameters and authorization logs.

## Assess Impact

Estimate realized slippage, market impact, resulting inventory, liquidity concentration, and whether order slicing would have reduced risk without violating execution requirements.

## Remediation

A quote-size reduction or strategy-parameter change must be proposed with an expiry time and approved by the strategy owner or trader. Do not automatically reverse a valid client or hedge trade solely because it exceeded the monitoring threshold.
