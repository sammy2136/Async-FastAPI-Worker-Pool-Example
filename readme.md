# Async FastAPI Worker Pool Example

A minimal example showing how to build a small async job system using:

- FastAPI for job submission
- asyncio for scheduling
- subprocess workers
- UNIX domain sockets for IPC
- JSON command protocol
- live worker stdout/stderr streaming
- heartbeat health checks

This project is intentionally simple and educational, but demonstrates patterns used in real task runners.

---

## Features

- `/submit` endpoint accepting JSON jobs
- Worker pool managed by the main process
- Automatic assignment to non-busy workers
- Async IPC via `/tmp/<worker>.sock`
- Structured logging with DEBUG output
- Periodic scheduler tasks (heartbeat included)
- Extensible command protocol (`ping`, `job`, etc.)

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


## How It Works

1. Main process launches workers as subprocesses
2. Each worker opens a UNIX socket in /tmp
3. Scheduler assigns jobs from a queue
4. Jobs are sent via JSON over the socket
5. Worker responds with JSON results
6. Heartbeat periodically verifies worker health

## Extending This

Common next steps for production use:
- worker restart on crash
- job persistence (Redis/Postgres/etc.)
- job timeouts and cancellation
- priority queues
- metrics & tracing
- container orchestration support

## License

This project is released under the MIT-0 License.
You may use it in commercial, corporate, internal, or proprietary software
without attribution.

See the LICENSE file for full terms.
