from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import OrderedDict

from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import config
from evaluator import regenerate_response

log = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN) if config.BOT_TOKEN else None
dp = Dispatcher()


class CallbackStore:
    """In-memory store for callback data with TTL and max size."""

    def __init__(self, max_size: int = 100, ttl: int = 3600) -> None:
        self._data: OrderedDict[int, tuple[float, dict[str, str]]] = OrderedDict()
        self._counter: int = 0
        self._max_size = max_size
        self._ttl = ttl

    def store(self, order_text: str, response_text: str) -> str:
        self._counter += 1
        self._cleanup()
        self._data[self._counter] = (time.time(), {"order": order_text, "response": response_text})
        return str(self._counter)

    def get(self, key: str) -> dict[str, str] | None:
        try:
            entry = self._data.get(int(key))
        except ValueError:
            return None
        if entry is None:
            return None
        ts, data = entry
        if time.time() - ts > self._ttl:
            self._data.pop(int(key), None)
            return None
        return data

    def _cleanup(self) -> None:
        now = time.time()
        expired = [k for k, (ts, _) in self._data.items() if now - ts > self._ttl]
        for k in expired:
            del self._data[k]
        while len(self._data) > self._max_size:
            self._data.popitem(last=False)


_store = CallbackStore()


def build_keyboard(order_text: str, response_text: str) -> InlineKeyboardMarkup:
    """Build inline keyboard with regenerate button. Store data as callback_data."""
    # callback_data has 64 byte limit — store in memory instead
    callback_id = _store.store(order_text, response_text)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Другой вариант", callback_data=f"regen:{callback_id}")]
    ])


@dp.callback_query(F.data.startswith("regen:"))
async def handle_regenerate(callback: CallbackQuery) -> None:
    """Handle inline button press — regenerate response."""
    callback_id = callback.data.split(":", 1)[1]

    data = _store.get(callback_id)
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
    except (ConnectionError, ValueError):
        log.exception("Failed to edit message with new response")


async def start_bot() -> None:
    """Start the aiogram bot polling."""
    if not bot:
        log.warning("BOT_TOKEN not set, inline buttons disabled")
        return
    log.info("Starting inline button bot...")
    await dp.start_polling(bot)
