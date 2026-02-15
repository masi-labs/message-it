import pathlib
import sys
from collections.abc import Iterator


def iter_messages(source: str) -> Iterator[str]:
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
