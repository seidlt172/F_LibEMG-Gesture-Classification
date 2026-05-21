"""Study operator helpers for the EMG + voice pilot prototype."""

from __future__ import annotations

from datetime import datetime
from typing import Any


CONDITIONS = ("Voice only", "Gesture only", "CAN use both")
CONDITION_ORDERS = ("A", "B", "C")
CATEGORIES = ("Accept/Reject", "Select+Adjust", "Browse+Select", "Confirm+Modify")

SCENARIOS = {
    "Voice only": {
        "Accept/Reject": {
            "scenario_id": "VO-AR",
            "study_ref": "1.1",
            "prompt": "An incoming call appears. Accept or reject it using voice only.",
        },
        "Select+Adjust": {
            "scenario_id": "VO-SA",
            "study_ref": "2.1",
            "prompt": "Select the volume control and make it louder using voice only.",
        },
        "Browse+Select": {
            "scenario_id": "VO-BS",
            "study_ref": "3.1",
            "prompt": "Open a received message and close it again using voice only.",
        },
        "Confirm+Modify": {
            "scenario_id": "VO-CM",
            "study_ref": "4.1",
            "prompt": "Accept navigation guidance and increase announcement volume using voice only.",
        },
    },
    "Gesture only": {
        "Accept/Reject": {
            "scenario_id": "GE-AR",
            "study_ref": "1.2",
            "prompt": "A suggested song appears. Accept or reject it using EMG gesture only.",
        },
        "Select+Adjust": {
            "scenario_id": "GE-SA",
            "study_ref": "2.2",
            "prompt": "Select seat heating and increase it using EMG gesture only.",
        },
        "Browse+Select": {
            "scenario_id": "GE-BS",
            "study_ref": "3.2",
            "prompt": "Browse route options and select one route using EMG gesture only.",
        },
        "Confirm+Modify": {
            "scenario_id": "GE-CM",
            "study_ref": "4.2",
            "prompt": "Accept an ambient light suggestion and increase brightness using EMG gesture only.",
        },
    },
    "CAN use both": {
        "Accept/Reject": {
            "scenario_id": "MM-AR",
            "study_ref": "1.3",
            "prompt": "A navigation route suggestion appears. Accept or reject it using voice, gesture, or both.",
        },
        "Select+Adjust": {
            "scenario_id": "MM-SA",
            "study_ref": "2.3",
            "prompt": "Change the ambient light color and make it brighter using voice, gesture, or both.",
        },
        "Browse+Select": {
            "scenario_id": "MM-BS",
            "study_ref": "3.3",
            "prompt": "Resume paused media and skip to the next song using voice, gesture, or both.",
        },
        "Confirm+Modify": {
            "scenario_id": "MM-CM",
            "study_ref": "4.3",
            "prompt": "Accept an incoming call and regulate volume using voice, gesture, or both.",
        },
    },
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def get_scenario(condition: str, category: str) -> dict[str, str]:
    condition = condition if condition in CONDITIONS else CONDITIONS[0]
    category = category if category in CATEGORIES else CATEGORIES[0]
    return SCENARIOS[condition][category]


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
) -> str:
    operator_note = ""
    if operator_gesture:
        operator_note = (
            f" Operator/Wizard gesture annotation: {operator_gesture}. "
            "Treat it as recovery support, not participant ground truth."
        )
    return (
        f"{base_context} Study condition: {condition}. Category: {category}. "
        f"Scenario ID: {scenario_id}. Scenario prompt: {scenario_prompt}. "
        f"Gesture source: {gesture_source or 'none'}.{operator_note}"
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
