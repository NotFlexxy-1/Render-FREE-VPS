#!/bin/bash
set -e

PORT="${PORT:-10000}"
CONSOLE_TOKEN="${CONSOLE_TOKEN:-}"

if [ -z "$CONSOLE_TOKEN" ] || [ "$CONSOLE_TOKEN" = "change-me" ]; then
  echo "ERROR: Set a strong CONSOLE_TOKEN in Render Environment Variables."
  exit 1
fi

mkdir -p /run/sshd

exec /opt/venv/bin/uvicorn server:app --host 0.0.0.0 --port "$PORT"
