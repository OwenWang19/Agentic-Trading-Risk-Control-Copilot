---
document_id: RUN-REC-001
document_type: runbook
title: Settlement Break Investigation Runbook
risk_domain: reconciliation_break
version: 2.2
effective_from: 2026-01-15
status: active
jurisdiction: global
owner: trading-operations
synthetic: true
---

# Settlement Break Investigation Runbook

## Establish the Timeline

Collect order, fill, allocation, venue-confirmation, settlement, and internal-ledger timestamps. Determine whether the break may be explained by an allowed processing delay.

## Match Identifiers

Match venue execution ID, client order ID, internal trade ID, symbol, account, side, and settlement currency. Search for duplicated, missing, or out-of-order events.

## Classify the Break

Classify the case as partial fill, partial settlement, rejection, late event, duplicate, fee or currency difference, stale internal ledger, or unknown. Do not change either ledger solely to remove the alert.

## Escalate and Close

Escalate material or aging breaks to operations and finance. Attach venue evidence, record any approved adjustment, and verify that expected and settled quantities agree before closure.
