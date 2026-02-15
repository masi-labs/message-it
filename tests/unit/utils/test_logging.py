import json
import logging
import sys

from src.utils.logging import JsonFormatter, setup_json_logging


class TestJsonFormatter:
    def test_formats_basic_payload_as_json(self) -> None:
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello %s",
            args=("world",),
            exc_info=None,
        )

        payload = json.loads(formatter.format(record))
        assert payload["level"] == "INFO"
        assert payload["logger"] == "test_logger"
        assert payload["message"] == "hello world"
        assert "ts" in payload

    def test_merges_extra_dict_into_payload(self) -> None:
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.WARNING,
            pathname=__file__,
            lineno=1,
            msg="event",
            args=(),
            exc_info=None,
        )
        record.extra = {"run_id": "r1", "stage": "enqueue"}

        payload = json.loads(formatter.format(record))
        assert payload["run_id"] == "r1"
        assert payload["stage"] == "enqueue"

    def test_includes_exc_info_when_present(self) -> None:
        formatter = JsonFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname=__file__,
                lineno=1,
                msg="failed",
                args=(),
                exc_info=exc_info,
            )

        payload = json.loads(formatter.format(record))
        assert payload["message"] == "failed"
        assert "exc_info" in payload
        assert "ValueError" in payload["exc_info"]


class TestSetupJsonLogging:
    def test_is_idempotent_and_does_not_add_duplicate_handlers(self) -> None:
        logger = logging.getLogger("message_it")
        logger.handlers.clear()

        setup_json_logging()
        first_count = len(logger.handlers)
        setup_json_logging()
        second_count = len(logger.handlers)

        assert first_count == 1
        assert second_count == 1
