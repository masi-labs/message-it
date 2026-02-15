import argparse
import pathlib
import sys

# import requests
# import notifee

from parsers import TimeIntervalParser, URLParser


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


def iter_messages(source: str):
    if source == "-":
        for line in sys.stdin:
            message = line.rstrip("\n")
            if message:
                yield message
        return

    path = pathlib.Path(source)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"messages file not found: {source}")
    if path.suffix.lower() != ".txt":
        raise ValueError(f"messages file must be a .txt file: {source}")

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            message = line.rstrip("\n")
            if message:
                yield message


def main() -> None:
    args = parse_args()
    url: str = args.url
    interval_seconds: float = args.interval
    messages_source: str = args.messages

    print(f"URL: {url}")
    print(f"Interval: {interval_seconds}s")

    for message in iter_messages(messages_source):
        print(message)


if __name__ == "__main__":
    main()
