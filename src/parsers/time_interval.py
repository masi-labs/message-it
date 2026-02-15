import argparse
import re

from .base import Parser

INTERVAL_PATTERN = re.compile(r"^(\d+)(s|m)$")

class TimeIntervalParser(Parser):
    @staticmethod
    def parse(value: str) -> float:
        """Parse an interval string like '5s' or '2m' into seconds."""
        match = INTERVAL_PATTERN.match(value)
        if not match:
            raise argparse.ArgumentTypeError(
                f"invalid interval '{value}': must be a number followed by 's'"
                " (seconds) or 'm' (minutes), e.g. 5s, 2m"
            )
        amount = int(match.group(1))
        unit = match.group(2)
        if amount <= 0:
            raise argparse.ArgumentTypeError("interval must be greater than 0")
        return float(amount * 60) if unit == "m" else float(amount)
