from __future__ import annotations

import re


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
