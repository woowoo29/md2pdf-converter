#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_PATH="${1:-$PROJECT_DIR/dist/md2pdf-converter.app}"
IDENTITY="${APPLE_CODESIGN_IDENTITY:-${2:-}}"
ENTITLEMENTS_PATH="${APPLE_ENTITLEMENTS_PATH:-}"

if [ -z "$IDENTITY" ]; then
  echo "Usage: APPLE_CODESIGN_IDENTITY='Developer ID Application: Your Name (TEAMID)' bash scripts/sign_macos_app.sh" >&2
  exit 1
fi

if [ ! -d "$APP_PATH" ]; then
  echo "App bundle not found: $APP_PATH" >&2
  exit 1
fi

SIGN_ARGS=(
  --force
  --deep
  --options runtime
  --timestamp
  --sign "$IDENTITY"
)

if [ -n "$ENTITLEMENTS_PATH" ]; then
  SIGN_ARGS+=(--entitlements "$ENTITLEMENTS_PATH")
fi

codesign "${SIGN_ARGS[@]}" "$APP_PATH"
codesign --verify --deep --strict --verbose=2 "$APP_PATH"
spctl --assess --type execute --verbose=4 "$APP_PATH"

echo "Signed app bundle: $APP_PATH"
