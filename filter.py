from __future__ import annotations

import logging
import re

log = logging.getLogger(__name__)


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


def _build_stop_pattern(word: str) -> re.Pattern[str]:
    """Build regex pattern for a stop word with special rules."""
    lower = word.lower()

    if lower == "java":
        # "Java" but NOT "JavaScript" or "Java Script"
        return re.compile(r"\bJava\b(?!\s*Script)", re.IGNORECASE)

    if lower == "wp":
        # "WP" only as standalone word
        return re.compile(r"\bWP\b", re.IGNORECASE)

    if lower == "make":
        # Only "Make" as platform — match "make.com" or capitalized "Make" at word boundary
        # but not lowercase "make" in regular text
        return re.compile(r"\bmake\.com\b|(?<!\w)Make(?!\w)")

    # Cyrillic words: \b doesn't work reliably, use Unicode lookaround
    escaped = re.escape(word)
    if any(ord(c) > 127 for c in word):
        return re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE | re.UNICODE)

    # Default: word boundary match for ASCII words
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


def should_forward(text: str, *, min_price: float, stop_words: list[str]) -> bool:
    """Check if message passes all filters and should be forwarded."""
    for word in stop_words:
        pattern = _build_stop_pattern(word)
        if pattern.search(text):
            log.info("REJECTED: stop word '%s' found", word)
            return False

    price = parse_price(text)
    if price is None:
        log.info("PASSED: no price found, forwarding")
        return True
    if price < min_price:
        log.info("REJECTED: price %.0f < min %.0f", price, min_price)
        return False

    log.info("PASSED: price %.0f >= min %.0f", price, min_price)
    return True
