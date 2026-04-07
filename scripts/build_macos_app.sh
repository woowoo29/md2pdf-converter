#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

APP_NAME="md2pdf-converter.app"
DMG_NAME="md2pdf-converter-unsigned.dmg"
DIST_DIR="$PROJECT_DIR/dist"
ROOT_APP_PATH="$PROJECT_DIR/$APP_NAME"
DMG_ROOT="$DIST_DIR/dmg-root"
DMG_PATH="$DIST_DIR/$DMG_NAME"
PIP_CACHE_DIR="$PROJECT_DIR/.pip-cache"
BUILD_VENV="$PROJECT_DIR/.venv-desktop-build"
BUILD_VENV_PY313="$PROJECT_DIR/.venv-desktop-build313"
ICON_SOURCE="$PROJECT_DIR/assets/icon/source/md2pdf-icon-1024.png"
ICON_ICNS="$PROJECT_DIR/assets/icon/md2pdf-converter.icns"
LOCAL_LAUNCHER_SCRIPT="$PROJECT_DIR/scripts/build_local_launcher_app.sh"

if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
  PYTHON_BIN="$VIRTUAL_ENV/bin/python"
else
  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required to create the desktop build environment." >&2
    exit 1
  fi

  if [ -x "$BUILD_VENV_PY313/bin/python" ]; then
    BUILD_VENV="$BUILD_VENV_PY313"
  fi

  if [ ! -x "$BUILD_VENV/bin/python" ]; then
    python3 -m venv "$BUILD_VENV"
  fi

  PYTHON_BIN="$BUILD_VENV/bin/python"
fi

echo "Using Python interpreter: $PYTHON_BIN"

PIP_CACHE_DIR="$PIP_CACHE_DIR" "$PYTHON_BIN" -m pip install -r requirements-desktop.txt

if [ -f "$ICON_SOURCE" ]; then
  bash "$PROJECT_DIR/scripts/build_icns.sh" "$ICON_SOURCE" "$ICON_ICNS"
fi

rm -rf build "$DIST_DIR"
PYTHON_BASE_LIB_DIR="$("$PYTHON_BIN" -c 'import sys; print(sys.base_prefix + "/lib")')"
BUILD_LIBRARY_PATH="/opt/homebrew/lib:$PYTHON_BASE_LIB_DIR"
DYLD_LIBRARY_PATH="$BUILD_LIBRARY_PATH" \
DYLD_FALLBACK_LIBRARY_PATH="$BUILD_LIBRARY_PATH" \
  "$PYTHON_BIN" setup.py py2app

# Re-sign the bundle after py2app assembles nested frameworks so Finder can launch it.
# Some bundled Homebrew dylibs may still trigger strict-validation warnings, but the
# app can remain launchable in local unsigned distribution mode.
if ! codesign --force --deep --sign - --timestamp=none "$DIST_DIR/$APP_NAME"; then
  echo "Warning: ad-hoc codesign reported validation issues; continuing with local unsigned bundle." >&2
fi

mkdir -p "$DMG_ROOT"
cp -R "$DIST_DIR/$APP_NAME" "$DMG_ROOT/"
ln -s /Applications "$DMG_ROOT/Applications"

rm -f "$DMG_PATH"
if ! hdiutil create \
  -volname "md2pdf-converter" \
  -srcfolder "$DMG_ROOT" \
  -ov \
  -format UDZO \
  "$DMG_PATH"; then
  echo "Warning: failed to build DMG; the app bundle is still available in dist/." >&2
fi

rm -rf "$DMG_ROOT"

rm -rf "$ROOT_APP_PATH"
if [ -x "$LOCAL_LAUNCHER_SCRIPT" ]; then
  bash "$LOCAL_LAUNCHER_SCRIPT"
else
  ditto "$DIST_DIR/$APP_NAME" "$ROOT_APP_PATH"
fi

rm -rf build

echo "Built local launcher app at $ROOT_APP_PATH"
echo "Built py2app bundle at $DIST_DIR/$APP_NAME"
if [ -f "$DMG_PATH" ]; then
  echo "Built unsigned DMG at $DMG_PATH"
fi
