# Interview Notes

## 30-second pitch

This project is a trading operations AI-agent prototype. An optional OpenAI-compatible LLM router converts natural-language requests into validated risk intents and symbol scopes; the supervisor then selects deterministic specialist checks for trades, positions, venue settlement, and control policies. The copilot produces both a human-readable incident report and a machine-readable audit trace, while market-impacting actions remain behind human approval.

## Why it is not just a chatbot

- The system is tool-driven: agents call explicit deterministic tools over structured trading data.
- The optional LLM has bounded authority: it routes requests but cannot calculate risk values or execute trades.
- The output is auditable: every policy retrieval and detector invocation is written into a trace.
- It has guardrails: market-impacting actions are proposed but blocked behind human approval.
- It is evaluated: findings are compared against labeled expected incidents with precision, recall, and F1.

## Mapping to AI Engineer roles

- Multi-agent workflow: supervisor plus specialist agents.
- Structured LLM output: allow-listed intent, symbol, requested action, confidence, and rationale.
- Tool orchestration: each agent calls structured tools rather than free-form text generation.
- Domain grounding: policies are retrieved from a local control-policy file.
- Observability: report plus JSON audit trace.
- Safety: human-in-the-loop approval gates.
- Testing: unit tests cover expected findings, action guardrails, and output generation.

## Mapping to algo/data/risk roles

- Uses trading-like data: trades, positions, ledger settlement, policy thresholds.
- Detects risk/control gaps: notional limits, inventory breach, settlement break, fee-bps outlier.
- Connects analytics to workflow: findings become action-queue items.
- Separates detection from action: useful for production control design.

## Honest limitations

- The live LLM is limited to intent routing; it does not yet dynamically choose arbitrary tools.
- There is no persistent observe-act-replan loop, policy RAG, or long-term memory.
- Sample data is synthetic and designed for reproducibility, not live venue replay.
- It does not place trades or modify limits; that is intentional for safety.
- Policy retrieval is local JSON, not vector-database RAG yet.

## Next improvements

- Expose detectors as function/MCP tools and add bounded dynamic tool selection.
- Add LLM report drafting and analyst Q&A with structured output.
- Add vector retrieval over internal control documents.
- Add FastAPI endpoints and a small Streamlit dashboard.
- Add real exchange API ingestion or replay from historical trading logs.
- Add OpenTelemetry-style spans for richer observability.
