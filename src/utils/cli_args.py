import argparse

from src.parsers import TimeIntervalParser, URLParser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="message-it",
        description=(
            "Send stdin lines as HTTP notifications at a fixed interval."
        ),
    )
    parser.add_argument(
        "messages",
        nargs="?",
        default="-",
        help=(
            "Path to a .txt file with one message per line."
            " Use '-' or omit to read from stdin."
        ),
    )
    parser.add_argument(
        "--url",
        type=URLParser.parse,
        required=True,
        help="URL to which notifications are sent",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=TimeIntervalParser.parse,
        default="5s",
        help="Notification interval (e.g. 5s, 2m). Default: 5s",
    )
    return parser.parse_args(argv)
