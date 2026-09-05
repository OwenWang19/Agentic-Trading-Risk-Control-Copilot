---
document_id: INC-INV-001
document_type: incident
title: Inventory Breach Caused by Delayed Hedge Fills
risk_domain: inventory_limit
version: 1.0
effective_from: 2026-05-18
status: active
jurisdiction: global
owner: market-risk
synthetic: true
---

# Inventory Breach Caused by Delayed Hedge Fills

## Summary

A synthetic ETH perpetual market-making strategy accumulated inventory above its symbol limit after several customer fills. Hedge orders remained open because the configured limit price did not follow a rapid market move.

## Evidence

The position service was current, the mark price passed freshness checks, and the exposure increased after customer fills. The hedge order lifecycle showed repeated unfilled orders with unchanged limit prices.

## Root Cause

The hedge-pricing parameter did not adapt to the volatility regime. The monitoring alert was correct; there was no position-data or mark-price error.

## Resolution

An authorized trader replaced the hedge orders within a bounded slippage limit. The team added hedge-age monitoring and required an expiring human approval for parameter changes.

## Reuse Warning

This historical incident is analogous evidence only. It must not be treated as proof that a new inventory breach has the same root cause.
