import io

import pytest

from src.utils.message_source import iter_messages


class TestIterMessages:
    def test_reads_from_stdin_dash(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.stdin", io.StringIO("hello\n\nworld\n"))
        assert list(iter_messages("-")) == ["hello", "world"]

    def test_reads_from_file_streaming(self, tmp_path) -> None:
        p = tmp_path / "messages.txt"
        p.write_text("a\n\nB\n", encoding="utf-8")
        assert list(iter_messages(str(p))) == ["a", "B"]

    def test_missing_file_raises(self, tmp_path) -> None:
        p = tmp_path / "missing.txt"
        with pytest.raises(FileNotFoundError):
            list(iter_messages(str(p)))

    def test_non_txt_extension_raises(self, tmp_path) -> None:
        p = tmp_path / "messages.md"
        p.write_text("hello\n", encoding="utf-8")
        with pytest.raises(ValueError):
            list(iter_messages(str(p)))
