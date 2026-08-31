PYTHON ?= python3
LOCAL_PYTHON = PYTHONPATH=src $(PYTHON)

.PHONY: install configure-llm check-llm llm-demo demo test clean

install:
	$(PYTHON) -m pip install -e .

configure-llm:
	$(PYTHON) scripts/configure_llm.py

check-llm:
	$(LOCAL_PYTHON) -m agentic_trading_risk_copilot.cli --check-llm-config

llm-demo:
	$(LOCAL_PYTHON) -m agentic_trading_risk_copilot.cli --data data/sample --out reports --request "Review ETH-PERP inventory risk and recommend an action"

demo:
	$(LOCAL_PYTHON) -m agentic_trading_risk_copilot.cli --data data/sample --out reports

test:
	$(LOCAL_PYTHON) -m unittest discover -s tests -p "test_*.py"

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	rm -f reports/audit_trace.json reports/incident_report.md
