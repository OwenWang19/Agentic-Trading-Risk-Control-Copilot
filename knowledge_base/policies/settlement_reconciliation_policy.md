---
document_id: POL-REC-001
document_type: policy
title: Venue Settlement Reconciliation Control
risk_domain: reconciliation_break
version: 3.0
effective_from: 2026-01-15
status: active
jurisdiction: global
owner: trading-operations
synthetic: true
---

# Venue Settlement Reconciliation Control

## Purpose

This synthetic policy requires internal trade obligations to be reconciled against the quantities and statuses confirmed by the execution venue or settlement system.

## Definitions

Expected quantity is the quantity that the internal order and fill ledger expects to settle. Settled quantity is the quantity confirmed and posted by the venue or settlement ledger. Break quantity is settled quantity minus expected quantity.

## Break Detection

A case must be opened when the absolute break quantity exceeds the approved tolerance or when the venue status is not matched. The case must retain trade ID, symbol, expected quantity, settled quantity, break quantity, venue status, reason, and event timestamps.

## Investigation and Escalation

Operations must determine whether the difference is caused by a partial fill, partial settlement, rejected fill, late event, duplicated event, currency conversion, stale internal ledger, or venue outage. Material or aging breaks must be escalated based on notional, asset, client impact, and settlement deadline.

## Closure

A reconciliation case closes only after both ledgers agree or an authorized accounting adjustment is recorded. The system must not silently overwrite either ledger to force a match.
