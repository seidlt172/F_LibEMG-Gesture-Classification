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
WIDGET_EVENT_TYPES = ("scenario_start", "step_update", "trial_completed")


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


def decision_for_step(task_id: str | None, decision: str, intent_result: dict[str, Any]) -> str:
    """Normalize a semantic intent decision for the currently active widget step."""
    normalized = coerce_decision(decision)
    task_id = (task_id or "").strip()
    target = (intent_result.get("target") or "").strip().lower()
    intent = (intent_result.get("intent") or "").strip().lower()
    action = (intent_result.get("action") or "").strip().lower()

    if task_id == "CALL-INCOMING" and target == "call":
        if intent in {"accept_call"} or action in {"accept", "confirm"}:
            return "execute"
        if intent in {"reject_call"} or action in {"reject", "cancel"}:
            return "cancel"

    if task_id == "CALL-ACTIVE" and target == "call":
        if intent in {"end_call", "reject_call"} or action in {"close", "reject", "cancel"}:
            return "execute"

    if task_id == "CALL-VOLUME" and target in {"call", "volume"}:
        if intent in {"adjust_volume"} or action in {"increase", "decrease", "set"}:
            return "execute"

    if task_id == "CALL-ENDED":
        return "execute"
    return normalized


def build_widget_payload(
    *,
    intent_result: dict[str, Any],
    study_context: dict[str, Any],
    voice_event: dict[str, Any] | None = None,
    gesture_event: dict[str, Any] | None = None,
    step_index: int = 0,
    step_count: int = 0,
    step: Any | None = None,
    trial_id: str | None = None,
    domain: str | None = None,
    used_modalities: str | None = None,
    event_type: str = "step_update",
    decision_override: str | None = None,
) -> dict[str, Any]:
    decision = coerce_decision(decision_override) if decision_override else decision_from_intent_result(intent_result)
    scenario_id = study_context.get("scenario_id", "")
    study_ref = (
        study_context.get("study_ref")
        or study_context.get("scenario_ref")
        or scenario_id
    )
    payload = {
        "event_type": event_type if event_type in WIDGET_EVENT_TYPES else "step_update",
        "trial_id": trial_id or study_context.get("trial_id", ""),
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
        "step_count": int(step_count),
        "domain": domain or _step_value(step, "domain") or _domain_from_target(intent_result.get("target")),
        "source": {
            "voice_event": voice_event,
            "gesture_event": gesture_event,
            "used_modalities": used_modalities
            or intent_result.get("used_modalities")
            or "none",
        },
    }
    payload.update(_step_payload(step))
    return payload


def build_scenario_start_payload(
    *,
    study_context: dict[str, Any],
    step: Any | None = None,
    step_index: int = 0,
    step_count: int = 0,
    trial_id: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    scenario_id = study_context.get("scenario_id", "")
    study_ref = (
        study_context.get("study_ref")
        or study_context.get("scenario_ref")
        or scenario_id
    )
    payload = {
        "event_type": "scenario_start",
        "trial_id": trial_id or study_context.get("trial_id", ""),
        "condition": study_context.get("condition", ""),
        "category": study_context.get("category", ""),
        "scenario_id": scenario_id,
        "study_ref": study_ref,
        "scenario_prompt": study_context.get("scenario_prompt", ""),
        "step_index": int(step_index),
        "step_count": int(step_count),
        "domain": domain or _step_value(step, "domain") or "unknown",
    }
    payload.update(_step_payload(step))
    return payload


def build_trial_completed_payload(
    *,
    intent_result: dict[str, Any],
    study_context: dict[str, Any],
    step: Any | None = None,
    step_index: int = 0,
    step_count: int = 0,
    trial_id: str | None = None,
    success: bool = True,
    decision_override: str | None = None,
    voice_event: dict[str, Any] | None = None,
    gesture_event: dict[str, Any] | None = None,
    used_modalities: str | None = None,
) -> dict[str, Any]:
    if decision_override is None and _step_value(step, "task_id") == "CALL-ENDED":
        decision_override = "execute"
    payload = build_widget_payload(
        intent_result=intent_result,
        study_context=study_context,
        voice_event=voice_event,
        gesture_event=gesture_event,
        step=step,
        step_index=step_index,
        step_count=step_count,
        trial_id=trial_id,
        used_modalities=used_modalities,
        event_type="trial_completed",
        decision_override=decision_override,
    )
    payload["success"] = bool(success)
    return payload


def _step_payload(step: Any | None) -> dict[str, Any]:
    if step is None:
        return {}
    return {
        "task_id": _step_value(step, "task_id"),
        "prompt": _step_value(step, "prompt"),
        "overlay_title": _step_value(step, "overlay_title"),
        "overlay_body": _step_value(step, "overlay_body"),
        "modality": _step_value(step, "modality"),
        "expected_decision": _step_value(step, "expected_status"),
        "expected_voice": _step_value(step, "voice_input"),
        "expected_gesture": _step_value(step, "gesture_label"),
        "gesture_ref": _step_value(step, "gesture_ref"),
        "accepted_text": _step_value(step, "accepted_text"),
        "rejected_text": _step_value(step, "rejected_text"),
        "unclear_text": _step_value(step, "unclear_text"),
    }


def _step_value(step: Any | None, name: str) -> Any:
    if step is None:
        return ""
    if isinstance(step, dict):
        return step.get(name, "")
    return getattr(step, name, "")


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
