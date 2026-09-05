from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from .rag.index import FaissKnowledgeIndex


@dataclass(frozen=True)
class RetrievalMetrics:
    case_count: int
    answerable_count: int
    recall_at_k: float
    hit_rate_at_k: float
    mean_reciprocal_rank: float
    metadata_filter_abstention_accuracy: float

    def to_dict(self) -> dict[str, int | float]:
        return {
            "case_count": self.case_count,
            "answerable_count": self.answerable_count,
            "recall_at_k": self.recall_at_k,
            "hit_rate_at_k": self.hit_rate_at_k,
            "mean_reciprocal_rank": self.mean_reciprocal_rank,
            "metadata_filter_abstention_accuracy": self.metadata_filter_abstention_accuracy,
        }


def evaluate_retrieval(
    index: FaissKnowledgeIndex,
    benchmark_path: Path,
    *,
    top_k: int = 4,
    min_score: float = 0.70,
) -> tuple[RetrievalMetrics, list[dict[str, object]]]:
    cases = [json.loads(line) for line in benchmark_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not cases:
        raise ValueError("RAG benchmark contains no cases")

    recall_sum = 0.0
    hit_sum = 0.0
    reciprocal_rank_sum = 0.0
    answerable_count = 0
    abstention_correct = 0
    abstention_count = 0
    details: list[dict[str, object]] = []

    for case in cases:
        results = index.search(
            str(case["query"]),
            top_k=top_k,
            risk_domain=case.get("risk_domain"),
            status="active",
            jurisdiction=str(case.get("jurisdiction", "global")),
            min_score=min_score,
        )
        retrieved_ids = [item.chunk.document_id for item in results]
        expected_ids = [str(item) for item in case.get("expected_document_ids", [])]
        should_abstain = bool(case.get("should_abstain", False))
        unique_retrieved = set(retrieved_ids)

        if should_abstain:
            abstention_count += 1
            abstained = not results
            abstention_correct += int(abstained)
            recall = None
            reciprocal_rank = None
            hit = None
        else:
            if not expected_ids:
                raise ValueError(f"Answerable case {case.get('case_id')} has no expected documents")
            answerable_count += 1
            matches = unique_retrieved & set(expected_ids)
            recall = len(matches) / len(set(expected_ids))
            hit = float(bool(matches))
            reciprocal_rank = 0.0
            for rank, document_id in enumerate(retrieved_ids, start=1):
                if document_id in expected_ids:
                    reciprocal_rank = 1.0 / rank
                    break
            recall_sum += recall
            hit_sum += hit
            reciprocal_rank_sum += reciprocal_rank
            abstained = False

        details.append(
            {
                "case_id": case.get("case_id"),
                "query": case["query"],
                "expected_document_ids": expected_ids,
                "retrieved_document_ids": retrieved_ids,
                "retrieved_chunk_ids": [item.chunk.chunk_id for item in results],
                "recall_at_k": recall,
                "reciprocal_rank": reciprocal_rank,
                "abstained": abstained,
                "passed": abstained if should_abstain else bool(hit),
            }
        )

    metrics = RetrievalMetrics(
        case_count=len(cases),
        answerable_count=answerable_count,
        recall_at_k=recall_sum / answerable_count if answerable_count else 0.0,
        hit_rate_at_k=hit_sum / answerable_count if answerable_count else 0.0,
        mean_reciprocal_rank=reciprocal_rank_sum / answerable_count if answerable_count else 0.0,
        metadata_filter_abstention_accuracy=abstention_correct / abstention_count if abstention_count else 0.0,
    )
    return metrics, details


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate FAISS policy retrieval against a labeled JSONL benchmark.")
    parser.add_argument("--index", type=Path, default=Path("data/rag_index"))
    parser.add_argument("--benchmark", type=Path, default=Path("data/rag_eval/evaluation.jsonl"))
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--min-score", type=float, default=0.70)
    parser.add_argument("--details-out", type=Path, default=Path("reports/rag_evaluation.json"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    index = FaissKnowledgeIndex.load(args.index)
    metrics, details = evaluate_retrieval(
        index, args.benchmark, top_k=args.top_k, min_score=args.min_score
    )
    payload = {"metrics": metrics.to_dict(), "cases": details}
    args.details_out.parent.mkdir(parents=True, exist_ok=True)
    args.details_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(metrics.to_dict(), indent=2))
    print(f"wrote={args.details_out}")


if __name__ == "__main__":
    main()
