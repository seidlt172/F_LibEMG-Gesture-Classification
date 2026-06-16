"""Study operator helpers for the EMG + voice pilot prototype."""

from __future__ import annotations

from datetime import datetime
from typing import Any


CONDITION_ORDERS = ("A", "B", "C")

def now_iso() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def make_trial_id(participant_id: str, trial_number: int) -> str:
    participant = (participant_id or "P000").strip() or "P000"
    return f"{participant}-T{trial_number:03d}"


def normalize_gesture_for_intent(gesture: str | None) -> str:
    gesture = (gesture or "").strip()
    if not gesture or gesture.lower() in {"none", "rest", "unknown"}:
        return ""
    return gesture


def filter_intent_inputs_for_condition(
    *,
    condition: str,
    transcript: str,
    gesture: str,
    gesture_source: str,
) -> dict[str, Any]:
    """Return the participant inputs that should be interpreted for a condition."""
    filtered_transcript = (transcript or "").strip()
    filtered_gesture = normalize_gesture_for_intent(gesture)
    filtered_source = (gesture_source or "none").strip() or "none"
    ignored_voice = False
    ignored_gesture = False

    if condition == "Voice only":
        ignored_gesture = bool(filtered_gesture)
        filtered_gesture = ""
        filtered_source = "none"
    elif condition == "Gesture only":
        ignored_voice = bool(filtered_transcript)
        filtered_transcript = ""
    elif condition != "CAN use both":
        condition = "Voice only"
        ignored_gesture = bool(filtered_gesture)
        filtered_gesture = ""
        filtered_source = "none"

    if not filtered_gesture:
        filtered_source = "none"

    return {
        "condition": condition,
        "transcript": filtered_transcript,
        "gesture": filtered_gesture,
        "gesture_source": filtered_source,
        "ignored_voice": ignored_voice,
        "ignored_gesture": ignored_gesture,
    }


def build_intent_context(
    *,
    base_context: str,
    condition: str,
    category: str,
    scenario_id: str,
    scenario_prompt: str,
    gesture_source: str,
    operator_gesture: str | None = None,
    current_task_id: str = "",
    current_prompt: str = "",
    expected_voice: str = "",
    current_domain: str = "",
) -> str:
    operator_note = ""
    if operator_gesture:
        operator_note = (
            f" Operator/Wizard gesture annotation: {operator_gesture}. "
            "Treat it as recovery support, not participant ground truth."
        )
    current_step_note = ""
    if current_task_id:
        current_step_note = (
            f" Current widget task: {current_task_id}. Current domain: {current_domain or 'unknown'}. "
            f"Current prompt: {current_prompt or 'unknown'}. Expected voice command: {expected_voice or 'none'}."
        )
    return (
        f"{base_context} Study condition: {condition}. Category: {category}. "
        f"Scenario ID: {scenario_id}. Scenario prompt: {scenario_prompt}. "
        f"Gesture source: {gesture_source or 'none'}.{current_step_note}{operator_note}"
    )


def gesture_recognition_metadata(
    *,
    gesture_label: str | None,
    source: str,
    confidence: float | None = None,
) -> dict[str, Any]:
    source = (source or "none").strip() or "none"
    if not gesture_label:
        return {
            "gesture_label": None,
            "gesture_source": source,
            "gesture_confidence": confidence,
            "recognition_outcome": "no recognition",
            "wizard_intervention": source == "manual",
        }

    if source == "manual":
        return {
            "gesture_label": gesture_label,
            "gesture_source": source,
            "gesture_confidence": confidence,
            "recognition_outcome": "Wizard intervention",
            "wizard_intervention": True,
        }

    return {
        "gesture_label": gesture_label,
        "gesture_source": source,
        "gesture_confidence": confidence,
        "recognition_outcome": "correct",
        "wizard_intervention": False,
    }


def infer_multimodal_usage_pattern(condition: str, transcript: str, gesture: str) -> str:
    if condition != "CAN use both":
        return ""
    has_voice = bool((transcript or "").strip())
    has_gesture = bool(normalize_gesture_for_intent(gesture))
    if has_voice and has_gesture:
        return "voice->gesture"
    if has_voice:
        return "voice only"
    if has_gesture:
        return "gesture only"
    return "none"
