"""Normalized middleware input events for voice and gesture sources.

The middleware treats real EMG, manual operator input, Wizard fallback, and
Whisper transcripts as input events with a stable schema. Downstream intent
parsing should consume these events instead of depending on a concrete sensor
or GUI implementation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


CONDITIONS = {"Voice only", "Gesture only", "CAN use both"}
ACTIONABLE_GESTURE_LABELS = {
    "Daumen hoch": 1,
    "Swipe": 2,
    "Handgelenk drehen": 3,
    "Tippen": 4,
    "Tippen": 4,
}
NON_ACTION_GESTURES = {"", "none", "no gesture", "rest", "unknown", "none [no recognition]"}
GESTURE_SOURCES = {"emg", "manual", "wizard", "none"}
VOICE_SOURCES = {"whisper", "manual", "wizard", "none"}
RECOGNITION_OUTCOMES = {
    "correct",
    "wrong",
    "no_recognition",
    "delayed",
    "wizard_intervention",
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def normalize_source(source: str | None, *, modality: str) -> str:
    value = (source or "none").strip().lower()
    if value == "emg":
        return "emg"
    if value in {"manual", "operator"}:
        return "manual"
    if value in {"wizard", "woz", "wizard-of-oz"}:
        return "wizard"
    if modality == "voice" and value in VOICE_SOURCES:
        return value
    if modality == "gesture" and value in GESTURE_SOURCES:
        return value
    return "none"


def normalize_gesture_label(gesture_label: str | None) -> str:
    label = (gesture_label or "").strip()
    if label.lower() in NON_ACTION_GESTURES:
        return ""
    if label == "Tippen":
        return "Tippen"
    return label


def gesture_id_for_label(gesture_label: str | None) -> int | None:
    return ACTIONABLE_GESTURE_LABELS.get(normalize_gesture_label(gesture_label))


def normalize_recognition_outcome(outcome: str | None, *, fallback: str) -> str:
    value = (outcome or fallback).strip().lower().replace(" ", "_")
    if value in {"wizard", "wizard-of-oz", "wizard_intervention"}:
        return "wizard_intervention"
    if value in {"no_recognition", "none", "not_recognized", "no"}:
        return "no_recognition"
    if value in RECOGNITION_OUTCOMES:
        return value
    return fallback


def create_gesture_event(
    gesture_label: str | None,
    *,
    source: str = "emg",
    gesture_id: int | None = None,
    confidence: float | None = None,
    timestamp: str | None = None,
    recognition_outcome: str | None = None,
) -> dict[str, Any]:
    normalized_source = normalize_source(source, modality="gesture")
    normalized_label = normalize_gesture_label(gesture_label)
    resolved_id = gesture_id if gesture_id is not None else gesture_id_for_label(normalized_label)

    if not normalized_label:
        fallback_outcome = "no_recognition"
    elif normalized_source in {"manual", "wizard"}:
        fallback_outcome = "wizard_intervention"
    else:
        fallback_outcome = "correct"

    return {
        "source": normalized_source,
        "modality": "gesture",
        "gesture_label": normalized_label or None,
        "gesture_id": resolved_id,
        "confidence": confidence,
        "timestamp": timestamp or now_iso(),
        "recognition_outcome": normalize_recognition_outcome(
            recognition_outcome,
            fallback=fallback_outcome,
        ),
    }


def create_voice_event(
    transcript: str | None,
    *,
    source: str = "whisper",
    confidence: float | None = None,
    timestamp: str | None = None,
    recognition_outcome: str | None = None,
) -> dict[str, Any]:
    normalized_transcript = (transcript or "").strip()
    normalized_source = normalize_source(source, modality="voice")
    fallback_outcome = "correct" if normalized_transcript else "no_recognition"
    return {
        "source": normalized_source,
        "modality": "voice",
        "transcript": normalized_transcript,
        "confidence": confidence,
        "timestamp": timestamp or now_iso(),
        "recognition_outcome": normalize_recognition_outcome(
            recognition_outcome,
            fallback=fallback_outcome,
        ),
    }


def has_actionable_voice(event: dict[str, Any] | None) -> bool:
    return bool((event or {}).get("transcript", "").strip())


def has_actionable_gesture(event: dict[str, Any] | None) -> bool:
    return bool(normalize_gesture_label((event or {}).get("gesture_label")))


def infer_modalities(transcript: str, gesture: str) -> str:
    has_voice = bool((transcript or "").strip())
    has_gesture = bool(normalize_gesture_label(gesture))
    if has_voice and has_gesture:
        return "voice+gesture"
    if has_voice:
        return "voice"
    if has_gesture:
        return "gesture"
    return "none"


def build_intent_inputs(
    *,
    condition: str,
    voice_event: dict[str, Any] | None = None,
    gesture_event: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build condition-filtered input for the intent manager.

    The original events are returned unchanged for logging and later study
    analysis, even when a condition excludes that modality from interpretation.
    """
    normalized_condition = condition if condition in CONDITIONS else "Voice only"
    transcript = (voice_event or {}).get("transcript", "").strip()
    gesture = normalize_gesture_label((gesture_event or {}).get("gesture_label"))
    gesture_source = normalize_source((gesture_event or {}).get("source"), modality="gesture")
    ignored_voice = False
    ignored_gesture = False

    if normalized_condition == "Voice only":
        ignored_gesture = bool(gesture)
        gesture = ""
        gesture_source = "none"
    elif normalized_condition == "Gesture only":
        ignored_voice = bool(transcript)
        transcript = ""
    elif normalized_condition != "CAN use both":
        normalized_condition = "Voice only"
        ignored_gesture = bool(gesture)
        gesture = ""
        gesture_source = "none"

    if not gesture:
        gesture_source = "none"

    return {
        "condition": normalized_condition,
        "transcript": transcript,
        "gesture": gesture,
        "gesture_source": gesture_source,
        "voice_event": voice_event,
        "gesture_event": gesture_event,
        "ignored_voice": ignored_voice,
        "ignored_gesture": ignored_gesture,
        "observed_modalities": infer_modalities(
            (voice_event or {}).get("transcript", ""),
            (gesture_event or {}).get("gesture_label", ""),
        ),
        "used_modalities": infer_modalities(transcript, gesture),
    }
