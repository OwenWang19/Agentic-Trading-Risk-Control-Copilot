---
document_id: POL-INV-001
document_type: policy
title: Marked Inventory Exposure Control
risk_domain: inventory_limit
version: 2.1
effective_from: 2026-01-01
status: active
jurisdiction: global
owner: market-risk
synthetic: true
---

# Marked Inventory Exposure Control

## Purpose

This synthetic policy defines how a trading desk monitors marked inventory exposure. It applies to perpetual and spot inventory recorded by the internal position service.

## Exposure Calculation

The desk calculates single-symbol inventory notional as the absolute position quantity multiplied by the approved mark price and any applicable contract multiplier. A mark must be rejected when it is stale, missing, or outside the approved index-price deviation band.

## Limit Breach

Inventory utilization is inventory notional divided by the configured symbol-level notional limit. Utilization above 100 percent is a limit breach and must be escalated to the market-risk desk. The finding must include the position snapshot, mark timestamp, notional, configured limit, utilization, account or desk scope, and policy version.

## Authorization Boundary

The monitoring system may recommend inventory reduction or a hedge review, but it must not place a hedge, change a limit, or pause a strategy without an authenticated human approval. Approval must bind the symbol, account, quantity, maximum notional, slippage limit, and expiry time.

## Evidence and Closure

A breach remains open until the risk desk verifies fresh prices, reviews recent fills, records an approved remediation, and confirms that post-action utilization has returned within the limit. The final case must preserve an immutable audit trail.
