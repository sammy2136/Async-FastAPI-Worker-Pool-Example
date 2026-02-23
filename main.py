import asyncio
import json
import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# ---------- logging ----------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
log = logging.getLogger("main")

# ---------- config ----------
NAMES = ["alice", "bob", "carol", "dave", "eve"]
SOCK_DIR = Path("/tmp")

app = FastAPI()


# ---------------- Worker helper ----------------

class Worker:
    def __init__(self, name: str):
        self.name = name
        self.sock_path = SOCK_DIR / f"{name}.sock"
        self.proc: asyncio.subprocess.Process | None = None
        self.busy = False
        self.log = logging.getLogger(f"worker.{name}")

    async def start(self):
        try:
            os.unlink(self.sock_path)
        except FileNotFoundError:
            pass

        self.proc = await asyncio.create_subprocess_exec(
            sys.executable, "worker.py", self.name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        asyncio.create_task(self._stream(self.proc.stdout, "OUT"))
        asyncio.create_task(self._stream(self.proc.stderr, "ERR"))

        while not self.sock_path.exists():
            await asyncio.sleep(0.001)

        self.log.debug("worker socket ready")

    async def _stream(self, stream, label):
        while True:
            line = await stream.readline()
            if not line:
                break
            self.log.debug(f"{label}: {line.decode().rstrip()}")

    async def _send_cmd(self, payload: dict):
        reader, writer = await asyncio.open_unix_connection(str(self.sock_path))
        writer.write(json.dumps(payload).encode() + b"\n")
        await writer.drain()

        line = await reader.readline()
        writer.close()
        await writer.wait_closed()

        return json.loads(line)

    async def send_job(self, payload: dict):
        self.busy = True
        self.log.debug(f"assigning job {payload}")
        try:
            result = await self._send_cmd({"cmd": "job", "payload": payload})
            return result
        finally:
            self.busy = False

    async def ping(self):
        try:
            resp = await self._send_cmd({"cmd": "ping"})
            return resp
        except Exception as e:
            self.log.error(f"ping failed: {e}")
            return None


# ---------------- Scheduler ----------------

class Scheduler:
    def __init__(self, workers: list[Worker]):
        self.workers = workers
        self.queue: asyncio.Queue = asyncio.Queue()
        self.log = logging.getLogger("scheduler")

    async def start(self):
        asyncio.create_task(self._run())

    async def submit(self, job: dict):
        await self.queue.put(job)
        self.log.debug(f"job queued {job}")

    async def _run(self):
        while True:
            job = await self.queue.get()
            worker = await self._wait_for_free_worker()
            asyncio.create_task(self._handle_job(worker, job))

    async def _wait_for_free_worker(self) -> Worker:
        while True:
            free = next((w for w in self.workers if not w.busy), None)
            if free:
                return free
            await asyncio.sleep(0.05)

    async def _handle_job(self, worker: Worker, job: dict):
        result = await worker.send_job(job)
        self.log.debug(f"job result {result}")

    # -------- periodic --------

    def add_periodic(self, coro, interval: float):
        async def loop():
            while True:
                await asyncio.sleep(interval)
                try:
                    await coro()
                except Exception:
                    self.log.exception("periodic task failed")

        asyncio.create_task(loop())


# ---------------- API ----------------

class Job(BaseModel):
    payload: dict


workers: list[Worker] = []
scheduler: Scheduler | None = None


@app.post("/submit")
async def submit(job: Job):
    await scheduler.submit(job.payload)
    return {"queued": True}


# ---------------- Startup ----------------

@app.on_event("startup")
async def startup():
    global scheduler

    # start workers
    for n in NAMES:
        w = Worker(n)
        await w.start()
        workers.append(w)

    scheduler = Scheduler(workers)
    await scheduler.start()

    # -------- heartbeat --------
    async def heartbeat():
        log.debug("heartbeat start")
        for w in workers:
            resp = await w.ping()
            log.debug(f"heartbeat {w.name}: {resp}")

    scheduler.add_periodic(heartbeat, 5)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
