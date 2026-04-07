#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

DYLD_LIBRARY_PATH=/opt/homebrew/lib uvicorn app.main:app --host 127.0.0.1 --reload --port 8000
