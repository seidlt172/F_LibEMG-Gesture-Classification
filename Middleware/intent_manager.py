"""
Local Ollama-backed intent parsing for the multimodal prototype.

The intent manager is deliberately narrow: it converts a voice transcript plus
an optional EMG gesture into a structured in-car action. It is not a general
chatbot and it does not use cloud APIs.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3.5:4b"
DEFAULT_TIMEOUT = 120.0
DEFAULT_KEEP_ALIVE = "10m"

ALLOWED_INTENTS = {
    "accept_call",
    "reject_call",
    "accept_route",
    "reject_route",
    "select_route",
    "adjust_volume",
    "set_ambient_light",
    "adjust_ambient_light",
    "adjust_seat_heating",
    "skip_song",
    "resume_media",
    "open_message",
    "close_message",
    "confirm",
    "reject",
    "unknown",
}

ALLOWED_ACTIONS = {
    "accept",
    "reject",
    "increase",
    "decrease",
    "select",
    "open",
    "close",
    "resume",
    "skip",
    "set",
    "confirm",
    "unknown",
}

ALLOWED_TARGETS = {
    "call",
    "route",
    "volume",
    "ambient_light",
    "seat_heating",
    "message",
    "media",
    "navigation",
    "unknown",
}

ALLOWED_MODALITIES = {"voice", "gesture", "voice+gesture", "none"}

GESTURE_HINTS = {
    "Daumen hoch": "accept or confirm",
    "Swipe": "reject, dismiss, skip, or next option",
    "Handgelenk drehen": "adjust a continuous value such as volume, brightness, or heating",
    "Zeigen / Tippen": "select, point, or tap an option",
    "Zeigen/Tippen": "select, point, or tap an option",
    "Rest": "neutral, no intentional command",
    "Unknown": "unrecognized gesture",
    "NONE": "no gesture available",
}


class OllamaIntentError(RuntimeError):
    """Raised when Ollama cannot return a usable intent result."""


class OllamaIntentClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = float(timeout)

    @classmethod
    def from_env(cls) -> "OllamaIntentClient":
        timeout_raw = os.environ.get("OLLAMA_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT))
        try:
            timeout = float(timeout_raw)
        except ValueError:
            timeout = DEFAULT_TIMEOUT

        return cls(
            base_url=os.environ.get("OLLAMA_BASE_URL", DEFAULT_BASE_URL),
            model=os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL),
            timeout=timeout,
        )

    def interpret(
        self,
        transcript: str,
        gesture: str,
        context: str | None = None,
    ) -> dict[str, Any]:
        transcript = (transcript or "").strip()
        gesture = (gesture or "").strip()
        context = (context or "").strip()

        if not _has_actionable_input(transcript, gesture):
            return _unknown_result(
                used_modalities="none",
                clarification="Bitte wiederhole die Spracheingabe oder Geste.",
            )

        request_body = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "think": False,
            "keep_alive": DEFAULT_KEEP_ALIVE,
            "options": {
                "temperature": 0.1,
                "top_p": 0.8,
                "num_ctx": 2048,
                "num_predict": 160,
            },
            "messages": [
                {
                    "role": "system",
                    "content": _system_prompt(),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "voice_transcript": transcript,
                            "gesture": gesture,
                            "gesture_hint": GESTURE_HINTS.get(gesture, ""),
                            "context": context,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        }

        try:
            response = self._post_chat(request_body)
        except urllib.error.URLError as exc:
            raise OllamaIntentError(
                f"Ollama nicht erreichbar unter {self.base_url}. Läuft 'ollama serve'?"
            ) from exc
        except TimeoutError as exc:
            raise OllamaIntentError("Ollama-Anfrage hat zu lange gedauert.") from exc
        except json.JSONDecodeError:
            return _unknown_result(
                used_modalities=_infer_modalities(transcript, gesture),
                clarification="Ich konnte die lokale LLM-Antwort nicht auswerten.",
                error="Ollama hat kein gültiges JSON zurückgegeben.",
            )

        try:
            content = response.get("message", {}).get("content", "")
            parsed = json.loads(content)
        except (json.JSONDecodeError, TypeError, KeyError):
            result = _unknown_result(
                used_modalities=_infer_modalities(transcript, gesture),
                clarification="Ich konnte die lokale LLM-Antwort nicht auswerten.",
                error="Ollama hat kein gültiges JSON zurückgegeben.",
            )
            return result

        return normalize_intent_result(parsed, transcript=transcript, gesture=gesture)

    def _post_chat(self, body: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        encoded = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            raw = response.read().decode("utf-8")
        return json.loads(raw)


def normalize_intent_result(
    result: dict[str, Any],
    *,
    transcript: str = "",
    gesture: str = "",
) -> dict[str, Any]:
    if not isinstance(result, dict):
        result = {}

    raw_modality = _normalize_modality(result.get("used_modalities"))
    inferred_modality = _infer_modalities(transcript, gesture)

    normalized = {
        "intent": _allowed(result.get("intent"), ALLOWED_INTENTS),
        "action": _allowed(result.get("action"), ALLOWED_ACTIONS),
        "target": _allowed(result.get("target"), ALLOWED_TARGETS),
        "value": _string_or_empty(result.get("value")),
        "needs_clarification": bool(result.get("needs_clarification", False)),
        "clarification": _string_or_empty(result.get("clarification")),
        "used_modalities": raw_modality if raw_modality in ALLOWED_MODALITIES else inferred_modality,
        "llm_confidence_estimate": _clamp_float(
            result.get("llm_confidence_estimate"),
            default=0.0,
        ),
        "error": _string_or_empty(result.get("error")),
    }

    if normalized["intent"] == "unknown":
        normalized["action"] = "unknown"
        normalized["target"] = "unknown"
        normalized["needs_clarification"] = True
        if not normalized["clarification"]:
            normalized["clarification"] = "Ich bin mir nicht sicher. Bitte wiederhole die Eingabe."

    return normalized


def _system_prompt() -> str:
    return (
        "You are an intent parser for a research prototype in an automotive cockpit. "
        "Return only valid JSON. Do not answer as a conversational assistant. "
        "Infer a structured vehicle interaction intent from German or English voice text, "
        "an EMG micro-gesture label, and optional scenario context. "
        "Allowed intents: "
        f"{sorted(ALLOWED_INTENTS)}. "
        "Allowed actions: "
        f"{sorted(ALLOWED_ACTIONS)}. "
        "Allowed targets: "
        f"{sorted(ALLOWED_TARGETS)}. "
        "Output exactly these keys: intent, action, target, value, needs_clarification, "
        "clarification, used_modalities, llm_confidence_estimate. "
        "If the command is ambiguous, set intent/action/target to unknown, "
        "needs_clarification to true, and provide a short German clarification question."
    )


def _has_actionable_input(transcript: str, gesture: str) -> bool:
    if transcript.strip():
        return True
    return gesture.strip().lower() not in {"", "none", "unknown", "rest"}


def _unknown_result(
    *,
    used_modalities: str = "none",
    clarification: str = "",
    error: str = "",
) -> dict[str, Any]:
    return {
        "intent": "unknown",
        "action": "unknown",
        "target": "unknown",
        "value": "",
        "needs_clarification": True,
        "clarification": clarification or "Ich bin mir nicht sicher. Bitte wiederhole die Eingabe.",
        "used_modalities": used_modalities,
        "llm_confidence_estimate": 0.0,
        "error": error,
    }


def _infer_modalities(transcript: str, gesture: str) -> str:
    has_voice = bool(transcript.strip())
    has_gesture = _has_actionable_input("", gesture)
    if has_voice and has_gesture:
        return "voice+gesture"
    if has_voice:
        return "voice"
    if has_gesture:
        return "gesture"
    return "none"


def _normalize_modality(value: Any) -> str:
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, list):
        normalized = {
            item.strip().lower()
            for item in value
            if isinstance(item, str)
        }
        has_voice = "voice" in normalized
        has_gesture = "gesture" in normalized
        if has_voice and has_gesture:
            return "voice+gesture"
        if has_voice:
            return "voice"
        if has_gesture:
            return "gesture"
    return "unknown"


def _allowed(value: Any, allowed: set[str]) -> str:
    if not isinstance(value, str):
        return "unknown"
    normalized = value.strip().lower()
    return normalized if normalized in allowed else "unknown"


def _string_or_empty(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _clamp_float(value: Any, *, default: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, numeric))
