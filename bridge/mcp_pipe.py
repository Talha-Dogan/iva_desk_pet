"""
Iva MCP koprusu: xiaozhi.me MCP endpoint'ine baglanir ve yerel arac
sunucusunu (tools.py) bu baglanti uzerinden Iva'ya acar.

Kullanim:
    python mcp_pipe.py tools.py

Endpoint adresi .env dosyasindaki MCP_ENDPOINT degiskeninden okunur.
"""
import asyncio
import logging
import os
import random
import sys

import websockets

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("iva-bridge")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INITIAL_BACKOFF = 1
MAX_BACKOFF = 60


def load_env():
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


async def ws_to_proc(ws, proc):
    async for message in ws:
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        log.debug("<< %s", message[:200])
        proc.stdin.write((message + "\n").encode("utf-8"))
        await proc.stdin.drain()


async def proc_to_ws(ws, proc):
    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        text = line.decode("utf-8").strip()
        if text:
            log.debug(">> %s", text[:200])
            await ws.send(text)


async def proc_stderr_to_terminal(proc):
    while True:
        line = await proc.stderr.readline()
        if not line:
            break
        sys.stderr.write(line.decode("utf-8", errors="replace"))


async def run_once(endpoint, script):
    proc = await asyncio.create_subprocess_exec(
        sys.executable, os.path.join(BASE_DIR, script),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        async with websockets.connect(endpoint) as ws:
            log.info("Baglanti kuruldu! Konsolda 'Connected' gorunmeli. Arac sunucusu: %s", script)
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(ws_to_proc(ws, proc)),
                    asyncio.create_task(proc_to_ws(ws, proc)),
                    asyncio.create_task(proc_stderr_to_terminal(proc)),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
    finally:
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()


async def main():
    load_env()
    endpoint = os.environ.get("MCP_ENDPOINT", "").strip()
    if not endpoint.startswith("wss://"):
        log.error("MCP_ENDPOINT ayarlanmamis!")
        log.error(".env dosyasini ac ve xiaozhi.me konsolundan kopyaladigin")
        log.error("wss://api.xiaozhi.me/mcp/?token=... adresini MCP_ENDPOINT= satirina yapistir.")
        sys.exit(1)

    script = sys.argv[1] if len(sys.argv) > 1 else "tools.py"
    backoff = INITIAL_BACKOFF
    while True:
        try:
            await run_once(endpoint, script)
            backoff = INITIAL_BACKOFF
            log.warning("Baglanti kapandi, yeniden baglaniliyor...")
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            log.warning("Baglanti hatasi: %s", exc)
        delay = backoff + random.uniform(0, 1)
        log.info("%.0f saniye sonra tekrar denenecek...", delay)
        await asyncio.sleep(delay)
        backoff = min(backoff * 2, MAX_BACKOFF)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Kapatildi.")
