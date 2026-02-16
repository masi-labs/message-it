# Program flow

This document describes the high-level runtime flow of the `message-it` CLI.

```mermaid
flowchart TD
  A[Start] --> B[main()]
  B --> C[parse_args()]
  C --> D[_run(url, interval_seconds, messages_source)]
  D --> E[setup_json_logging()]
  E --> F[Install SIGINT handler\n(stop_requested=True)]
  F --> G[_prepare_run_files()\ncreate runs/YYYYmmdd_HHMMSS/]
  G --> H[Open artifacts files\nsuccess.txt / failed.txt / diagnostics.json]
  H --> I[Create Notifier(url, CustomJsonMessage)]
  I --> J[Create DiagnosticsWriter]
  J --> K[Build RunContext]
  K --> L[_enqueue_messages(ctx)]

  L --> M[for message in iter_messages(source)]
  M --> N{stop_requested?}
  N -- yes --> Z[Drain + process in-flight\nthen return failures]
  N -- no --> O{in_flight full\nor every N messages?}
  O -- yes --> P[_process_completed_futures()\nwrite success/failed + diagnostics]
  O -- no --> Q[_sleep_until_tick(next_tick)]
  P --> Q
  Q --> R[Try notifier.notify(message)]
  R --> S{QueueFullError?}
  S -- no --> T[Record enqueued\nin_flight.append(future)]
  S -- yes --> U{Exceeded\nmax_queue_wait_seconds?}
  U -- no --> V[Backoff then retry]
  V --> R
  U -- yes --> W[Record enqueue failure\nwrite failed + diagnostics]
  W --> X[Advance tick\n(skip missed)]
  T --> X
  X --> M

  Z --> Y[Close files/notifier/diagnostics]
  Y --> AA[Return exit code\n0 if failures==0 else 1]
```
