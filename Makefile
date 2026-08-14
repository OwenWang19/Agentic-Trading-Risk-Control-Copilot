.PHONY: install demo test clean

install:
	python -m pip install -e .

demo:
	python -m agentic_trading_risk_copilot.cli --data data/sample --out reports

test:
	python -m unittest discover -s tests -p "test_*.py"

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	rm -f reports/audit_trace.json reports/incident_report.md
