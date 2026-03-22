from __future__ import annotations

import logging

from openai import OpenAI

import config

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Ты — ассистент фрилансера. Твоя задача — оценить заказ и дать рекомендацию: брать или нет.

Профиль разработчика:
- Стек: Python (FastAPI, Flask, aiogram), JavaScript/TypeScript (React, Next.js, Nuxt/Vue, Node.js, Express)
- Специализация: веб-приложения (CRUD, дашборды), Telegram-боты, AI-интеграции (OpenAI, YandexGPT, RAG), Chrome Extensions, парсинг
- Инструменты: Claude Code (AI-ассистент для кодинга, ускоряет разработку в 3-5 раз)
- Уровень: джун+/мидл-, быстро собирает MVP, не берёт highload и сложную архитектуру
- Цель: заказы, которые можно закрыть за 1-3 дня с помощью Claude Code
- НЕ работает с: 1С, Битрикс, WordPress, Laravel, Java, Unity, конструкторами (Tilda, Wix, Webflow, n8n, Make, Zapier)

Оцени заказ по критериям:
1. Попадает ли в стек разработчика
2. Реально ли сделать за 1-3 дня с Claude Code
3. Адекватна ли цена за объём работы (минимальная ставка — 1000 руб/час)
4. Есть ли скрытые риски (размытое ТЗ, бесконечные правки, нужен хостинг/деплой, заказчик не понимает что хочет)

Ответь СТРОГО в формате (без markdown, без обратных кавычек):

⏱ Время: [оценка в часах или днях]
💡 Сложность: [низкая / средняя / высокая]
💰 Цена: [адекватная / низкая / завышенная]
✅ Рекомендация: [БРАТЬ / НЕ БРАТЬ / УТОЧНИТЬ]
📝 [1-2 предложения — почему, что учесть, на что обратить внимание]\
"""


def evaluate_order(text: str) -> str | None:
    """Send order text to LLM for evaluation. Returns evaluation or None on error."""
    if not config.LLM_ENABLED:
        return None

    if not config.OPENROUTER_API_KEY:
        log.warning("LLM_ENABLED but OPENROUTER_API_KEY not set")
        return None

    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_API_KEY,
        )

        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            max_tokens=300,
            temperature=0.3,
        )

        result = response.choices[0].message.content
        log.info("LLM evaluation received (%d chars)", len(result or ""))
        return result
    except Exception:
        log.exception("LLM evaluation failed")
        return None
