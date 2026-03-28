from __future__ import annotations

import time

import pytest

from bot import CallbackStore, build_keyboard


class TestCallbackStore:
    def test_store_and_get(self) -> None:
        store = CallbackStore()
        key = store.store("order text", "response text")
        data = store.get(key)
        assert data is not None
        assert data["order"] == "order text"
        assert data["response"] == "response text"

    def test_get_missing_key(self) -> None:
        store = CallbackStore()
        assert store.get("999") is None

    def test_get_invalid_key(self) -> None:
        store = CallbackStore()
        assert store.get("abc") is None

    def test_max_size_eviction(self) -> None:
        store = CallbackStore(max_size=3)
        keys = [store.store(f"order {i}", f"resp {i}") for i in range(5)]
        # cleanup runs before adding, so oldest is evicted when size > max
        assert store.get(keys[0]) is None  # evicted
        assert store.get(keys[2]) is not None
        assert store.get(keys[3]) is not None
        assert store.get(keys[4]) is not None

    def test_ttl_expiration(self) -> None:
        store = CallbackStore(ttl=0)
        key = store.store("order", "response")
        time.sleep(0.01)
        assert store.get(key) is None


class TestBuildKeyboard:
    def test_returns_keyboard_with_regen_button(self) -> None:
        kb = build_keyboard("order", "response")
        assert len(kb.inline_keyboard) == 1
        assert kb.inline_keyboard[0][0].text == "🔄 Другой вариант"
        assert kb.inline_keyboard[0][0].callback_data is not None
        assert kb.inline_keyboard[0][0].callback_data.startswith("regen:")
