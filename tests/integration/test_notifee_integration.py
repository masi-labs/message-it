import time

import requests

from src.main import _run


def _wait_for_health(url: str, timeout_s: float = 15.0) -> None:
    deadline = time.monotonic() + timeout_s
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            r = requests.get(url, timeout=1.0)
            r.raise_for_status()
            return
        except Exception as exc:  # pylint: disable=broad-exception-caught
            last_err = exc
            time.sleep(0.2)
    raise RuntimeError(f"receiver not healthy in time: {last_err}")


def test_notifee_sends_payload_to_receiver(tmp_path) -> None:
    receiver_base = "http://receiver:8000"
    _wait_for_health(f"{receiver_base}/health")

    requests.delete(f"{receiver_base}/events", timeout=2.0)

    messages_path = tmp_path / "messages.txt"
    messages = ["m1", "m2"]
    messages_path.write_text("\n".join(messages) + "\n", encoding="utf-8")

    exit_code = _run(
        url=f"{receiver_base}/notify",
        interval_seconds=1.0,
        messages_source=str(messages_path),
    )

    assert exit_code == 0

    events = requests.get(f"{receiver_base}/events", timeout=2.0).json()
    payloads = [e.get("payload") for e in events]

    assert {"notification": "m1"} in payloads
    assert {"notification": "m2"} in payloads
