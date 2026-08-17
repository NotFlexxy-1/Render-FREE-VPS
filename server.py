import asyncio
import fcntl
import json
import os
import pty
import select
import shutil
import signal
import struct
import termios
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
CONSOLE_TOKEN = os.environ.get("CONSOLE_TOKEN", "")

app = FastAPI(title="HyperVM Render Console")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def safe_token(candidate: str) -> bool:
    return bool(CONSOLE_TOKEN) and candidate == CONSOLE_TOKEN


def set_winsize(fd: int, rows: int, cols: int) -> None:
    rows = max(1, min(int(rows), 200))
    cols = max(1, min(int(cols), 400))
    packed = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, packed)


def child_shell() -> None:
    os.environ.setdefault("TERM", "xterm-256color")
    os.environ.setdefault("LANG", "C.UTF-8")
    os.environ["PS1"] = "\\[\\e[1;32m\\]root@hypervm\\[\\e[0m\\]:\\w# "
    os.environ["HOME"] = "/root"
    os.chdir("/root")
    os.execv("/bin/bash", ["/bin/bash", "--login"])


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def status() -> JSONResponse:
    return JSONResponse({
        "online": True,
        "debian": Path("/etc/debian_version").read_text().strip() if Path("/etc/debian_version").exists() else "unknown",
        "hostname": os.uname().nodename,
        "shell": "/bin/bash",
        "systemctl": shutil.which("systemctl") is not None,
    })


@app.websocket("/ws/terminal")
async def terminal(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        auth = await asyncio.wait_for(websocket.receive_text(), timeout=10)
    except Exception:
        await websocket.close(code=1008, reason="Authentication timeout")
        return

    try:
        auth_data = json.loads(auth)
    except json.JSONDecodeError:
        await websocket.close(code=1008, reason="Invalid authentication payload")
        return

    if not safe_token(str(auth_data.get("token", ""))):
        await websocket.close(code=1008, reason="Invalid console token")
        return

    rows = int(auth_data.get("rows", 30) or 30)
    cols = int(auth_data.get("cols", 120) or 120)

    pid, fd = pty.fork()
    if pid == 0:
        child_shell()
        return

    try:
        set_winsize(fd, rows, cols)

        async def browser_to_pty() -> None:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                raw = message.get("text")
                if raw is None:
                    continue
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = {"type": "input", "data": raw}

                kind = data.get("type")
                if kind == "input":
                    payload = str(data.get("data", "")).encode("utf-8", errors="ignore")
                    if payload:
                        os.write(fd, payload)
                elif kind == "resize":
                    try:
                        set_winsize(fd, int(data.get("rows", rows)), int(data.get("cols", cols)))
                    except (TypeError, ValueError, OSError):
                        pass

        async def pty_to_browser() -> None:
            loop = asyncio.get_running_loop()
            while True:
                try:
                    ready, _, _ = await loop.run_in_executor(None, select.select, [fd], [], [], 0.5)
                    if not ready:
                        try:
                            waited, _ = os.waitpid(pid, os.WNOHANG)
                        except ChildProcessError:
                            waited = pid
                        if waited == pid:
                            break
                        continue
                    data = os.read(fd, 65536)
                    if not data:
                        break
                    await websocket.send_text(json.dumps({"type": "output", "data": data.decode("utf-8", errors="replace")}))
                except OSError:
                    break

        await websocket.send_text(json.dumps({
            "type": "ready",
            "message": "Authenticated. Connected to Debian 13 PTY.\r\n",
        }))

        sender = asyncio.create_task(browser_to_pty())
        receiver = asyncio.create_task(pty_to_browser())
        done, pending = await asyncio.wait({sender, receiver}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        for task in done:
            try:
                task.result()
            except (WebSocketDisconnect, asyncio.CancelledError):
                pass
            except Exception:
                pass

    finally:
        try:
            os.kill(pid, signal.SIGHUP)
        except OSError:
            pass
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            pass
        try:
            await websocket.close()
        except Exception:
            pass
