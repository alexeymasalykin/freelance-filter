from filter import parse_price, evaluate_order, Priority


class TestParsePrice:
    def test_parses_rub_price(self) -> None:
        assert parse_price("💰 Цена: 1500.0 RUB") == 1500.0

    def test_parses_integer_price(self) -> None:
        assert parse_price("💰 Цена: 30000 RUB") == 30000.0

    def test_returns_none_when_no_price(self) -> None:
        assert parse_price("Какой-то текст без цены") is None

    def test_parses_price_with_spaces(self) -> None:
        assert parse_price("💰 Цена: 15 000.0 RUB") == 15000.0


class TestLevel1Price:
    def test_passes_no_price_without_stop_words(self) -> None:
        msg = "Какой-то заказ\n📋 ID: 123\nБез цены"
        r = evaluate_order(msg)
        assert r.passed is True
        assert r.priority == Priority.OTHER

    def test_rejects_no_price_with_stop_word(self) -> None:
        msg = "Парсинг данных\n📋 ID: 123\nБез цены"
        r = evaluate_order(msg)
        assert r.passed is False
        assert "stop word" in r.reject_reason

    def test_rejects_low_price(self) -> None:
        msg = "Задача\n📋 ID: 123\n💰 Цена: 5000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is False
        assert "< 10000" in r.reject_reason

    def test_passes_10000(self) -> None:
        msg = "Задача\n📋 ID: 123\n💰 Цена: 10000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is True


class TestLevel2StopWords:
    def test_rejects_bitrix(self) -> None:
        msg = "Доработка Bitrix\n📋 ID: 123\n💰 Цена: 50000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is False
        assert "stop word" in r.reject_reason

    def test_rejects_1c(self) -> None:
        msg = "Доработка 1С модуля\n📋 ID: 123\n💰 Цена: 30000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is False

    def test_rejects_wordpress(self) -> None:
        msg = "Сайт на WordPress\n📋 ID: 123\n💰 Цена: 20000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is False

    def test_rejects_mobile_app(self) -> None:
        msg = "Мобильное приложение для доставки\n📋 ID: 123\n💰 Цена: 100000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is False

    def test_rejects_seo(self) -> None:
        msg = "SEO продвижение сайта\n📋 ID: 123\n💰 Цена: 20000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is False

    def test_rejects_video(self) -> None:
        msg = "Создать ролик для инстаграмм\n📋 ID: 123\n💰 Цена: 15000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is False

    def test_rejects_parser(self) -> None:
        msg = "Парсинг сайтов\n📋 ID: 123\n💰 Цена: 12000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is False

    def test_rejects_vacancy(self) -> None:
        msg = "Вакансия frontend\n📋 ID: 123\n💰 Цена: 50000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is False

    def test_rejects_php(self) -> None:
        msg = "PHP разработчик нужен\n📋 ID: 123\n💰 Цена: 30000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is False

    def test_rejects_android(self) -> None:
        msg = "Приложение Android\n📋 ID: 123\n💰 Цена: 40000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is False

    def test_rejects_internet_shop(self) -> None:
        msg = "Интернет-магазин одежды\n📋 ID: 123\n💰 Цена: 50000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is False


class TestLevel3Priority:
    def test_hot_landing(self) -> None:
        msg = "Создать лендинг для студии\n📋 ID: 123\n💰 Цена: 14000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is True
        assert r.priority == Priority.HOT

    def test_hot_react(self) -> None:
        msg = "React приложение\n📋 ID: 123\n💰 Цена: 30000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is True
        assert r.priority == Priority.HOT

    def test_hot_frontend(self) -> None:
        msg = "Фронтенд разработка\n📋 ID: 123\n💰 Цена: 15000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is True
        assert r.priority == Priority.HOT

    def test_interesting_bot(self) -> None:
        msg = "Разработать телеграм бота\n📋 ID: 123\n💰 Цена: 40000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is True
        assert r.priority == Priority.INTERESTING

    def test_interesting_python(self) -> None:
        msg = "Python скрипт автоматизации\n📋 ID: 123\n💰 Цена: 20000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is True
        assert r.priority == Priority.INTERESTING

    def test_interesting_ai(self) -> None:
        msg = "AI интеграция в CRM\n📋 ID: 123\n💰 Цена: 50000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is True
        assert r.priority == Priority.INTERESTING

    def test_interesting_needs_15000(self) -> None:
        msg = "Телеграм бот\n📋 ID: 123\n💰 Цена: 10000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is True
        assert r.priority == Priority.OTHER  # < 15000, no hot keywords

    def test_other_generic(self) -> None:
        msg = "Доработка сайта\n📋 ID: 123\n💰 Цена: 12000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is True
        assert r.priority == Priority.OTHER

    def test_not_order(self) -> None:
        msg = "Подписка оформлена. Спасибо!"
        r = evaluate_order(msg)
        assert r.passed is False


class TestEdgeCases:
    def test_empty_message(self) -> None:
        r = evaluate_order("")
        assert r.passed is False

    def test_only_whitespace(self) -> None:
        r = evaluate_order("   \n\n  ")
        assert r.passed is False

    def test_unicode_emoji_in_text(self) -> None:
        msg = "🚀 Крутой проект 💪\n📋 ID: 123\n💰 Цена: 20000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is True

    def test_zero_price(self) -> None:
        msg = "Бесплатно\n📋 ID: 123\n💰 Цена: 0 RUB"
        r = evaluate_order(msg)
        assert r.passed is False

    def test_huge_price(self) -> None:
        msg = "Большой проект\n📋 ID: 123\n💰 Цена: 999999.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is True

    def test_price_with_decimals(self) -> None:
        assert parse_price("💰 Цена: 10500.50 RUB") == 10500.50

    def test_stop_word_java_not_blocks_javascript(self) -> None:
        msg = "JavaScript разработка\n📋 ID: 123\n💰 Цена: 20000.0 RUB"
        r = evaluate_order(msg)
        assert r.passed is True

    def test_is_order_false_for_service_message(self) -> None:
        from filter import is_order
        assert is_order("Спасибо за подписку!") is False

    def test_is_order_true(self) -> None:
        from filter import is_order
        assert is_order("Разработка сайта\n📋 ID: 456") is True

    def test_title_extraction_skips_emoji_lines(self) -> None:
        from filter import _extract_title
        text = "📋 ID: 123\nНастоящий заголовок"
        assert _extract_title(text) == "Настоящий заголовок"

    def test_title_truncated_at_80_chars(self) -> None:
        from filter import _extract_title
        long = "A" * 100
        assert len(_extract_title(long)) == 80
