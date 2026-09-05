PYTHON ?= python3
LOCAL_PYTHON = PYTHONPATH=src $(PYTHON)

.PHONY: install install-rag configure-llm check-llm llm-demo rag-index rag-eval rag-demo demo test clean

install:
	$(PYTHON) -m pip install -e .

install-rag:
	$(PYTHON) -m pip install -e ".[rag]"

configure-llm:
	$(PYTHON) scripts/configure_llm.py

check-llm:
	$(LOCAL_PYTHON) -m agentic_trading_risk_copilot.cli --check-llm-config

llm-demo:
	$(LOCAL_PYTHON) -m agentic_trading_risk_copilot.cli --data data/sample --out reports --request "Review ETH-PERP inventory risk and recommend an action"

rag-index:
	$(LOCAL_PYTHON) -m agentic_trading_risk_copilot.cli --build-rag-index --no-eval

rag-eval:
	$(LOCAL_PYTHON) -m agentic_trading_risk_copilot.rag_evaluation --index data/rag_index --benchmark data/rag_eval/evaluation.jsonl --top-k 4

rag-demo:
	$(LOCAL_PYTHON) -m agentic_trading_risk_copilot.cli --data data/sample --out reports --rag --request "Review ETH-PERP inventory risk, explain the applicable policy and recommend an action"

demo:
	$(LOCAL_PYTHON) -m agentic_trading_risk_copilot.cli --data data/sample --out reports

test:
	$(LOCAL_PYTHON) -m unittest discover -s tests -p "test_*.py"

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	rm -f reports/audit_trace.json reports/incident_report.md
