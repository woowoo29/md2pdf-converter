#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_URL="http://127.0.0.1:8000"
HEALTH_URL="$APP_URL/healthz"

is_md2pdf_running() {
  curl -fs "$HEALTH_URL" 2>/dev/null | grep -q '"status":"ok"\|"status": "ok"'
}

stop_listener_processes() {
  local listener_pids="$1"
  local remaining_pids

  if [ -z "$listener_pids" ]; then
    return 0
  fi

  kill $listener_pids >/dev/null 2>&1 || true

  for _ in 1 2 3 4 5; do
    sleep 1
    if ! lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
      return 0
    fi
  done

  remaining_pids="$(lsof -tiTCP:8000 -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "$remaining_pids" ]; then
    kill -9 $remaining_pids >/dev/null 2>&1 || true
  fi
}

describe_listener() {
  local listener_pids="$1"
  if [ -z "$listener_pids" ]; then
    return
  fi

  ps -o command= -p $listener_pids 2>/dev/null | sed '/^$/d' | head -n 3
}

confirm_restart_existing_server() {
  local listener_pids="$1"
  local description message button

  description="$(describe_listener "$listener_pids")"
  message="127.0.0.1:8000 포트가 이미 다른 로컬 서버에서 사용 중입니다."
  if [ -n "$description" ]; then
    message="$message\n\n현재 프로세스:\n$description"
  fi
  message="$message\n\n기존 서버를 종료하고 md2pdf-converter를 실행할까요?"

  if button="$(MESSAGE="$message" osascript 2>/dev/null <<'EOF'
set dialogMessage to system attribute "MESSAGE"
button returned of (display dialog dialogMessage with title "md2pdf-converter" buttons {"아니요", "예"} default button "예" with icon caution)
EOF
)"; then
    [ "$button" = "예" ]
    return
  fi

  printf '%b\n' "$message"
  printf '기존 서버를 종료하고 실행할까요? [y/N]: '
  read -r answer || true

  case "$answer" in
    [Yy]|[Yy][Ee][Ss]|"예")
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

if is_md2pdf_running; then
  open "$APP_URL"
  exit 0
fi

if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  listener_pids="$(lsof -tiTCP:8000 -sTCP:LISTEN 2>/dev/null || true)"
  if confirm_restart_existing_server "$listener_pids"; then
    stop_listener_processes "$listener_pids"
  else
    exit 0
  fi
fi

cd "$SCRIPT_DIR"

# Give the local server a moment to boot before opening the browser.
(sleep 2; open "$APP_URL") >/dev/null 2>&1 &

exec bash "$SCRIPT_DIR/run.sh"
