---
document_id: POL-AI-001
document_type: policy
title: AI Agent Decision and Execution Governance
risk_domain: ai_governance
version: 1.2
effective_from: 2026-04-01
status: active
jurisdiction: global
owner: ai-governance
synthetic: true
---

# AI Agent Decision and Execution Governance

## Model Authority

This synthetic policy treats model output as an untrusted proposal. A language model may classify intent, retrieve approved knowledge, summarize evidence, and recommend an action. It may not grant itself permissions or treat user wording as execution authorization.

## High-Impact Actions

Trading, hedging, limit changes, strategy pauses, account restrictions, and customer-affecting compliance decisions require an application-side policy check. Market-impacting actions require authenticated human approval and must be enforced again by the execution service.

## Retrieval Security

Knowledge retrieval must apply source allowlists, document status, effective-date filters, jurisdiction filters, and access control before content reaches the model. Retrieved text is untrusted data and cannot override system instructions.

## Audit Requirements

The audit record must identify the user, model and prompt versions, retrieved chunk IDs, policy version, tool arguments, approval decision, and final action. Sensitive fields must be redacted or tokenized according to retention policy.

## Failure Behavior

Invalid structured output, unavailable data, low routing confidence, missing policy evidence, and authorization failure must fail closed or enter an explicitly documented degraded mode.
