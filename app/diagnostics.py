from __future__ import annotations

import logging
import os
import platform
import sys
import traceback
from pathlib import Path

from app import runtime_paths


LOGGER_NAME = "md2pdf-converter"
_logger: logging.Logger | None = None


def log_path() -> Path:
    runtime_paths.ensure_runtime_directories()
    return runtime_paths.diagnostics_log_path()


def get_logger() -> logging.Logger:
    global _logger

    if _logger is not None:
        return _logger

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_file = log_path()
    if not any(isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == log_file for handler in logger.handlers):
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(file_handler)

    _logger = logger
    return logger


def _runtime_snapshot(extra: dict[str, object] | None = None) -> str:
    details = {
        "bundled": runtime_paths.is_bundled(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "mac_ver": platform.mac_ver()[0],
        "python": sys.version.replace("\n", " "),
        "executable": sys.executable,
        "resource_root": str(runtime_paths.resource_root()),
        "frameworks_dir": str(runtime_paths.frameworks_dir()) if runtime_paths.frameworks_dir() else "None",
        "log_path": str(log_path()),
        "DYLD_LIBRARY_PATH": os.environ.get("DYLD_LIBRARY_PATH", ""),
        "DYLD_FALLBACK_LIBRARY_PATH": os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", ""),
        "FONTCONFIG_PATH": os.environ.get("FONTCONFIG_PATH", ""),
        "FONTCONFIG_FILE": os.environ.get("FONTCONFIG_FILE", ""),
        "XDG_CACHE_HOME": os.environ.get("XDG_CACHE_HOME", ""),
        "GIO_MODULE_DIR": os.environ.get("GIO_MODULE_DIR", ""),
        "GDK_PIXBUF_MODULE_FILE": os.environ.get("GDK_PIXBUF_MODULE_FILE", ""),
    }

    if extra:
        details.update(extra)

    return "\n".join(f"{key}: {value}" for key, value in details.items())


def record_exception(title: str, exc: BaseException, extra: dict[str, object] | None = None) -> Path:
    logger = get_logger()
    snapshot = _runtime_snapshot(extra)
    stack = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error("%s\n%s\n%s", title, snapshot, stack)
    return log_path()
