from __future__ import annotations

import json
import os
import re
from pathlib import Path


class ConfigurationError(RuntimeError):
    """Raised when a local configuration file is malformed."""


_ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def load_env_file(path: Path = Path(".env"), *, override: bool = False) -> bool:
    """Load a small, dependency-free .env file without overwriting shell variables."""

    if not path.exists():
        return False
    if not path.is_file():
        raise ConfigurationError(f"Environment path is not a file: {path}")

    for line_number, original_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = original_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ConfigurationError(f"Invalid {path} entry on line {line_number}: expected NAME=VALUE")

        name, raw_value = line.split("=", 1)
        name = name.strip()
        if _ENV_NAME.fullmatch(name) is None:
            raise ConfigurationError(f"Invalid environment variable name on line {line_number}: {name!r}")

        value = _parse_env_value(raw_value.strip(), path, line_number)
        if override or name not in os.environ:
            os.environ[name] = value
    return True


def _parse_env_value(raw_value: str, path: Path, line_number: int) -> str:
    if not raw_value:
        return ""
    if raw_value.startswith('"'):
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ConfigurationError(f"Invalid double-quoted value in {path} on line {line_number}") from exc
        if not isinstance(value, str):
            raise ConfigurationError(f"Expected a string value in {path} on line {line_number}")
        return value
    if raw_value.startswith("'"):
        if len(raw_value) < 2 or not raw_value.endswith("'"):
            raise ConfigurationError(f"Invalid single-quoted value in {path} on line {line_number}")
        return raw_value[1:-1]
    return raw_value.split(" #", 1)[0].rstrip()
