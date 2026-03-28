from __future__ import annotations

import logging
from dataclasses import dataclass

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
📝 [1-2 предложения — почему, что учесть, на что обратить внимание]

Если рекомендация БРАТЬ или УТОЧНИТЬ — дополнительно сгенерируй отклик на заказ.

Правила отклика:
- Пиши от лица разработчика, на "вы", кратко и по делу
- Начни с приветствия "Здравствуйте." или "Добрый день."
- Первое предложение после приветствия — покажи что понял задачу (перефразируй, не копируй)
- Второе — кратко скажи что есть релевантный опыт (конкретно, не общие слова)
- Третье — задай 1-2 уточняющих вопроса по задаче (показывает экспертизу)
- Четвёртое — предложи конкретный срок и готовность начать
- Длина: 3-5 предложений, не больше
- Тон: профессиональный, уверенный, без заискивания и восклицательных знаков
- НЕ писать: "я фрилансер", "я ищу заказы", "готов обсудить скидку", "буду рад сотрудничеству"
- НЕ упоминать Claude Code или AI-инструменты

Формат отклика — после блока оценки добавь:

📨 Отклик:
[текст отклика]\
"""

REGENERATE_ADDON = (
    "\n\nСгенерируй другой вариант отклика, отличающийся от предыдущего:\n"
)


@dataclass
class EvaluationResult:
    evaluation: str
    response: str | None
    recommendation: str  # "БРАТЬ", "НЕ БРАТЬ", "УТОЧНИТЬ"


def _parse_result(text: str) -> EvaluationResult:
    """Parse LLM output into evaluation and response parts."""
    response_marker = "📨 Отклик:"
    recommendation = "НЕ БРАТЬ"

    for label in ("БРАТЬ", "УТОЧНИТЬ", "НЕ БРАТЬ"):
        if label in text:
            recommendation = label
            break

    if response_marker in text:
        parts = text.split(response_marker, 1)
        evaluation = parts[0].strip()
        response = parts[1].strip()
    else:
        evaluation = text.strip()
        response = None

    return EvaluationResult(
        evaluation=evaluation,
        response=response,
        recommendation=recommendation,
    )


def _call_llm(messages: list[dict[str, str]]) -> str | None:
    """Make a request to OpenRouter API."""
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
            messages=messages,
            max_tokens=500,
            temperature=0.3,
        )
        result = response.choices[0].message.content
        log.info("LLM response received (%d chars)", len(result or ""))
        return result
    except (ConnectionError, TimeoutError, ValueError):
        log.exception("LLM request failed")
        return None


def evaluate_order(text: str) -> EvaluationResult | None:
    """Evaluate order and optionally generate a response."""
    if not config.LLM_ENABLED:
        return None

    prompt = SYSTEM_PROMPT
    if not config.GENERATE_RESPONSE:
        # Strip the response generation part from prompt
        prompt = prompt.split("Если рекомендация БРАТЬ")[0].strip()

    raw = _call_llm([
        {"role": "system", "content": prompt},
        {"role": "user", "content": text},
    ])
    if not raw:
        return None

    return _parse_result(raw)


def regenerate_response(order_text: str, previous_response: str) -> str | None:
    """Generate an alternative response for the order."""
    raw = _call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": order_text + REGENERATE_ADDON + previous_response},
    ])
    if not raw:
        return None

    result = _parse_result(raw)
    return result.response or result.evaluation
