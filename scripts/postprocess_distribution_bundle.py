#!/usr/bin/env python3

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


APPLE_SILICON_FRAMEWORK_ALIASES = {
    "libgobject-2.0-0": "libgobject-2.0.0.dylib",
    "gobject-2.0-0": "libgobject-2.0.0.dylib",
    "gobject-2.0": "libgobject-2.0.0.dylib",
    "libgobject-2.0.dylib": "libgobject-2.0.0.dylib",
    "libgobject-2.0.so.0": "libgobject-2.0.0.dylib",
    "libgio-2.0-0": "libgio-2.0.0.dylib",
    "gio-2.0-0": "libgio-2.0.0.dylib",
    "gio-2.0": "libgio-2.0.0.dylib",
    "libgio-2.0.dylib": "libgio-2.0.0.dylib",
    "libgio-2.0.so.0": "libgio-2.0.0.dylib",
    "libglib-2.0-0": "libglib-2.0.0.dylib",
    "glib-2.0-0": "libglib-2.0.0.dylib",
    "glib-2.0": "libglib-2.0.0.dylib",
    "libglib-2.0.dylib": "libglib-2.0.0.dylib",
    "libglib-2.0.so.0": "libglib-2.0.0.dylib",
    "libgmodule-2.0-0": "libgmodule-2.0.0.dylib",
    "gmodule-2.0-0": "libgmodule-2.0.0.dylib",
    "gmodule-2.0": "libgmodule-2.0.0.dylib",
    "libgmodule-2.0.dylib": "libgmodule-2.0.0.dylib",
    "libgmodule-2.0.so.0": "libgmodule-2.0.0.dylib",
    "libpango-1.0-0": "libpango-1.0.0.dylib",
    "pango-1.0-0": "libpango-1.0.0.dylib",
    "pango-1.0": "libpango-1.0.0.dylib",
    "libpango-1.0.dylib": "libpango-1.0.0.dylib",
    "libpango-1.0.so.0": "libpango-1.0.0.dylib",
    "libpangoft2-1.0-0": "libpangoft2-1.0.0.dylib",
    "pangoft2-1.0-0": "libpangoft2-1.0.0.dylib",
    "pangoft2-1.0": "libpangoft2-1.0.0.dylib",
    "libpangoft2-1.0.dylib": "libpangoft2-1.0.0.dylib",
    "libpangoft2-1.0.so.0": "libpangoft2-1.0.0.dylib",
    "libfontconfig-1": "libfontconfig.1.dylib",
    "fontconfig-1": "libfontconfig.1.dylib",
    "fontconfig": "libfontconfig.1.dylib",
    "libfontconfig.so.1": "libfontconfig.1.dylib",
    "libharfbuzz-0": "libharfbuzz.0.dylib",
    "harfbuzz": "libharfbuzz.0.dylib",
    "harfbuzz-0.0": "libharfbuzz.0.dylib",
    "libharfbuzz.so.0": "libharfbuzz.0.dylib",
    "libharfbuzz-subset-0": "libharfbuzz-subset.0.dylib",
    "harfbuzz-subset": "libharfbuzz-subset.0.dylib",
    "harfbuzz-subset-0.0": "libharfbuzz-subset.0.dylib",
    "libharfbuzz-subset.dylib": "libharfbuzz-subset.0.dylib",
    "libharfbuzz-subset.so.0": "libharfbuzz-subset.0.dylib",
}

OPTIONAL_FRAMEWORKS = {
    "libharfbuzz-subset.0.dylib": Path("/opt/homebrew/lib/libharfbuzz-subset.0.dylib"),
}

SYSTEM_DEPENDENCY_PREFIXES = ("/System/Library/", "/usr/lib/")
HOMEBREW_DEPENDENCY_PREFIXES = ("/opt/homebrew/", "/usr/local/")
SYSTEM_LIBRARY_OVERRIDES = {
    "libiconv.2.dylib": "/usr/lib/libiconv.2.dylib",
}


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def framework_path(bundle_path: Path) -> Path:
    return bundle_path / "Contents" / "Frameworks"


