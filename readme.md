# Async FastAPI Worker Pool Example

A minimal example showing a small async job system using:

- FastAPI for job submission
- asyncio for scheduling
- subprocess workers
- UNIX domain sockets for IPC
- JSON command protocol
- live worker stdout/stderr streaming
- event-driven SSE streams for job lifecycle
- periodic heartbeat health checks

This project demonstrates patterns used in distributed job runners and workflow engines.

---

## Features

- `/submit` endpoint accepting JSON jobs
- Worker pool managed by the main process
- Automatic assignment to non-busy workers
- Async IPC via `/tmp/<worker>.sock`
- Structured logging (DEBUG level)
- Scheduler emits events for job lifecycle:
  - `"submitted"` → when job is queued
  - `"result"` → when job completes
  - Extendable for `"started"`, `"error"`, `"heartbeat"`, etc.
- SSE streams:
  - `/events` → global stream of all events
  - `/events/{worker}` → per-worker event stream
- Periodic heartbeat tasks for liveness checking

---

## Project Structure
- main.py - FastAPI app, scheduler, worker manager
- worker.py - Worker subprocess implementation

---

## Requirements

Python 3.10+

Install dependencies:

```bash
pip install fastapi uvicorn
```

## Running

### Start the system:

```bash
python main.py
```

### Submit a job:
```bash
curl -X POST localhost:8000/submit \
  -H "content-type: application/json" \
  -d '{"payload": {"task": "hello"}}'
```

You should see:
- workers booting
- heartbeat ping/pong logs
- job execution logs
- worker stdout streamed in real time

## SSE Event Streams
### Global stream
```bash
curl localhost:8000/events
```

Example output:

```
data: {"type":"submitted","payload":{"task":"hello"}}

data: {"type":"result","worker":"bob","result":{"cmd":"result","worker":"bob","status":"done","input":{"task":"hello"}}}
```

### Per-worker stream

```bash
curl localhost:8000/events/alice
```

Only events related to that worker are streamed.

---

## How It Works

1. Main process launches workers as subprocesses
2. Each worker opens a UNIX socket in /tmp
3. Scheduler assigns jobs from a queue
4. Jobs are sent via JSON over the socket
5. Scheduler emits events:
  - when a job is submitted
  - when a job is completed
  - optionally when a job starts or fails
6. SSE endpoints stream events globally or per worker
7. Heartbeat periodically verifies worker health

---

## Extending This

You can easily add:
- job "started" events before sending to worker
- error events for retries or failed jobs
- job IDs / correlation IDs for tracing
- persistent queues (Redis, PostgreSQL)
- worker auto-restart on crash
- priority queues and throttling
- metrics collection / monitoring
- WebSocket interface instead of SSE if needed

## License

This project is released under the MIT-0 License.
You may use it in commercial, corporate, internal, or proprietary software
without attribution.

See the LICENSE file for full terms.
