import tempfile
import unittest
from pathlib import Path

from agentic_trading_risk_copilot.cli import run
from agentic_trading_risk_copilot.intent_router import IntentRouter
from agentic_trading_risk_copilot.models import RiskIntent
from agentic_trading_risk_copilot.rag.agent import PolicyRAGAgent, RAGGenerationError
from agentic_trading_risk_copilot.rag.knowledge import parse_markdown_document
from agentic_trading_risk_copilot.rag.schemas import KnowledgeChunk, RetrievedChunk


class FakeJSONChatClient:
    def __init__(self, response):
        self.response = response

    def complete_json(self, system_prompt, user_prompt):
        return self.response


class FakeRetriever:
    def __init__(self, results):
        self.results = results
        self.requests = []

    def search(self, query, **kwargs):
        self.requests.append((query, kwargs))
        return self.results


def retrieved_inventory_chunk():
    return RetrievedChunk(
        chunk=KnowledgeChunk(
            chunk_id="POL-INV-001:003",
            document_id="POL-INV-001",
            document_type="policy",
            title="Marked Inventory Exposure Control",
            section="Limit Breach",
            risk_domain="inventory_limit",
            version="2.1",
            effective_from="2026-01-01",
            status="active",
            jurisdiction="global",
            owner="market-risk",
            synthetic=True,
            content="Inventory utilization above 100 percent is a limit breach.",
        ),
        score=0.91,
    )


class RAGTest(unittest.TestCase):
    def test_frontmatter_parser_requires_synthetic_metadata(self):
        metadata, body = parse_markdown_document(Path("knowledge_base/policies/inventory_risk_policy.md"))
        self.assertEqual(metadata["document_id"], "POL-INV-001")
        self.assertIs(metadata["synthetic"], True)
        self.assertIn("Limit Breach", body)

    def test_rag_enriches_finding_with_validated_citation(self):
        client = FakeJSONChatClient(
            {
                "grounded": True,
                "answer": "The inventory policy requires escalation and human approval for a hedge.",
                "root_cause_hypotheses": ["A delayed hedge is a hypothesis, not a confirmed cause."],
                "recommended_next_steps": ["Verify the position and mark timestamps."],
                "citation_chunk_ids": ["POL-INV-001:003"],
            }
        )
        rag_agent = PolicyRAGAgent(FakeRetriever([retrieved_inventory_chunk()]), client)
        router = IntentRouter(
            FakeJSONChatClient(
                {
                    "intent": "inventory_risk_review",
                    "symbol": "ETH-PERP",
                    "requested_action": "recommend",
                    "confidence": 0.98,
                    "rationale": "Inventory review requested.",
                }
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            state = run(
                Path("data/sample"),
                Path(tmp),
                evaluate=False,
                user_request="Review ETH inventory",
                intent_router=router,
                policy_rag_agent=rag_agent,
            )

        self.assertEqual(state.findings[0].rag_analysis.citations[0].document_id, "POL-INV-001")
        self.assertIn("policy-rag-agent.retrieval", [call.tool_name for call in state.tool_trace])

    def test_rag_rejects_hallucinated_citation(self):
        agent = PolicyRAGAgent(
            FakeRetriever([retrieved_inventory_chunk()]),
            FakeJSONChatClient(
                {
                    "grounded": True,
                    "answer": "Invented answer.",
                    "root_cause_hypotheses": [],
                    "recommended_next_steps": [],
                    "citation_chunk_ids": ["NOT-RETRIEVED:999"],
                }
            ),
        )
        with self.assertRaises(RAGGenerationError):
            agent._generate_or_abstain("question", [retrieved_inventory_chunk()])

    def test_rag_allows_explicit_insufficient_context_without_citations(self):
        agent = PolicyRAGAgent(
            FakeRetriever([retrieved_inventory_chunk()]),
            FakeJSONChatClient(
                {
                    "grounded": False,
                    "answer": "The retrieved inventory policy does not specify KYC retention periods.",
                    "root_cause_hypotheses": [],
                    "recommended_next_steps": ["Retrieve the approved KYC retention policy."],
                    "citation_chunk_ids": [],
                }
            ),
        )
        result = agent._generate_or_abstain("How long should KYC documents be retained?", [retrieved_inventory_chunk()])
        self.assertFalse(result.grounded)
        self.assertEqual(result.citations, [])

    def test_policy_qa_route_returns_grounded_answer_without_actions(self):
        router = IntentRouter(
            FakeJSONChatClient(
                {
                    "intent": "policy_qa",
                    "symbol": None,
                    "requested_action": "analyze",
                    "confidence": 0.96,
                    "rationale": "The user asked about policy.",
                }
            )
        )
        rag_agent = PolicyRAGAgent(
            FakeRetriever([retrieved_inventory_chunk()]),
            FakeJSONChatClient(
                {
                    "grounded": True,
                    "answer": "A hedge needs authenticated human approval.",
                    "root_cause_hypotheses": [],
                    "recommended_next_steps": ["Ask an authorized trader and risk reviewer."],
                    "citation_chunk_ids": ["POL-INV-001:003"],
                }
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            state = run(
                Path("data/sample"),
                Path(tmp),
                evaluate=False,
                user_request="Can the agent hedge automatically?",
                intent_router=router,
                policy_rag_agent=rag_agent,
            )

        self.assertEqual(state.routing_decision.intent, RiskIntent.POLICY_QA)
        self.assertEqual(state.actions, [])
        self.assertIsNotNone(state.knowledge_answer)
        self.assertEqual(state.knowledge_answer.citations[0].chunk_id, "POL-INV-001:003")


if __name__ == "__main__":
    unittest.main()
