import datetime
import json
from typing import Any, TextIO


class DiagnosticsWriter:
    def __init__(self, file: TextIO) -> None:
        self._file = file
        self._first = True
        self._started = False

    def start(self) -> None:
        self._file.write("[\n")
        self._file.flush()
        self._started = True

    def write(
        self,
        message: str,
        *,
        status: str,
        stage: str | None = None,
        error: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        record: dict[str, Any] = {
            "ts": datetime.datetime.now().isoformat(),
            "status": status,
            "message": message,
        }
        if stage is not None:
            record["stage"] = stage
        if error is not None:
            record["error"] = error
        if extra:
            record.update(extra)

        if self._first:
            self._first = False
        else:
            self._file.write(",\n")

        json.dump(record, self._file, ensure_ascii=False)
        self._file.flush()

    def finish(self) -> None:
        if not self._started:
            return
        self._file.write("\n]\n")
        self._file.flush()
        self._started = False

    def __enter__(self) -> "DiagnosticsWriter":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb,
    ) -> None:
        self.finish()
