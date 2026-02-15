import logging
import os
from collections import deque
from typing import Any

from fastapi import FastAPI, Request, Response

LOGGER = logging.getLogger("mock_receiver")

MAX_EVENTS = int(os.environ.get("MOCK_RECEIVER_MAX_EVENTS", "200"))

app = FastAPI()

_EVENTS: deque[dict[str, Any]] = deque(maxlen=MAX_EVENTS)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/notify")
async def notify(request: Request) -> Response:
    try:
        payload = await request.json()
    except Exception:  # pylint: disable=broad-exception-caught
        payload = {"raw": (await request.body()).decode("utf-8", errors="replace")}

    event = {
        "method": request.method,
        "path": str(request.url.path),
        "headers": {k.lower(): v for k, v in request.headers.items()},
        "payload": payload,
    }
    _EVENTS.append(event)

    LOGGER.info("received", extra={"extra": event})
    return Response(status_code=200)


@app.get("/events")
def events() -> list[dict[str, Any]]:
    return list(_EVENTS)


@app.delete("/events")
def clear_events() -> dict[str, int]:
    _EVENTS.clear()
    return {"cleared": 1}