def resources_path(bundle_path: Path) -> Path:
    return bundle_path / "Contents" / "Resources"


def macos_path(bundle_path: Path) -> Path:
    return bundle_path / "Contents" / "MacOS"


def ensure_optional_frameworks(frameworks_dir: Path) -> None:
    frameworks_dir.mkdir(parents=True, exist_ok=True)

    for name, source in OPTIONAL_FRAMEWORKS.items():
        destination = frameworks_dir / name
        if destination.exists() or not source.exists():
            continue
        shutil.copy2(source, destination)


def patch_framework_install_names(frameworks_dir: Path) -> None:
    for library in frameworks_dir.glob("*.dylib"):
        run(
            [
                "install_name_tool",
                "-id",
                f"@executable_path/../Frameworks/{library.name}",
                str(library),
            ]
        )

def collect_bundle_binaries(bundle_path: Path) -> list[Path]:
    binaries: list[Path] = []

    for path in framework_path(bundle_path).glob("*.dylib"):
        binaries.append(path)

    for path in macos_path(bundle_path).glob("*"):
        if path.is_file():
            binaries.append(path)

    return binaries


def patch_bundle_dependency_references(bundle_path: Path, frameworks_dir: Path) -> None:
    for binary_path in collect_bundle_binaries(bundle_path):
        output = subprocess.check_output(["otool", "-L", str(binary_path)], text=True)
        for line in output.splitlines()[1:]:
            dependency = line.strip().split(" (compatibility")[0]
            dependency_name = Path(dependency).name

            if dependency_name in SYSTEM_LIBRARY_OVERRIDES and dependency != SYSTEM_LIBRARY_OVERRIDES[dependency_name]:
                run(
                    [
                        "install_name_tool",
                        "-change",
                        dependency,
                        SYSTEM_LIBRARY_OVERRIDES[dependency_name],
                        str(binary_path),
                    ]
                )
                continue

            if dependency.startswith(SYSTEM_DEPENDENCY_PREFIXES):
                continue
            if not dependency.startswith(HOMEBREW_DEPENDENCY_PREFIXES):
                continue

            replacement = frameworks_dir / dependency_name
            if replacement.exists():
                run(
                    [
                        "install_name_tool",
                        "-change",
                        dependency,
                        f"@executable_path/../Frameworks/{replacement.name}",
                        str(binary_path),
                    ]
                )


def ensure_framework_aliases(frameworks_dir: Path) -> None:
    for alias_name, target_name in APPLE_SILICON_FRAMEWORK_ALIASES.items():
        alias_path = frameworks_dir / alias_name
        target_path = frameworks_dir / target_name

        if alias_path.exists() or not target_path.exists():
            continue

        alias_path.symlink_to(target_name)


def copy_fontconfig(bundle_path: Path) -> None:
    source_dir = Path("/opt/homebrew/etc/fonts")
    if not source_dir.exists():
        return

    destination_dir = resources_path(bundle_path) / "etc" / "fonts"
    destination_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, destination_dir, dirs_exist_ok=True)

    fonts_conf = destination_dir / "fonts.conf"
    if not fonts_conf.exists():
        return

    contents = fonts_conf.read_text(encoding="utf-8")
    contents = contents.replace("\t<cachedir>/opt/homebrew/var/cache/fontconfig</cachedir>\n", "")
    contents = contents.replace("  <cachedir>/opt/homebrew/var/cache/fontconfig</cachedir>\n", "")
    fonts_conf.write_text(contents, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: postprocess_distribution_bundle.py /path/to/md2pdf-converter.app")

    bundle_path = Path(sys.argv[1]).resolve()
    frameworks_dir = framework_path(bundle_path)

    ensure_optional_frameworks(frameworks_dir)
    patch_framework_install_names(frameworks_dir)
    patch_bundle_dependency_references(bundle_path, frameworks_dir)
    ensure_framework_aliases(frameworks_dir)
    copy_fontconfig(bundle_path)


if __name__ == "__main__":
    main()
