from concurrent.futures import Future
from dataclasses import dataclass
import datetime
import logging
import pathlib
import signal
import time
import types
from typing import Callable, TextIO

import notifee  # type: ignore[import-untyped]

from src.utils.cli_args import parse_args
from src.utils.message_source import iter_messages
from src.utils.diagnostics import DiagnosticsWriter
from src.utils.logging import setup_json_logging


LOGGER = logging.getLogger("message_it")


InFlightNotification = tuple[str, Future[None]]
InFlightNotifications = list[InFlightNotification]


class CustomJsonMessage(notifee.MessageFormatter):  # type: ignore[misc]
    def format_message(self, message: str) -> dict[str, str]:
        return {"notification": message}


@dataclass(frozen=True)
class RunFiles:
    run_dir: pathlib.Path
    success_path: pathlib.Path
    failed_path: pathlib.Path
    diagnostics_path: pathlib.Path


def _prepare_run_files() -> RunFiles:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = pathlib.Path("runs") / timestamp
    run_dir.mkdir(parents=True, exist_ok=False)
    return RunFiles(
        run_dir=run_dir,
        success_path=run_dir / "success.txt",
        failed_path=run_dir / "failed.txt",
        diagnostics_path=run_dir / "diagnostics.json",
    )


@dataclass(frozen=True)
class RunContext:
    notifier: notifee.Notifier
    diagnostics: DiagnosticsWriter
    success_file: TextIO
    failed_file: TextIO
    messages_source: str
    interval_seconds: float
    max_queue_wait_seconds: float
    stop_requested_getter: Callable[[], bool]


def _sleep_until_tick(next_tick: float) -> None:
    now = time.monotonic()
    sleep_for = next_tick - now
    if sleep_for > 0:
        time.sleep(sleep_for)


def _advance_tick_skip_missed(
    next_tick: float,
    interval_seconds: float,
) -> float:
    next_tick += interval_seconds
    now = time.monotonic()
    if now > next_tick:
        return now + interval_seconds
    return next_tick


def _enqueue_messages(ctx: RunContext) -> tuple[InFlightNotifications, int]:
    failures = 0
    in_flight: InFlightNotifications = []
    next_tick = time.monotonic()

    for message in iter_messages(ctx.messages_source):
        if ctx.stop_requested_getter():
            break

        _sleep_until_tick(next_tick)

        enqueue_deadline = time.monotonic() + ctx.max_queue_wait_seconds
        future: Future[None] | None = None
        while future is None and not ctx.stop_requested_getter():
            try:
                future = ctx.notifier.notify(message)
            except notifee.QueueFullError as exc:
                if time.monotonic() >= enqueue_deadline:
                    failures += 1
                    ctx.failed_file.write(f"{message}\n")
                    ctx.failed_file.flush()
                    ctx.diagnostics.write(
                        message,
                        status="failed",
                        stage="enqueue",
                        error=str(exc),
                    )
                    LOGGER.error(
                        "enqueue_failed",
                        extra={
                            "extra": {
                                "stage": "enqueue",
                                "message": message,
                                "error": str(exc),
                            }
                        },
                    )
                    break

                LOGGER.warning(
                    "queue_full_retrying",
                    extra={
                        "extra": {
                            "stage": "enqueue",
                            "error": str(exc),
                        }
                    },
                )
                time.sleep(min(0.25, ctx.interval_seconds))

        if future is not None:
            in_flight.append((message, future))
            ctx.diagnostics.write(message, status="enqueued")
            LOGGER.info(
                "message_enqueued",
                extra={"extra": {"message": message}},
            )

        next_tick = _advance_tick_skip_missed(next_tick, ctx.interval_seconds)

    return in_flight, failures


def _drain_in_flight(
    *,
    ctx: RunContext,
    in_flight: InFlightNotifications,
) -> int:
    failures = 0
    for message, future_obj in in_flight:
        try:
            future_obj.result()
            ctx.success_file.write(f"{message}\n")
            ctx.success_file.flush()
            ctx.diagnostics.write(message, status="success", stage="http")
            LOGGER.info(
                "message_sent",
                extra={
                    "extra": {
                        "stage": "http",
                        "message": message,
                    }
                },
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            failures += 1
            ctx.failed_file.write(f"{message}\n")
            ctx.failed_file.flush()
            LOGGER.error(
                "message_failed",
                extra={
                    "extra": {
                        "stage": "http",
                        "message": message,
                        "error": str(exc),
                    }
                },
                exc_info=True,
            )
            ctx.diagnostics.write(
                message,
                status="failed",
                stage="http",
                error=str(exc),
            )

    return failures


def _run(*, url: str, interval_seconds: float, messages_source: str) -> int:
    stop_requested = False
    max_queue_wait_seconds = 30.0

    setup_json_logging()

    def _handle_sigint(_signum: int, _frame: types.FrameType | None) -> None:
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, _handle_sigint)

    run_files = _prepare_run_files()

    LOGGER.info(
        "run_started",
        extra={
            "extra": {
                "url": url,
                "interval_seconds": interval_seconds,
                "messages_source": messages_source,
                "run_dir": str(run_files.run_dir),
            }
        },
    )

    with (
        run_files.success_path.open("w", encoding="utf-8") as success_file,
        run_files.failed_path.open("w", encoding="utf-8") as failed_file,
        run_files.diagnostics_path.open("w", encoding="utf-8") as diag_file,
        notifee.Notifier(url=url, formatter=CustomJsonMessage()) as notifier,
        DiagnosticsWriter(diag_file) as diagnostics,
    ):
        ctx = RunContext(
            notifier=notifier,
            diagnostics=diagnostics,
            success_file=success_file,
            failed_file=failed_file,
            messages_source=messages_source,
            interval_seconds=interval_seconds,
            max_queue_wait_seconds=max_queue_wait_seconds,
            stop_requested_getter=lambda: stop_requested,
        )
        in_flight, failures = _enqueue_messages(ctx)
        failures += _drain_in_flight(ctx=ctx, in_flight=in_flight)

    LOGGER.info(
        "run_finished",
        extra={
            "extra": {
                "failures": failures,
            }
        },
    )

    return 0 if failures == 0 else 1


def main() -> int:
    args = parse_args()
    return _run(
        url=args.url,
        interval_seconds=args.interval,
        messages_source=args.messages,
    )


if __name__ == "__main__":
    raise SystemExit(main())
