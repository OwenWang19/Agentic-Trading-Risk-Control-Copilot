import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from agentic_trading_risk_copilot.cli import run
from agentic_trading_risk_copilot.intent_router import (
    IntentRouter,
    IntentRoutingError,
    OpenAICompatibleChatClient,
)
from agentic_trading_risk_copilot.models import RiskIntent


class FakeJSONChatClient:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.requests: list[str] = []

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        self.requests.append(user_prompt)
        return self.response


class CopilotTest(unittest.TestCase):
    def test_llm_configuration_loads_from_local_env_without_overriding_shell(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "TRADING_RISK_LLM_API_KEY=file-key\n"
                "TRADING_RISK_LLM_BASE_URL=https://api.groq.com/openai/v1\n"
                "TRADING_RISK_LLM_MODEL=openai/gpt-oss-20b\n",
                encoding="utf-8",
            )
            with patch.dict(
                "os.environ",
                {
                    "TRADING_RISK_LLM_API_KEY": "shell-key",
                    "TRADING_RISK_LLM_BASE_URL": "https://shell.example/v1",
                    "TRADING_RISK_LLM_MODEL": "shell-model",
                },
                clear=True,
            ):
                client = OpenAICompatibleChatClient.from_env(env_path)

        self.assertEqual(client.api_key, "shell-key")
        self.assertEqual(client.base_url, "https://shell.example/v1")
        self.assertEqual(client.model, "shell-model")

    def test_llm_configuration_rejects_nonlocal_http_endpoint(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "TRADING_RISK_LLM_API_KEY": "test-key",
                "TRADING_RISK_LLM_BASE_URL": "http://remote.example/v1",
                "TRADING_RISK_LLM_MODEL": "test-model",
            },
            clear=True,
        ):
            with self.assertRaises(IntentRoutingError):
                OpenAICompatibleChatClient.from_env(env_file=None)

    def test_openai_compatible_client_requests_structured_json(self) -> None:
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "intent": "inventory_risk_review",
                                    "symbol": "ETH-PERP",
                                    "requested_action": "analyze",
                                    "confidence": 0.96,
                                    "rationale": "Inventory review requested.",
                                }
                            )
                        }
                    }
                ]
            }
        ).encode("utf-8")
        client = OpenAICompatibleChatClient(
            api_key="test-key",
            base_url="https://api.groq.com/openai/v1",
            model="openai/gpt-oss-20b",
        )

        with patch("agentic_trading_risk_copilot.intent_router.urlopen", return_value=response) as mock_urlopen:
            result = client.complete_json("system", "user")

        request = mock_urlopen.call_args.args[0]
        request_payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "https://api.groq.com/openai/v1/chat/completions")
        self.assertEqual(request.get_header("User-agent"), "AgenticTradingRiskCopilot/0.1")
        self.assertEqual(request_payload["response_format"], {"type": "json_object"})
        self.assertEqual(request_payload["model"], "openai/gpt-oss-20b")
        self.assertEqual(result["intent"], "inventory_risk_review")

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

    def test_llm_intent_router_scopes_inventory_review(self) -> None:
        client = FakeJSONChatClient(
            {
                "intent": "inventory_risk_review",
                "symbol": "eth-perp",
                "requested_action": "recommend",
                "confidence": 0.97,
                "rationale": "The user asked for an ETH inventory risk review.",
            }
        )
        router = IntentRouter(client)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            state = run(
                Path("data/sample"),
                tmp_path,
                user_request="Review ETH inventory risk and recommend an action",
                intent_router=router,
            )
            report = (tmp_path / "incident_report.md").read_text()

        self.assertEqual(state.routing_decision.intent, RiskIntent.INVENTORY_RISK_REVIEW)
        self.assertEqual(state.routing_decision.symbol, "ETH-PERP")
        self.assertEqual({finding.finding_id for finding in state.findings}, {"F-INV-ETH-PERP"})
        self.assertEqual(state.actions[0].status, "awaiting_human_approval")
        self.assertNotIn("precision", state.metrics)
        self.assertIn("Request Routing", report)
        self.assertEqual(client.requests, ["Review ETH inventory risk and recommend an action"])

    def test_execution_request_remains_a_recommendation_only(self) -> None:
        router = IntentRouter(
            FakeJSONChatClient(
                {
                    "intent": "trade_notional_review",
                    "symbol": "ETH-PERP",
                    "requested_action": "execute",
                    "confidence": 0.94,
                    "rationale": "The user asked to reduce a large ETH trade.",
                }
            )
        )

        with tempfile.TemporaryDirectory() as tmp:
            state = run(
                Path("data/sample"),
                Path(tmp),
                evaluate=False,
                user_request="Reduce my large ETH trade",
                intent_router=router,
            )

        self.assertEqual(state.routing_decision.requested_action, "execute")
        self.assertEqual({finding.finding_id for finding in state.findings}, {"F-TRADE-T-1005"})
        self.assertTrue(all(action.approval_required for action in state.actions))
        self.assertTrue(all(action.status == "awaiting_human_approval" for action in state.actions))

    def test_fee_route_uses_global_baseline_and_symbol_scope(self) -> None:
        router = IntentRouter(
            FakeJSONChatClient(
                {
                    "intent": "fee_anomaly_review",
                    "symbol": "SOL-PERP",
                    "requested_action": "analyze",
                    "confidence": 0.93,
                    "rationale": "The user asked to inspect SOL execution fees.",
                }
            )
        )

        with tempfile.TemporaryDirectory() as tmp:
            state = run(
                Path("data/sample"),
                Path(tmp),
                evaluate=False,
                user_request="Check SOL-PERP fee anomalies",
                intent_router=router,
            )

        self.assertEqual({finding.finding_id for finding in state.findings}, {"F-FEE-T-1003"})

    def test_router_rejects_unsupported_intent(self) -> None:
        router = IntentRouter(
            FakeJSONChatClient(
                {
                    "intent": "unsupported",
                    "symbol": None,
                    "requested_action": "analyze",
                    "confidence": 0.99,
                    "rationale": "The request is unrelated to trading risk.",
                }
            )
        )

        with self.assertRaises(IntentRoutingError):
            router.route("Write me a poem")


if __name__ == "__main__":
    unittest.main()
