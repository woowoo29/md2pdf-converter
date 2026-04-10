#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REQUIRED_FILES = (
    "Contents/Frameworks/libpango-1.0.dylib",
    "Contents/Frameworks/libpangoft2-1.0.dylib",
    "Contents/Frameworks/libharfbuzz-subset.0.dylib",
    "Contents/Resources/etc/fonts/fonts.conf",
)
FORBIDDEN_DEPENDENCY_PREFIXES = ("/opt/homebrew/", "/usr/local/")


def collect_binary_files(bundle_path: Path) -> list[Path]:
    binaries: list[Path] = []

    for path in bundle_path.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix in {".dylib", ".so"} or ".so." in path.name:
            binaries.append(path)

    macos_dir = bundle_path / "Contents" / "MacOS"
    if macos_dir.exists():
        for path in macos_dir.iterdir():
            if path.is_file():
                binaries.append(path)

    return binaries


def verify_required_files(bundle_path: Path) -> list[str]:
    errors: list[str] = []
    for relative_path in REQUIRED_FILES:
        if not (bundle_path / relative_path).exists():
            errors.append(f"Missing required bundled file: {relative_path}")
    return errors


def verify_no_external_library_refs(bundle_path: Path) -> list[str]:
    errors: list[str] = []
    for binary_path in collect_binary_files(bundle_path):
        try:
            output = subprocess.check_output(["otool", "-L", str(binary_path)], text=True)
        except subprocess.CalledProcessError as exc:
            errors.append(f"Failed to inspect dependencies for {binary_path}: {exc}")
            continue

        for line in output.splitlines()[1:]:
            dependency = line.strip().split(" (compatibility")[0]
            if dependency.startswith(FORBIDDEN_DEPENDENCY_PREFIXES):
                errors.append(f"{binary_path} still depends on external library {dependency}")

    return errors


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify_distribution_bundle.py /path/to/md2pdf-converter.app")

    bundle_path = Path(sys.argv[1]).resolve()
    errors = [
        *verify_required_files(bundle_path),
        *verify_no_external_library_refs(bundle_path),
    ]

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)

    print(f"Verified distribution bundle: {bundle_path}")


if __name__ == "__main__":
    main()
