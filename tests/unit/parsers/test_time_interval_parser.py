import argparse

import pytest

from src.parsers.time_interval import TimeIntervalParser


class TestTimeIntervalParser:
    
    @pytest.mark.parametrize("value, expected", [
        ("1s", 1.0),
        ("5s", 5.0),
        ("0.1s", 0.1),
        ("1.5s", 1.5),
        ("3600s", 3600.0),
        ("1m", 60.0),
        ("2m", 120.0),
        ("1.5m", 90.0),
        ("60m", 3600.0),
    ])
    def test_parses_valid_interval(self, value: str, expected: float) -> None:
        result = TimeIntervalParser.parse(value)
        assert result == expected
        assert isinstance(result, float)

    @pytest.mark.parametrize("value", [
        "10",       # no unit
        "",         # empty string
        "s",        # unit only (seconds)
        "m",        # unit only (minutes)
        "1h",       # unsupported unit (hours)
        "1d",       # unsupported unit (days)
        "-5s",      # negative value
        "5 s",      # spaces in value
        "5S",       # uppercase unit
        "fast",     # random text
        "s5",       # unit before number
    ])
    def test_rejects_invalid_format(self, value: str) -> None:
        with pytest.raises(argparse.ArgumentTypeError, match="invalid interval"):
            TimeIntervalParser.parse(value)

    @pytest.mark.parametrize("value", ["0s", "0m"])
    def test_rejects_zero_interval(self, value: str) -> None:
        with pytest.raises(argparse.ArgumentTypeError, match="greater than 0"):
            TimeIntervalParser.parse(value)
