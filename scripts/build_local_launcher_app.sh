#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_NAME="md2pdf-converter.app"
APP_DIR="$PROJECT_DIR/$APP_NAME"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
ICON_SOURCE="$PROJECT_DIR/assets/icon/md2pdf-converter.icns"
FALLBACK_ICON="$PROJECT_DIR/dist/md2pdf-converter.app/Contents/Resources/PythonApplet.icns"
ICON_NAME="md2pdf-converter.icns"

rm -rf "$APP_DIR"
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

cat >"$MACOS_DIR/md2pdf-converter" <<'EOF'
#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PYTHON_BIN=""

if [ -x "$PROJECT_DIR/.venv-desktop-build313/bin/python" ]; then
  PYTHON_BIN="$PROJECT_DIR/.venv-desktop-build313/bin/python"
elif [ -x "$PROJECT_DIR/.venv-desktop-build/bin/python" ]; then
  PYTHON_BIN="$PROJECT_DIR/.venv-desktop-build/bin/python"
elif [ -x "$PROJECT_DIR/.venv/bin/python" ]; then
  PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
fi

if [ ! -d "$PROJECT_DIR/app" ] || [ ! -d "$PROJECT_DIR/desktop" ]; then
  osascript -e 'display alert "md2pdf-converter" message "프로젝트 소스 폴더를 찾을 수 없어 앱을 실행할 수 없습니다." as critical'
  exit 1
fi

cd "$PROJECT_DIR"

if [ -n "$PYTHON_BIN" ]; then
  "$PYTHON_BIN" -m desktop "$@" >/tmp/md2pdf-desktop.log 2>&1 &
  DESKTOP_PID=$!

  sleep 2

  if kill -0 "$DESKTOP_PID" >/dev/null 2>&1; then
    wait "$DESKTOP_PID"
    exit $?
  fi
fi

if [ -f "$PROJECT_DIR/launch_md2pdf.command" ]; then
  exec bash "$PROJECT_DIR/launch_md2pdf.command"
fi

osascript -e 'display alert "md2pdf-converter" message "앱 실행에 실패했고 브라우저 fallback도 찾지 못했습니다." as critical'
exit 1
EOF

chmod +x "$MACOS_DIR/md2pdf-converter"

cat >"$CONTENTS_DIR/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "https://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>English</string>
  <key>CFBundleDisplayName</key>
  <string>md2pdf-converter</string>
  <key>CFBundleExecutable</key>
  <string>md2pdf-converter</string>
  <key>CFBundleIdentifier</key>
  <string>com.woowoo29.md2pdf-converter.local-launcher</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>md2pdf-converter</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>3.1.0</string>
  <key>CFBundleVersion</key>
  <string>3.1.0</string>
  <key>LSMinimumSystemVersion</key>
  <string>13.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>CFBundleDocumentTypes</key>
  <array>
    <dict>
      <key>CFBundleTypeExtensions</key>
      <array>
        <string>md</string>
        <string>markdown</string>
      </array>
      <key>CFBundleTypeName</key>
      <string>Markdown Document</string>
      <key>CFBundleTypeRole</key>
      <string>Viewer</string>
      <key>LSHandlerRank</key>
      <string>Owner</string>
    </dict>
  </array>
</dict>
</plist>
EOF

if [ -f "$ICON_SOURCE" ]; then
  cp "$ICON_SOURCE" "$RESOURCES_DIR/$ICON_NAME"
  /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string $ICON_NAME" "$CONTENTS_DIR/Info.plist" >/dev/null 2>&1 || \
    /usr/libexec/PlistBuddy -c "Set :CFBundleIconFile $ICON_NAME" "$CONTENTS_DIR/Info.plist" >/dev/null 2>&1
elif [ -f "$FALLBACK_ICON" ]; then
  cp "$FALLBACK_ICON" "$RESOURCES_DIR/$ICON_NAME"
  /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string $ICON_NAME" "$CONTENTS_DIR/Info.plist" >/dev/null 2>&1 || \
    /usr/libexec/PlistBuddy -c "Set :CFBundleIconFile $ICON_NAME" "$CONTENTS_DIR/Info.plist" >/dev/null 2>&1
fi

echo "Built local launcher app at $APP_DIR"
