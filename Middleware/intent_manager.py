"""
Local Ollama-backed intent parsing for the multimodal prototype.

The intent manager is deliberately narrow: it converts a voice transcript plus
an optional EMG gesture into a structured in-car action. It is not a general
chatbot and it does not use cloud APIs.
"""

from __future__ import annotations

import json
import os
import re
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
    "end_call",
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
    "Tippen": "select, point, or tap an option",
    "Rest": "neutral, no intentional command",
    "Unknown": "unrecognized gesture",
    "NONE": "no gesture available",
}

INTENT_ALIASES = {
    "hang_up_call": "end_call",
    "close_call": "end_call",
    "stop_call": "end_call",
    "increase_volume": "adjust_volume",
    "decrease_volume": "adjust_volume",
    "set_volume": "adjust_volume",
    "volume_up": "adjust_volume",
    "volume_down": "adjust_volume",
    "change_volume": "adjust_volume",
    "change_ambient_light": "set_ambient_light",
    "increase_ambient_light": "adjust_ambient_light",
    "decrease_ambient_light": "adjust_ambient_light",
    "change_seat_heating": "adjust_seat_heating",
    "increase_seat_heating": "adjust_seat_heating",
    "decrease_seat_heating": "adjust_seat_heating",
    "next_song": "skip_song",
    "skip_media": "skip_song",
    "play_media": "resume_media",
}

ACTION_ALIASES = {
    "up": "increase",
    "down": "decrease",
    "higher": "increase",
    "lower": "decrease",
    "louder": "increase",
    "quieter": "decrease",
    "next": "skip",
    "approve": "accept",
    "decline": "reject",
}

TARGET_ALIASES = {
    "audio": "volume",
    "sound": "volume",
    "brightness": "ambient_light",
    "light": "ambient_light",
    "lights": "ambient_light",
    "heating": "seat_heating",
    "seat": "seat_heating",
    "song": "media",
    "music": "media",
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
        gesture_source: str | None = None,
    ) -> dict[str, Any]:
        transcript = (transcript or "").strip()
        gesture = (gesture or "").strip()
        context = (context or "").strip()
        gesture_source = (gesture_source or "").strip()

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
                            "gesture_source": gesture_source,
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
        "intent": _allowed(
            result.get("intent"),
            ALLOWED_INTENTS,
            aliases=INTENT_ALIASES,
        ),
        "action": _allowed(
            result.get("action"),
            ALLOWED_ACTIONS,
            aliases=ACTION_ALIASES,
        ),
        "target": _allowed(
            result.get("target"),
            ALLOWED_TARGETS,
            aliases=TARGET_ALIASES,
        ),
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

    fallback = _rule_based_intent(transcript, gesture)
    if _should_prefer_rule_based_intent(normalized, fallback):
        fallback["used_modalities"] = normalized["used_modalities"]
        fallback["error"] = normalized["error"]
        return fallback

    if (
        fallback["intent"] == "end_call"
        and normalized["intent"] in {"reject_call", "unknown"}
    ):
        fallback["used_modalities"] = normalized["used_modalities"]
        fallback["error"] = normalized["error"]
        return fallback

    if normalized["intent"] == "unknown" and fallback["intent"] != "unknown":
        fallback["used_modalities"] = normalized["used_modalities"]
        fallback["error"] = normalized["error"]
        return fallback

    if normalized["intent"] == "unknown":
        normalized["action"] = "unknown"
        normalized["target"] = "unknown"
        normalized["needs_clarification"] = True
        if not normalized["clarification"]:
            normalized["clarification"] = "Ich bin mir nicht sicher. Bitte wiederhole die Eingabe."

    return normalized


def _should_prefer_rule_based_intent(
    normalized: dict[str, Any],
    fallback: dict[str, Any],
) -> bool:
    if fallback.get("intent") == "unknown":
        return False
    if normalized.get("intent") == "unknown":
        return True
    if normalized.get("target") != fallback.get("target"):
        return True
    if normalized.get("action") != fallback.get("action"):
        return True
    return False


