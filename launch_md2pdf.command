#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_URL="http://127.0.0.1:8000"
HEALTH_URL="$APP_URL/healthz"

is_md2pdf_running() {
  curl -fs "$HEALTH_URL" 2>/dev/null | grep -q '"status":"ok"\|"status": "ok"'
}

restart_stale_md2pdf() {
  local listener_pids
  listener_pids="$(lsof -tiTCP:8000 -sTCP:LISTEN 2>/dev/null || true)"

  if [ -n "$listener_pids" ]; then
    kill $listener_pids >/dev/null 2>&1 || true
  fi

  pkill -f "uvicorn app.main:app" >/dev/null 2>&1 || true
  sleep 1
}

if is_md2pdf_running; then
  open "$APP_URL"
  exit 0
fi

if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  restart_stale_md2pdf
fi

cd "$SCRIPT_DIR"

# Give the local server a moment to boot before opening the browser.
(sleep 2; open "$APP_URL") >/dev/null 2>&1 &

exec bash "$SCRIPT_DIR/run.sh"
