import argparse

from .base import Parser

class URLParser(Parser):
    @staticmethod
    def parse(value: str) -> str:
        """Validate that the URL starts with http:// or https://."""
        if not value.startswith(("http://", "https://")):
            raise argparse.ArgumentTypeError(
                f"invalid URL '{value}': must start with http:// or https://"
            )
        return value
