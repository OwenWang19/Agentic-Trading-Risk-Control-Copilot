---
document_id: RUN-FEE-001
document_type: runbook
title: Execution Fee Anomaly Investigation Runbook
risk_domain: fee_bps_outlier
version: 1.2
effective_from: 2026-03-01
status: active
jurisdiction: global
owner: execution-operations
synthetic: true
---

# Execution Fee Anomaly Investigation Runbook

## Validate Inputs

Recalculate absolute trade notional and fee basis points. Verify fee currency, quote-to-USD conversion, maker-taker classification, and whether the value includes funding or settlement charges.

## Compare the Schedule

Retrieve the venue fee schedule and account VIP tier that were effective at execution time. Check promotional discounts, rebates, broker markups, and account migration events.

## Investigate Routing

Compare expected and actual routing. A passive order that crossed the spread may be charged as taker. Confirm whether the strategy, smart-order router, or venue changed the final liquidity classification.

## Resolve

Correct configuration or open a venue dispute when evidence supports an incorrect charge. Record the expected rate, actual rate, monetary impact, owner, and final resolution. Trading changes require separate authorization.
