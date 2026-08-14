from __future__ import annotations

import argparse
from pathlib import Path

from .agents import SupervisorAgent
from .data_loader import load_dataset
from .evaluation import evaluate_findings
from .models import AgentState
from .reporting import write_json_audit, write_markdown_report


def run(data_dir: Path, output_dir: Path, evaluate: bool = True) -> AgentState:
    dataset = load_dataset(data_dir)
    state = AgentState(
        trades=dataset["trades"],
        positions=dataset["positions"],
        ledger=dataset["ledger"],
        policies=dataset["policies"],
    )
    state = SupervisorAgent().run(state)

    expected_path = data_dir / "expected_findings.json"
    if evaluate and expected_path.exists():
        evaluate_findings(state, expected_path)

    write_json_audit(state, output_dir / "audit_trace.json")
    write_markdown_report(state, output_dir / "incident_report.md")
    return state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the trading risk control copilot.")
    parser.add_argument("--data", type=Path, default=Path("data/sample"), help="Dataset directory")
    parser.add_argument("--out", type=Path, default=Path("reports"), help="Output report directory")
    parser.add_argument("--no-eval", action="store_true", help="Skip ground-truth evaluation")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    state = run(args.data, args.out, evaluate=not args.no_eval)
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
