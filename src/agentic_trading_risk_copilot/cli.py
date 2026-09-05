from __future__ import annotations

import argparse
from pathlib import Path

from .agents import SupervisorAgent
from .data_loader import load_dataset
from .evaluation import evaluate_findings
from .intent_router import IntentRouter, IntentRoutingError, OpenAICompatibleChatClient
from .models import AgentState, RiskIntent
from .reporting import write_json_audit, write_markdown_report


def run(
    data_dir: Path,
    output_dir: Path,
    evaluate: bool = True,
    user_request: str | None = None,
    intent_router: IntentRouter | None = None,
    policy_rag_agent: object | None = None,
) -> AgentState:
    dataset = load_dataset(data_dir)
    state = AgentState(
        trades=dataset["trades"],
        positions=dataset["positions"],
        ledger=dataset["ledger"],
        policies=dataset["policies"],
        user_request=user_request,
    )

    if user_request is not None:
        router = intent_router or IntentRouter(OpenAICompatibleChatClient.from_env())
        decision = router.route(user_request)
        state.routing_decision = decision
        state.trace(
            "llm-intent-router",
            {"user_request": user_request},
            {
                "intent": decision.intent.value,
                "symbol": decision.symbol,
                "requested_action": decision.requested_action,
                "confidence": decision.confidence,
                "rationale": decision.rationale,
            },
        )

    state = SupervisorAgent(policy_rag_agent=policy_rag_agent).run(state)

    expected_path = data_dir / "expected_findings.json"
    full_scan = state.routing_decision is None or state.routing_decision.intent is RiskIntent.FULL_RISK_SCAN
    if evaluate and expected_path.exists() and full_scan:
        evaluate_findings(state, expected_path)
    elif evaluate and expected_path.exists():
        state.trace(
            "evaluation-skipped",
            {"expected_path": str(expected_path)},
            {"reason": "The bundled ground truth covers a full scan, not a scoped intent route."},
        )

    write_json_audit(state, output_dir / "audit_trace.json")
    write_markdown_report(state, output_dir / "incident_report.md")
    return state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the trading risk control copilot.")
    parser.add_argument("--data", type=Path, default=Path("data/sample"), help="Dataset directory")
    parser.add_argument("--out", type=Path, default=Path("reports"), help="Output report directory")
    parser.add_argument("--no-eval", action="store_true", help="Skip ground-truth evaluation")
    parser.add_argument(
        "--request",
        type=str,
        help="Natural-language risk request. When supplied, the configured LLM routes the workflow.",
    )
    parser.add_argument("--rag", action="store_true", help="Ground findings or policy Q&A in the local FAISS knowledge index")
    parser.add_argument("--rag-index", type=Path, default=Path("data/rag_index"), help="FAISS index directory")
    parser.add_argument("--knowledge", type=Path, default=Path("knowledge_base"), help="Knowledge document directory")
    parser.add_argument("--build-rag-index", action="store_true", help="Build or replace the local RAG index before running")
    parser.add_argument(
        "--check-llm-config",
        action="store_true",
        help="Validate local LLM settings without printing the API key or calling the provider.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        if args.check_llm_config:
            client = OpenAICompatibleChatClient.from_env()
            print("llm_api_key=configured")
            print(f"llm_base_url={client.base_url}")
            print(f"llm_model={client.model}")
            return
        policy_rag_agent = None
        if args.rag or args.build_rag_index:
            from .rag import FaissKnowledgeIndex, PolicyRAGAgent

            if args.build_rag_index:
                knowledge_index = FaissKnowledgeIndex.build(args.knowledge, args.rag_index)
                print(
                    f"rag_index=documents:{knowledge_index.manifest['document_count']} "
                    f"chunks:{knowledge_index.manifest['chunk_count']} "
                    f"dimension:{knowledge_index.manifest['embedding_dimension']}"
                )
            else:
                knowledge_index = FaissKnowledgeIndex.load(args.rag_index)
            if args.rag:
                policy_rag_agent = PolicyRAGAgent(knowledge_index, OpenAICompatibleChatClient.from_env())
        state = run(
            args.data,
            args.out,
            evaluate=not args.no_eval,
            user_request=args.request,
            policy_rag_agent=policy_rag_agent,
        )
    except IntentRoutingError as exc:
        raise SystemExit(f"intent-routing-error: {exc}") from exc
    if state.routing_decision:
        print(
            "route="
            f"{state.routing_decision.intent.value} "
            f"symbol:{state.routing_decision.symbol or 'ALL'} "
            f"confidence:{state.routing_decision.confidence:.2f}"
        )
    print(f"findings={len(state.findings)}")
    print(f"approval_required={int(state.metrics.get('approval_required_count', 0))}")
    if "precision" in state.metrics:
        print(
            "evaluation="
            f"precision:{state.metrics['precision']:.4f} "
            f"recall:{state.metrics['recall']:.4f} "
            f"f1:{state.metrics['f1']:.4f}"
        )
    print(f"wrote={args.out / 'incident_report.md'}")
    print(f"wrote={args.out / 'audit_trace.json'}")


if __name__ == "__main__":
    main()
