import socket
import threading
import time
from urllib.error import URLError
from urllib.request import urlopen

import uvicorn


def reserve_local_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.getsockname()[1]


def wait_for_healthcheck(url: str, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (OSError, URLError):
            time.sleep(0.1)

    raise RuntimeError(f"Timed out waiting for local server at {url}")


class DesktopServer:
    def __init__(self, app_target: str = "app.main:app", host: str = "127.0.0.1", port: int | None = None):
        self.app_target = app_target
        self.host = host
        self.port = port or reserve_local_port(host)
        self._server = None
        self._thread = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def health_url(self) -> str:
        return f"{self.base_url}/healthz"

    def start(self, timeout: float = 10.0) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        config = uvicorn.Config(
            self.app_target,
            host=self.host,
            port=self.port,
            reload=False,
            access_log=False,
            log_level="warning",
        )
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()
        wait_for_healthcheck(self.health_url, timeout=timeout)

    def stop(self, timeout: float = 5.0) -> None:
        if self._server is None or self._thread is None:
            return

        self._server.should_exit = True
        self._thread.join(timeout)

        if self._thread.is_alive():
            self._server.force_exit = True
            self._thread.join(timeout)

        self._server = None
        self._thread = None
