import unittest
from pathlib import Path
from unittest.mock import patch

from app import runtime_paths


class RuntimePathTests(unittest.TestCase):
    def test_source_mode_uses_repo_root(self):
        with patch.object(runtime_paths.sys, "frozen", False, create=True):
            self.assertEqual(runtime_paths.resource_root(), runtime_paths.SOURCE_ROOT)
            self.assertIsNone(runtime_paths.frameworks_dir())
            self.assertEqual(runtime_paths.writable_data_root(), runtime_paths.SOURCE_ROOT)

    def test_bundled_mode_uses_resourcepath_and_frameworks(self):
        resource_root = "/Applications/md2pdf-converter.app/Contents/Resources"
        executable = "/Applications/md2pdf-converter.app/Contents/MacOS/md2pdf-converter"

        with patch.object(runtime_paths.sys, "frozen", True, create=True):
            with patch.object(runtime_paths.sys, "executable", executable):
                with patch.dict(runtime_paths.os.environ, {"RESOURCEPATH": resource_root}, clear=True):
                    self.assertEqual(runtime_paths.resource_root(), Path(resource_root))
                    self.assertEqual(
                        runtime_paths.frameworks_dir(),
                        Path("/Applications/md2pdf-converter.app/Contents/Frameworks"),
                    )
                    self.assertEqual(
                        runtime_paths.templates_dir(),
                        Path("/Applications/md2pdf-converter.app/Contents/Resources/templates"),
                    )
                    self.assertEqual(
                        runtime_paths.themes_dir(),
                        Path("/Applications/md2pdf-converter.app/Contents/Resources/themes"),
                    )
                    self.assertEqual(
                        runtime_paths.writable_data_root(),
                        Path.home() / "Library" / "Application Support" / "md2pdf-converter",
                    )

    def test_supported_markdown_file_accepts_md_and_markdown(self):
        self.assertTrue(runtime_paths.supported_markdown_file("notes.md"))
        self.assertTrue(runtime_paths.supported_markdown_file("notes.markdown"))
        self.assertFalse(runtime_paths.supported_markdown_file("notes.txt"))
