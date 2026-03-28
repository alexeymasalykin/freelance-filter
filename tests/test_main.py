"""Tests for main.py — pure functions and handler logic with mocks."""

from __future__ import annotations

import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set required env vars before importing main (config.validate() runs at import time)
os.environ.setdefault("API_ID", "123456")
os.environ.setdefault("API_HASH", "fake_hash")
os.environ.setdefault("PHONE", "+70000000000")
os.environ.setdefault("GROUP_ID", "-100999")
os.environ.setdefault("LLM_ENABLED", "false")
os.environ.setdefault("GENERATE_RESPONSE", "false")

from main import _format_price, _reset_stats, _stats, handler  # noqa: E402
from filter import FilterResult, Priority  # noqa: E402


# ---------------------------------------------------------------------------
# _format_price
# ---------------------------------------------------------------------------


class TestFormatPrice:
    def test_formats_thousands(self) -> None:
        assert _format_price(14000) == "14 000"

    def test_formats_small_number(self) -> None:
        assert _format_price(500) == "500"

    def test_formats_large_number(self) -> None:
        assert _format_price(1_000_000) == "1 000 000"

    def test_formats_decimal_rounds(self) -> None:
        assert _format_price(14999.99) == "15 000"

    def test_formats_zero(self) -> None:
        assert _format_price(0) == "0"

    def test_formats_exact_thousand(self) -> None:
        assert _format_price(1000) == "1 000"


# ---------------------------------------------------------------------------
# _reset_stats
# ---------------------------------------------------------------------------


class TestResetStats:
    def test_resets_all_counters(self) -> None:
        _stats["total"] = 10
        _stats["rejected"] = 5
        _stats["passed"] = 5
        _stats["hot"] = 2
        _stats["interesting"] = 1
        _stats["other"] = 2
        _reset_stats()
        for key in _stats:
            assert _stats[key] == 0, f"_stats['{key}'] should be 0"

    def test_resets_already_zero(self) -> None:
        _reset_stats()
        _reset_stats()
        for key in _stats:
            assert _stats[key] == 0


# ---------------------------------------------------------------------------
# handler (mocked Telethon event)
# ---------------------------------------------------------------------------


def _make_event(text: str = "test order", msg_timestamp: float | None = None) -> MagicMock:
    """Create a fake Telethon NewMessage event."""
    event = MagicMock()
    event.message.text = text
    event.message.date.timestamp.return_value = (
        msg_timestamp if msg_timestamp is not None else time.time()
    )
    event.message.reply_markup = None  # no inline buttons
    event.message.chat_id = -100999
    event.message.id = 42
    return event


class TestHandler:
    """Test handler logic with mocked Telethon objects."""

    @pytest.fixture(autouse=True)
    def _reset(self) -> None:
        """Reset stats before each test."""
        _reset_stats()

    @pytest.mark.asyncio
    @patch("main.filter_order")
    async def test_skips_old_messages(self, mock_filter: MagicMock) -> None:
        """Messages older than _start_time - 60 should be skipped."""
        event = _make_event(msg_timestamp=0)  # epoch = very old
        await handler(event)
        mock_filter.assert_not_called()

    @pytest.mark.asyncio
    @patch("main.filter_order")
    async def test_rejects_filtered_orders(self, mock_filter: MagicMock) -> None:
        """Orders not passing filter should increment rejected counter."""
        mock_filter.return_value = FilterResult(
            passed=False, reject_reason="too cheap"
        )
        event = _make_event()
        await handler(event)
        assert _stats["rejected"] == 1
        assert _stats["passed"] == 0

    @pytest.mark.asyncio
    @patch("main._send_via_userbot", new_callable=AsyncMock)
    @patch("main.llm_evaluate", return_value=None)
    @patch("main.client")
    @patch("main.filter_order")
    async def test_passed_order_increments_stats(
        self,
        mock_filter: MagicMock,
        mock_client: MagicMock,
        mock_llm: MagicMock,
        mock_send: AsyncMock,
    ) -> None:
        """Passed HOT order should increment passed + hot counters."""
        mock_filter.return_value = FilterResult(
            passed=True, priority=Priority.HOT, price=25000, title="Лендинг"
        )
        mock_client.forward_messages = AsyncMock()
        mock_client.get_messages = AsyncMock(return_value=None)

        event = _make_event()
        await handler(event)

        assert _stats["total"] == 1
        assert _stats["passed"] == 1
        assert _stats["hot"] == 1
        assert _stats["rejected"] == 0

    @pytest.mark.asyncio
    @patch("main._send_via_userbot", new_callable=AsyncMock)
    @patch("main.llm_evaluate", return_value=None)
    @patch("main.client")
    @patch("main.filter_order")
    async def test_interesting_priority_counted(
        self,
        mock_filter: MagicMock,
        mock_client: MagicMock,
        mock_llm: MagicMock,
        mock_send: AsyncMock,
    ) -> None:
        """INTERESTING priority should increment interesting counter."""
        mock_filter.return_value = FilterResult(
            passed=True, priority=Priority.INTERESTING, price=20000, title="Telegram бот"
        )
        mock_client.forward_messages = AsyncMock()
        mock_client.get_messages = AsyncMock(return_value=None)

        event = _make_event()
        await handler(event)

        assert _stats["interesting"] == 1
        assert _stats["hot"] == 0

    @pytest.mark.asyncio
    @patch("main._send_via_userbot", new_callable=AsyncMock)
    @patch("main.llm_evaluate", return_value=None)
    @patch("main.client")
    @patch("main.filter_order")
    async def test_other_priority_counted(
        self,
        mock_filter: MagicMock,
        mock_client: MagicMock,
        mock_llm: MagicMock,
        mock_send: AsyncMock,
    ) -> None:
        """OTHER priority should increment other counter."""
        mock_filter.return_value = FilterResult(
            passed=True, priority=Priority.OTHER, price=15000, title="Задача"
        )
        mock_client.forward_messages = AsyncMock()
        mock_client.get_messages = AsyncMock(return_value=None)

        event = _make_event()
        await handler(event)

        assert _stats["other"] == 1
        assert _stats["hot"] == 0
        assert _stats["interesting"] == 0

    @pytest.mark.asyncio
    @patch("main.filter_order")
    async def test_total_increments_on_reject(self, mock_filter: MagicMock) -> None:
        """Even rejected orders should increment total counter."""
        mock_filter.return_value = FilterResult(
            passed=False, reject_reason="stop word"
        )
        event = _make_event()
        await handler(event)
        assert _stats["total"] == 1
