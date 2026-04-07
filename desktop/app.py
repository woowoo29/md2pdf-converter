from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import runtime_paths
from desktop.bridge import DesktopBridge, PendingOpenFiles
from desktop.server import DesktopServer
from desktop.single_instance import SingleInstanceController


APP_TITLE = "md2pdf-converter"
WINDOW_SIZE = (1240, 900)
WINDOW_MIN_SIZE = (980, 760)


def _collect_initial_open_paths() -> list[Path]:
    open_paths: list[Path] = []
    for arg in sys.argv[1:]:
        potential_path = Path(arg).expanduser()
        if potential_path.exists():
            open_paths.append(potential_path)
    return open_paths


def _install_open_file_delegate(pending_files: PendingOpenFiles):
    if sys.platform != "darwin":
        return None

    try:
        import objc
        from Cocoa import NSApplication, NSApplicationDelegateReplySuccess, NSObject
    except ImportError:
        return None

    class OpenFileDelegate(NSObject):
        def initWithPendingFiles_(self, store):
            self = objc.super(OpenFileDelegate, self).init()
            if self is None:
                return None
            self.pending_files = store
            return self

        def application_openFiles_(self, app, filenames):
            for filename in filenames:
                self.pending_files.enqueue_path(filename)

            try:
                app.replyToOpenOrPrint_(NSApplicationDelegateReplySuccess)
            except Exception:
                pass

    delegate = OpenFileDelegate.alloc().initWithPendingFiles_(pending_files)
    NSApplication.sharedApplication().setDelegate_(delegate)
    return delegate


def main() -> None:
    runtime_paths.configure_dynamic_library_paths()
    runtime_paths.ensure_runtime_directories()

    initial_paths = _collect_initial_open_paths()
    instance_controller = SingleInstanceController()
    if instance_controller.notify_existing_instance(initial_paths):
        return

    pending_files = PendingOpenFiles()
    for path in initial_paths:
        pending_files.enqueue_path(path)
    delegate = _install_open_file_delegate(pending_files)

    server = DesktopServer()
    server.start()

    try:
        import webview
    except ImportError as exc:
        server.stop()
        raise RuntimeError(
            "pywebview is not installed. Install desktop dependencies with "
            "`python -m pip install -r requirements-desktop.txt`."
        ) from exc

    bridge = DesktopBridge(
        pending_files,
        open_dialog_type=getattr(webview, "FileDialog", webview).OPEN,
        save_dialog_type=getattr(webview, "FileDialog", webview).SAVE,
    )

    window = webview.create_window(
        APP_TITLE,
        server.base_url,
        js_api=bridge,
        width=WINDOW_SIZE[0],
        height=WINDOW_SIZE[1],
        min_size=WINDOW_MIN_SIZE,
    )
    bridge.attach_window(window)

    def handle_secondary_launch(payload: dict[str, object]) -> None:
        for path in payload.get("open_paths", []):
            pending_files.enqueue_path(path)
        bridge.activate_window()
        bridge.notify_pending_open_file()

    instance_controller.start(handle_secondary_launch)

    try:
        webview.start(debug=False)
    finally:
        instance_controller.stop()
        server.stop()
        _ = delegate


if __name__ == "__main__":
    main()
