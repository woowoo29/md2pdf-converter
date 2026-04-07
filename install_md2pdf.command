#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="md2pdf-converter.app"
BUILD_SCRIPT="$SCRIPT_DIR/scripts/build_macos_app.sh"
SKIP_OPEN="${MD2PDF_INSTALL_SKIP_OPEN:-0}"

echo "----------------------------------------"
echo "md2pdf-converter installer"
echo "----------------------------------------"
echo

if [ ! -f "$BUILD_SCRIPT" ]; then
  echo "Build script not found: $BUILD_SCRIPT" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to build the app." >&2
  echo "Install Python 3 and try again." >&2
  exit 1
fi

if [ ! -f /opt/homebrew/lib/libpango-1.0.0.dylib ] && [ ! -f /usr/local/lib/libpango-1.0.0.dylib ]; then
  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew is required to install the macOS PDF rendering dependency (pango)." >&2
    echo "Install Homebrew from https://brew.sh and run this installer again." >&2
    exit 1
  fi

  echo "Installing Homebrew dependency: pango"
  brew install pango
fi

echo
echo "Building the desktop app bundle..."
bash "$BUILD_SCRIPT"

echo
echo "App created at: $SCRIPT_DIR/$APP_NAME"

if [ "$SKIP_OPEN" = "1" ]; then
  echo "Skipping automatic launch because MD2PDF_INSTALL_SKIP_OPEN=1"
  exit 0
fi

echo "Opening the app..."
open "$SCRIPT_DIR/$APP_NAME"
