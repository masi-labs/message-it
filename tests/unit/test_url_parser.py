import argparse

import pytest

from src.parsers.url import URLParser


class TestURLParser:
    
    @pytest.mark.parametrize("url", [
        "http://localhost:8080/notify",
        "https://example.com/webhook",
        "http://127.0.0.1:3000",
        "https://api.example.com/v1/notify?key=abc",
        "http://x",
        "https://x",
    ])
    def test_accepts_valid_url(self, url: str) -> None:
        assert URLParser.parse(url) == url

    @pytest.mark.parametrize("url", [
        "ftp://example.com",       # unsupported scheme
        "example.com",             # no scheme
        "",                        # empty string
        "http",                    # just protocol name
        "http:example.com",        # missing slashes
        "http:/example.com",       # single slash
        "ws://example.com",        # websocket scheme
        "not-a-url-at-all",        # random text
    ])
    def test_rejects_invalid_url(self, url: str) -> None:
        with pytest.raises(argparse.ArgumentTypeError, match="invalid URL"):
            URLParser.parse(url)
