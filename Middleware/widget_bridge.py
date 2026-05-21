"""Bridge normalized middleware decisions to participant-facing widgets."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import urllib.error
import urllib.request
from typing import Any


DEFAULT_WIDGET_URL = "http://127.0.0.1:8765/widget-event"
DEFAULT_TIMEOUT = 2.0

DECISIONS = ("execute", "cancel", "clarify")
LEGACY_STATUS_BY_DECISION = {
    "execute": "accepted",
    "cancel": "rejected",
    "clarify": "unclear",
}
DECISION_BY_LEGACY_STATUS = {
    "accepted": "execute",
    "rejected": "cancel",
    "unclear": "clarify",
}
EXECUTE_ACTIONS = {
    "accept",
    "confirm",
    "open",
    "close",
    "increase",
    "decrease",
    "select",
    "skip",
    "resume",
    "set",
}
CANCEL_ACTIONS = {"reject", "cancel"}


@dataclass(frozen=True)
class WidgetBridgeResult:
    sent: bool
    error: str = ""
    response_status: int | None = None


def coerce_decision(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if normalized in DECISIONS:
        return normalized
    if normalized in DECISION_BY_LEGACY_STATUS:
        return DECISION_BY_LEGACY_STATUS[normalized]
    return "clarify"


def legacy_status_from_decision(decision: str | None) -> str:
    return LEGACY_STATUS_BY_DECISION[coerce_decision(decision)]


def decision_from_intent_result(result: dict[str, Any]) -> str:
    if not isinstance(result, dict):
        return "clarify"
    if result.get("needs_clarification") or result.get("intent") == "unknown":
        return "clarify"

    action = (result.get("action") or "").strip().lower()
    if action in CANCEL_ACTIONS:
        return "cancel"
    if action in EXECUTE_ACTIONS:
        return "execute"
    return "clarify"


def build_widget_payload(
    *,
    intent_result: dict[str, Any],
    study_context: dict[str, Any],
    voice_event: dict[str, Any] | None = None,
    gesture_event: dict[str, Any] | None = None,
    step_index: int = 0,
    domain: str | None = None,
    used_modalities: str | None = None,
) -> dict[str, Any]:
    decision = decision_from_intent_result(intent_result)
    scenario_id = study_context.get("scenario_id", "")
    study_ref = (
        study_context.get("study_ref")
        or study_context.get("scenario_ref")
        or scenario_id
    )
    payload = {
        "decision": decision,
        "status": legacy_status_from_decision(decision),
        "intent": intent_result.get("intent", "unknown"),
        "action": intent_result.get("action", "unknown"),
        "target": intent_result.get("target", "unknown"),
        "value": intent_result.get("value"),
        "needs_clarification": bool(intent_result.get("needs_clarification")),
        "clarification": intent_result.get("clarification") or "",
        "condition": study_context.get("condition", ""),
        "category": study_context.get("category", ""),
        "scenario_id": scenario_id,
        "study_ref": study_ref,
        "scenario_prompt": study_context.get("scenario_prompt", ""),
        "step_index": int(step_index),
        "domain": domain or _domain_from_target(intent_result.get("target")),
        "source": {
            "voice_event": voice_event,
            "gesture_event": gesture_event,
            "used_modalities": used_modalities
            or intent_result.get("used_modalities")
            or "none",
        },
    }
    return payload


def _domain_from_target(target: str | None) -> str:
    value = (target or "").strip().lower()
    if value == "call":
        return "calls"
    if value in {"media", "volume"}:
        return "audio"
    if value == "message":
        return "messages"
    if value in {"route", "navigation"}:
        return "navigation"
    if value == "ambient_light":
        return "ambient_light"
    if value == "seat_heating":
        return "climate"
    return "unknown"


class WidgetBridgeClient:
    """Small local HTTP client for sending widget decision payloads."""

    def __init__(self, url: str | None = None, timeout: float | None = None):
        self.url = (url or os.environ.get("WIDGET_BRIDGE_URL") or DEFAULT_WIDGET_URL).strip()
        timeout_raw = (
            str(timeout)
            if timeout is not None
            else os.environ.get("WIDGET_BRIDGE_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT))
        )
        try:
            self.timeout = float(timeout_raw)
        except ValueError:
            self.timeout = DEFAULT_TIMEOUT

    def send(self, payload: dict[str, Any]) -> WidgetBridgeResult:
        if not self.url:
            return WidgetBridgeResult(sent=False, error="Widget bridge URL is empty.")
        try:
            return self._post_json(payload)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return WidgetBridgeResult(sent=False, error=str(exc))

    def _post_json(self, payload: dict[str, Any]) -> WidgetBridgeResult:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            response.read()
            return WidgetBridgeResult(sent=True, response_status=response.status)
