#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

SOURCE_PNG="${1:-$PROJECT_DIR/assets/icon/source/md2pdf-icon-1024.png}"
OUTPUT_ICNS="${2:-$PROJECT_DIR/assets/icon/md2pdf-converter.icns}"
ICONSET_DIR="$PROJECT_DIR/assets/icon/md2pdf-converter.iconset"

if ! command -v sips >/dev/null 2>&1; then
  echo "sips is required to generate .icns files on macOS." >&2
  exit 1
fi

if ! command -v iconutil >/dev/null 2>&1; then
  echo "iconutil is required to generate .icns files on macOS." >&2
  exit 1
fi

if [ ! -f "$SOURCE_PNG" ]; then
  echo "Source PNG not found: $SOURCE_PNG" >&2
  echo "Export a 1024x1024 PNG from Figma to this path first." >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_ICNS")"
rm -rf "$ICONSET_DIR"
mkdir -p "$ICONSET_DIR"

create_icon() {
  local base_size="$1"
  local retina_size=$((base_size * 2))

  sips -z "$base_size" "$base_size" "$SOURCE_PNG" --out "$ICONSET_DIR/icon_${base_size}x${base_size}.png" >/dev/null
  sips -z "$retina_size" "$retina_size" "$SOURCE_PNG" --out "$ICONSET_DIR/icon_${base_size}x${base_size}@2x.png" >/dev/null
}

create_icon 16
create_icon 32
create_icon 128
create_icon 256
create_icon 512

iconutil -c icns "$ICONSET_DIR" -o "$OUTPUT_ICNS"
rm -rf "$ICONSET_DIR"

echo "Generated app icon at $OUTPUT_ICNS"
