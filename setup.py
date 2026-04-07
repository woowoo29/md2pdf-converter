import os
import platform
import subprocess
from pathlib import Path
import sys

from setuptools import setup


APP = ["desktop/app.py"]
APP_NAME = "md2pdf-converter"
ICON_FILE = Path("assets/icon/md2pdf-converter.icns")
RESOURCE_PATHS = ["app/templates", "app/themes", "static"]
FRAMEWORK_SEEDS = (
    "libpango-1.0.0.dylib",
    "libpangocairo-1.0.0.dylib",
    "libpangoft2-1.0.0.dylib",
    "libharfbuzz.0.dylib",
    "libglib-2.0.0.dylib",
    "libgobject-2.0.0.dylib",
    "libgio-2.0.0.dylib",
    "libcairo.2.dylib",
    "libfontconfig.1.dylib",
    "libfreetype.6.dylib",
    "libfribidi.0.dylib",
    "libffi.8.dylib",
    "libpng16.16.dylib",
    "libpixman-1.0.dylib",
    "libexpat.1.dylib",
    "libgraphite2.3.2.1.dylib",
    "libdatrie.1.dylib",
    "libthai.0.dylib",
    "libbrotlidec.1.dylib",
    "libbrotlicommon.1.dylib",
)


def library_search_roots() -> tuple[Path, ...]:
    roots: list[Path] = [
        Path("/opt/homebrew/lib"),
        Path(sys.base_prefix) / "lib",
        Path(sys.prefix) / "lib",
    ]

    if platform.machine() != "arm64":
        roots.append(Path("/usr/local/lib"))

    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        roots.append(Path(conda_prefix) / "lib")

    unique_roots: list[Path] = []
    for root in roots:
        if root.exists() and root not in unique_roots:
            unique_roots.append(root)

    return tuple(unique_roots)


def _find_seed_libraries() -> list[Path]:
    seeds: list[Path] = []
    for root in library_search_roots():
        for filename in FRAMEWORK_SEEDS:
            candidate = root / filename
            if candidate.exists() and _supports_target_arch(candidate):
                seeds.append(candidate)
    return seeds


def _is_homebrew_library(path: str) -> bool:
    return any(path.startswith(str(root)) for root in library_search_roots())


def _supports_target_arch(path: Path) -> bool:
    target_arch = platform.machine()

    try:
        output = subprocess.check_output(["lipo", "-info", str(path)], text=True, stderr=subprocess.STDOUT)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return True

    return target_arch in output


def collect_frameworks() -> list[str]:
    queue = _find_seed_libraries()
    discovered: dict[str, Path] = {}

    while queue:
        library_path = queue.pop()
        resolved = library_path.resolve()
        if str(resolved) in discovered:
            continue

        discovered[str(resolved)] = resolved

        try:
            output = subprocess.check_output(["otool", "-L", str(resolved)], text=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

        for line in output.splitlines()[1:]:
            dependency = line.strip().split(" (compatibility")[0]
            if not _is_homebrew_library(dependency):
                continue

            dependency_path = Path(dependency)
            if dependency_path.exists() and _supports_target_arch(dependency_path):
                queue.append(dependency_path)

    return sorted(discovered)


def patch_py2app_recipes() -> None:
    """Disable py2app's Tk probing for this app bundle.

    WeasyPrint pulls in Pillow, and Pillow exposes optional tkinter helpers.
    py2app's default tkinter recipe probes those modules by creating a Tk app,
    which crashes the build on some macOS/Python combinations even though this
    project never uses Tk.
    """

    try:
        import py2app.recipes.tkinter as tkinter_recipe
    except Exception:
        tkinter_recipe = None

    if tkinter_recipe is not None:
        tkinter_recipe.check = lambda cmd, mf: None

    try:
        import py2app.recipes.PIL as pil_recipe
    except Exception:
        pil_recipe = None

    if pil_recipe is not None:
        original_check = pil_recipe.check

        def patched_pil_check(cmd, mf):
            result = original_check(cmd, mf)

            for module_name in ("PIL.features", "PIL._tkinter_finder", "PIL.ImageTk"):
                node = mf.findNode(module_name)
                if node is None:
                    continue
                for ref in ("PIL._tkinter_finder", "tkinter", "_tkinter", "ImageTk"):
                    try:
                        mf.removeReference(node, ref)
                    except Exception:
                        continue

            return result

        pil_recipe.check = patched_pil_check


plist = {
    "CFBundleName": APP_NAME,
    "CFBundleDisplayName": APP_NAME,
    "CFBundleIdentifier": "com.woowoo29.md2pdf-converter",
    "CFBundleShortVersionString": "3.0.0",
    "CFBundleVersion": "3.0.0",
    "LSMinimumSystemVersion": "13.0",
    "NSHighResolutionCapable": True,
    "CFBundleDocumentTypes": [
        {
            "CFBundleTypeName": "Markdown Document",
            "CFBundleTypeExtensions": ["md", "markdown"],
            "CFBundleTypeRole": "Viewer",
            "LSHandlerRank": "Owner",
        }
    ],
}

OPTIONS = {
    "argv_emulation": False,
    "frameworks": collect_frameworks(),
    "excludes": [
        "FixTk",
        "PIL.ImageTk",
        "PIL._tkinter_finder",
        "Tkinter",
        "_tkinter",
        "tkinter",
    ],
    "includes": [
        "app.main",
        "app.routers.convert",
        "app.services.markdown_service",
        "app.services.pdf_service",
        "anyio._backends",
        "anyio._backends._asyncio",
        "desktop.app",
        "desktop.bridge",
        "desktop.server",
        "desktop.single_instance",
        "html",
        "html.entities",
        "html.parser",
        "jinja2",
        "markdown",
        "pymdownx.highlight",
        "pymdownx.superfences",
        "pymdownx.tasklist",
        "uvicorn",
        "uvicorn.lifespan.on",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
        "webview",
        "weasyprint",
        "zoneinfo",
    ],
    "packages": [
        "PIL",
        "aiofiles",
        "anyio",
        "app",
        "cffi",
        "cssselect2",
        "desktop",
        "dotenv",
        "fastapi",
        "fontTools",
        "httpcore",
        "httpx",
        "jinja2",
        "markdown",
        "multipart",
        "pydantic",
        "pydantic_core",
        "pymdownx",
        "pyphen",
        "starlette",
        "tinycss2",
        "tinyhtml5",
        "uvicorn",
        "watchfiles",
        "websockets",
        "webview",
        "weasyprint",
        "yaml",
        "zoneinfo",
    ],
    "plist": plist,
    "resources": RESOURCE_PATHS,
    "site_packages": False,
    "strip": False,
}

patch_py2app_recipes()

if ICON_FILE.exists():
    OPTIONS["iconfile"] = str(ICON_FILE)
    plist["CFBundleIconFile"] = ICON_FILE.name


setup(
    app=APP,
    name=APP_NAME,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
