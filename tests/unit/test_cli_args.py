import pytest

from src.utils.cli_args import parse_args


class TestCliArgs:
    def test_requires_url(self) -> None:
        with pytest.raises(SystemExit):
            parse_args([])

    def test_default_messages_is_stdin_dash(self) -> None:
        args = parse_args(["--url", "http://localhost:8080/notify"])
        assert args.messages == "-"

    def test_messages_positional_is_parsed(self) -> None:
        args = parse_args(["messages.txt", "--url", "http://localhost:8080/notify"])
        assert args.messages == "messages.txt"

    def test_default_interval_is_5_seconds(self) -> None:
        args = parse_args(["--url", "http://localhost:8080/notify"])
        assert args.interval == 5.0

    def test_interval_minutes_is_converted(self) -> None:
        args = parse_args(["--url", "http://localhost:8080/notify", "--interval", "2m"])
        assert args.interval == 120.0

    def test_invalid_url_raises_systemexit(self) -> None:
        with pytest.raises(SystemExit):
            parse_args(["--url", "ftp://example.com"])

    def test_invalid_interval_raises_systemexit(self) -> None:
        with pytest.raises(SystemExit):
            parse_args(["--url", "http://localhost:8080/notify", "--interval", "1h"])
