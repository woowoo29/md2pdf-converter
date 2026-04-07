import base64
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from desktop.bridge import DesktopBridge, PendingOpenFiles, read_markdown_payload


class FakeWindow:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.scripts = []
        self.restore_called = False
        self.show_called = False

    def create_file_dialog(self, dialog_type, **kwargs):
        _ = kwargs
        return self.responses.get(dialog_type)

    def evaluate_js(self, script):
        self.scripts.append(script)

    def restore(self):
        self.restore_called = True

    def show(self):
        self.show_called = True


class DesktopBridgeTests(unittest.TestCase):
    def test_read_markdown_payload_rejects_unsupported_extension(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            txt_path = Path(tmp_dir) / "notes.txt"
            txt_path.write_text("plain text", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, ".md and .markdown"):
                read_markdown_payload(txt_path)

    def test_open_markdown_dialog_returns_none_when_cancelled(self):
        bridge = DesktopBridge(PendingOpenFiles(), open_dialog_type="open")
        bridge.attach_window(FakeWindow({"open": None}))

        self.assertIsNone(bridge.open_markdown_dialog())

    def test_open_markdown_dialog_reads_file_contents(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            markdown_path = Path(tmp_dir) / "notes.markdown"
            markdown_path.write_text("# Hello", encoding="utf-8")

            bridge = DesktopBridge(PendingOpenFiles(), open_dialog_type="open")
            bridge.attach_window(FakeWindow({"open": [str(markdown_path)]}))

            payload = bridge.open_markdown_dialog()

            self.assertEqual(payload, {"name": "notes.markdown", "content": "# Hello"})

    def test_read_markdown_payload_handles_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing_path = Path(tmp_dir) / "missing.md"

            with self.assertRaisesRegex(ValueError, "could not be found"):
                read_markdown_payload(missing_path)

    def test_read_markdown_payload_handles_permission_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            markdown_path = Path(tmp_dir) / "notes.md"
            markdown_path.write_text("# Hello", encoding="utf-8")

            with patch.object(Path, "read_text", side_effect=PermissionError):
                with self.assertRaisesRegex(ValueError, "permission to open"):
                    read_markdown_payload(markdown_path)

    def test_save_pdf_returns_false_when_user_cancels(self):
        bridge = DesktopBridge(PendingOpenFiles(), save_dialog_type="save")
        bridge.attach_window(FakeWindow({"save": None}))

        result = bridge.save_pdf("notes.pdf", base64.b64encode(b"pdf").decode("ascii"))

        self.assertEqual(result, {"saved": False})

    def test_save_pdf_writes_bytes_to_selected_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "saved.pdf"
            bridge = DesktopBridge(PendingOpenFiles(), save_dialog_type="save")
            bridge.attach_window(FakeWindow({"save": [str(output_path)]}))

            result = bridge.save_pdf(
                "notes.pdf",
                base64.b64encode(b"%PDF-1.4 desktop test").decode("ascii"),
            )

            self.assertTrue(result["saved"])
            self.assertEqual(output_path.read_bytes(), b"%PDF-1.4 desktop test")

    def test_save_pdf_returns_error_for_invalid_base64(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "saved.pdf"
            bridge = DesktopBridge(PendingOpenFiles(), save_dialog_type="save")
            bridge.attach_window(FakeWindow({"save": [str(output_path)]}))

            result = bridge.save_pdf("notes.pdf", "%%%not-base64%%%")

            self.assertEqual(
                result,
                {"saved": False, "error": "Generated PDF data was invalid."},
            )
            self.assertFalse(output_path.exists())

    def test_save_pdf_returns_error_when_write_fails(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "saved.pdf"
            bridge = DesktopBridge(PendingOpenFiles(), save_dialog_type="save")
            bridge.attach_window(FakeWindow({"save": [str(output_path)]}))

            with patch.object(Path, "write_bytes", side_effect=PermissionError):
                result = bridge.save_pdf(
                    "notes.pdf",
                    base64.b64encode(b"%PDF-1.4 desktop test").decode("ascii"),
                )

            self.assertEqual(
                result,
                {
                    "saved": False,
                    "error": "You do not have permission to save to that location.",
                },
            )

    def test_pending_open_file_is_consumed_once(self):
        pending_files = PendingOpenFiles()
        pending_files.enqueue_payload({"name": "notes.md", "content": "# Hello"})
        bridge = DesktopBridge(pending_files)

        first = bridge.consume_pending_open_file()
        second = bridge.consume_pending_open_file()

        self.assertEqual(first, {"name": "notes.md", "content": "# Hello"})
        self.assertIsNone(second)

    def test_get_launch_context_includes_first_pending_file(self):
        pending_files = PendingOpenFiles()
        pending_files.enqueue_payload({"name": "launch.md", "content": "# Launch"})
        bridge = DesktopBridge(pending_files)

        context = bridge.get_launch_context()

        self.assertEqual(
            context,
            {
                "desktopMode": True,
                "openedFile": {"name": "launch.md", "content": "# Launch"},
            },
        )

    def test_convert_markdown_returns_encoded_pdf_payload(self):
        bridge = DesktopBridge(PendingOpenFiles())

        with patch("desktop.bridge.markdown_service.render", return_value="<h1>Hello</h1>"), patch(
            "desktop.bridge.pdf_service.generate", return_value=b"%PDF-test"
        ):
            result = bridge.convert_markdown("notes.md", "# Hello", "default")

        self.assertEqual(result["filename"], "notes.pdf")
        self.assertEqual(base64.b64decode(result["base64Pdf"]), b"%PDF-test")

    def test_notify_pending_open_file_dispatches_event(self):
        window = FakeWindow()
        bridge = DesktopBridge(PendingOpenFiles())
        bridge.attach_window(window)

        bridge.notify_pending_open_file()

        self.assertEqual(
            window.scripts,
            ["window.dispatchEvent(new CustomEvent('desktop-open-file'));"],
        )

    def test_activate_window_uses_window_methods(self):
        window = FakeWindow()
        bridge = DesktopBridge(PendingOpenFiles())
        bridge.attach_window(window)

        fake_app = SimpleNamespace(activateIgnoringOtherApps_=lambda _flag: None)
        fake_ns_application = SimpleNamespace(sharedApplication=lambda: fake_app)

        with patch.dict(sys.modules, {"Cocoa": SimpleNamespace(NSApplication=fake_ns_application)}):
            bridge.activate_window()

        self.assertTrue(window.restore_called)
        self.assertTrue(window.show_called)
