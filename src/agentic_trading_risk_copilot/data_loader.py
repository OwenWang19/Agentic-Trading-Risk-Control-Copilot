from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from .models import LedgerEntry, PolicyRule, Position, Severity, Trade


def load_trades(path: Path) -> list[Trade]:
    with path.open(newline="") as handle:
        return [
            Trade(
                trade_id=row["trade_id"],
                timestamp=datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
                venue=row["venue"],
                symbol=row["symbol"],
                side=row["side"],
                quantity=float(row["quantity"]),
                price=float(row["price"]),
                fee=float(row["fee"]),
                order_type=row["order_type"],
                strategy=row["strategy"],
            )
            for row in csv.DictReader(handle)
        ]


def load_positions(path: Path) -> list[Position]:
    with path.open(newline="") as handle:
        return [
            Position(
                symbol=row["symbol"],
                quantity=float(row["quantity"]),
                mark_price=float(row["mark_price"]),
                limit_quantity=float(row["limit_quantity"]),
                limit_notional=float(row["limit_notional"]),
            )
            for row in csv.DictReader(handle)
        ]


def load_ledger(path: Path) -> list[LedgerEntry]:
    with path.open(newline="") as handle:
        return [
            LedgerEntry(
                trade_id=row["trade_id"],
                expected_quantity=float(row["expected_quantity"]),
                settled_quantity=float(row["settled_quantity"]),
                status=row["status"],
                reason=row["reason"],
            )
            for row in csv.DictReader(handle)
        ]


def load_policies(path: Path) -> dict[str, PolicyRule]:
    raw = json.loads(path.read_text())
    policies = {}
    for item in raw["rules"]:
        policies[item["rule_id"]] = PolicyRule(
            rule_id=item["rule_id"],
            description=item["description"],
            threshold=float(item["threshold"]),
            unit=item["unit"],
            severity=Severity(item["severity"]),
            action_type=item["action_type"],
        )
    return policies


def load_dataset(data_dir: Path):
    return {
        "trades": load_trades(data_dir / "trades.csv"),
        "positions": load_positions(data_dir / "positions.csv"),
        "ledger": load_ledger(data_dir / "ledger.csv"),
        "policies": load_policies(data_dir / "control_policy.json"),
    }
