---
document_id: INC-TRD-001
document_type: incident
title: Oversized RFQ Hedge Configuration
risk_domain: single_trade_notional
version: 1.0
effective_from: 2026-04-11
status: active
jurisdiction: global
owner: trading-risk
synthetic: true
---

# Oversized RFQ Hedge Configuration

## Summary

A synthetic RFQ hedge exceeded the single-trade notional threshold after a strategy configuration used position units where quote-currency notional was expected.

## Evidence

The trade was unique and correctly reported by the venue. Configuration history showed a unit mismatch introduced shortly before execution. Final inventory remained within its separate position limit.

## Root Cause

The strategy parameter lacked unit validation and an independent pre-trade notional check.

## Resolution

The team corrected the unit, reduced the maximum quote size after human approval, and added typed configuration validation plus a dry-run preview.

## Reuse Warning

An oversized trade can also be a valid block or client execution. Historical similarity is not proof of a configuration error.
