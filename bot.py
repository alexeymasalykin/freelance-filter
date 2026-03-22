from __future__ import annotations

import asyncio
import json
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import config
from evaluator import regenerate_response

log = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN) if config.BOT_TOKEN else None
dp = Dispatcher()


def build_keyboard(order_text: str, response_text: str) -> InlineKeyboardMarkup:
    """Build inline keyboard with regenerate button. Store data as callback_data."""
    # callback_data has 64 byte limit — store in memory instead
    callback_id = _store_callback(order_text, response_text)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Другой вариант", callback_data=f"regen:{callback_id}")]
    ])


# In-memory store for callback data (order text + current response)
_callback_store: dict[str, dict[str, str]] = {}
_counter = 0


def _store_callback(order_text: str, response_text: str) -> str:
    global _counter
    _counter += 1
    key = str(_counter)
    _callback_store[key] = {"order": order_text, "response": response_text}
    # Keep only last 100 entries to avoid memory leak
    if len(_callback_store) > 100:
        oldest = list(_callback_store.keys())[0]
        del _callback_store[oldest]
    return key


@dp.callback_query(F.data.startswith("regen:"))
async def handle_regenerate(callback: CallbackQuery) -> None:
    """Handle inline button press — regenerate response."""
    callback_id = callback.data.split(":", 1)[1]

    data = _callback_store.get(callback_id)
    if not data:
        await callback.answer("Данные устарели, сгенерируйте оценку заново")
        return

    await callback.answer("Генерирую новый вариант...")

    new_response = await asyncio.to_thread(
        regenerate_response, data["order"], data["response"]
    )

    if not new_response:
        await callback.answer("Не удалось сгенерировать новый вариант")
        return

    # Update stored response
    data["response"] = new_response

    # Rebuild message text — find and replace response part
    msg = callback.message
    old_text = msg.text or ""

    response_marker = "📨 Отклик:"
    if response_marker in old_text:
        eval_part = old_text.split(response_marker, 1)[0].strip()
        new_text = f"{eval_part}\n\n📨 Отклик:\n{new_response}"
    else:
        new_text = f"{old_text}\n\n📨 Отклик:\n{new_response}"

    keyboard = build_keyboard(data["order"], new_response)
    try:
        await msg.edit_text(new_text, reply_markup=keyboard)
    except Exception:
        log.exception("Failed to edit message with new response")


async def start_bot() -> None:
    """Start the aiogram bot polling."""
    if not bot:
        log.warning("BOT_TOKEN not set, inline buttons disabled")
        return
    log.info("Starting inline button bot...")
    await dp.start_polling(bot)
