from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

API_ID: int = int(os.environ["API_ID"])
API_HASH: str = os.environ["API_HASH"]
PHONE: str = os.environ["PHONE"]
GROUP_ID: int = int(os.environ["GROUP_ID"])
MIN_PRICE: float = float(os.getenv("MIN_PRICE", "5000"))
STOP_WORDS: list[str] = [
    w.strip() for w in os.getenv(
        "STOP_WORDS",
        "1С,Битрикс,Bitrix,WordPress,WP,Laravel,Java,Unity,n8n,Zapier,Tilda,Тильда,Wix,Webflow,Bubble,Shopify,OpenCart,Joomla,Drupal,ModX"
    ).split(",") if w.strip()
]

BOT_USERNAME: str = "Freelance_find_bot"
SESSION_NAME: str = "data/freelance_filter"
