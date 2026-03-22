from __future__ import annotations

import asyncio
import logging
import sys
import time

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

import config
from bot import bot as tg_bot, build_keyboard, start_bot
from evaluator import evaluate_order
from filter import should_forward

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


client = TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)
_start_time = time.time()


@client.on(events.NewMessage(from_users=config.BOT_USERNAME))
async def handler(event: events.NewMessage.Event) -> None:
    # Skip messages that arrived before bot started (queued offline messages)
    msg_time = event.message.date.timestamp()
    if msg_time < _start_time - 60:
        log.info("SKIPPED: old message (age=%.0fs)", _start_time - msg_time)
        return

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

    # LLM evaluation + response
    result = await asyncio.to_thread(evaluate_order, text)

    if result:
        parts = [f"🤖 Оценка:\n{result.evaluation}"]
        if result.response:
            parts.append(f"📨 Отклик:\n{result.response}")
        eval_msg = "\n\n".join(parts)

        # Send via bot (for inline buttons) if available and response exists
        if tg_bot and result.response:
            keyboard = build_keyboard(text, result.response)
            try:
                await tg_bot.send_message(
                    config.GROUP_ID, eval_msg, reply_markup=keyboard
                )
                log.info("EVALUATION + RESPONSE sent via bot")
            except Exception:
                log.exception("Failed to send via bot, falling back to userbot")
                await _send_via_userbot(eval_msg)
        else:
            await _send_via_userbot(eval_msg)
    else:
        await _send_via_userbot("⚠️ Оценка недоступна")


async def _send_via_userbot(text: str) -> None:
    """Send message via Telethon userbot."""
    try:
        await client.send_message(config.GROUP_ID, text)
        log.info("EVALUATION sent to group")
    except Exception:
        log.exception("Failed to send evaluation")


async def main() -> None:
    log.info("Starting freelance filter bot...")
    log.info("Listening for messages from @%s", config.BOT_USERNAME)
    log.info("Forwarding to group %s", config.GROUP_ID)
    log.info("Min price: %.0f RUB", config.MIN_PRICE)
    log.info("Stop words: %d configured", len(config.STOP_WORDS))
    log.info("LLM evaluation: %s (model: %s)", "enabled" if config.LLM_ENABLED else "disabled", config.LLM_MODEL)
    log.info("Response generation: %s", "enabled" if config.GENERATE_RESPONSE else "disabled")
    log.info("Inline bot: %s", "enabled" if tg_bot else "disabled")

    await client.start(phone=config.PHONE)

    # Run both Telethon userbot and aiogram bot concurrently
    tasks = [client.run_until_disconnected()]
    if tg_bot:
        tasks.append(start_bot())

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        log.info("Shutting down gracefully...")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
