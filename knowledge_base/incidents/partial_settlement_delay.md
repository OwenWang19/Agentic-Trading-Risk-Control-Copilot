---
document_id: INC-REC-001
document_type: incident
title: Venue Partial Settlement Delay
risk_domain: reconciliation_break
version: 1.0
effective_from: 2026-06-07
status: active
jurisdiction: global
owner: trading-operations
synthetic: true
---

# Venue Partial Settlement Delay

## Summary

A synthetic venue confirmation reported only part of an expected asset quantity while the internal ledger contained the full fill. The remaining settlement event arrived after the normal processing window.

## Evidence

Order and fill identifiers matched, no duplicate was present, and the first venue event carried a partial-settlement status. A second event later completed the quantity.

## Root Cause

The venue delivered settlement events in two batches during a maintenance period. The internal ledger was not incorrect, but the temporary difference required an open reconciliation case.

## Resolution

Operations linked both venue events, verified the final quantity, and closed the case. The team added venue-specific delay monitoring without increasing the hard quantity tolerance.

## Reuse Warning

An old partial-settlement incident does not prove that a current break will self-resolve. Current venue evidence and aging must be checked.
