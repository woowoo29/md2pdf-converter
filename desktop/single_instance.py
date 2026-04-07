import json
import os
import socket
import threading
from pathlib import Path
from typing import Callable

from app import runtime_paths


class SingleInstanceController:
    def __init__(self, socket_path: str | Path | None = None):
        self.socket_path = Path(socket_path or runtime_paths.control_socket_path())
        self._listener: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._handler: Callable[[dict[str, object]], None] | None = None

    def notify_existing_instance(self, open_paths: list[Path] | None = None, timeout: float = 0.4) -> bool:
        payload = {
            "action": "activate",
            "open_paths": [str(Path(path).expanduser()) for path in (open_paths or [])],
        }

        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(timeout)
                client.connect(str(self.socket_path))
                client.sendall(json.dumps(payload).encode("utf-8"))
                return True
        except OSError:
            return False

    def start(self, handler: Callable[[dict[str, object]], None]) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        self._remove_stale_socket()

        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(self.socket_path))
        listener.listen()
        listener.settimeout(0.5)
        os.chmod(self.socket_path, 0o600)

        self._handler = handler
        self._listener = listener
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

        if self._listener is not None:
            try:
                self._listener.close()
            except OSError:
                pass
            self._listener = None

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        try:
            self.socket_path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass

    def _remove_stale_socket(self) -> None:
        if not self.socket_path.exists():
            return

        if self.notify_existing_instance(timeout=0.2):
            raise RuntimeError("Another instance is already running.")

        self.socket_path.unlink(missing_ok=True)

    def _serve(self) -> None:
        while not self._stop_event.is_set():
            if self._listener is None:
                break

            try:
                connection, _ = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            with connection:
                try:
                    raw = connection.recv(65536)
                except OSError:
                    continue

            if not raw:
                continue

            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue

            if self._handler is not None:
                self._handler(payload)
