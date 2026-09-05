---
document_id: POL-FEE-001
document_type: policy
title: Execution Fee Economics Control
risk_domain: fee_bps_outlier
version: 1.7
effective_from: 2026-03-01
status: active
jurisdiction: global
owner: execution-quality
synthetic: true
---

# Execution Fee Economics Control

## Purpose

This synthetic policy detects execution fees that are inconsistent with approved venue, maker-taker, VIP-tier, and routing economics.

## Fee Basis Points

Fee basis points are calculated as fee divided by absolute trade notional, multiplied by 10,000. Rebates must preserve their signed value and must not be converted to positive charges.

## Expected Fee Context

The expected fee must account for venue, account tier, maker or taker status, instrument type, promotional schedule, and effective timestamp. A statistical peer group should not mix materially different fee schedules.

## Alert Investigation

When actual fee basis points exceed the approved static threshold or an approved robust statistical threshold, operations must verify the charged tier, order classification, routing path, currency conversion, and duplicate-fee possibility. A fee alert does not by itself authorize a trading change.

## Data Quality

The baseline must use point-in-time historical observations and a minimum sample size. Current-event information must not leak into a production baseline. Median and median absolute deviation are preferred when the fee distribution is skewed or contains outliers.
