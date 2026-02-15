from __future__ import annotations

import contextlib
import datetime as _datetime
import functools
import os
from argparse import Namespace
from concurrent.futures import Future
from typing import Iterator
from unittest.mock import MagicMock, patch

import src.main as main_mod


class _FixedDateTime(_datetime.datetime):
    @classmethod
    def now(cls, tz=None):  # type: ignore[override]
        return cls(2020, 1, 1, 0, 0, 0, tzinfo=tz)


class _FakeDiagnostics:
    def __init__(self, _file) -> None:
        self.records: list[dict[str, object]] = []

    def write(
        self,
        message: str,
        *,
        status: str,
        stage: str | None = None,
        error: str | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        record: dict[str, object] = {"message": message, "status": status}
        if stage is not None:
            record["stage"] = stage
        if error is not None:
            record["error"] = error
        if extra:
            record.update(extra)
        self.records.append(record)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


@contextlib.contextmanager
def _cwd(path) -> Iterator[None]:
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


class _FakeNotifier:
    def __init__(
        self,
        *,
        url: str,
        futures: list[Future],
        **_kwargs,
    ) -> None:
        self._url = url
        self._futures = futures
        self._i = 0

    def notify(self, _message: str) -> Future:
        fut = self._futures[self._i]
        self._i += 1
        return fut

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def _passthrough_next_tick(next_tick: float, _interval: float) -> float:
    return next_tick


def test_advance_tick_skip_missed_does_not_skip_when_on_time() -> None:
    with patch.object(main_mod.time, "monotonic", return_value=6.0):
        assert main_mod._advance_tick_skip_missed(5.0, 2.0) == 7.0


def test_advance_tick_skip_missed_skips_when_missed() -> None:
    with patch.object(main_mod.time, "monotonic", return_value=10.0):
        assert main_mod._advance_tick_skip_missed(5.0, 2.0) == 12.0


def test_main_success_path_writes_success_and_returns_0(
    tmp_path,
) -> None:
    def _iter_messages(_src: str) -> Iterator[str]:
        yield "m1"
        yield "m2"

    fut1: Future = Future()
    fut1.set_result(None)
    fut2: Future = Future()
    fut2.set_result(None)

    logger = MagicMock()

    with (
        _cwd(tmp_path),
        patch.object(main_mod, "parse_args", return_value=Namespace(url="http://example", interval=0.0, messages="-")),
        patch.object(main_mod, "iter_messages", _iter_messages),
        patch.object(main_mod, "LOGGER", logger),
        patch.object(
            main_mod.notifee,
            "Notifier",
            side_effect=functools.partial(_FakeNotifier, futures=[fut1, fut2]),
        ),
        patch.object(main_mod, "DiagnosticsWriter", side_effect=_FakeDiagnostics),
        patch.object(main_mod, "setup_json_logging"),
        patch.object(main_mod.signal, "signal"),
        patch.object(main_mod.time, "sleep"),
        patch.object(main_mod, "_sleep_until_tick"),
        patch.object(main_mod, "_advance_tick_skip_missed", side_effect=_passthrough_next_tick),
        patch.object(main_mod.datetime, "datetime", _FixedDateTime),
    ):
        assert main_mod.main() == 0

    run_dir = tmp_path / "runs" / "20200101_000000"
    assert (run_dir / "success.txt").read_text(encoding="utf-8").splitlines() == ["m1", "m2"]
    assert (run_dir / "failed.txt").read_text(encoding="utf-8") == ""


def test_main_failure_path_writes_failed_and_returns_1(
    tmp_path,
) -> None:
    def _iter_messages(_src: str) -> Iterator[str]:
        yield "m1"

    fut: Future = Future()
    fut.set_exception(RuntimeError("boom"))

    logger = MagicMock()

    with (
        _cwd(tmp_path),
        patch.object(main_mod, "parse_args", return_value=Namespace(url="http://example", interval=0.0, messages="-")),
        patch.object(main_mod, "iter_messages", _iter_messages),
        patch.object(main_mod, "LOGGER", logger),
        patch.object(
            main_mod.notifee,
            "Notifier",
            side_effect=functools.partial(_FakeNotifier, futures=[fut]),
        ),
        patch.object(main_mod, "DiagnosticsWriter", side_effect=_FakeDiagnostics),
        patch.object(main_mod, "setup_json_logging"),
        patch.object(main_mod.signal, "signal"),
        patch.object(main_mod.time, "sleep"),
        patch.object(main_mod, "_sleep_until_tick"),
        patch.object(main_mod, "_advance_tick_skip_missed", side_effect=_passthrough_next_tick),
        patch.object(main_mod.datetime, "datetime", _FixedDateTime),
    ):
        assert main_mod.main() == 1

    run_dir = tmp_path / "runs" / "20200101_000000"
    assert (run_dir / "success.txt").read_text(encoding="utf-8") == ""
    assert (run_dir / "failed.txt").read_text(encoding="utf-8").splitlines() == ["m1"]
