#!/bin/zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

(
  sleep 1
  open "http://127.0.0.1:8765"
) &

/usr/bin/env python3 internal_package/webui/server.py
