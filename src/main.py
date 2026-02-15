from concurrent.futures import Future
import datetime
import pathlib
import signal
import time

import notifee

from src.utils.cli_args import parse_args
from src.utils.message_source import iter_messages
from src.utils.diagnostics import DiagnosticsWriter
from src.utils.logging import setup_json_logging


InFlightNotification = tuple[str, Future]
InFlightNotifications = list[InFlightNotification]


def sleep_until_tick(next_tick: float) -> None:
    now = time.monotonic()
    sleep_for = next_tick - now
    if sleep_for > 0:
        time.sleep(sleep_for)

def advance_tick_skip_missed(
    next_tick: float,
    interval_seconds: float,
) -> float:
    next_tick += interval_seconds
    now = time.monotonic()
    if now > next_tick:
        return now + interval_seconds
    return next_tick


def main() -> int:
    args = parse_args()
    url: str = args.url
    interval_seconds: float = args.interval
    messages_source: str = args.messages
    stop_requested = False
    max_queue_wait_seconds = 30.0

    logger = setup_json_logging()

    def _handle_sigint(_signum: int, _frame) -> None:
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, _handle_sigint)

    failures = 0
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = pathlib.Path("runs") / timestamp
    run_dir.mkdir(parents=True, exist_ok=False)
    success_path = run_dir / "success.txt"
    failed_path = run_dir / "failed.txt"
    diagnostics_path = run_dir / "diagnostics.json"

    base_extra = {"run_id": run_dir.name}

    logger.info(
        "run_started",
        extra={
            "extra": {
                **base_extra,
                "url": url,
                "interval_seconds": interval_seconds,
                "messages_source": messages_source,
                "run_dir": str(run_dir),
            }
        },
    )

    in_flight: InFlightNotifications = []

    with (
        success_path.open("w", encoding="utf-8") as success_file,
        failed_path.open("w", encoding="utf-8") as failed_file,
        diagnostics_path.open("w", encoding="utf-8") as diag_file,
        notifee.Notifier(url=url) as notifier,
        DiagnosticsWriter(diag_file) as diagnostics,
    ):
        next_tick = time.monotonic()
        for message in iter_messages(messages_source):
            if stop_requested:
                break

            sleep_until_tick(next_tick)

            enqueue_deadline = time.monotonic() + max_queue_wait_seconds
            future = None
            while future is None and not stop_requested:
                try:
                    future = notifier.notify(message)
                except notifee.QueueFullError as exc:
                    if time.monotonic() >= enqueue_deadline:
                        failures += 1
                        failed_file.write(f"{message}\n")
                        failed_file.flush()
                        diagnostics.write(
                            message,
                            status="failed",
                            stage="enqueue",
                            error=str(exc),
                        )
                        logger.error(
                            "enqueue_failed",
                            extra={
                                "extra": {
                                    **base_extra,
                                    "stage": "enqueue",
                                    "message": message,
                                    "error": str(exc),
                                }
                            },
                        )
                        break
                    logger.warning(
                        "queue_full_retrying",
                        extra={
                            "extra": {
                                **base_extra,
                                "stage": "enqueue",
                                "error": str(exc),
                            }
                        },
                    )
                    time.sleep(min(0.25, interval_seconds))

            if future is not None:
                in_flight.append((message, future))
                diagnostics.write(message, status="enqueued")
                logger.info(
                    "message_enqueued",
                    extra={
                        "extra": {
                            **base_extra,
                            "message": message,
                        }
                    },
                )

            next_tick = advance_tick_skip_missed(next_tick, interval_seconds)

        for message, future_obj in in_flight:
            try:
                future_obj.result()
                success_file.write(f"{message}\n")
                success_file.flush()
                diagnostics.write(message, status="success", stage="http")
                logger.info(
                    "message_sent",
                    extra={
                        "extra": {
                            **base_extra,
                            "stage": "http",
                            "message": message,
                        }
                    },
                )
            except Exception as exc:  # pylint: disable=broad-exception-caught
                failures += 1
                failed_file.write(f"{message}\n")
                failed_file.flush()
                logger.error(
                    "message_failed",
                    extra={
                        "extra": {
                            **base_extra,
                            "stage": "http",
                            "message": message,
                            "error": str(exc),
                        }
                    },
                    exc_info=True,
                )
                diagnostics.write(
                    message,
                    status="failed",
                    stage="http",
                    error=str(exc),
                )

    logger.info(
        "run_finished",
        extra={
            "extra": {
                **base_extra,
                "failures": failures,
            }
        },
    )

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
