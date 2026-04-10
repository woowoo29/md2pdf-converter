import builtins
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services import pdf_service


class PdfServiceTests(unittest.TestCase):
    @patch("app.services.pdf_service.runtime_paths.is_bundled", return_value=False)
    def test_source_dependency_error_mentions_homebrew_setup(self, _is_bundled):
        message = pdf_service._dependency_error_message()

        self.assertIn("brew install pango", message)
        self.assertNotIn("Apple Silicon", message)

    @patch("app.services.pdf_service.runtime_paths.is_bundled", return_value=True)
    @patch(
        "app.services.pdf_service.diagnostics.log_path",
        return_value=Path("/Users/test/Library/Application Support/md2pdf-converter/logs/app.log"),
    )
    def test_bundled_dependency_error_points_to_log_file(self, _log_path, _is_bundled):
        message = pdf_service._dependency_error_message()

        self.assertIn("Apple Silicon", message)
        self.assertIn("macOS 13 or later", message)
        self.assertIn("/Users/test/Library/Application Support/md2pdf-converter/logs/app.log", message)

    @patch("app.services.pdf_service.runtime_paths.dynamic_library_dirs", return_value=[Path("/tmp/frameworks")])
    @patch("app.services.pdf_service.runtime_paths.is_bundled", return_value=True)
    @patch(
        "app.services.pdf_service.diagnostics.log_path",
        return_value=Path("/Users/test/Library/Application Support/md2pdf-converter/logs/app.log"),
    )
    @patch("app.services.pdf_service.diagnostics.record_exception")
    def test_load_weasyprint_failure_logs_and_raises_bundle_message(
        self,
        mock_record_exception,
        _log_path,
        _is_bundled,
        _dynamic_dirs,
    ):
        original_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "weasyprint" or name.startswith("weasyprint."):
                raise ImportError("missing weasyprint test dependency")
            return original_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=fake_import):
            with self.assertRaises(RuntimeError) as context:
                pdf_service._load_weasyprint()

        self.assertIn("packaged PDF engine could not be loaded", str(context.exception))
        mock_record_exception.assert_called_once()
