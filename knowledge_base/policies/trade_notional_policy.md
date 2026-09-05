---
document_id: POL-TRD-001
document_type: policy
title: Single-Trade Notional Review Control
risk_domain: single_trade_notional
version: 1.4
effective_from: 2026-02-01
status: active
jurisdiction: global
owner: trading-risk
synthetic: true
---

# Single-Trade Notional Review Control

## Purpose

This synthetic policy limits the market-impact, fat-finger, liquidity, and mandate risk created by a single automated trade.

## Notional Calculation

Trade notional is the absolute filled quantity multiplied by execution price, contract multiplier, and the applicable quote-to-USD conversion rate. The control uses filled notional for post-trade monitoring and projected notional for pre-trade authorization.

## Threshold Breach

A trade above the approved single-trade notional threshold must be flagged even when the resulting net inventory remains within its position limit. The evidence must include trade ID, symbol, venue, strategy, order type, notional, threshold, and policy version.

## Required Review

The trading desk must review whether the trade resulted from an approved RFQ, strategy configuration, manual override, or erroneous quantity. A proposed quote-size reduction affects future execution behavior and therefore requires an authorized human before activation.

## Separation from Inventory Control

Single-trade control and inventory control address different risks. A large trade may create unacceptable execution loss without breaching final inventory, while many individually small trades may accumulate into an inventory breach.
