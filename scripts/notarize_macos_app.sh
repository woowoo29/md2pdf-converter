#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_PATH="${PROJECT_DIR}/dist/md2pdf-converter.app"
DMG_PATH="${PROJECT_DIR}/dist/md2pdf-converter-unsigned.dmg"
DMG_ROOT="${PROJECT_DIR}/dist/notary-dmg-root"
PROFILE="${APPLE_NOTARY_PROFILE:-${1:-}}"

if [ -z "$PROFILE" ]; then
  echo "Usage: APPLE_NOTARY_PROFILE='NotaryToolProfile' bash scripts/notarize_macos_app.sh" >&2
  exit 1
fi

if [ ! -d "$APP_PATH" ]; then
  echo "Signed app bundle not found: $APP_PATH" >&2
  echo "Run 'bash scripts/build_macos_app.sh' and then sign the dist app first." >&2
  exit 1
fi

rm -rf "$DMG_ROOT"
mkdir -p "$DMG_ROOT"
cp -R "$APP_PATH" "$DMG_ROOT/"
ln -s /Applications "$DMG_ROOT/Applications"
rm -f "$DMG_PATH"

hdiutil create \
  -volname "md2pdf-converter" \
  -srcfolder "$DMG_ROOT" \
  -ov \
  -format UDZO \
  "$DMG_PATH"

rm -rf "$DMG_ROOT"

xcrun notarytool submit "$DMG_PATH" --keychain-profile "$PROFILE" --wait
xcrun stapler staple "$APP_PATH"
xcrun stapler staple "$DMG_PATH"
spctl --assess --type execute --verbose=4 "$APP_PATH"

echo "Notarized and stapled:"
echo "  $APP_PATH"
echo "  $DMG_PATH"
