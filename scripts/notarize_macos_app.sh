#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_PATH="${PROJECT_DIR}/md2pdf-converter.app"
DMG_PATH="${PROJECT_DIR}/dist/md2pdf-converter-unsigned.dmg"
PROFILE="${APPLE_NOTARY_PROFILE:-${1:-}}"

if [ -z "$PROFILE" ]; then
  echo "Usage: APPLE_NOTARY_PROFILE='NotaryToolProfile' bash scripts/notarize_macos_app.sh" >&2
  exit 1
fi

if [ ! -f "$DMG_PATH" ]; then
  echo "DMG not found: $DMG_PATH" >&2
  echo "Run 'bash scripts/build_macos_app.sh' first." >&2
  exit 1
fi

xcrun notarytool submit "$DMG_PATH" --keychain-profile "$PROFILE" --wait
xcrun stapler staple "$APP_PATH"
xcrun stapler staple "$DMG_PATH"
spctl --assess --type execute --verbose=4 "$APP_PATH"

echo "Notarized and stapled:"
echo "  $APP_PATH"
echo "  $DMG_PATH"
