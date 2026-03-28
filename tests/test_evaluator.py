from unittest.mock import patch, MagicMock

from evaluator import evaluate_order, regenerate_response, _parse_result, EvaluationResult


class TestParseResult:
    def test_parses_evaluation_with_response(self) -> None:
        text = (
            "⏱ Время: 2 дня\n💡 Сложность: средняя\n✅ Рекомендация: БРАТЬ\n📝 Хороший заказ"
            "\n\n📨 Отклик:\nЗдравствуйте. Готов взяться."
        )
        result = _parse_result(text)
        assert result.recommendation == "БРАТЬ"
        assert result.response == "Здравствуйте. Готов взяться."
        assert "📨" not in result.evaluation

    def test_parses_evaluation_without_response(self) -> None:
        text = "⏱ Время: 1 час\n✅ Рекомендация: НЕ БРАТЬ\n📝 Слишком дёшево"
        result = _parse_result(text)
        assert result.recommendation == "НЕ БРАТЬ"
        assert result.response is None

    def test_parses_recommendation_clarify(self) -> None:
        text = "✅ Рекомендация: УТОЧНИТЬ\n📝 Нужно ТЗ"
        result = _parse_result(text)
        assert result.recommendation == "УТОЧНИТЬ"

    def test_defaults_to_ne_brat(self) -> None:
        text = "Непонятный ответ без рекомендации"
        result = _parse_result(text)
        assert result.recommendation == "НЕ БРАТЬ"


class TestEvaluateOrder:
    @patch("evaluator._call_llm")
    def test_returns_none_when_llm_disabled(self, mock_llm: MagicMock) -> None:
        with patch("evaluator.config") as mock_config:
            mock_config.LLM_ENABLED = False
            result = evaluate_order("test order")
            assert result is None
            mock_llm.assert_not_called()

    @patch("evaluator._call_llm")
    def test_returns_none_when_llm_returns_none(self, mock_llm: MagicMock) -> None:
        with patch("evaluator.config") as mock_config:
            mock_config.LLM_ENABLED = True
            mock_config.GENERATE_RESPONSE = True
            mock_llm.return_value = None
            result = evaluate_order("test order")
            assert result is None

    @patch("evaluator._call_llm")
    def test_returns_parsed_result(self, mock_llm: MagicMock) -> None:
        with patch("evaluator.config") as mock_config:
            mock_config.LLM_ENABLED = True
            mock_config.GENERATE_RESPONSE = True
            mock_config.LLM_MODEL = "test-model"
            mock_llm.return_value = (
                "⏱ Время: 1 день\n✅ Рекомендация: БРАТЬ\n📝 OK\n\n📨 Отклик:\nПривет"
            )
            result = evaluate_order("test order")
            assert result is not None
            assert result.recommendation == "БРАТЬ"
            assert result.response == "Привет"


class TestRegenerateResponse:
    @patch("evaluator._call_llm")
    def test_returns_new_response(self, mock_llm: MagicMock) -> None:
        mock_llm.return_value = (
            "⏱ Время: 1 день\n✅ Рекомендация: БРАТЬ\n📝 OK\n\n📨 Отклик:\nНовый отклик"
        )
        result = regenerate_response("order text", "old response")
        assert result == "Новый отклик"

    @patch("evaluator._call_llm")
    def test_returns_none_on_failure(self, mock_llm: MagicMock) -> None:
        mock_llm.return_value = None
        result = regenerate_response("order text", "old response")
        assert result is None
