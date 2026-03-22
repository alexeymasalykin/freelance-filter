# Freelance Filter — Telegram Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Python-скрипт на Telethon, который слушает сообщения от @Freelance_find_bot, фильтрует по цене и стоп-словам, пересылает подходящие в Telegram-группу.

**Architecture:** Три модуля — config (настройки из .env), filter (парсинг + фильтрация), main (Telethon-клиент + event handler). Фильтрация: парсинг цены regex → проверка минимума → проверка стоп-слов regex. Пересылка через `client.forward_messages`.

**Tech Stack:** Python 3.11+, Telethon, python-dotenv, pytest, Docker (deploy on Ubuntu VPS)

---

## File Structure

```
freelance_filter/
├── .dockerignore      # Исключения для Docker build
├── .env.example       # Шаблон переменных окружения
├── .gitignore         # .env, .session, __pycache__, .venv
├── Dockerfile         # Multi-stage build, non-root user
├── docker-compose.yml # Запуск с .env и volume для .session
├── config.py          # Загрузка настроек из .env
├── filter.py          # parse_price() + should_forward()
├── main.py            # Telethon client, event handler, graceful shutdown
├── README.md          # Инструкция по запуску
├── requirements.txt   # telethon, python-dotenv
├── tests/
│   ├── __init__.py
│   └── test_filter.py # Тесты фильтрации
└── docs/
    └── superpowers/
        └── plans/
            └── 2026-03-22-freelance-filter.md
```

---

### Task 1: Project Setup — .gitignore, requirements.txt, .env.example

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `.env.example`

- [ ] **Step 1: Create .gitignore**

```
.env
*.session
__pycache__/
*.pyc
.venv/
.mypy_cache/
.pytest_cache/
```

- [ ] **Step 2: Create .dockerignore**

```
.env
*.session
__pycache__/
*.pyc
.venv/
.git/
.mypy_cache/
.pytest_cache/
tests/
docs/
README.md
```

- [ ] **Step 3: Create requirements.txt**

```
telethon==1.36.0
python-dotenv==1.0.1
pytest==8.3.4
```

- [ ] **Step 4: Create .env.example**

```env
# Telegram API (official Telegram Desktop credentials)
API_ID=2040
API_HASH=b18441a1ff607e10a989891a5462e627

# Your phone number for Telethon auth
PHONE=+79001234567

# Telegram group ID to forward orders to (negative number for groups)
GROUP_ID=-1001234567890

# Minimum price in RUB (orders below this are filtered out)
MIN_PRICE=5000

# Comma-separated stop words (case-insensitive)
STOP_WORDS=1С,Битрикс,Bitrix,WordPress,WP,Laravel,Java,Unity,n8n,Zapier,Tilda,Тильда,Wix,Webflow,Bubble,Shopify,OpenCart,Joomla,Drupal,ModX
```

- [ ] **Step 5: Commit**

```bash
git add .gitignore .dockerignore requirements.txt .env.example
git commit -m "chore: initial project setup — gitignore, dockerignore, deps, env template"
```

---

### Task 2: Config Module

**Files:**
- Create: `config.py`

- [ ] **Step 1: Create config.py**

```python
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

API_ID: int = int(os.environ["API_ID"])
API_HASH: str = os.environ["API_HASH"]
PHONE: str = os.environ["PHONE"]
GROUP_ID: int = int(os.environ["GROUP_ID"])
MIN_PRICE: float = float(os.getenv("MIN_PRICE", "5000"))
STOP_WORDS: list[str] = [
    w.strip() for w in os.getenv(
        "STOP_WORDS",
        "1С,Битрикс,Bitrix,WordPress,WP,Laravel,Java,Unity,n8n,Zapier,Tilda,Тильда,Wix,Webflow,Bubble,Shopify,OpenCart,Joomla,Drupal,ModX"
    ).split(",") if w.strip()
]

BOT_USERNAME: str = "Freelance_find_bot"
SESSION_NAME: str = "freelance_filter"
```

- [ ] **Step 2: Commit**

```bash
git add config.py
git commit -m "feat(config): load settings from .env"
```

---

### Task 3: Filter — parse_price (TDD)

**Files:**
- Create: `filter.py`
- Create: `tests/__init__.py`
- Create: `tests/test_filter.py`

- [ ] **Step 1: Write failing tests for parse_price**

```python
# tests/test_filter.py
from filter import parse_price


class TestParsePrice:
    def test_parses_rub_price(self) -> None:
        msg = "💰 Цена: 1500.0 RUB"
        assert parse_price(msg) == 1500.0

    def test_parses_integer_price(self) -> None:
        msg = "💰 Цена: 30000 RUB"
        assert parse_price(msg) == 30000.0

    def test_returns_none_when_no_price(self) -> None:
        msg = "Какой-то текст без цены"
        assert parse_price(msg) is None

    def test_parses_price_with_spaces(self) -> None:
        msg = "💰 Цена: 15 000.0 RUB"
        assert parse_price(msg) == 15000.0

    def test_parses_price_without_rub(self) -> None:
        msg = "💰 Цена: договорная"
        assert parse_price(msg) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_filter.py::TestParsePrice -v`
