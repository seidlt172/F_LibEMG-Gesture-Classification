import type React from "react";
import type { Decision, WidgetPayload } from "../types";

export type PreviewGesture =
  | "Daumen hoch"
  | "Swipe"
  | "Handgelenk drehen"
  | "Zeigen / Tippen"
  | "Annehmen"
  | "Ablehnen"
  | "Beenden"
  | "Auflegen"
  | "Anruf beenden"
  | "Nächstes Lied"
  | "Lauter"
  | "Lauter machen"
  | "Nachricht öffnen"
  | "Schließen"
  | "Zeigen/Tippen"
  | "Zeigen"
  | "Tippen";

export interface CockpitState {
  activePayload: WidgetPayload | null;
  completed: boolean;
  feedback: string;
  decision: Decision | "";
  callActive: boolean;
  callIncoming: boolean;
  callEnded: boolean;
  routeActive: boolean;
  routeIndex: number;
  audioPlaying: boolean;
  track: string;
  messageOpen: boolean;
  volume: number;
  ambientColor: string;
  ambientBrightness: number;
  seatLevel: number;
}

export function normalizeGestureLabel(label: string | null | undefined): string {
  const normalized = String(label ?? "").toLowerCase().replace(/\s+/g, "").replace(/\//g, "");
  if (normalized === "zeigentippen" || normalized === "zeigen" || normalized === "tippen") {
    return "tap";
  }
  return normalized;
}

export function previewChipProps(gesture: PreviewGesture, onPreviewGesture?: (gesture: PreviewGesture) => void) {
  return onPreviewGesture
    ? {
        role: "button",
        tabIndex: 0,
        onClick: () => onPreviewGesture(gesture),
        onKeyDown: (event: React.KeyboardEvent<HTMLElement>) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onPreviewGesture(gesture);
          }
        },
      }
    : {};
}

export function popupModalityVisibility(payload: WidgetPayload) {
  if (payload.condition === "Voice only") {
    return { showVoiceActions: true, showGestureActions: false };
  }

  if (payload.condition === "Gesture only") {
    return { showVoiceActions: false, showGestureActions: true };
  }

  if (payload.condition === "CAN use both") {
    return { showVoiceActions: true, showGestureActions: true };
  }

  const usedModalities = payload.source?.used_modalities ?? "";
  return {
    showVoiceActions: Boolean(payload.expected_voice || usedModalities.includes("voice")),
    showGestureActions: Boolean(payload.expected_gesture || usedModalities.includes("gesture")),
  };
}

export function voiceActionLabel(payload: WidgetPayload): string {
  if (payload.expected_voice) {
    return payload.expected_voice;
  }

  switch (payload.task_id) {
    case "CALL-INCOMING":
    case "NAV-ACCEPT-ROUTE":
      return "Annehmen";
    case "NAV-REJECT-ROUTE":
      return "Route ablehnen";
    case "NAV-ACTIVE":
      return "Lauter";
    case "CALL-ACTIVE":
      return "Auflegen";
    case "CALL-ENDED":
      return "";
    case "AUDIO-NEXT":
      return "Nächstes Lied";
    case "AUDIO-VOLUME-UP":
      return "Lauter";
    case "NAV-VOLUME-UP":
      return "Lauter machen";
    case "MESSAGE-OPEN":
      return "Nachricht öffnen";
    case "MESSAGE-CLOSE":
      return "Schließen";
    default:
      return "Ausführen";
  }
}

export function previewGestureForVoiceTask(payload: WidgetPayload): PreviewGesture {
  switch (payload.task_id) {
    case "AUDIO-NEXT":
    case "MESSAGE-CLOSE":
      return "Swipe";
    case "AUDIO-VOLUME-UP":
    case "NAV-ACTIVE":
    case "NAV-VOLUME-UP":
      return "Handgelenk drehen";
    case "MESSAGE-OPEN":
      return "Zeigen / Tippen";
    case "CALL-INCOMING":
    case "NAV-ACCEPT-ROUTE":
    case "CALL-ACTIVE":
      return "Daumen hoch";
    case "NAV-REJECT-ROUTE":
      return "Ablehnen";
    default:
      return "Daumen hoch";
  }
}

