import pytest

from src.parsers.base import Parser


class TestParserABC:
    """Test that Parser enforces the abstract contract."""

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            Parser()  # type: ignore[abstract]

    def test_subclass_must_implement_parse(self) -> None:
        class IncompleteParser(Parser):
            pass

        with pytest.raises(TypeError):
            IncompleteParser()  # type: ignore[abstract]

    def test_subclass_with_parse_can_be_called(self) -> None:
        class ConcreteParser(Parser):
            @staticmethod
            def parse(line: str) -> str:
                return line

        assert ConcreteParser.parse("hello") == "hello"
