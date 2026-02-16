
# message-it

Send lines of text as HTTP notifications to a configurable server endpoint at a fixed interval.

This project is intentionally small:

- **Input**: a `.txt` file (one message per line) or `stdin`
- **Output**: one HTTP request per message (JSON body)
- **Artifacts**: a timestamped folder under `runs/` with `success.txt`, `failed.txt`, and `diagnostics.json`

## Requirements

- Python **3.14** (see `Makefile` / Docker images)
- Access to the private dependency `notifee` (installed from GitHub over SSH)

## Installation

Create and activate a virtual environment, then install dependencies:

```bash
pip install -r requirements/prod.txt
```

For development (tests, lint, mypy):

```bash
pip install -r requirements/dev.txt
```

Note: `requirements/prod.txt` installs `notifee` via `git+ssh`. Your machine (or CI) must have SSH access to GitHub.

## CLI usage

The entrypoint is `src/main.py`.

Program flow diagram:

- `docs/program-flow.md`

### Send messages from a file

`messages.txt` must be a `.txt` file containing **one message per line**.

```bash
python -m src.main ./messages.txt --url http://localhost:8000/notify --interval 5s
```

### Send messages from stdin

If you omit the `messages` argument (or pass `-`), messages are read from `stdin`:

```bash
cat ./messages.txt | python -m src.main --url http://localhost:8000/notify --interval 2s
```

### Arguments

- **`messages`** (positional, optional)
  - `-` (default) reads from `stdin`
  - otherwise a path to a `.txt` file
- **`--url`** (required)
  - must start with `http://` or `https://`
- **`--interval` / `-i`** (optional, default: `5s`)
  - supported formats: `<number>s` or `<number>m` (seconds/minutes)

## What gets sent to the server

For each input message string `message`, the application sends an HTTP notification using the `notifee` library.

### Payload format (JSON)

The current request body is:

```json
{ "notification": "<message>" }
```

This is defined in:

- `src/main.py` → `class CustomJsonMessage(notifee.MessageFormatter)` → `format_message()`

```python
def format_message(self, message: str) -> dict[str, str]:
    return {"notification": message}
```

### How to change the payload format

Edit `src/main.py` and change `CustomJsonMessage.format_message()`.

Examples:

- **Change key name**
  - from `{"notification": message}`
  - to `{"text": message}`
- **Add more fields**
  - e.g. timestamps, message ids, metadata

After changing the payload shape, also update the integration test expectation:

- `tests/integration/test_notifee_integration.py`

It currently asserts that the receiver sees `{"notification": "m1"}` / `{"notification": "m2"}`.

## Run artifacts (`runs/`)

Each execution creates a new directory under `runs/` named `YYYYmmdd_HHMMSS/` containing:

- **`success.txt`**
  - each line is a message that completed successfully (HTTP stage)
- **`failed.txt`**
  - each line is a message that failed either:
    - **enqueue** (queue full for too long)
    - **http** (request failed)
- **`diagnostics.json`**
  - a JSON array of per-message records, including timestamps, status, optional stage, and error details

## Logging

The app logs to stdout as JSON lines via:

- `src/utils/logging.py` (`setup_json_logging()`)

## Development

### Running tests / lint / typecheck (Docker)

The `Makefile` runs tests and tooling inside a Docker “runner” image.

Common targets:

```bash
make runner
make test-unit
make test-integration
make lint
make typecheck
```

Integration tests use `docker-compose.itest.yml` which starts a mock receiver on port `8008`.

## Building a macOS executable

This project can be packaged into a standalone macOS executable using PyInstaller.

Note: at the time of writing, PyInstaller supports Python `<3.14`, so if you're running the project with Python 3.14 you will typically need a separate packaging environment using Python 3.13.

1. Install dev dependencies (includes PyInstaller):

```bash
pip install -r requirements/dev.txt
```

2. Build:

```bash
make exe-macos-arm64
```

The resulting binary will be at:

- `dist/message-it`

If you have multiple Python installations, you can choose which interpreter is used for packaging:

```bash
make exe-macos-arm64 PACKAGER_PYTHON=python3.13
```

To build an Intel (x86_64) binary, you need an x86_64 Python available on your machine:

```bash
make exe-macos-x86_64 PACKAGER_PYTHON=python3.13
```

### Manual end-to-end test (from your console)

After installing dependencies, you can manually run an end-to-end test locally using the same mock receiver used by integration tests.

Terminal 1: start the receiver

```bash
make itest-up
```

Terminal 1: watch receiver logs

```bash
docker compose -f docker-compose.itest.yml logs -f receiver
```

Terminal 2: run `message-it` against the receiver with an input file

```bash
python -m src.main ./messages.txt --url http://localhost:8008/notify --interval 1s
```

When you’re done, stop and remove the integration-test containers/volumes:

```bash
make itest-down
```

### Mock receiver

The mock receiver is a small FastAPI service under `tests/mock_receiver/`.

Endpoints:

- `GET /health`
- `POST /notify` (records received payloads)
- `GET /events` (returns recorded events)
- `DELETE /events` (clears events)

## Where to change behavior (quick map)

- **CLI args**: `src/utils/cli_args.py`
- **Message input (stdin / file)**: `src/utils/message_source.py`
- **Interval parsing**: `src/parsers/time_interval.py`
- **URL validation**: `src/parsers/url.py`
- **Payload shape**: `src/main.py` → `CustomJsonMessage.format_message()`
