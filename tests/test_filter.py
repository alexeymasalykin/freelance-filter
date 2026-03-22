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
