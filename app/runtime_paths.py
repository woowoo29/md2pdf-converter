import os
import platform
import sys
from pathlib import Path


MARKDOWN_SUFFIXES = {".md", ".markdown"}
SOURCE_ROOT = Path(__file__).resolve().parent.parent
SOURCE_LIBRARY_DIRS = (
    Path("/opt/homebrew/lib"),
    *(tuple() if platform.machine() == "arm64" else (Path("/usr/local/lib"),)),
)
APP_SUPPORT_SUBDIR = "md2pdf-converter"
CONTROL_SOCKET_NAME = "desktop-instance.sock"
LOG_FILENAME = "app.log"


def is_bundled() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundle_contents_dir() -> Path | None:
    if not is_bundled():
        return None

    resource_root = os.environ.get("RESOURCEPATH")
    if resource_root:
        resource_path = Path(resource_root).resolve()
        if resource_path.name == "Resources" and resource_path.parent.name == "Contents":
            return resource_path.parent

    executable_path = Path(sys.executable).resolve()
    for parent in executable_path.parents:
        if parent.name == "Contents":
            return parent

    return None


def resource_root() -> Path:
    if is_bundled():
        resource_env = os.environ.get("RESOURCEPATH")
        if resource_env:
            return Path(resource_env).resolve()

        contents_dir = bundle_contents_dir()
        if contents_dir is not None:
            return contents_dir / "Resources"

    return SOURCE_ROOT


def frameworks_dir() -> Path | None:
    contents_dir = bundle_contents_dir()
    if contents_dir is None:
        return None
    return contents_dir / "Frameworks"


def static_dir() -> Path:
    return resource_root() / "static"


def templates_dir() -> Path:
    if is_bundled():
        candidates = [
            resource_root() / "templates",
            resource_root() / "app" / "templates",
        ]
    else:
        candidates = [SOURCE_ROOT / "app" / "templates"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def themes_dir() -> Path:
    if is_bundled():
        candidates = [
            resource_root() / "themes",
            resource_root() / "app" / "themes",
        ]
    else:
        candidates = [SOURCE_ROOT / "app" / "themes"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def writable_data_root() -> Path:
    if not is_bundled():
        return SOURCE_ROOT

    application_support = Path.home() / "Library" / "Application Support" / APP_SUPPORT_SUBDIR
    return application_support


def uploads_dir() -> Path:
    return writable_data_root() / "uploads"


def outputs_dir() -> Path:
    return writable_data_root() / "outputs"


def cache_dir() -> Path:
    return writable_data_root() / "cache"


def logs_dir() -> Path:
    return writable_data_root() / "logs"


def diagnostics_log_path() -> Path:
    return logs_dir() / LOG_FILENAME


def control_socket_path() -> Path:
    return writable_data_root() / CONTROL_SOCKET_NAME


def bundled_fontconfig_dir() -> Path:
    return resource_root() / "etc" / "fonts"


def bundled_fontconfig_file() -> Path:
    return bundled_fontconfig_dir() / "fonts.conf"


def bundled_gio_modules_dir() -> Path:
    return resource_root() / "lib" / "gio" / "modules"


def bundled_gdk_pixbuf_module_dir() -> Path:
    return resource_root() / "lib" / "gdk-pixbuf-2.0" / "2.10.0" / "loaders"


def bundled_gdk_pixbuf_module_file() -> Path:
    return resource_root() / "lib" / "gdk-pixbuf-2.0" / "2.10.0" / "loaders.cache"


def ensure_runtime_directories() -> None:
    writable_data_root().mkdir(parents=True, exist_ok=True)
    uploads_dir().mkdir(exist_ok=True)
    outputs_dir().mkdir(exist_ok=True)
    cache_dir().mkdir(exist_ok=True)
    logs_dir().mkdir(exist_ok=True)


def supported_markdown_file(filename: str | None) -> bool:
    if not filename:
        return False
    return Path(filename).suffix.lower() in MARKDOWN_SUFFIXES


def dynamic_library_dirs() -> list[Path]:
    candidates: list[Path] = []

    bundled_frameworks = frameworks_dir()
    if bundled_frameworks is not None and bundled_frameworks.exists():
        candidates.append(bundled_frameworks)

    if is_bundled():
        return candidates

    python_library_dirs = (
        Path(sys.base_prefix) / "lib",
        Path(sys.prefix) / "lib",
    )
    conda_prefix = os.environ.get("CONDA_PREFIX")
    conda_library_dir = Path(conda_prefix) / "lib" if conda_prefix else None

    for directory in (*SOURCE_LIBRARY_DIRS, *python_library_dirs):
        if directory.exists():
            candidates.append(directory)

    if conda_library_dir is not None and conda_library_dir.exists():
        candidates.append(conda_library_dir)

    return candidates


def _set_or_clear_bundle_env(env_key: str, path: Path) -> None:
    if path.exists():
        os.environ[env_key] = str(path.resolve())
        return

    os.environ.pop(env_key, None)


def configure_dynamic_library_paths() -> None:
    library_dirs = [str(path) for path in dynamic_library_dirs()]
    if library_dirs:
        for env_key in ("DYLD_FALLBACK_LIBRARY_PATH", "DYLD_LIBRARY_PATH"):
            existing = [entry for entry in os.environ.get(env_key, "").split(":") if entry]
            merged: list[str] = []
            for entry in [*library_dirs, *existing]:
                if entry not in merged:
                    merged.append(entry)
            os.environ[env_key] = ":".join(merged)

    if not is_bundled():
        return

    os.environ["XDG_CACHE_HOME"] = str(cache_dir().resolve())
    _set_or_clear_bundle_env("FONTCONFIG_PATH", bundled_fontconfig_dir())
    _set_or_clear_bundle_env("FONTCONFIG_FILE", bundled_fontconfig_file())
    _set_or_clear_bundle_env("GIO_MODULE_DIR", bundled_gio_modules_dir())
    _set_or_clear_bundle_env("GDK_PIXBUF_MODULEDIR", bundled_gdk_pixbuf_module_dir())
    _set_or_clear_bundle_env("GDK_PIXBUF_MODULE_FILE", bundled_gdk_pixbuf_module_file())
