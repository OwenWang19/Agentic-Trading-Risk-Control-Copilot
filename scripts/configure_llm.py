#!/usr/bin/env python3
from __future__ import annotations

import getpass
import os
from pathlib import Path


ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "openai/gpt-oss-20b"


def main() -> None:
    api_key = getpass.getpass("Paste a newly created Groq API key (input is hidden): ").strip()
    if not api_key.startswith("gsk_") or len(api_key) < 20 or any(character.isspace() for character in api_key):
        raise SystemExit("Invalid Groq API key format; no file was written.")

    content = (
        "# Local secret configuration. This file is ignored by Git.\n"
        f"TRADING_RISK_LLM_API_KEY={api_key}\n"
        f"TRADING_RISK_LLM_BASE_URL={GROQ_BASE_URL}\n"
        f"TRADING_RISK_LLM_MODEL={GROQ_MODEL}\n"
    )
    file_descriptor = os.open(ENV_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(file_descriptor, "w", encoding="utf-8") as env_file:
        env_file.write(content)
    os.chmod(ENV_PATH, 0o600)
    print("Configured .env with owner-only permissions. The API key was not printed.")
    print("Next: make check-llm")


if __name__ == "__main__":
    main()