Expected: FAIL — `ImportError: cannot import name 'parse_price'`

- [ ] **Step 3: Implement parse_price**

```python
# filter.py
from __future__ import annotations

import re


def parse_price(text: str) -> float | None:
    """Extract price in RUB from bot message. Returns None if not found."""
    match = re.search(r"Цена:\s*([\d\s]+(?:\.\d+)?)\s*RUB", text)
    if not match:
        return None
    price_str = match.group(1).replace(" ", "")
    try:
        return float(price_str)
    except ValueError:
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_filter.py::TestParsePrice -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add filter.py tests/__init__.py tests/test_filter.py
git commit -m "feat(filter): add parse_price with tests"
```

---

### Task 4: Filter — should_forward stop words (TDD)

**Files:**
- Modify: `filter.py`
- Modify: `tests/test_filter.py`

- [ ] **Step 1: Write failing tests for stop words**

Append to `tests/test_filter.py`:

```python
from filter import parse_price, should_forward

STOP_WORDS = [
    "1С", "Битрикс", "Bitrix", "WordPress", "WP", "Laravel",
    "Java", "Unity", "n8n", "Zapier", "Tilda", "Тильда",
    "Wix", "Webflow", "Bubble", "Shopify", "OpenCart",
    "Joomla", "Drupal", "ModX",
]


class TestShouldForwardStopWords:
    def test_blocks_bitrix(self) -> None:
        msg = "Нужен разработчик Bitrix для интернет-магазина\n💰 Цена: 50000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=STOP_WORDS) is False

    def test_blocks_1c_cyrillic(self) -> None:
        msg = "Доработка 1С модуля\n💰 Цена: 10000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=STOP_WORDS) is False

    def test_blocks_wordpress_case_insensitive(self) -> None:
        msg = "Сделать сайт на wordpress\n💰 Цена: 8000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=STOP_WORDS) is False

    def test_java_does_not_block_javascript(self) -> None:
        msg = "Нужен JavaScript разработчик\n💰 Цена: 20000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=STOP_WORDS) is True

    def test_java_does_not_block_java_space_script(self) -> None:
        msg = "Нужен Java Script разработчик\n💰 Цена: 20000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=STOP_WORDS) is True

    def test_java_blocks_java_standalone(self) -> None:
        msg = "Нужен Java разработчик\n💰 Цена: 20000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=STOP_WORDS) is False

    def test_wp_only_as_whole_word(self) -> None:
        msg = "Viewport размер важен\n💰 Цена: 10000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=STOP_WORDS) is True

    def test_wp_blocks_standalone(self) -> None:
        msg = "Сайт на WP нужен\n💰 Цена: 10000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=STOP_WORDS) is False

    def test_make_blocks_make_com(self) -> None:
        msg = "Автоматизация через make.com\n💰 Цена: 10000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=["Make"]) is False

    def test_make_blocks_capitalized(self) -> None:
        msg = "Настроить сценарий в Make\n💰 Цена: 10000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=["Make"]) is False

    def test_make_does_not_block_regular_text(self) -> None:
        msg = "We need to make a website\n💰 Цена: 10000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=["Make"]) is True

    def test_blocks_tilda_cyrillic(self) -> None:
        msg = "Сайт на Тильда\n💰 Цена: 7000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=STOP_WORDS) is False

    def test_blocks_bitrix_cyrillic(self) -> None:
        msg = "Доработка Битрикс магазина\n💰 Цена: 15000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=STOP_WORDS) is False

    def test_passes_clean_message(self) -> None:
        msg = "Создать React приложение\n💰 Цена: 50000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=STOP_WORDS) is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_filter.py::TestShouldForwardStopWords -v`
Expected: FAIL — `ImportError: cannot import name 'should_forward'`

- [ ] **Step 3: Implement should_forward**

Add to `filter.py`:

```python
def _build_stop_pattern(word: str) -> re.Pattern[str]:
    """Build regex pattern for a stop word with special rules."""
    lower = word.lower()

    if lower == "java":
        # "Java" but NOT "JavaScript" or "Java Script"
        return re.compile(r"\bJava\b(?!\s*Script)", re.IGNORECASE)

    if lower == "wp":
        # "WP" only as standalone word
        return re.compile(r"\bWP\b", re.IGNORECASE)

    if lower == "make":
        # Only "Make" as platform — match "make.com" or capitalized "Make" at word boundary
        # but not lowercase "make" in regular text
        return re.compile(r"\bmake\.com\b|(?<!\w)Make(?!\w)")

    # Check if word contains non-ASCII (cyrillic) — use Unicode word boundaries
    escaped = re.escape(word)
    if any(ord(c) > 127 for c in word):
        # \b doesn't work reliably with cyrillic; use lookaround with \w and re.UNICODE
        return re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE | re.UNICODE)

    # Default: word boundary match for ASCII words
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


def should_forward(text: str, *, min_price: float, stop_words: list[str]) -> bool:
    """Check if message passes all filters and should be forwarded."""
    # Check stop words
    for word in stop_words:
        pattern = _build_stop_pattern(word)
        if pattern.search(text):
            return False

    # Check price
    price = parse_price(text)
    if price is None:
        return True  # No price — forward (don't lose potentially good orders)
    return price >= min_price
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_filter.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add filter.py tests/test_filter.py
git commit -m "feat(filter): add should_forward with stop words and price check"
```

