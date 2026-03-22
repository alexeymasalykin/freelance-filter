# Freelance Filter

Telegram-скрипт на Telethon — слушает заказы от @Freelance_find_bot, фильтрует по цене и стоп-словам, пересылает подходящие в группу.

## Быстрый старт (Docker на VPS)

1. Клонировать и настроить:

```bash
git clone <repo-url> freelance_filter
cd freelance_filter
cp .env.example .env
nano .env  # заполнить PHONE, GROUP_ID
mkdir -p data
```

2. Первый запуск (авторизация — нужен ввод кода из Telegram):

```bash
docker compose run --rm freelance-filter
```

3. После успешной авторизации — запуск в фоне:

```bash
docker compose up -d
```

4. Просмотр логов:

```bash
docker compose logs -f freelance-filter
```

## Локальная разработка (без Docker)

```bash
pip install -r requirements.txt
mkdir -p data
cp .env.example .env
python main.py
```

## Настройка

Все параметры в `.env`:
- `PHONE` — номер телефона для авторизации
- `GROUP_ID` — ID группы (отрицательное число)
- `MIN_PRICE` — минимальная цена (по умолчанию 5000)
- `STOP_WORDS` — список стоп-слов через запятую

## Фильтрация

- Заказы с ценой < MIN_PRICE — отклоняются
- Если цена не указана — пересылается (не терять заказ)
- Стоп-слова: 1С, Битрикс, WordPress, Laravel, Java, Unity, и др.
- "Java" не блокирует "JavaScript"
