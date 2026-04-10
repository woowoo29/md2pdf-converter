#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

library_paths=()

for candidate in /opt/homebrew/lib /usr/local/lib; do
  if [ -d "$candidate" ]; then
    library_paths+=("$candidate")
  fi
done

if [ ${#library_paths[@]} -gt 0 ]; then
  joined_library_paths="$(IFS=:; printf '%s' "${library_paths[*]}")"

  if [ -n "${DYLD_LIBRARY_PATH:-}" ]; then
    export DYLD_LIBRARY_PATH="$joined_library_paths:$DYLD_LIBRARY_PATH"
  else
    export DYLD_LIBRARY_PATH="$joined_library_paths"
  fi

  if [ -n "${DYLD_FALLBACK_LIBRARY_PATH:-}" ]; then
    export DYLD_FALLBACK_LIBRARY_PATH="$joined_library_paths:$DYLD_FALLBACK_LIBRARY_PATH"
  else
    export DYLD_FALLBACK_LIBRARY_PATH="$joined_library_paths"
  fi
fi

exec uvicorn app.main:app --host 127.0.0.1 --reload --port 8000
