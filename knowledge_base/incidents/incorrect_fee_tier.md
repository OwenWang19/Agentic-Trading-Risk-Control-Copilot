---
document_id: INC-FEE-001
document_type: incident
title: Incorrect Venue Fee Tier After Account Migration
risk_domain: fee_bps_outlier
version: 1.0
effective_from: 2026-07-02
status: active
jurisdiction: global
owner: execution-operations
synthetic: true
---

# Incorrect Venue Fee Tier After Account Migration

## Summary

A synthetic trading account was charged the default taker rate after migration to a new venue sub-account, producing fee basis points above the expected peer group.

## Evidence

Trade notional and fee currency were correct. Venue account metadata showed that the VIP tier had not propagated to the new sub-account. Similar strategies on the original account were charged the approved rate.

## Root Cause

The account-migration workflow created the sub-account before the fee-tier configuration completed.

## Resolution

Operations corrected the venue configuration, requested a fee adjustment, and added a pre-activation fee-tier verification step to account onboarding.

## Reuse Warning

Fee-tier migration is one hypothesis. A new alert still requires checks for maker-taker classification, routing, conversion, and duplicate charges.
