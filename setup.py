from pathlib import Path
import subprocess

from setuptools import setup


APP = ["desktop/app.py"]
APP_NAME = "md2pdf-converter"
RESOURCE_PATHS = ["app/templates", "app/themes", "static"]
BREW_LIBRARY_ROOTS = (Path("/opt/homebrew/lib"), Path("/usr/local/lib"))
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


def _find_seed_libraries() -> list[Path]:
    seeds: list[Path] = []
    for root in BREW_LIBRARY_ROOTS:
        for filename in FRAMEWORK_SEEDS:
            candidate = root / filename
            if candidate.exists():
                seeds.append(candidate)
    return seeds


def _is_homebrew_library(path: str) -> bool:
    return any(path.startswith(str(root)) for root in BREW_LIBRARY_ROOTS)


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
            if dependency_path.exists():
                queue.append(dependency_path)

    return sorted(discovered)


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
    ],
    "packages": ["app", "desktop"],
    "plist": plist,
    "resources": RESOURCE_PATHS,
    "site_packages": True,
    "strip": False,
}


setup(
    app=APP,
    name=APP_NAME,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
