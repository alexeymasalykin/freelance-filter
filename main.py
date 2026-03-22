from __future__ import annotations

import asyncio
import logging
import sys

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

import config
from evaluator import evaluate_order
from filter import should_forward

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


client = TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)


@client.on(events.NewMessage(from_users=config.BOT_USERNAME))
async def handler(event: events.NewMessage.Event) -> None:
    text = event.message.text or ""
    log.info("Received message from %s (len=%d)", config.BOT_USERNAME, len(text))

    if not should_forward(text, min_price=config.MIN_PRICE, stop_words=config.STOP_WORDS):
        log.info("FILTERED: message did not pass filters")
        return

    try:
        await client.forward_messages(config.GROUP_ID, event.message)
        log.info("FORWARDED: message sent to group %s", config.GROUP_ID)
    except FloodWaitError as e:
        log.warning("FloodWait: sleeping %d seconds", e.seconds)
        await asyncio.sleep(e.seconds)
        try:
            await client.forward_messages(config.GROUP_ID, event.message)
            log.info("FORWARDED (after wait): message sent to group %s", config.GROUP_ID)
        except Exception:
            log.exception("Failed to forward message after FloodWait retry")
            return
    except Exception:
        log.exception("Failed to forward message")
        return

    # LLM evaluation
    evaluation = await asyncio.to_thread(evaluate_order, text)
    if evaluation:
        eval_msg = f"🤖 Оценка:\n{evaluation}"
    else:
        eval_msg = "⚠️ Оценка недоступна"
    try:
        await client.send_message(config.GROUP_ID, eval_msg)
        log.info("EVALUATION sent to group")
    except Exception:
        log.exception("Failed to send evaluation")


def main() -> None:
    log.info("Starting freelance filter bot...")
    log.info("Listening for messages from @%s", config.BOT_USERNAME)
    log.info("Forwarding to group %s", config.GROUP_ID)
    log.info("Min price: %.0f RUB", config.MIN_PRICE)
    log.info("Stop words: %d configured", len(config.STOP_WORDS))
    log.info("LLM evaluation: %s (model: %s)", "enabled" if config.LLM_ENABLED else "disabled", config.LLM_MODEL)

    client.start(phone=config.PHONE)

    try:
        client.run_until_disconnected()
    except KeyboardInterrupt:
        log.info("Shutting down gracefully...")
        sys.exit(0)


if __name__ == "__main__":
    main()