---

### Task 5: Filter — should_forward price logic (TDD)

**Files:**
- Modify: `tests/test_filter.py`

- [ ] **Step 1: Write failing tests for price filtering**

Append to `tests/test_filter.py`:

```python
class TestShouldForwardPrice:
    def test_blocks_low_price(self) -> None:
        msg = "Простая задача\n💰 Цена: 1500.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=[]) is False

    def test_passes_exact_min_price(self) -> None:
        msg = "Задача\n💰 Цена: 5000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=[]) is True

    def test_passes_above_min_price(self) -> None:
        msg = "Задача\n💰 Цена: 50000.0 RUB"
        assert should_forward(msg, min_price=5000, stop_words=[]) is True

    def test_passes_when_no_price(self) -> None:
        msg = "Задача без указания цены"
        assert should_forward(msg, min_price=5000, stop_words=[]) is True
```

- [ ] **Step 2: Run tests to verify they pass** (implementation already done in Task 4)

Run: `python -m pytest tests/test_filter.py::TestShouldForwardPrice -v`
Expected: all PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_filter.py
git commit -m "test(filter): add price filtering tests"
```

---

### Task 6: Main Module — Telethon Client

**Files:**
- Create: `main.py`

- [ ] **Step 1: Create main.py**

```python
from __future__ import annotations

import logging
import sys

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

import config
from filter import should_forward

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


client = TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)


@client.on(events.NewMessage(from_users=config.BOT_USERNAME))
async def handler(event: events.NewMessage.Event) -> None:
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
        import asyncio
        await asyncio.sleep(e.seconds)
        await client.forward_messages(config.GROUP_ID, event.message)
        log.info("FORWARDED (after wait): message sent to group %s", config.GROUP_ID)
    except Exception:
        log.exception("Failed to forward message")


def main() -> None:
    log.info("Starting freelance filter bot...")
    log.info("Listening for messages from @%s", config.BOT_USERNAME)
    log.info("Forwarding to group %s", config.GROUP_ID)
    log.info("Min price: %.0f RUB", config.MIN_PRICE)
    log.info("Stop words: %d configured", len(config.STOP_WORDS))

    client.start(phone=config.PHONE)

    try:
        client.run_until_disconnected()
    except KeyboardInterrupt:
        log.info("Shutting down gracefully...")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add main.py
git commit -m "feat(main): telethon client with event handler and graceful shutdown"
```

---

### Task 7: Filter Detail Logging

**Files:**
- Modify: `filter.py`

- [ ] **Step 1: Add logging to should_forward for rejection reasons**

Add at the top of `filter.py`:

```python
import logging

log = logging.getLogger(__name__)
```

Update `should_forward` to log rejection reasons:

```python
def should_forward(text: str, *, min_price: float, stop_words: list[str]) -> bool:
    """Check if message passes all filters and should be forwarded."""
    # Check stop words
    for word in stop_words:
        pattern = _build_stop_pattern(word)
        if pattern.search(text):
            log.info("REJECTED: stop word '%s' found", word)
            return False

    # Check price
    price = parse_price(text)
    if price is None:
        log.info("PASSED: no price found, forwarding")
        return True
    if price < min_price:
        log.info("REJECTED: price %.0f < min %.0f", price, min_price)
        return False

    log.info("PASSED: price %.0f >= min %.0f", price, min_price)
    return True
```

- [ ] **Step 2: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: all PASS

- [ ] **Step 3: Commit**

```bash
git add filter.py
git commit -m "feat(filter): add rejection reason logging"
```

---

### Task 8: Docker + README

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `README.md`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.11-slim AS base

RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py filter.py main.py ./

RUN chown -R appuser:appuser /app
USER appuser

CMD ["python", "-u", "main.py"]
```

- [ ] **Step 2: Create docker-compose.yml**

```yaml
services:
  freelance-filter:
    build: .
    container_name: freelance-filter
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./data:/app/data
    stdin_open: true
    tty: true
```

- [ ] **Step 3: Update config.py — session path to data/ dir**

In `config.py`, change `SESSION_NAME` to store session in a mounted volume:

```python
SESSION_NAME: str = "data/freelance_filter"
```

- [ ] **Step 4: Create README.md**

````markdown
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
````

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml README.md
git commit -m "feat: add Docker setup for VPS deployment"
```

---

### Task 9: Final Verification

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: all PASS

- [ ] **Step 2: Verify imports work**

Run: `python -c "from filter import parse_price, should_forward; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Create initial commit with plan and task**

```bash
git add docs/ freelance_filter_task.md
git commit -m "docs: add task spec and implementation plan"
```
