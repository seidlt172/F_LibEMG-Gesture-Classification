"""Feedback mapping between middleware decisions and widget state changes."""

from __future__ import annotations

from typing import Any

from .scenarios import StudyScenario
from .state import CarState
from .state import advance_step_or_complete


DECISIONS = ("execute", "cancel", "clarify")
LEGACY_STATUS_TO_DECISION = {
    "accepted": "execute",
    "rejected": "cancel",
    "unclear": "clarify",
}
DECISION_TO_LEGACY_STATUS = {
    "execute": "accepted",
    "cancel": "rejected",
    "clarify": "unclear",
}
ACCEPT_ACTIONS = {"accept", "confirm", "open", "resume", "select", "increase", "set", "skip", "close", "decrease"}
REJECT_ACTIONS = {"reject"}


def coerce_decision(value: str | None) -> str:
    value = (value or "").strip().lower()
    if value in DECISIONS:
        return value
    if value in LEGACY_STATUS_TO_DECISION:
        return LEGACY_STATUS_TO_DECISION[value]
    return "clarify"


def coerce_status(value: str | None) -> str:
    """Compatibility wrapper for older accepted/rejected/unclear payloads."""
    return DECISION_TO_LEGACY_STATUS[coerce_decision(value)]


def decision_from_intent_result(result: dict[str, Any]) -> str:
    if result.get("needs_clarification") or result.get("intent") == "unknown":
        return "clarify"
    action = (result.get("action") or "").strip().lower()
    if action in REJECT_ACTIONS:
        return "cancel"
    if action in ACCEPT_ACTIONS:
        return "execute"
    return "clarify"


def status_from_intent_result(result: dict[str, Any]) -> str:
    """Compatibility wrapper for older callers."""
    return DECISION_TO_LEGACY_STATUS[decision_from_intent_result(result)]


def build_payload(
    *,
    condition: str,
    scenario: StudyScenario,
    decision: str | None = None,
    status: str | None = None,
    intent: str = "",
    action: str = "",
    target: str = "",
    value: str | None = None,
    clarification: str | None = None,
) -> dict[str, Any]:
    normalized_decision = coerce_decision(decision or status)
    return {
        "condition": condition,
        "scenario_id": scenario.scenario_id,
        "study_ref": scenario.study_ref,
        "domain": scenario.domain,
        "decision": normalized_decision,
        "status": DECISION_TO_LEGACY_STATUS[normalized_decision],
        "intent": intent,
        "action": action,
        "target": target,
        "value": value,
        "clarification": clarification or "",
    }


def payload_from_intent_result(
    *,
    condition: str,
    scenario: StudyScenario,
    result: dict[str, Any],
) -> dict[str, Any]:
    return build_payload(
        condition=condition,
        scenario=scenario,
        decision=decision_from_intent_result(result),
        intent=result.get("intent", ""),
        action=result.get("action", ""),
        target=result.get("target", ""),
        value=result.get("value"),
        clarification=result.get("clarification") or "",
    )


def apply_feedback(state: CarState, payload: dict[str, Any]) -> CarState:
    scenario = state.active_scenario
    step = state.current_step()
    decision = coerce_decision(payload.get("decision") or payload.get("status"))
    state.feedback_status = decision

    if scenario is None or step is None:
        state.feedback_text = "Keine aktive Aufgabe."
        state.log("Feedback ohne aktive Aufgabe ignoriert.")
        return state

    if decision == "clarify":
        state.overlay_visible = True
        state.clarification_text = payload.get("clarification") or step.unclear_text
        state.feedback_text = f"Eingabe unklar: {state.clarification_text}"
        state.log(f"Unklar: {scenario.study_ref} Schritt {state.current_step_index + 1}.")
        return state

    state.clarification_text = ""
    if decision == "execute":
        _apply_accepted(state, step.task_id)
        state.feedback_text = step.accepted_text
        state.log(f"Ausgefuehrt: {scenario.study_ref} Schritt {state.current_step_index + 1}.")
    else:
        _apply_rejected(state, step.task_id)
        state.feedback_text = step.rejected_text
        state.log(f"Abgebrochen: {scenario.study_ref} Schritt {state.current_step_index + 1}.")

    advance_step_or_complete(state)
    return state


def _apply_accepted(state: CarState, task_id: str) -> None:
    if task_id == "CALL-INCOMING":
        state.call_incoming = False
        state.call_active = True
    elif task_id == "CALL-END":
        state.call_active = False
    elif task_id == "CALL-VOLUME":
        state.volume = min(100, state.volume + 10)
    elif task_id == "AUDIO-SUGGESTION":
        state.audio_track = "Night Drive"
        state.audio_playing = True
    elif task_id == "AUDIO-NEXT":
        state.audio_track = "City Lights"
        state.audio_playing = True
    elif task_id == "AUDIO-LOUDER":
        state.volume = min(100, state.volume + 12)
    elif task_id == "AUDIO-RESUME":
        state.audio_playing = True
    elif task_id == "MESSAGE-OPEN":
        state.message_available = True
        state.message_open = True
    elif task_id == "MESSAGE-CLOSE":
        state.message_open = False
    elif task_id == "NAV-ACCEPT-ROUTE":
        state.route_selected = True
        state.route_suggestion_visible = False
    elif task_id == "NAV-NEXT-ROUTE":
        state.route_index = 2 if state.route_index == 1 else 1
        state.route_suggestion_visible = True
    elif task_id == "NAV-SELECT-SECOND":
        state.route_index = 2
        state.route_selected = True
        state.route_suggestion_visible = False
    elif task_id == "NAV-VOLUME-UP":
        state.nav_volume = min(100, state.nav_volume + 15)
    elif task_id == "AMBIENT-COLOR":
        state.ambient_color = "Warm"
    elif task_id == "AMBIENT-BRIGHTER":
        state.ambient_brightness = min(100, state.ambient_brightness + 20)
    elif task_id == "AMBIENT-NIGHTMODE":
        state.night_mode = True
        state.ambient_color = "Warm"
    elif task_id == "CLIMATE-SEAT-HEAT":
        state.seat_heating_selected = True
    elif task_id == "CLIMATE-SEAT-WARMER":
        state.seat_heating_level = min(3, state.seat_heating_level + 1)


def _apply_rejected(state: CarState, task_id: str) -> None:
    if task_id == "CALL-INCOMING":
        state.call_incoming = False
        state.call_active = False
    elif task_id == "NAV-REJECT-ROUTE":
        state.route_selected = False
        state.route_suggestion_visible = False
    elif task_id == "MESSAGE-CLOSE":
        state.message_open = False
    elif task_id == "AUDIO-SUGGESTION":
        state.audio_track = "Low Beam"
    elif task_id == "AMBIENT-NIGHTMODE":
        state.night_mode = False