def _system_prompt() -> str:
    return (
        "You are an intent parser for a research prototype in an automotive cockpit. "
        "Return only valid JSON. Do not answer as a conversational assistant. "
        "Infer a structured vehicle interaction intent from German or English voice text, "
        "an EMG micro-gesture label, and optional scenario context. "
        "Use voice as the primary semantic signal when the voice command is clear. "
        "Use the gesture as a secondary signal for confirmation, selection, rejection, "
        "or adjustment. A conflicting gesture must not force unknown when the voice "
        "command clearly states an action and target. "
        "A manually confirmed gesture is intentional input and must be considered. "
        "Gestures typically map as follows if the domain context is known: "
        "Audio ('Daumen hoch'=play_audio, 'Swipe'=next_track, 'Handgelenk drehen'=adjust_volume). "
        "Navigation ('Daumen hoch'=accept_route, 'Swipe'=reject_route). "
        "Call ('Daumen hoch'=accept_call, 'Swipe'=reject_call or end_call). "
        "Allowed intents: "
        f"{sorted(ALLOWED_INTENTS)}. "
        "Allowed actions: "
        f"{sorted(ALLOWED_ACTIONS)}. "
        "Allowed targets: "
        f"{sorted(ALLOWED_TARGETS)}. "
        "For an active call, commands like 'Anruf beenden', 'auflegen', "
        "or 'hang up' must be end_call with action close and target call, "
        "not reject_call. Use reject_call only for declining an incoming call. "
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


def _rule_based_intent(transcript: str, gesture: str) -> dict[str, Any]:
    text = _normalize_text(transcript)
    if not text:
        return _unknown_result(used_modalities=_infer_modalities(transcript, gesture))

    if _contains_any(text, ("lautstaerke", "lautstarke", "volume", "sound", "audio")):
        if _contains_any(text, ("hoeher", "hoher", "lauter", "erhoehen", "erhoeh", "increase", "up", "louder")):
            return _known_result(
                intent="adjust_volume",
                action="increase",
                target="volume",
                value="louder",
                used_modalities=_infer_modalities(transcript, gesture),
            )
        if _contains_any(text, ("leiser", "niedriger", "senken", "runter", "decrease", "down", "quieter")):
            return _known_result(
                intent="adjust_volume",
                action="decrease",
                target="volume",
                value="quieter",
                used_modalities=_infer_modalities(transcript, gesture),
            )
        return _known_result(
            intent="adjust_volume",
            action="set",
            target="volume",
            used_modalities=_infer_modalities(transcript, gesture),
        )

    if _contains_any(text, ("licht", "ambient", "beleuchtung", "helligkeit", "brightness")):
        action = "set"
        value = ""
        if _contains_any(text, ("heller", "brighter", "hoeher", "increase")):
            action = "increase"
            value = "brighter"
        elif _contains_any(text, ("dunkler", "dim", "decrease", "senken")):
            action = "decrease"
            value = "dimmer"
        return _known_result(
            intent="adjust_ambient_light" if action in {"increase", "decrease"} else "set_ambient_light",
            action=action,
            target="ambient_light",
            value=value,
            used_modalities=_infer_modalities(transcript, gesture),
        )

    if _contains_any(text, ("sitzheizung", "seat heating", "heizung")):
        action = "increase" if _contains_any(text, ("waermer", "warmer", "hoeher", "increase", "mehr")) else "set"
        return _known_result(
            intent="adjust_seat_heating",
            action=action,
            target="seat_heating",
            value="warmer" if action == "increase" else "",
            used_modalities=_infer_modalities(transcript, gesture),
        )

    if _contains_any(text, ("anruf", "call")):
        if _contains_any(text, ("annehmen", "accept", "rangehen")):
            return _known_result("accept_call", "accept", "call", used_modalities=_infer_modalities(transcript, gesture))
        if _contains_any(text, ("beenden", "beende", "ende", "auflegen", "aufgelegt", "lege auf", "leg auf", "stopp", "stop", "hang up", "end call")):
            return _known_result("end_call", "close", "call", used_modalities=_infer_modalities(transcript, gesture))
        if _contains_any(text, ("ablehnen", "reject", "wegdruecken", "decline")):
            return _known_result("reject_call", "reject", "call", used_modalities=_infer_modalities(transcript, gesture))

    if _contains_any(text, ("route", "navigation", "navi")):
        if _contains_any(text, ("annehmen", "nehmen", "accept", "bestaetigen")):
            return _known_result("accept_route", "accept", "route", used_modalities=_infer_modalities(transcript, gesture))
        if _contains_any(text, ("ablehnen", "reject", "nicht")):
            return _known_result("reject_route", "reject", "route", used_modalities=_infer_modalities(transcript, gesture))
        if _contains_any(text, ("auswaehlen", "select", "waehlen")):
            return _known_result("select_route", "select", "route", used_modalities=_infer_modalities(transcript, gesture))

    if _contains_any(text, ("song", "lied", "musik", "media")):
        if _contains_any(text, ("weiter", "naechste", "next", "skip", "ueberspring")):
            return _known_result("skip_song", "skip", "media", value="next", used_modalities=_infer_modalities(transcript, gesture))
        if _contains_any(text, ("fortsetzen", "resume", "play", "abspielen")):
            return _known_result("resume_media", "resume", "media", used_modalities=_infer_modalities(transcript, gesture))

    if _contains_any(text, ("nachricht", "message")):
        if _contains_any(text, ("oeffnen", "open", "anzeigen")):
            return _known_result("open_message", "open", "message", used_modalities=_infer_modalities(transcript, gesture))
        if _contains_any(text, ("schliessen", "close", "weg")):
            return _known_result("close_message", "close", "message", used_modalities=_infer_modalities(transcript, gesture))

    return _unknown_result(used_modalities=_infer_modalities(transcript, gesture))


def _known_result(
    intent: str,
    action: str,
    target: str,
    value: str = "",
    used_modalities: str = "none",
) -> dict[str, Any]:
    return {
        "intent": intent,
        "action": action,
        "target": target,
        "value": value,
        "needs_clarification": False,
        "clarification": "",
        "used_modalities": used_modalities,
        "llm_confidence_estimate": 0.65,
        "error": "",
    }


def _normalize_text(value: str) -> str:
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
    }
    text = value.lower()
    for source, target in replacements.items():
        text = text.replace(source, target)
    return re.sub(r"\s+", " ", text)


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _allowed(value: Any, allowed: set[str], aliases: dict[str, str] | None = None) -> str:
    if not isinstance(value, str):
        return "unknown"
    normalized = value.strip().lower()
    if aliases and normalized in aliases:
        normalized = aliases[normalized]
    return normalized if normalized in allowed else "unknown"


def _string_or_empty(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _clamp_float(value: Any, *, default: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, numeric))
