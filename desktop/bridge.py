import base64
from collections import deque
from pathlib import Path
from threading import Lock

from app.services import markdown_service, pdf_service
from app.runtime_paths import supported_markdown_file


def read_markdown_payload(path: str | Path) -> dict[str, str]:
    file_path = Path(path)

    if not supported_markdown_file(file_path.name):
        raise ValueError("Only .md and .markdown files are supported.")

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("File must be UTF-8 encoded.") from exc

    return {"name": file_path.name, "content": content}


class PendingOpenFiles:
    def __init__(self):
        self._items: deque[dict[str, str]] = deque()
        self._lock = Lock()

    def enqueue_payload(self, payload: dict[str, str]) -> None:
        with self._lock:
            self._items.append(payload)

    def enqueue_path(self, path: str | Path) -> dict[str, str] | None:
        try:
            payload = read_markdown_payload(path)
        except ValueError:
            return None

        self.enqueue_payload(payload)
        return payload

    def consume(self) -> dict[str, str] | None:
        with self._lock:
            if not self._items:
                return None
            return self._items.popleft()


class DesktopBridge:
    def __init__(self, pending_files: PendingOpenFiles, open_dialog_type=None, save_dialog_type=None):
        self._pending_files = pending_files
        self._open_dialog_type = open_dialog_type
        self._save_dialog_type = save_dialog_type
        self._window = None

    def attach_window(self, window) -> None:
        self._window = window

    def get_launch_context(self) -> dict[str, object]:
        launch_context: dict[str, object] = {"desktopMode": True}
        opened_file = self.consume_pending_open_file()
        if opened_file is not None:
            launch_context["openedFile"] = opened_file
        return launch_context

    def open_markdown_dialog(self) -> dict[str, str] | dict[str, object] | None:
        if self._window is None or self._open_dialog_type is None:
            return {"error": "Desktop file picker is not ready."}

        paths = self._window.create_file_dialog(
            self._open_dialog_type,
            allow_multiple=False,
            file_types=("Markdown files (*.md;*.markdown)",),
        )
        if not paths:
            return None

        try:
            return read_markdown_payload(paths[0])
        except ValueError as exc:
            return {"error": str(exc)}

    def save_pdf(self, suggested_filename: str, base64_pdf: str) -> dict[str, object]:
        if self._window is None or self._save_dialog_type is None:
            return {"saved": False, "error": "Desktop save dialog is not ready."}

        destination = self._window.create_file_dialog(
            self._save_dialog_type,
            save_filename=suggested_filename,
            file_types=("PDF files (*.pdf)",),
        )
        if not destination:
            return {"saved": False}

        output_path = Path(destination if isinstance(destination, str) else destination[0])
        output_path.write_bytes(base64.b64decode(base64_pdf))
        return {"saved": True, "path": str(output_path)}

    def consume_pending_open_file(self) -> dict[str, str] | None:
        return self._pending_files.consume()

    def convert_markdown(self, filename: str, content: str, theme: str = "default") -> dict[str, str]:
        if not supported_markdown_file(filename):
            return {"error": "Only .md and .markdown files are supported."}

        try:
            html_body = markdown_service.render(content)
            pdf_bytes = pdf_service.generate(html_body, theme)
        except RuntimeError as exc:
            return {"error": str(exc)}

        output_name = f"{Path(filename).stem}.pdf"
        return {
            "filename": output_name,
            "base64Pdf": base64.b64encode(pdf_bytes).decode("ascii"),
        }

    def notify_pending_open_file(self) -> None:
        if self._window is None:
            return

        try:
            self._window.evaluate_js(
                "window.dispatchEvent(new CustomEvent('desktop-open-file'));"
            )
        except Exception:
            pass

    def activate_window(self) -> None:
        if self._window is None:
            return

        for method_name in ("restore", "show"):
            method = getattr(self._window, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception:
                    pass

        try:
            from Cocoa import NSApplication

            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        except Exception:
            pass
