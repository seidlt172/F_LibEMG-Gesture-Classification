#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/.logs/local-stack"
PID_DIR="$LOG_DIR/pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
NPM_BIN="${NPM_BIN:-npm}"
OLLAMA_BIN="${OLLAMA_BIN:-ollama}"

START_GUI="${START_GUI:-1}"
START_OLLAMA="${START_OLLAMA:-1}"
START_WIDGET_SERVER="${START_WIDGET_SERVER:-1}"
START_REACT="${START_REACT:-1}"
START_MINDROVE="${START_MINDROVE:-0}"

is_port_open() {
  local port="$1"
  lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
}

start_process() {
  local name="$1"
  local workdir="$2"
  local command="$3"
  local logfile="$LOG_DIR/${name}.log"
  local pidfile="$PID_DIR/${name}.pid"

  if [[ -f "$pidfile" ]]; then
    local existing_pid
    existing_pid="$(cat "$pidfile")"
    if kill -0 "$existing_pid" >/dev/null 2>&1; then
      echo "$name already running with PID $existing_pid"
      return
    fi
    rm -f "$pidfile"
  fi

  cd "$workdir"
  nohup bash -lc "$command" >"$logfile" 2>&1 &
  local child_pid=$!
  echo "$child_pid" >"$pidfile"
  cd "$ROOT_DIR"

  echo "Started $name (PID $child_pid)"
}

if [[ "$START_OLLAMA" == "1" ]]; then
  if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "ollama already reachable on 127.0.0.1:11434"
  else
    start_process "ollama" "$ROOT_DIR" "$OLLAMA_BIN serve"
  fi
fi

if [[ "$START_WIDGET_SERVER" == "1" ]]; then
  if is_port_open 8765; then
    echo "widget_event_server already listening on 8765"
  else
    start_process "widget_event_server" "$ROOT_DIR" "$PYTHON_BIN -m Middleware.widget_event_server"
  fi
fi

if [[ "$START_REACT" == "1" ]]; then
  if is_port_open 5173; then
    echo "react frontend already listening on 5173"
  else
    start_process "react_vite" "$ROOT_DIR/car_widgets_react" "$NPM_BIN run dev"
  fi
fi

if [[ "$START_MINDROVE" == "1" ]]; then
  start_process "mindrove_streamer" "$ROOT_DIR" "$PYTHON_BIN scripts/mindrove_streamer.py"
fi

if [[ "$START_GUI" == "1" ]]; then
  start_process "gesture_gui" "$ROOT_DIR" "$PYTHON_BIN gesture_gui.py"
fi

echo
echo "Stack status:"
echo "- React frontend:      http://127.0.0.1:5173"
echo "- Widget event server: http://127.0.0.1:8765/latest"
echo "- Ollama API:          http://127.0.0.1:11434/api/tags"
echo
echo "Logs:"
echo "- $LOG_DIR"
echo
echo "Hint:"
echo "- For real EMG prediction you still need a trained model at models/clf."
echo "- Enable hardware streaming with START_MINDROVE=1 if the armband is connected."
