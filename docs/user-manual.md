# message-it user manual

This document is for testers of the `message-it` CLI.

`message-it` reads messages (one per line) from a `.txt` file or from `stdin`, and sends one HTTP POST request per message at a fixed interval.

## What you need

You have two ways to run the application:

- Use the prebuilt executable (recommended for testing)
- Run using Python (requires a local Python installation)

You also need a server endpoint that accepts HTTP POST requests.

- If you already have your own server that accepts POST requests, the mock server is not needed.
- If you do not have a server available, you can start the included mock receiver (Docker) described below.

## Payload sent to the server

Each message line is sent as JSON:

```json
{ "notification": "<message>" }
```

## Option A: run using the executable

### 1) Locate the binary

If you received a packaged binary, run it directly (no `python` required).

Example (macOS):

```bash
./message-it --help
```

### 2) Send messages from a file

Your input file must be a `.txt` file with one message per line.

```bash
./message-it ./test_messages.txt --url http://localhost:8008/notify --interval 1s
```

### 3) Send messages from stdin

Omit the `messages` argument (or pass `-`) to read from `stdin`:

```bash
cat ./test_messages.txt | ./message-it --url http://localhost:8008/notify --interval 1s
```

## Option B: run using Python

All commands in this section must be run from the repository folder (project root).

### 1) Create a virtual environment

From the repository root:

```bash
python -m venv venv
source venv/bin/activate
```

### 2) Install dependencies

Install production dependencies:

```bash
pip install -r requirements/prod.txt
```

Note: `requirements/prod.txt` installs the private dependency `notifee` via `git+ssh`. Your machine must have SSH access to GitHub.

### 3) Run

Use the thin wrapper script:

```bash
python ./message-it.py ./test_messages.txt --url http://localhost:8008/notify --interval 1s
```

## Starting the mock receiver (optional)

Use this only if you do not already have a server endpoint.

The mock receiver listens on:

- `http://localhost:8008/notify`

### Start

```bash
make mock-up
```

This starts the receiver and follows its logs.

### Stop

In another terminal:

```bash
make mock-down
```

## Output artifacts

Each run creates a new timestamped folder under `runs/` containing:

- `success.txt` (messages that completed successfully)
- `failed.txt` (messages that failed)
- `diagnostics.json` (per-message records)
