import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
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

    def test_bundled_mode_prefers_frameworks_and_sets_bundle_env_vars(self):
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            home_dir = temp_path / "home"
            resource_root = temp_path / "md2pdf-converter.app" / "Contents" / "Resources"
            frameworks_dir = temp_path / "md2pdf-converter.app" / "Contents" / "Frameworks"
            executable = temp_path / "md2pdf-converter.app" / "Contents" / "MacOS" / "md2pdf-converter"
            fontconfig_dir = resource_root / "etc" / "fonts"
            gio_modules_dir = resource_root / "lib" / "gio" / "modules"
            gdk_pixbuf_module_dir = resource_root / "lib" / "gdk-pixbuf-2.0" / "2.10.0" / "loaders"

            frameworks_dir.mkdir(parents=True)
            fontconfig_dir.mkdir(parents=True)
            gio_modules_dir.mkdir(parents=True)
            gdk_pixbuf_module_dir.mkdir(parents=True)
            executable.parent.mkdir(parents=True, exist_ok=True)
            executable.write_text("", encoding="utf-8")
            (fontconfig_dir / "fonts.conf").write_text("<fontconfig/>", encoding="utf-8")
            (gdk_pixbuf_module_dir.parent / "loaders.cache").write_text("png", encoding="utf-8")

            with patch.object(runtime_paths.sys, "frozen", True, create=True):
                with patch.object(runtime_paths.sys, "executable", str(executable)):
                    with patch.object(runtime_paths.Path, "home", return_value=home_dir):
                        with patch.dict(
                            runtime_paths.os.environ,
                            {
                                "RESOURCEPATH": str(resource_root),
                                "FONTCONFIG_PATH": "/tmp/external-fonts",
                                "FONTCONFIG_FILE": "/tmp/external-fonts.conf",
                                "GIO_MODULE_DIR": "/tmp/external-gio",
                                "GDK_PIXBUF_MODULEDIR": "/tmp/external-gdk",
                                "GDK_PIXBUF_MODULE_FILE": "/tmp/external-loaders.cache",
                                "XDG_CACHE_HOME": "/tmp/external-cache",
                            },
                            clear=True,
                        ):
                            self.assertEqual(runtime_paths.dynamic_library_dirs(), [frameworks_dir.resolve()])

                            runtime_paths.configure_dynamic_library_paths()

                            self.assertEqual(
                                runtime_paths.os.environ["DYLD_LIBRARY_PATH"],
                                str(frameworks_dir.resolve()),
                            )
                            self.assertEqual(
                                runtime_paths.os.environ["DYLD_FALLBACK_LIBRARY_PATH"],
                                str(frameworks_dir.resolve()),
                            )
                            self.assertEqual(
                                runtime_paths.os.environ["FONTCONFIG_PATH"],
                                str(fontconfig_dir.resolve()),
                            )
                            self.assertEqual(
                                runtime_paths.os.environ["FONTCONFIG_FILE"],
                                str((fontconfig_dir / "fonts.conf").resolve()),
                            )
                            self.assertEqual(
                                runtime_paths.os.environ["GIO_MODULE_DIR"],
                                str(gio_modules_dir.resolve()),
                            )
                            self.assertEqual(
                                runtime_paths.os.environ["GDK_PIXBUF_MODULEDIR"],
                                str(gdk_pixbuf_module_dir.resolve()),
                            )
                            self.assertEqual(
                                runtime_paths.os.environ["GDK_PIXBUF_MODULE_FILE"],
                                str((gdk_pixbuf_module_dir.parent / "loaders.cache").resolve()),
                            )
                            self.assertEqual(
                                runtime_paths.os.environ["XDG_CACHE_HOME"],
                                str(
                                    (
                                        home_dir
                                        / "Library"
                                        / "Application Support"
                                        / "md2pdf-converter"
                                        / "cache"
                                    ).resolve()
                                ),
                            )

    def test_bundled_mode_clears_external_env_vars_when_bundle_resources_are_missing(self):
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            home_dir = temp_path / "home"
            resource_root = temp_path / "md2pdf-converter.app" / "Contents" / "Resources"
            frameworks_dir = temp_path / "md2pdf-converter.app" / "Contents" / "Frameworks"
            executable = temp_path / "md2pdf-converter.app" / "Contents" / "MacOS" / "md2pdf-converter"

            frameworks_dir.mkdir(parents=True)
            executable.parent.mkdir(parents=True, exist_ok=True)
            executable.write_text("", encoding="utf-8")
            resource_root.mkdir(parents=True, exist_ok=True)

            with patch.object(runtime_paths.sys, "frozen", True, create=True):
                with patch.object(runtime_paths.sys, "executable", str(executable)):
                    with patch.object(runtime_paths.Path, "home", return_value=home_dir):
                        with patch.dict(
                            runtime_paths.os.environ,
                            {
                                "RESOURCEPATH": str(resource_root),
                                "FONTCONFIG_PATH": "/tmp/external-fonts",
                                "FONTCONFIG_FILE": "/tmp/external-fonts.conf",
                                "GIO_MODULE_DIR": "/tmp/external-gio",
                                "GDK_PIXBUF_MODULEDIR": "/tmp/external-gdk",
                                "GDK_PIXBUF_MODULE_FILE": "/tmp/external-loaders.cache",
                            },
                            clear=True,
                        ):
                            runtime_paths.configure_dynamic_library_paths()

                            self.assertNotIn("FONTCONFIG_PATH", runtime_paths.os.environ)
                            self.assertNotIn("FONTCONFIG_FILE", runtime_paths.os.environ)
                            self.assertNotIn("GIO_MODULE_DIR", runtime_paths.os.environ)
                            self.assertNotIn("GDK_PIXBUF_MODULEDIR", runtime_paths.os.environ)
                            self.assertNotIn("GDK_PIXBUF_MODULE_FILE", runtime_paths.os.environ)

    def test_bundled_runtime_directories_include_logs_and_cache(self):
        with TemporaryDirectory() as temp_dir:
            home_dir = Path(temp_dir) / "home"

            with patch.object(runtime_paths.sys, "frozen", True, create=True):
                with patch.object(runtime_paths.Path, "home", return_value=home_dir):
                    runtime_paths.ensure_runtime_directories()

                    self.assertTrue(runtime_paths.cache_dir().exists())
                    self.assertTrue(runtime_paths.logs_dir().exists())
                    self.assertEqual(
                        runtime_paths.diagnostics_log_path(),
                        runtime_paths.logs_dir() / runtime_paths.LOG_FILENAME,
                    )
