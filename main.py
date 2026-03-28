from __future__ import annotations

import asyncio
import logging
import re
import signal
import sys
import time
from datetime import datetime, timezone

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.custom import Message

import config
from bot import bot as tg_bot, build_keyboard, start_bot
from evaluator import evaluate_order as llm_evaluate
from filter import evaluate_order as filter_order, Priority

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


client = TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)
_start_time = time.time()
_shutdown_event = asyncio.Event()

# Daily stats counters
_stats = {"total": 0, "rejected": 0, "passed": 0, "hot": 0, "interesting": 0, "other": 0}


def _reset_stats() -> None:
    for key in _stats:
        _stats[key] = 0


def _format_price(price: float) -> str:
    """Format price: 14000 -> '14 000'."""
    return f"{price:,.0f}".replace(",", " ")


async def _get_order_url(message: Message) -> str | None:
    """Click 'get_url' callback button and extract URL from bot's response."""
    if not hasattr(message, "reply_markup") or message.reply_markup is None:
        return None
    if not hasattr(message.reply_markup, "rows"):
        return None

    target_button = None
    for row in message.reply_markup.rows:
        for button in row.buttons:
            if hasattr(button, "data") and button.data and button.data.startswith(b"get_url:"):
                target_button = button
                break
        if target_button:
            break

    if not target_button:
        return None

    try:
        await message.click(data=target_button.data)
        log.info("Clicked get_url button, waiting for response...")
        await asyncio.sleep(2)

        updated = await client.get_messages(message.chat_id, ids=message.id)
        if updated and updated.reply_markup:
            for row in updated.reply_markup.rows:
                for button in row.buttons:
                    if hasattr(button, "url") and button.url:
                        return button.url

        if updated and updated.text:
            url_match = re.search(r"https?://\S+", updated.text)
            if url_match:
                return url_match.group(0)

    except (AttributeError, asyncio.TimeoutError, ConnectionError):
        log.exception("Failed to click get_url button")

    return None


@client.on(events.NewMessage(from_users=config.BOT_USERNAME))
async def handler(event: events.NewMessage.Event) -> None:
    # Skip old messages
    msg_time = event.message.date.timestamp()
    if msg_time < _start_time - 60:
        log.info("SKIPPED: old message (age=%.0fs)", _start_time - msg_time)
        return

    text = event.message.text or ""

    # 3-level filter
    result = filter_order(text)
    _stats["total"] += 1

    if not result.passed:
        _stats["rejected"] += 1
        return

    _stats["passed"] += 1
    if result.priority == Priority.HOT:
        _stats["hot"] += 1
    elif result.priority == Priority.INTERESTING:
        _stats["interesting"] += 1
    else:
        _stats["other"] += 1

    # Get order URL
    order_url = await _get_order_url(event.message)
    if order_url:
        log.info("Got order URL: %s", order_url)

    # Forward original message
    try:
        await client.forward_messages(config.GROUP_ID, event.message)
        log.info("FORWARDED: message sent to group %s", config.GROUP_ID)
    except FloodWaitError as e:
        log.warning("FloodWait: sleeping %d seconds", e.seconds)
        await asyncio.sleep(e.seconds)
        try:
            await client.forward_messages(config.GROUP_ID, event.message)
        except (ConnectionError, ValueError):
            log.exception("Failed to forward after FloodWait")
            return
    except (ConnectionError, ValueError):
        log.exception("Failed to forward message")
        return

    # Build priority header
    price_str = _format_price(result.price) if result.price else "?"
    header = f"{result.priority.value} {price_str}₽ | {result.title}"

    # LLM evaluation
    llm_result = await asyncio.to_thread(llm_evaluate, text)

    if llm_result:
        parts = [header, f"🤖 Оценка:\n{llm_result.evaluation}"]
        if llm_result.response:
            parts.append(f"📨 Отклик:\n{llm_result.response}")
        if order_url:
            parts.append(f"🔗 Ссылка: {order_url}")
        eval_msg = "\n\n".join(parts)

        if tg_bot and llm_result.response:
            keyboard = build_keyboard(text, llm_result.response)
            try:
                await tg_bot.send_message(
                    config.BOT_API_GROUP_ID, eval_msg, reply_markup=keyboard
                )
                log.info("EVALUATION sent via bot")
            except (ConnectionError, ValueError):
                log.exception("Failed to send via bot, falling back to userbot")
                await _send_via_userbot(eval_msg)
        else:
            await _send_via_userbot(eval_msg)
    else:
        await _send_via_userbot(f"{header}\n\n⚠️ Оценка недоступна")


async def _send_via_userbot(text: str) -> None:
    """Send message via Telethon userbot."""
    try:
        await client.send_message(config.GROUP_ID, text)
        log.info("EVALUATION sent to group")
    except (ConnectionError, ValueError):
        log.exception("Failed to send evaluation")


async def _daily_stats() -> None:
    """Send daily stats summary at 23:00 MSK."""
    while True:
        now = datetime.now(timezone.utc)
        # MSK = UTC+3
        msk_hour = (now.hour + 3) % 24
        msk_minute = now.minute

        # Calculate seconds until 23:00 MSK
        target_msk_hour = 23
        if msk_hour < target_msk_hour:
            wait_hours = target_msk_hour - msk_hour
        elif msk_hour == target_msk_hour and msk_minute == 0:
            wait_hours = 0
        else:
            wait_hours = 24 - msk_hour + target_msk_hour

        wait_seconds = wait_hours * 3600 - msk_minute * 60 - now.second
        if wait_seconds <= 0:
            wait_seconds += 86400

        log.info("Next stats report in %.0f hours", wait_seconds / 3600)
        try:
            await asyncio.wait_for(_shutdown_event.wait(), timeout=wait_seconds)
            break  # shutdown requested
        except asyncio.TimeoutError:
            pass  # time to send stats

        msg = (
            f"📊 Статистика за сутки\n\n"
            f"Всего получено: {_stats['total']}\n"
            f"Отсеяно: {_stats['rejected']}\n"
            f"Пропущено: {_stats['passed']} "
            f"(🔥 {_stats['hot']} / ⚡ {_stats['interesting']} / 📋 {_stats['other']})"
        )

        if tg_bot:
            try:
                await tg_bot.send_message(config.BOT_API_GROUP_ID, msg)
            except (ConnectionError, ValueError):
                log.exception("Failed to send stats via bot")
        else:
            await _send_via_userbot(msg)

        log.info("Daily stats sent: %s", _stats)
        _reset_stats()


async def main() -> None:
    log.info("Starting freelance filter bot...")
    log.info("Listening for messages from @%s", config.BOT_USERNAME)
    log.info("Forwarding to group %s", config.GROUP_ID)
    log.info("LLM evaluation: %s (model: %s)", "enabled" if config.LLM_ENABLED else "disabled", config.LLM_MODEL)
    log.info("Response generation: %s", "enabled" if config.GENERATE_RESPONSE else "disabled")
    log.info("Inline bot: %s", "enabled" if tg_bot else "disabled")

    await client.start(phone=config.PHONE)

    try:
        await client.get_dialogs()
        log.info("Dialogs cached, group entity should be available")
    except (ConnectionError, ValueError):
        log.exception("Failed to cache dialogs")

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _shutdown_event.set)

    tasks = [client.run_until_disconnected(), _daily_stats()]
    if tg_bot:
        tasks.append(start_bot())

    try:
        await asyncio.gather(*tasks)
    finally:
        _shutdown_event.set()
        log.info("Shutting down gracefully...")


if __name__ == "__main__":
    asyncio.run(main())
