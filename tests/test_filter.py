from filter import parse_price, should_forward

STOP_WORDS = [
    "1С", "Битрикс", "Bitrix", "WordPress", "WP", "Laravel",
    "Java", "Unity", "n8n", "Zapier", "Tilda", "Тильда",
    "Wix", "Webflow", "Bubble", "Shopify", "OpenCart",
    "Joomla", "Drupal", "ModX",
]


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
