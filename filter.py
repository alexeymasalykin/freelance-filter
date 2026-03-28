from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml

log = logging.getLogger(__name__)


class Priority(Enum):
    HOT = "🔥"
    INTERESTING = "⚡"
    OTHER = "📋"


@dataclass
class FilterResult:
    passed: bool
    priority: Priority = Priority.OTHER
    price: float | None = None
    title: str = ""
    reject_reason: str = ""


def _load_all_patterns() -> dict[str, list[re.Pattern[str]]]:
    """Load all pattern lists from patterns.yml (read file once)."""
    config_path = Path(__file__).parent / "patterns.yml"
    with open(config_path) as f:
        data: dict[str, list[str]] = yaml.safe_load(f)
    return {
        key: [re.compile(p, re.IGNORECASE) for p in patterns]
        for key, patterns in data.items()
    }


_PATTERNS = _load_all_patterns()

STOP_PATTERNS: list[re.Pattern[str]] = _PATTERNS["stop"]
HOT_PATTERNS: list[re.Pattern[str]] = _PATTERNS["hot"]
INTERESTING_PATTERNS: list[re.Pattern[str]] = _PATTERNS["interesting"]

MIN_PRICE_HOT: float = 10_000
MIN_PRICE_INTERESTING: float = 15_000
MIN_PRICE_OTHER: float = 10_000


def parse_price(text: str) -> float | None:
    """Extract price in RUB from bot message. Returns None if not found."""
    match = re.search(r"Цена:\s*([\d\s]+(?:\.\d+)?)\s*RUB", text)
    if not match:
        return None
    price_str = match.group(1).replace(" ", "")
    try:
        return float(price_str)
    except ValueError:
        return None


def _extract_title(text: str) -> str:
    """Extract order title — first non-empty line of the message."""
    for line in text.strip().split("\n"):
        line = line.strip()
        if line and not line.startswith(("📋", "🔗", "💰", "🎯", "❗")):
            return line[:80]
    return ""


def _has_stop_word(text: str) -> str | None:
    """Check if text contains any stop word. Returns matched pattern or None."""
    for pattern in STOP_PATTERNS:
        if pattern.search(text):
            return pattern.pattern
    return None


def _detect_priority(text: str, price: float) -> Priority:
    """Detect order priority based on keywords and price."""
    # Hot: price >= 10000 AND frontend keywords
    if price >= MIN_PRICE_HOT:
        for pattern in HOT_PATTERNS:
            if pattern.search(text):
                return Priority.HOT

    # Interesting: price >= 15000 AND bot/ai keywords
    if price >= MIN_PRICE_INTERESTING:
        for pattern in INTERESTING_PATTERNS:
            if pattern.search(text):
                return Priority.INTERESTING

    return Priority.OTHER


def is_order(text: str) -> bool:
    """Check if message is an actual order (not a service message from the bot)."""
    return "📋 ID:" in text


def evaluate_order(text: str) -> FilterResult:
    """
    3-level filter evaluation.

    Level 1: Price check (no price or < 10000 → reject)
    Level 2: Stop words (reject even if price is ok)
    Level 3: Priority detection (hot/interesting/other)
    """
    title = _extract_title(text)

    # Not an order
    if not is_order(text):
        return FilterResult(passed=False, reject_reason="not an order")

    # Level 1: Price
    price = parse_price(text)
    if price is None:
        # No price — check stop words only, forward with OTHER priority
        stop = _has_stop_word(text)
        if stop:
            log.info("REJECTED: no price + stop word '%s' — %s", stop, title)
            return FilterResult(passed=False, price=None, title=title, reject_reason=f"stop word: {stop}")
        log.info("PASSED 📋: no price, no stop words — %s", title)
        return FilterResult(passed=True, priority=Priority.OTHER, price=None, title=title)
    if price < MIN_PRICE_OTHER:
        log.info("REJECTED: price %.0f < 10000 — %s", price, title)
        return FilterResult(passed=False, price=price, title=title, reject_reason=f"price {price:.0f} < 10000")

    # Level 2: Stop words
    stop = _has_stop_word(text)
    if stop:
        log.info("REJECTED: stop word '%s' — %s", stop, title)
        return FilterResult(passed=False, price=price, title=title, reject_reason=f"stop word: {stop}")

    # Level 3: Priority
    priority = _detect_priority(text, price)
    log.info("PASSED %s: price %.0f — %s", priority.value, price, title)
    return FilterResult(passed=True, priority=priority, price=price, title=title)
