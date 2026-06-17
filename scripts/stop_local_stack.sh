#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$ROOT_DIR/.logs/local-stack/pids"

if [[ ! -d "$PID_DIR" ]]; then
  echo "No PID directory found: $PID_DIR"
  exit 0
fi

shopt -s nullglob
for pidfile in "$PID_DIR"/*.pid; do
  name="$(basename "$pidfile" .pid)"
  pid="$(cat "$pidfile")"
  if kill -0 "$pid" >/dev/null 2>&1; then
    kill "$pid" >/dev/null 2>&1 || true
    echo "Stopped $name ($pid)"
  else
    echo "$name not running ($pid)"
  fi
  rm -f "$pidfile"
done
