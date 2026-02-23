import asyncio
import json
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [worker] %(message)s",
)

SOCK_DIR = Path("/tmp")


async def worker_main(name: str):
    log = logging.getLogger(name)

    sock = SOCK_DIR / f"{name}.sock"
    try:
        os.unlink(sock)
    except FileNotFoundError:
        pass

    async def handle(reader, writer):
        line = await reader.readline()
        msg = json.loads(line)

        cmd = msg.get("cmd")

        if cmd == "ping":
            log.debug("received ping")
            writer.write(json.dumps({"cmd": "pong", "worker": name}).encode() + b"\n")

        elif cmd == "job":
            payload = msg["payload"]
            log.debug(f"processing job {payload}")

            await asyncio.sleep(5)

            writer.write(
                json.dumps(
                    {"cmd": "result", "worker": name, "status": "done", "input": payload}
                ).encode()
                + b"\n"
            )

        else:
            writer.write(json.dumps({"error": "unknown cmd"}).encode() + b"\n")

        await writer.drain()
        writer.close()

    server = await asyncio.start_unix_server(handle, path=str(sock))
    log.debug(f"{name} ready")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(worker_main(sys.argv[1]))
