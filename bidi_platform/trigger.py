"""Unix-socket trigger for Wayland / desktop shortcut integration."""

from __future__ import annotations

import os
import socket
import threading
from pathlib import Path
from typing import Callable


def socket_path() -> Path:
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime:
        base = Path(runtime) / "bidi-popup"
    else:
        base = Path.home() / ".local" / "share" / "bidi-popup"
    base.mkdir(parents=True, exist_ok=True)
    return base / "trigger.sock"


class TriggerServer:
    """Background UNIX socket — desktop shortcuts call the trigger client."""

    def __init__(self, on_trigger: Callable[[], None]) -> None:
        self._on_trigger = on_trigger
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._serve, name="trigger-server", daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        path = socket_path()
        if path.exists():
            path.unlink()

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(path))
            server.listen(5)
            server.settimeout(1.0)

            while not self._stop.is_set():
                try:
                    conn, _addr = server.accept()
                except TimeoutError:
                    continue
                except OSError:
                    break

                with conn:
                    try:
                        data = conn.recv(64).decode("utf-8", errors="ignore").strip().lower()
                    except OSError:
                        continue
                    if data in ("trigger", "show", "open"):
                        self._on_trigger()

    def stop(self) -> None:
        self._stop.set()
        path = socket_path()
        if path.exists():
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                    client.connect(str(path))
                    client.sendall(b"stop\n")
            except OSError:
                pass


def send_trigger() -> bool:
    """Ask a running listener to show the popup. Used by desktop shortcuts."""
    path = socket_path()
    if not path.exists():
        print(
            "bidi-popup: listener is not running — start it first with ./start.sh",
            file=__import__("sys").stderr,
        )
        return False

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(2.0)
            client.connect(str(path))
            client.sendall(b"trigger\n")
    except OSError as exc:
        print(f"bidi-popup: could not send trigger ({exc})", file=__import__("sys").stderr)
        return False
    return True
