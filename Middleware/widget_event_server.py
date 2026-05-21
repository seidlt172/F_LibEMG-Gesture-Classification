"""Local event bridge for browser-based car widgets.

The operator GUI posts widget payloads to /widget-event. A React frontend can
poll /latest to receive the most recent payload. This keeps React independent
from EMG, Whisper, and Ollama while preserving the existing middleware contract.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
import json
import os
import threading
from typing import Any


HOST = os.environ.get("WIDGET_EVENT_HOST", "127.0.0.1")
PORT = int(os.environ.get("WIDGET_EVENT_PORT", "8765"))


class EventStore:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.event_id = 0
        self.latest_payload: dict[str, Any] | None = None

    def set(self, payload: dict[str, Any]) -> int:
        with self.lock:
            self.event_id += 1
            self.latest_payload = payload
            return self.event_id

    def get(self) -> dict[str, Any]:
        with self.lock:
            return {
                "event_id": self.event_id,
                "payload": self.latest_payload,
            }


STORE = EventStore()


class WidgetEventHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self._send_empty(204)

    def do_GET(self) -> None:
        if self.path != "/latest":
            self.send_error(404)
            return
        self._send_json(STORE.get())

    def do_POST(self) -> None:
        if self.path != "/widget-event":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError("Payload must be a JSON object.")
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_error(400, str(exc))
            return

        event_id = STORE.set(payload)
        self._send_json({"received": True, "event_id": event_id}, status=202)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_empty(self, status: int) -> None:
        self.send_response(status)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), WidgetEventHandler)
    print(f"Widget event server listening on http://{HOST}:{PORT}")
    print("POST /widget-event receives middleware payloads.")
    print("GET  /latest returns the newest payload for React widgets.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