export function voicePreviewActions(payload: WidgetPayload): Array<{ label: string; action: PreviewGesture; kind?: "accept" | "decline" }> | null {
  if (!payload.condition || payload.condition !== "Voice only") {
    return null;
  }

  if (payload.study_ref === "1.1" || payload.scenario_id === "STUDY-1.1") {
    if (payload.task_id === "CALL-ACTIVE") {
      return [
        { label: "Auflegen", action: "Auflegen", kind: "decline" },
      ];
    }
    if (payload.task_id === "CALL-ENDED") {
      return null;
    }
    return [
      { label: "Annehmen", action: "Annehmen", kind: "accept" },
      { label: "Ablehnen", action: "Ablehnen", kind: "decline" },
    ];
  }

  if (payload.study_ref === "2.1" || payload.scenario_id === "STUDY-2.1") {
    if (payload.task_id === "AUDIO-VOLUME-UP" && payload.event_type === "trial_completed") {
      return null;
    }
    if (payload.task_id === "AUDIO-NEXT" && payload.decision === "execute") {
      return [{ label: "Lauter", action: "Lauter", kind: "accept" }];
    }
    if (payload.task_id === "AUDIO-VOLUME-UP") {
      return [{ label: "Lauter", action: "Lauter", kind: "accept" }];
    }
    return [
      { label: "Nächstes Lied", action: "Nächstes Lied", kind: "accept" },
    ];
  }

  if (payload.study_ref === "3.1" || payload.scenario_id === "STUDY-3.1") {
    if (payload.task_id === "MESSAGE-CLOSED" || payload.task_id === "MESSAGE-OPENED") {
      return [];
    }
    if (payload.task_id === "MESSAGE-CLOSE") {
      return [{ label: "Schließen", action: "Schließen", kind: "decline" }];
    }
    return [{ label: "Nachricht öffnen", action: "Nachricht öffnen", kind: "accept" }];
  }

  if (payload.study_ref === "4.1" || payload.scenario_id === "STUDY-4.1") {
    if (payload.task_id === "NAV-ACTIVE") {
      return [{ label: "Lauter", action: "Lauter", kind: "accept" }];
    }
    if (payload.task_id === "NAV-VOLUME-UP") {
      return [];
    }
    return [
      { label: "Annehmen", action: "Annehmen", kind: "accept" },
      { label: "Ablehnen", action: "Ablehnen", kind: "decline" },
    ];
  }

  return null;
}

export function waitingTextFor(payload: WidgetPayload): string {
  if (payload.condition === "Voice only") {
    return "Warte auf Spracheingabe";
  }
  if (payload.condition === "Gesture only") {
    return "Warte auf Geste";
  }
  return "Warte auf Sprache oder Geste";
}

export function PopupProcessNotice({
  isWaiting,
  isClarify,
  waitingText,
  clarifyText,
}: {
  isWaiting: boolean;
  isClarify: boolean;
  waitingText: string;
  clarifyText: string;
}) {
  if (!isWaiting && !isClarify) {
    return null;
  }

  return (
    <div className={`popup-process-notice ${isClarify ? "popup-process-notice--clarify" : "popup-process-notice--waiting"}`} role="status" aria-live="polite">
      <span className={isClarify ? "popup-process-notice__alert" : "popup-process-notice__spinner"} aria-hidden>
        {isClarify ? "!" : ""}
      </span>
      <div>
        <strong>{isClarify ? "Eingabe nicht erkannt" : waitingText}</strong>
        <p>{isClarify ? clarifyText : "Das System wartet auf deine Eingabe."}</p>
      </div>
    </div>
  );
}