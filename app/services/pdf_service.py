import platform
from io import BytesIO

from jinja2 import Environment, FileSystemLoader

from app import diagnostics, runtime_paths

_jinja_env = Environment(loader=FileSystemLoader(str(runtime_paths.templates_dir())))

VALID_THEMES = {"default", "github", "academic", "dark_print"}
BUNDLED_CFFI_LIBRARY_MAP = {
    "libgobject-2.0-0": "libgobject-2.0.0.dylib",
    "gobject-2.0-0": "libgobject-2.0.0.dylib",
    "gobject-2.0": "libgobject-2.0.0.dylib",
    "libgobject-2.0.so.0": "libgobject-2.0.0.dylib",
    "libgobject-2.0.0.dylib": "libgobject-2.0.0.dylib",
    "libpango-1.0-0": "libpango-1.0.0.dylib",
    "pango-1.0-0": "libpango-1.0.0.dylib",
    "pango-1.0": "libpango-1.0.0.dylib",
    "libpango-1.0.so.0": "libpango-1.0.0.dylib",
    "libpango-1.0.dylib": "libpango-1.0.0.dylib",
    "libharfbuzz-0": "libharfbuzz.0.dylib",
    "harfbuzz": "libharfbuzz.0.dylib",
    "harfbuzz-0.0": "libharfbuzz.0.dylib",
    "libharfbuzz.so.0": "libharfbuzz.0.dylib",
    "libharfbuzz.0.dylib": "libharfbuzz.0.dylib",
    "libharfbuzz-subset-0": "libharfbuzz-subset.0.dylib",
    "harfbuzz-subset": "libharfbuzz-subset.0.dylib",
    "harfbuzz-subset-0.0": "libharfbuzz-subset.0.dylib",
    "libharfbuzz-subset.so.0": "libharfbuzz-subset.0.dylib",
    "libharfbuzz-subset.0.dylib": "libharfbuzz-subset.0.dylib",
    "libfontconfig-1": "libfontconfig.1.dylib",
    "fontconfig-1": "libfontconfig.1.dylib",
    "fontconfig": "libfontconfig.1.dylib",
    "libfontconfig.so.1": "libfontconfig.1.dylib",
    "libfontconfig.1.dylib": "libfontconfig.1.dylib",
    "libpangoft2-1.0-0": "libpangoft2-1.0.0.dylib",
    "pangoft2-1.0-0": "libpangoft2-1.0.0.dylib",
    "pangoft2-1.0": "libpangoft2-1.0.0.dylib",
    "libpangoft2-1.0.so.0": "libpangoft2-1.0.0.dylib",
    "libpangoft2-1.0.dylib": "libpangoft2-1.0.0.dylib",
}


def _configure_bundled_cffi_lookup() -> None:
    if not runtime_paths.is_bundled():
        return

    frameworks_dir = runtime_paths.frameworks_dir()
    if frameworks_dir is None or not frameworks_dir.exists():
        return

    import cffi.api

    ffi_cls = cffi.api.FFI
    if getattr(ffi_cls, "_md2pdf_bundle_patch_installed", False):
        return

    original_dlopen = ffi_cls.dlopen

    def patched_dlopen(self, name, flags=0):
        if isinstance(name, str):
            target_name = BUNDLED_CFFI_LIBRARY_MAP.get(name)
            if target_name is not None:
                candidate = frameworks_dir / target_name
                if candidate.exists():
                    return original_dlopen(self, str(candidate), flags)

        return original_dlopen(self, name, flags)

    ffi_cls.dlopen = patched_dlopen
    ffi_cls._md2pdf_bundle_patch_installed = True


def _dependency_error_message() -> str:
    if runtime_paths.is_bundled():
        return (
            "The packaged PDF engine could not be loaded on this Mac. "
            "This unsigned build currently supports Apple Silicon Macs running macOS 13 or later. "
            f"Please send this log file to the developer: {diagnostics.log_path()}"
        )

    return (
        "WeasyPrint dependencies are not available. "
        "Install the required system libraries (for example: `brew install pango`) and try again."
    )


def _load_weasyprint():
    runtime_paths.configure_dynamic_library_paths()
    _configure_bundled_cffi_lookup()

    try:
        from weasyprint import CSS, HTML
        from weasyprint.text.fonts import FontConfiguration
    except (ImportError, OSError) as exc:
        diagnostics.record_exception(
            "Failed to load WeasyPrint runtime",
            exc,
            extra={
                "bundled": runtime_paths.is_bundled(),
                "machine": platform.machine(),
                "mac_ver": platform.mac_ver()[0],
                "dynamic_library_dirs": [str(path) for path in runtime_paths.dynamic_library_dirs()],
            },
        )
        raise RuntimeError(_dependency_error_message()) from exc

    return HTML, CSS, FontConfiguration


def generate(html_body: str, theme: str = "default") -> bytes:
    HTML, CSS, FontConfiguration = _load_weasyprint()

    if theme not in VALID_THEMES:
        theme = "default"

    template = _jinja_env.get_template("pdf_wrapper.html")
    full_html = template.render(
        body_html=html_body,
        theme=theme,
        themes_dir=str(runtime_paths.themes_dir()),
    )

    font_config = FontConfiguration()
    stylesheets = [
        CSS(filename=str(runtime_paths.themes_dir() / "base.css"), font_config=font_config),
        CSS(filename=str(runtime_paths.themes_dir() / f"{theme}.css"), font_config=font_config),
    ]

    buf = BytesIO()
    HTML(string=full_html, base_url=str(runtime_paths.resource_root())).write_pdf(
        buf,
        stylesheets=stylesheets,
        font_config=font_config,
    )
    buf.seek(0)
    return buf.read()
