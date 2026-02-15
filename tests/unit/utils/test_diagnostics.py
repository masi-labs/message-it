import io
import json

from src.utils.diagnostics import DiagnosticsWriter


class TestDiagnosticsWriter:
    def test_finish_before_start_is_noop_and_outputs_empty(self) -> None:
        buf = io.StringIO()
        writer = DiagnosticsWriter(buf)
        writer.finish()
        assert buf.getvalue() == ""

    def test_context_manager_writes_valid_json_array_for_single_record(self) -> None:
        buf = io.StringIO()
        with DiagnosticsWriter(buf) as writer:
            writer.write("hello", status="enqueued")

        raw = buf.getvalue()
        parsed = json.loads(raw)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["message"] == "hello"
        assert parsed[0]["status"] == "enqueued"
        assert "ts" in parsed[0]

    def test_multiple_records_are_comma_separated_and_parseable(self) -> None:
        buf = io.StringIO()
        with DiagnosticsWriter(buf) as writer:
            writer.write("m1", status="enqueued")
            writer.write("m2", status="success", stage="http")

        raw = buf.getvalue()
        parsed = json.loads(raw)
        assert [r["message"] for r in parsed] == ["m1", "m2"]
        assert parsed[1]["stage"] == "http"

    def test_error_and_extra_fields_are_included(self) -> None:
        buf = io.StringIO()
        with DiagnosticsWriter(buf) as writer:
            writer.write(
                "oops",
                status="failed",
                stage="enqueue",
                error="QueueFull",
                extra={"run_id": "r1", "attempt": 3},
            )

        parsed = json.loads(buf.getvalue())
        assert parsed[0]["status"] == "failed"
        assert parsed[0]["stage"] == "enqueue"
        assert parsed[0]["error"] == "QueueFull"
        assert parsed[0]["run_id"] == "r1"
        assert parsed[0]["attempt"] == 3
