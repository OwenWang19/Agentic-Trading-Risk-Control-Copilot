import tempfile
import unittest
from pathlib import Path

from agentic_trading_risk_copilot.cli import run


class CopilotTest(unittest.TestCase):
    def test_copilot_detects_expected_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = run(Path("data/sample"), Path(tmp))

        finding_ids = {finding.finding_id for finding in state.findings}

        self.assertIn("F-TRADE-T-1005", finding_ids)
        self.assertIn("F-INV-ETH-PERP", finding_ids)
        self.assertIn("F-RECON-T-1003", finding_ids)
        self.assertIn("F-FEE-T-1003", finding_ids)
        self.assertEqual(state.metrics["precision"], 1.0)
        self.assertEqual(state.metrics["recall"], 1.0)
        self.assertEqual(state.metrics["f1"], 1.0)

    def test_market_impacting_actions_require_human_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = run(Path("data/sample"), Path(tmp))

        guarded = {
            action.action_type: action.status
            for action in state.actions
            if action.action_type in {"quote_size_reduction", "manual_hedge_review"}
        }

        self.assertEqual(guarded["quote_size_reduction"], "awaiting_human_approval")
        self.assertEqual(guarded["manual_hedge_review"], "awaiting_human_approval")

    def test_audit_outputs_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run(Path("data/sample"), tmp_path)

            self.assertTrue((tmp_path / "incident_report.md").exists())
            self.assertTrue((tmp_path / "audit_trace.json").exists())
            self.assertIn("Tool Trace", (tmp_path / "incident_report.md").read_text())


if __name__ == "__main__":
    unittest.main()
