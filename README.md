# Freelance Filter

Telegram-бот для автоматической фильтрации фриланс-заказов. Слушает канал [@Freelance_find_bot](https://t.me/Freelance_find_bot) через Telethon userbot, фильтрует по цене, стоп-словам и приоритету, пересылает подходящие заказы в приватную группу с LLM-оценкой и готовым откликом.

## Как это работает

```
@Freelance_find_bot
        │
        ▼
   ┌─────────┐     отклонён
   │ Фильтр  │──────────────► /dev/null
   │ (3 ур.) │
   └────┬────┘
        │ прошёл
        ▼
  ┌───────────┐
  │  Пересылка│──► Приватная группа (оригинал)
  └─────┬─────┘
        │
        ▼
  ┌───────────┐
  │ LLM-оценка│──► Приватная группа (оценка + отклик)
  │ OpenRouter │    с кнопкой "Другой вариант"
  └───────────┘
```

### Трёхуровневая фильтрация

1. **Цена** — заказы дешевле 10 000 ₽ отсеиваются. Без цены — пропускаются (чтобы не потерять заказ)
2. **Стоп-слова** — 1С, Битрикс, WordPress, SEO, мобильные приложения, вакансии и т.д.
3. **Приоритет** — заказы ранжируются по ключевым словам:
   - 🔥 **Hot** — фронтенд (React, Next.js, верстка, лендинги) от 10 000 ₽
   - ⚡ **Interesting** — боты, Python, AI/нейросети от 15 000 ₽
   - 📋 **Other** — остальные прошедшие фильтр

### LLM-оценка

Каждый прошедший заказ оценивается LLM (по умолчанию Claude Haiku через OpenRouter):
- Время выполнения, сложность, адекватность цены
- Рекомендация: БРАТЬ / НЕ БРАТЬ / УТОЧНИТЬ
- Готовый текст отклика с кнопкой перегенерации

## Стек

- **Telethon** — userbot для чтения сообщений и пересылки
- **aiogram 3** — inline-бот для кнопки перегенерации отклика
- **OpenAI SDK** → OpenRouter — LLM-оценка заказов
- **Docker** — деплой на VPS

## Быстрый старт

### Docker (рекомендуется)

```bash
git clone https://github.com/username/freelance-filter.git
cd freelance-filter
cp .env.example .env
nano .env  # заполнить переменные
mkdir -p data
```

Первый запуск — нужен ввод кода авторизации из Telegram:

```bash
docker compose run --rm freelance-filter
```

После авторизации — запуск в фоне:

```bash
docker compose up -d
docker compose logs -f freelance-filter  # логи
```

### Локально

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p data
python main.py
```

## Конфигурация

Все параметры через `.env`:

| Переменная | Обязательная | Описание |
|---|---|---|
| `API_ID` | да | Telegram API ID ([my.telegram.org](https://my.telegram.org)) |
| `API_HASH` | да | Telegram API Hash |
| `PHONE` | да | Номер телефона для авторизации |
| `GROUP_ID` | да | ID приватной группы (отрицательное число) |
| `BOT_TOKEN` | нет | Токен бота для inline-кнопок |
| `LLM_ENABLED` | нет | Включить LLM-оценку (`true`/`false`, по умолчанию `true`) |
| `OPENROUTER_API_KEY` | нет | API-ключ OpenRouter |
| `LLM_MODEL` | нет | Модель для оценки (по умолчанию `anthropic/claude-haiku-4-5`) |
| `GENERATE_RESPONSE` | нет | Генерировать отклик (`true`/`false`, по умолчанию `true`) |

## Структура проекта

```
├── main.py          # Точка входа, Telethon event handler
├── filter.py        # 3-уровневый фильтр (цена, стоп-слова, приоритет)
├── evaluator.py     # LLM-оценка через OpenRouter
├── bot.py           # Inline-бот (aiogram) для перегенерации откликов
├── config.py        # Конфигурация из .env
├── tests/           # Тесты (pytest)
├── Dockerfile
└── docker-compose.yml
```

## Тесты

```bash
pip install pytest
pytest -v
```

## Лицензия

MIT
