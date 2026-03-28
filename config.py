from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()


def validate() -> None:
    """Validate required environment variables on startup."""
    missing = []
    for var in ("API_ID", "API_HASH", "PHONE", "GROUP_ID"):
        if not os.environ.get(var):
            missing.append(var)
    if missing:
        raise SystemExit(f"Missing required env vars: {', '.join(missing)}")

    llm_enabled = os.getenv("LLM_ENABLED", "true").lower() in ("true", "1", "yes")
    if llm_enabled and not os.getenv("OPENROUTER_API_KEY"):
        raise SystemExit("LLM_ENABLED=true but OPENROUTER_API_KEY not set")

    generate_response = os.getenv("GENERATE_RESPONSE", "true").lower() in ("true", "1", "yes")
    if generate_response and not os.getenv("BOT_TOKEN"):
        raise SystemExit("GENERATE_RESPONSE=true but BOT_TOKEN not set")


validate()

API_ID: int = int(os.environ["API_ID"])
API_HASH: str = os.environ["API_HASH"]
PHONE: str = os.environ["PHONE"]
GROUP_ID: int = int(os.environ["GROUP_ID"])
BOT_API_GROUP_ID: int = GROUP_ID

BOT_USERNAME: str = "Freelance_find_bot"
SESSION_NAME: str = "data/freelance_filter"

# LLM evaluation
LLM_ENABLED: bool = os.getenv("LLM_ENABLED", "true").lower() in ("true", "1", "yes")
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "anthropic/claude-haiku-4-5")

# Response generation
GENERATE_RESPONSE: bool = os.getenv("GENERATE_RESPONSE", "true").lower() in ("true", "1", "yes")
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
