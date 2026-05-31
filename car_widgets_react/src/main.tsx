import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import type { Decision, LatestResponse, WidgetPayload } from "./types";
import "./styles.css";

const bridgeUrl = import.meta.env.VITE_WIDGET_EVENT_URL ?? "http://127.0.0.1:8765/latest";

type PreviewScenario =
  | "off"
  | "ambient-waiting"
  | "ambient-swipe"
  | "ambient-rotate"
  | "ambient-confirmed"
  | "call-incoming"
  | "call-accepted"
  | "navigation-route"
  | "navigation-accepted"
  | "navigation-declined"
  | "navigation-selected"
  | "navigation-clarify"
  | "music-suggestion"
  | "audio-playing"
  | "audio-skipped"
  | "audio-volume"
  | "audio-clarify"
  | "message-open"
  | "message-opened"
  | "message-closed"
  | "message-confirmed"
  | "message-clarify"
  | "climate-seat"
  | "climate-adjusting"
  | "climate-confirmed"
  | "climate-cancelled"
  | "climate-clarify";

interface CockpitState {
  activePayload: WidgetPayload | null;
  completed: boolean;
  feedback: string;
  decision: Decision | "";
  callActive: boolean;
  callIncoming: boolean;
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

function createIdleState(): CockpitState {
  return {
    activePayload: null,
    completed: false,
    feedback: "Warte auf nächste Aufgabe.",
    decision: "",
    callActive: false,
    callIncoming: false,
    routeActive: false,
    routeIndex: 1,
    audioPlaying: true,
    track: "Low Beam",
    messageOpen: false,
    volume: 42,
    ambientColor: "Blau",
    ambientBrightness: 45,
    seatLevel: 1,
  };
}

function App() {
  const [state, setState] = useState<CockpitState>(() => createIdleState());
  const [lastEventId, setLastEventId] = useState(0);
  const [bridgeStatus, setBridgeStatus] = useState("Warte auf Middleware");
  const [previewScenario, setPreviewScenario] = useState<PreviewScenario>("off");
  const [taskInfoOpen, setTaskInfoOpen] = useState(false);

  useEffect(() => {
    const timer = window.setInterval(async () => {
      try {
        const response = await fetch(bridgeUrl);
        const data = (await response.json()) as LatestResponse;
        setBridgeStatus("Middleware verbunden");
        if (data.payload && data.event_id !== lastEventId) {
          setLastEventId(data.event_id);
          setState((current) => applyPayload(current, data.payload as WidgetPayload));
        }
      } catch {
        setBridgeStatus("Middleware nicht erreichbar");
      }
    }, 300);

    return () => window.clearInterval(timer);
  }, [lastEventId]);

  const livePayload = state.activePayload;
  // Temporary UI preview helper for popup/widget design. Remove or disable before final study run.
  const previewPayload = useMemo(() => createPreviewPayload(previewScenario), [previewScenario]);
  const displayPayload = previewPayload ?? livePayload;
  const displayState = useMemo(() => createPreviewState(state, previewScenario, previewPayload), [state, previewScenario, previewPayload]);
  const shouldShowPopup = Boolean(
    previewPayload ||
    (livePayload && (
      livePayload.event_type === "scenario_start" ||
      livePayload.event_type === "step_update" ||
      livePayload.event_type === "trial_completed"
    ))
  );
  const previewControlLabel = previewPayload ? previewScenarioDisplayLabel(previewScenario) : liveScenarioLabel(livePayload);
  const guidance = useMemo(() => guidanceFor(displayPayload), [displayPayload]);
  const stepLabel = displayPayload && typeof displayPayload.step_index === "number" && displayPayload.step_count
    ? `${(displayPayload.step_index ?? 0) + 1}/${displayPayload.step_count}`
    : "";

  return (
    <main className="shell cockpit-shell">
      <header className="topbar">
        <div>
          <h1>Driver Cockpit</h1>
          <p className="bridge-status">{bridgeStatus}</p>
        </div>
        <div className="topbar-tools">
          <PreviewScenarioControl
            value={previewScenario}
            onChange={setPreviewScenario}
            displayLabel={previewControlLabel}
          />
          <ModeBadge condition={displayPayload?.condition} />
        </div>
      </header>

      <div className="core">
        <MapPanel
          taskInfoOpen={taskInfoOpen}
          onToggleTaskInfo={() => setTaskInfoOpen((open) => !open)}
        >
          <TaskInfoOverlay
            payload={displayPayload}
            state={displayState}
            stepLabel={stepLabel}
            guidance={guidance}
          />
        </MapPanel>

        <aside className="sidebar">
          <SideWidgets />
        </aside>
      </div>

      {shouldShowPopup && <InteractionPopup payload={displayPayload} state={displayState} />}

      <FeedbackBadge decision={displayState.decision} feedback={displayState.feedback} />
    </main>
  );
}

function PreviewScenarioControl({
  value,
  onChange,
  displayLabel,
}: {
  value: PreviewScenario;
  onChange: (value: PreviewScenario) => void;
  displayLabel: string;
}) {
  return (
    <label className="preview-control">
      <span className="preview-control-title">Preview scenario</span>
      <span className="preview-select-shell">
        <select
          className="preview-select-native"
          value={value}
          onChange={(event) => onChange(event.target.value as PreviewScenario)}
          aria-label="Preview scenario"
        >
          <option value="off">Off / Live middleware</option>
          <option value="ambient-waiting">Ambient · Waiting</option>
          <option value="ambient-swipe">Ambient · Swipe detected</option>
          <option value="ambient-rotate">Ambient · Drehen detected</option>
          <option value="ambient-confirmed">Ambient · Confirmed</option>
          <option value="call-incoming">Call · Incoming</option>
          <option value="call-accepted">Call · Accepted</option>
          <option value="navigation-route">Navigation · Route suggestion</option>
          <option value="navigation-accepted">Navigation · Accepted</option>
          <option value="navigation-declined">Navigation · Declined</option>
          <option value="navigation-selected">Navigation · Selected</option>
          <option value="navigation-clarify">Navigation · Clarify</option>
          <option value="music-suggestion">Audio · Music suggestion</option>
          <option value="audio-playing">Audio · Playing</option>
          <option value="audio-skipped">Audio · Skipped</option>
          <option value="audio-volume">Audio · Volume adjusted</option>
          <option value="audio-clarify">Audio · Clarify</option>
          <option value="message-open">Message · New</option>
          <option value="message-opened">Message · Opened</option>
          <option value="message-closed">Message · Closed</option>
          <option value="message-confirmed">Message · Confirmed</option>
          <option value="message-clarify">Message · Clarify</option>
          <option value="climate-seat">Climate · Seat heating</option>
          <option value="climate-adjusting">Climate · Adjusting</option>
          <option value="climate-confirmed">Climate · Confirmed</option>
          <option value="climate-cancelled">Climate · Cancelled</option>
          <option value="climate-clarify">Climate · Clarify</option>
        </select>
        <span className="preview-select-value">{displayLabel}</span>
      </span>
    </label>
  );
}

function liveScenarioLabel(payload: WidgetPayload | null): string {
  if (!payload || !payload.domain || payload.domain === "unknown") {
    return "Live · No active scenario";
  }

  const domainLabel = domainDisplayLabel(payload.domain);
  const gestureLabel = payload.source?.gesture_event?.gesture_label;
  const hasGesture = Boolean(gestureLabel && gestureLabel !== "Rest");

  if (payload.decision === "clarify") {
    return `Live · ${domainLabel} · Clarify`;
  }
  if (payload.decision === "execute" || payload.event_type === "trial_completed" || gestureLabel === "Daumen hoch") {
    return `Live · ${domainLabel} · ${confirmedStateLabel(payload.domain)}`;
  }
  if (payload.decision === "cancel") {
    return `Live · ${domainLabel} · Rejected`;
  }
  if (hasGesture) {
    return `Live · ${domainLabel} · Gesture`;
  }
  if (payload.event_type === "scenario_start") {
    return `Live · ${domainLabel} · ${payload.domain === "calls" ? "Incoming" : "Idle"}`;
  }
  return `Live · ${domainLabel} · Active`;
}

function domainDisplayLabel(domain: WidgetPayload["domain"]): string {
  switch (domain) {
    case "ambient_light":
      return "Ambient";
    case "calls":
      return "Call";
    case "navigation":
      return "Navigation";
    case "audio":
      return "Audio";
    case "messages":
      return "Message";
    case "climate":
      return "Climate";
    default:
      return "Live middleware";
  }
}

function confirmedStateLabel(domain: WidgetPayload["domain"]): string {
  switch (domain) {
    case "calls":
    case "navigation":
      return "Accepted";
    case "audio":
      return "Playing";
    case "messages":
      return "Opened";
    default:
      return "Confirmed";
  }
}

function previewScenarioDisplayLabel(previewScenario: PreviewScenario): string {
  switch (previewScenario) {
    case "ambient-waiting": return "Ambient · Waiting";
    case "ambient-swipe": return "Ambient · Swipe detected";
    case "ambient-rotate": return "Ambient · Drehen detected";
    case "ambient-confirmed": return "Ambient · Confirmed";
    case "call-incoming": return "Call · Incoming";
    case "call-accepted": return "Call · Accepted";
    case "navigation-route": return "Navigation · Route suggestion";
    case "navigation-accepted": return "Navigation · Accepted";
    case "navigation-declined": return "Navigation · Declined";
    case "navigation-selected": return "Navigation · Selected";
    case "navigation-clarify": return "Navigation · Clarify";
    case "music-suggestion": return "Audio · Music suggestion";
    case "audio-playing": return "Audio · Playing";
    case "audio-skipped": return "Audio · Skipped";
    case "audio-volume": return "Audio · Volume adjusted";
    case "audio-clarify": return "Audio · Clarify";
    case "message-open": return "Message · New";
    case "message-opened": return "Message · Opened";
    case "message-closed": return "Message · Closed";
    case "message-confirmed": return "Message · Confirmed";
    case "message-clarify": return "Message · Clarify";
    case "climate-seat": return "Climate · Seat heating";
    case "climate-adjusting": return "Climate · Adjusting";
    case "climate-confirmed": return "Climate · Confirmed";
    case "climate-cancelled": return "Climate · Cancelled";
    case "climate-clarify": return "Climate · Clarify";
    case "off":
    default:
      return "Off / Live middleware";
  }
}

function createPreviewPayload(previewScenario: PreviewScenario): WidgetPayload | null {
  const basePayload: WidgetPayload = {
    event_type: "step_update",
    step_index: 0,
    step_count: 1,
    study_ref: "Preview",
  };

  switch (previewScenario) {
    case "ambient-waiting":
      return {
        ...basePayload,
        domain: "ambient_light",
        condition: "Gesture only",
        prompt: "Passe die Ambientebeleuchtung an.",
        overlay_title: "Ambientebeleuchtung",
        overlay_body: "Warte auf Geste.",
        expected_gesture: "Swipe",
        task_id: "AMBIENT-COLOR",
        source: { used_modalities: "none" },
      };
    case "ambient-swipe":
      return {
        ...basePayload,
        domain: "ambient_light",
        condition: "Gesture only",
        prompt: "Passe die Ambientebeleuchtung an.",
        overlay_title: "Ambientebeleuchtung",
        overlay_body: "Swipe erkannt.",
        expected_gesture: "Swipe",
        task_id: "AMBIENT-COLOR",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Swipe",
            gesture_id: 2,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "ambient-rotate":
      return {
        ...basePayload,
        domain: "ambient_light",
        condition: "Gesture only",
        prompt: "Passe die Ambientebeleuchtung an.",
        overlay_title: "Ambientebeleuchtung",
        overlay_body: "Drehen erkannt.",
        expected_gesture: "Handgelenk drehen",
        task_id: "AMBIENT-BRIGHTER",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Handgelenk drehen",
            gesture_id: 3,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "ambient-confirmed":
      return {
        ...basePayload,
        domain: "ambient_light",
        condition: "Gesture only",
        decision: "execute",
        prompt: "Ambientebeleuchtung aktualisiert.",
        overlay_title: "Ambientebeleuchtung",
        overlay_body: "Ambientebeleuchtung aktualisiert.",
        expected_gesture: "Daumen hoch",
        task_id: "AMBIENT-NIGHTMODE",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Daumen hoch",
            gesture_id: 1,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "call-incoming":
      return {
        ...basePayload,
        domain: "calls",
        condition: "Voice only",
        prompt: "Eingehenden Anruf von Max Mustermann annehmen oder ablehnen.",
        overlay_title: "Eingehender Anruf",
        overlay_body: "Max Mustermann ruft an.",
        expected_voice: "Annehmen",
        task_id: "CALL-INCOMING",
        source: { used_modalities: "voice" },
      };
    case "call-accepted":
      return {
        ...basePayload,
        domain: "calls",
        condition: "Voice only",
        decision: "execute",
        prompt: "Anruf wurde angenommen.",
        overlay_title: "Eingehender Anruf",
        overlay_body: "Max Mustermann ruft an.",
        accepted_text: "Der Anruf wurde angenommen.",
        expected_voice: "Annehmen",
        task_id: "CALL-INCOMING",
        source: { used_modalities: "voice" },
      };
    case "navigation-route":
      return {
        ...basePayload,
        domain: "navigation",
        condition: "CAN use both",
        prompt: "Neue Route ist 8 Minuten schneller.",
        overlay_title: "Navigation",
        overlay_body: "Route vorschlagen.",
        expected_gesture: "Daumen hoch",
        expected_voice: "Annehmen",
        task_id: "NAV-ACCEPT-ROUTE",
        source: { used_modalities: "voice+gesture" },
      };
    case "navigation-accepted":
      return {
        ...basePayload,
        domain: "navigation",
        condition: "CAN use both",
        decision: "execute",
        prompt: "Route wurde übernommen.",
        overlay_title: "Route vorgeschlagen",
        overlay_body: "Neue Route verfügbar.",
        accepted_text: "Route übernommen",
        expected_gesture: "Daumen hoch",
        expected_voice: "Annehmen",
        task_id: "NAV-ACCEPT-ROUTE",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Daumen hoch",
            gesture_id: 1,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "navigation-declined":
      return {
        ...basePayload,
        domain: "navigation",
        condition: "CAN use both",
        decision: "cancel",
        prompt: "Route wurde abgelehnt.",
        overlay_title: "Route vorgeschlagen",
        overlay_body: "Neue Route verfügbar.",
        rejected_text: "Route abgelehnt",
        expected_gesture: "Swipe",
        expected_voice: "Ablehnen",
        task_id: "NAV-REJECT-ROUTE",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Swipe",
            gesture_id: 2,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "navigation-selected":
      return {
        ...basePayload,
        domain: "navigation",
        condition: "Gesture only",
        prompt: "Zweite Route auswählen.",
        overlay_title: "Route vorgeschlagen",
        overlay_body: "Alternative Route verfügbar.",
        accepted_text: "Route ausgewählt",
        expected_gesture: "Zeigen/Tippen",
        task_id: "NAV-SELECT-SECOND",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Zeigen/Tippen",
            gesture_id: 4,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "navigation-clarify":
      return {
        ...basePayload,
        domain: "navigation",
        condition: "CAN use both",
        decision: "clarify",
        prompt: "Bitte Navigationsauswahl wiederholen.",
        overlay_title: "Navigation",
        overlay_body: "Eingabe unklar.",
        unclear_text: "Bitte Route bestätigen oder ablehnen.",
        expected_gesture: "Daumen hoch",
        expected_voice: "Annehmen",
        task_id: "NAV-ACCEPT-ROUTE",
        source: { used_modalities: "voice+gesture" },
      };
    case "music-suggestion":
      return {
        ...basePayload,
        domain: "audio",
        condition: "Voice only",
        prompt: "Musikvorschlag abspielen.",
        overlay_title: "Musik",
        overlay_body: "Night Drive abspielen?",
        expected_voice: "Abspielen",
        task_id: "AUDIO-SUGGESTION",
        source: { used_modalities: "voice" },
      };
    case "audio-playing":
      return {
        ...basePayload,
        domain: "audio",
        condition: "CAN use both",
        decision: "execute",
        prompt: "Wiedergabe gestartet.",
        overlay_title: "Musik",
        overlay_body: "Night Drive abspielen?",
        accepted_text: "Wiedergabe gestartet",
        expected_gesture: "Daumen hoch",
        expected_voice: "Abspielen",
        task_id: "AUDIO-SUGGESTION",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Daumen hoch",
            gesture_id: 1,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "audio-skipped":
      return {
        ...basePayload,
        domain: "audio",
        condition: "Gesture only",
        decision: "cancel",
        prompt: "Song übersprungen.",
        overlay_title: "Nächster Song",
        overlay_body: "City Lights abspielen.",
        rejected_text: "Song übersprungen",
        expected_gesture: "Swipe",
        task_id: "AUDIO-NEXT",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Swipe",
            gesture_id: 2,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "audio-volume":
      return {
        ...basePayload,
        domain: "audio",
        condition: "Gesture only",
        prompt: "Lautstärke angepasst.",
        overlay_title: "Musik",
        overlay_body: "Song lauter machen.",
        accepted_text: "Lautstärke angepasst",
        expected_gesture: "Handgelenk drehen",
        task_id: "AUDIO-LOUDER",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Handgelenk drehen",
            gesture_id: 3,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "audio-clarify":
      return {
        ...basePayload,
        domain: "audio",
        condition: "CAN use both",
        decision: "clarify",
        prompt: "Bitte Musikauswahl wiederholen.",
        overlay_title: "Musik",
        overlay_body: "Eingabe unklar.",
        unclear_text: "Bitte Abspielen, Weiter oder Lautstärke wiederholen.",
        expected_gesture: "Daumen hoch",
        expected_voice: "Abspielen",
        task_id: "AUDIO-SUGGESTION",
        source: { used_modalities: "voice+gesture" },
      };
    case "message-open":
      return {
        ...basePayload,
        domain: "messages",
        condition: "Voice only",
        prompt: "Neue Nachricht von Anna öffnen.",
        overlay_title: "Nachrichten",
        overlay_body: "Neue Nachricht von Anna.",
        expected_voice: "Öffnen",
        task_id: "MESSAGE-OPEN",
        source: { used_modalities: "voice" },
      };
    case "message-opened":
      return {
        ...basePayload,
        domain: "messages",
        condition: "CAN use both",
        decision: "execute",
        prompt: "Nachricht geöffnet.",
        overlay_title: "Nachricht von Anna",
        overlay_body: "Neue Nachricht von Anna.",
        accepted_text: "Nachricht geöffnet",
        expected_gesture: "Zeigen/Tippen",
        expected_voice: "Öffnen",
        task_id: "MESSAGE-OPEN",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Zeigen/Tippen",
            gesture_id: 4,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "message-closed":
      return {
        ...basePayload,
        domain: "messages",
        condition: "Gesture only",
        decision: "cancel",
        prompt: "Nachricht geschlossen.",
        overlay_title: "Nachricht",
        overlay_body: "Neue Nachricht von Anna.",
        rejected_text: "Nachricht geschlossen",
        expected_gesture: "Swipe",
        task_id: "MESSAGE-CLOSE",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Swipe",
            gesture_id: 2,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "message-confirmed":
      return {
        ...basePayload,
        domain: "messages",
        condition: "Gesture only",
        prompt: "Nachricht bestätigt.",
        overlay_title: "Nachricht von Anna",
        overlay_body: "Neue Nachricht von Anna.",
        accepted_text: "Bestätigt",
        expected_gesture: "Daumen hoch",
        task_id: "MESSAGE-OPEN",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Daumen hoch",
            gesture_id: 1,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "message-clarify":
      return {
        ...basePayload,
        domain: "messages",
        condition: "CAN use both",
        decision: "clarify",
        prompt: "Bitte Nachrichteneingabe wiederholen.",
        overlay_title: "Nachrichten",
        overlay_body: "Eingabe unklar.",
        unclear_text: "Soll die Nachricht geöffnet oder geschlossen werden?",
        expected_gesture: "Zeigen/Tippen",
        expected_voice: "Öffnen",
        task_id: "MESSAGE-OPEN",
        source: { used_modalities: "voice+gesture" },
      };
    case "climate-seat":
      return {
        ...basePayload,
        domain: "climate",
        condition: "Gesture only",
        prompt: "Sitzheizung wärmer stellen.",
        overlay_title: "Sitzheizung",
        overlay_body: "Sitz 1 wärmer stellen.",
        expected_gesture: "Handgelenk drehen",
        task_id: "CLIMATE-SEAT-WARMER",
        source: { used_modalities: "gesture" },
      };
    case "climate-adjusting":
      return {
        ...basePayload,
        domain: "climate",
        condition: "Gesture only",
        prompt: "Sitzheizung angepasst.",
        overlay_title: "Sitzheizung",
        overlay_body: "Sitz 1 wird wärmer gestellt.",
        accepted_text: "Sitzheizung angepasst",
        expected_gesture: "Handgelenk drehen",
        task_id: "CLIMATE-SEAT-WARMER",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Handgelenk drehen",
            gesture_id: 3,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "climate-confirmed":
      return {
        ...basePayload,
        domain: "climate",
        condition: "Gesture only",
        decision: "execute",
        prompt: "Sitzheizung aktualisiert.",
        overlay_title: "Sitzheizung",
        overlay_body: "Sitz 1 ist wärmer eingestellt.",
        accepted_text: "Sitzheizung aktualisiert",
        expected_gesture: "Daumen hoch",
        task_id: "CLIMATE-SEAT-WARMER",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Daumen hoch",
            gesture_id: 1,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "climate-cancelled":
      return {
        ...basePayload,
        domain: "climate",
        condition: "Gesture only",
        decision: "cancel",
        prompt: "Änderung abgebrochen.",
        overlay_title: "Sitzheizung",
        overlay_body: "Die Sitzheizung bleibt unverändert.",
        rejected_text: "Änderung abgebrochen",
        expected_gesture: "Swipe",
        task_id: "CLIMATE-SEAT-WARMER",
        source: {
          used_modalities: "gesture",
          gesture_event: {
            gesture_label: "Swipe",
            gesture_id: 2,
            source: "manual",
            confidence: null,
          },
        },
      };
    case "climate-clarify":
      return {
        ...basePayload,
        domain: "climate",
        condition: "CAN use both",
        decision: "clarify",
        prompt: "Bitte Eingabe für Sitzheizung wiederholen.",
        overlay_title: "Sitzheizung",
        overlay_body: "Eingabe unklar.",
        unclear_text: "Soll die Sitzheizung erhöht werden?",
        expected_gesture: "Handgelenk drehen",
        expected_voice: "Wärmer",
        task_id: "CLIMATE-SEAT-WARMER",
        source: { used_modalities: "voice+gesture" },
      };
    default:
      return null;
  }
}

function createPreviewState(state: CockpitState, previewScenario: PreviewScenario, previewPayload: WidgetPayload | null): CockpitState {
  if (!previewPayload) {
    return state;
  }

  const previewState: CockpitState = {
    ...state,
    activePayload: previewPayload,
    completed: previewPayload.decision === "execute",
    decision: previewPayload.decision ?? "",
    feedback: "Preview mode · not study data",
  };

  switch (previewScenario) {
    case "ambient-swipe":
      return { ...previewState, ambientColor: "Warm" };
    case "ambient-rotate":
      return { ...previewState, ambientBrightness: 75 };
    case "ambient-confirmed":
      return { ...previewState, ambientColor: "Warm", ambientBrightness: 70 };
    case "call-incoming":
      return { ...previewState, callIncoming: true, callActive: false };
    case "call-accepted":
      return { ...previewState, callIncoming: false, callActive: true };
    case "navigation-route":
      return { ...previewState, routeActive: true, routeIndex: 1 };
    case "navigation-accepted":
      return { ...previewState, routeActive: true, routeIndex: 1 };
    case "navigation-declined":
      return { ...previewState, routeActive: false, routeIndex: 1 };
    case "navigation-selected":
      return { ...previewState, routeActive: true, routeIndex: 2 };
    case "navigation-clarify":
      return { ...previewState, routeActive: true, routeIndex: 1 };
    case "music-suggestion":
      return { ...previewState, audioPlaying: true, track: "Night Drive" };
    case "audio-playing":
      return { ...previewState, audioPlaying: true, track: "Night Drive" };
    case "audio-skipped":
      return { ...previewState, audioPlaying: true, track: "City Lights" };
    case "audio-volume":
      return { ...previewState, audioPlaying: true, track: "Night Drive", volume: 72 };
    case "audio-clarify":
      return { ...previewState, audioPlaying: false, track: "Night Drive" };
    case "message-open":
      return { ...previewState, messageOpen: false };
    case "message-opened":
      return { ...previewState, messageOpen: true };
    case "message-closed":
      return { ...previewState, messageOpen: false };
    case "message-confirmed":
      return { ...previewState, messageOpen: true };
    case "message-clarify":
      return { ...previewState, messageOpen: false };
    case "climate-seat":
      return { ...previewState, seatLevel: 2 };
    case "climate-adjusting":
      return { ...previewState, seatLevel: 3 };
    case "climate-confirmed":
      return { ...previewState, seatLevel: 3 };
    case "climate-cancelled":
      return { ...previewState, seatLevel: 1 };
    case "climate-clarify":
      return { ...previewState, seatLevel: 2 };
    default:
      return previewState;
  }
}

function Icon({ name }: { name: string }) {
  switch (name) {
    case "phone":
      return <span className="icon phone" aria-hidden>📞</span>;
    case "nav":
      return <span className="icon nav" aria-hidden>🗺️</span>;
    case "music":
      return <span className="icon music" aria-hidden>🎵</span>;
    case "msg":
      return <span className="icon msg" aria-hidden>✉️</span>;
    case "light":
      return <span className="icon light" aria-hidden>💡</span>;
    case "climate":
      return <span className="icon climate" aria-hidden>🔥</span>;
    default:
      return <span className="icon" aria-hidden>•</span>;
  }
}

function ModeBadge({ condition }: { condition?: string | null }) {
  const label = condition ?? "Warte auf Aufgabe";
  const mode = (condition || "").toLowerCase();
  return (
    <div className="condition mode-badge" role="status" aria-live="polite">
      <span className={`mode-dot ${mode.includes("voice") ? "voice" : mode.includes("gesture") ? "gesture" : mode.includes("can") ? "both" : "idle"}`} />
      <span className="mode-label">{label}</span>
    </div>
  );
}

function MapPanel({
  children,
  taskInfoOpen,
  onToggleTaskInfo,
}: {
  children?: React.ReactNode;
  taskInfoOpen: boolean;
  onToggleTaskInfo: () => void;
}) {
  return (
    <section className="map-panel">
      <div className="fake-map">
        <button
          className={`map-info-button ${taskInfoOpen ? "active" : ""}`}
          type="button"
          aria-label={taskInfoOpen ? "Aufgabeninfo ausblenden" : "Aufgabeninfo anzeigen"}
          aria-expanded={taskInfoOpen}
          onClick={onToggleTaskInfo}
        >
          i
        </button>
        {taskInfoOpen && children}
      </div>
    </section>
  );
}

function TaskInfoOverlay({
  payload,
  state,
  stepLabel,
  guidance,
}: {
  payload: WidgetPayload | null;
  state: CockpitState;
  stepLabel: string;
  guidance: string;
}) {
  return (
    <div className="taskband inside-map taskband-overlay">
      <div>
        <span className="eyebrow">Aktuelle Aufgabe</span>
        <h2>{payload ? `${payload.study_ref ?? ""} ${payload.scenario_prompt || payload.overlay_title || "Studienaufgabe"}` : "Kein aktiver Trial"}</h2>
        <p>{taskText(payload, state.completed, stepLabel)}</p>
      </div>
      <div className="guidance guidance-inline">
        <span>{guidance}</span>
        {payload?.expected_voice && <strong className="pill voice">{payload.expected_voice}</strong>}
        {payload?.expected_gesture && <strong className="pill gesture">{payload.expected_gesture}{payload.gesture_ref ? ` (${payload.gesture_ref})` : ""}</strong>}
      </div>
    </div>
  );
}

function SideWidgets() {
  return (
    <div className="side-widgets">
      <MusicWidget />
      <MessageWidget />
      <NavigationWidget />
      <CallWidget />
      <AmbientWidget />
      <ClimateWidget />
    </div>
  );
}

function NavigationWidget() {
  return (
    <div className="widget-card navigation-widget voice">
      <div className="navigation-widget-main">
        <div className="navigation-widget-header">
          <span className="eyebrow navigation-widget-title">Navigation</span>
          <span className="side-widget-badge voice">Route</span>
        </div>

        <div className="navigation-route-alert">Neue Route <strong>8 min schneller</strong></div>
        <div className="navigation-mini-map" aria-hidden>
          <span className="navigation-map-line primary" />
          <span className="navigation-map-line secondary" />
          <span className="navigation-map-pin start" />
          <span className="navigation-map-pin end" />
        </div>
        <div className="navigation-action-row" aria-label="Navigationsoptionen">
          <button className="navigation-action accept" type="button">Annehmen</button>
          <button className="navigation-action decline" type="button">Ablehnen</button>
        </div>
      </div>
    </div>
  );
}

function CallWidget() {
  return (
    <div className="widget-card call-widget voice">
      <div className="call-widget-main">
        <div className="call-widget-header">
          <span className="eyebrow call-widget-title">Anruf</span>
          <span className="side-widget-badge success">Mobil</span>
        </div>

        <div className="call-info-row">
          <span className="call-phone-circle" aria-hidden>☎</span>
          <div className="call-copy">
            <strong>Max Mustermann</strong>
            <span>Mobil</span>
          </div>
        </div>
      </div>

      <div className="call-action-row" aria-label="Anrufaktionen">
        <button className="call-action-button accept" type="button">Annehmen</button>
        <button className="call-action-button decline" type="button">Ablehnen</button>
      </div>
    </div>
  );
}

function MusicWidget() {
  const volume = 75;

  return (
    <div className="widget-card music-widget">
      <div className="music-widget-frame">
        <div className="music-widget-main">
          <div className="side-widget-header">
            <span className="eyebrow music-widget-title">Musik</span>
            <span className="side-widget-badge voice">Audio</span>
          </div>
          <div className="music-widget-track">
            <div className="music-album-art" aria-hidden>
              <span>BL</span>
            </div>
            <div className="music-track-copy">
              <strong className="widget-title music-track-title">Blinding Lights</strong>
              <span className="music-track-meta">The Weeknd</span>
            </div>
          </div>
        </div>

        <div className="music-widget-controls">
          <div className="music-volume-row" aria-label={`Lautstärke ${volume}%`}>
            <div className="music-volume-track">
              <span className="music-volume-fill" style={{ width: `${volume}%` }} />
            </div>
            <span className="music-volume-value">{volume}%</span>
          </div>

          <div className="music-control-row" aria-label="Musiksteuerung">
            <button className="music-control-button" type="button" aria-label="Vorheriger Titel">
              <span aria-hidden>‹</span>
            </button>
            <button className="music-control-button play" type="button" aria-label="Abspielen">
              <span aria-hidden>▶</span>
            </button>
            <button className="music-control-button" type="button" aria-label="Nächster Titel">
              <span aria-hidden>›</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function MessageWidget() {
  return (
    <div className="widget-card message-widget">
      <div className="side-widget-header">
        <span className="eyebrow message-widget-title">Nachrichten</span>
        <span className="side-widget-badge gesture">Neu</span>
      </div>

      <div className="message-preview-panel">
        <strong className="message-preview-title">Neue Nachricht</strong>
        <span className="message-preview-sender">Von: <strong>Anna</strong></span>
      </div>

      <div className="message-action-row" aria-label="Nachrichtenaktionen">
        <button className="message-action-button" type="button">Öffnen</button>
        <button className="message-action-button" type="button">Schließen</button>
      </div>
    </div>
  );
}

function AmbientWidget() {
  const brightness = 45;
  const colorPosition = 70;

  return (
    <div className="widget-card ambient-widget gesture">
      <div className="ambient-widget-main">
        <div className="ambient-widget-header">
          <span className="eyebrow ambient-widget-title">Ambientebeleuchtung</span>
          <span className="side-widget-badge gesture">Licht</span>
        </div>

        <div className="ambient-slider-panel">
          <div className="ambient-slider-row" aria-label="Farbe Blau">
            <span className="ambient-slider-icon" aria-hidden>◌</span>
            <div className="ambient-slider rgb">
              <span className="ambient-slider-handle" style={{ left: `${colorPosition}%` }} />
            </div>
          </div>

          <div className="ambient-slider-row" aria-label={`Helligkeit ${brightness}%`}>
            <span className="ambient-slider-icon" aria-hidden>☼</span>
            <div className="ambient-slider brightness">
              <span className="ambient-slider-handle" style={{ left: `${brightness}%` }} />
            </div>
          </div>
        </div>
      </div>

      <div className="ambient-gesture-panel" aria-label="Gesten">
        <span className="ambient-gesture-chip"><span aria-hidden>↔</span>Swipe</span>
        <span className="ambient-gesture-chip"><span aria-hidden>↻</span>Drehen</span>
      </div>
    </div>
  );
}

function ClimateWidget() {
  return (
    <div className="widget-card climate-widget">
      <div className="climate-widget-main">
        <div className="side-widget-header">
          <span className="eyebrow climate-widget-title">Sitzheizung</span>
          <span className="side-widget-badge heat">Stufe 2</span>
        </div>

        <div className="climate-seat-list">
          <div className="climate-seat-row">
            <div className="climate-seat-label">
              <span>Sitz 1:</span>
              <span className="climate-seat-icon" aria-hidden>▰</span>
            </div>
            <div className="climate-seat-control">
              <strong>Stufe 2</strong>
              <span className="climate-stepper" aria-hidden>
                <span>⌃</span>
                <span>⌄</span>
              </span>
            </div>
          </div>

          <div className="climate-seat-row">
            <div className="climate-seat-label">
              <span>Sitz 2:</span>
              <span className="climate-seat-icon" aria-hidden>▰</span>
            </div>
            <div className="climate-seat-control">
              <strong>Stufe 1</strong>
              <span className="climate-stepper" aria-hidden>
                <span>⌃</span>
                <span>⌄</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="climate-gesture-panel" aria-label="Gesten">
        <span className="climate-gesture-chip"><span aria-hidden>↔</span>Swipe</span>
        <span className="climate-gesture-chip"><span aria-hidden>↻</span>Drehen</span>
      </div>
    </div>
  );
}

function InteractionPopup({ payload, state }: { payload: WidgetPayload | null; state: CockpitState }) {
  if (!payload) return null;

  if (payload.domain === "ambient_light") {
    return <AmbientPopupWidget payload={payload} state={state} />;
  }

  if (isCallDomain(payload.domain)) {
    return <CallPopupWidget payload={payload} state={state} />;
  }

  if (isNavigationDomain(payload.domain)) {
    return <NavigationPopupWidget payload={payload} state={state} />;
  }

  if (isAudioDomain(payload.domain)) {
    return <AudioPopupWidget payload={payload} state={state} />;
  }

  if (isMessagesDomain(payload.domain)) {
    return <MessagesPopupWidget payload={payload} state={state} />;
  }

  if (isClimateDomain(payload.domain)) {
    return <ClimatePopupWidget payload={payload} state={state} />;
  }

  const title = payload.overlay_title || payload.scenario_prompt || "Interaktion";
  const body = payload.overlay_body || payload.prompt || "";
  return (
    <div className={`interaction-popup ${payload.event_type || ""}`}>
      <div className="popup-card">
        <div className="popup-header">
          <div className="popup-left">
            <div className="popup-meta"><Icon name={payload.domain === "calls" ? "phone" : payload.domain === "navigation" ? "nav" : payload.domain === "audio" ? "music" : payload.domain === "messages" ? "msg" : payload.domain === "climate" ? "climate" : "light"} />
              <div>
                <span className="eyebrow">{payload.domain}</span>
                <strong className="popup-title">{title}</strong>
              </div>
            </div>
          </div>
          <div className="popup-actions">
            <button className="pill accept" aria-label="Annehmen">✔ Annehmen</button>
            <button className="pill decline" aria-label="Ablehnen">✖ Ablehnen</button>
          </div>
        </div>
        <div className="popup-body">{body}</div>
      </div>
    </div>
  );
}

function isCallDomain(domain: WidgetPayload["domain"]): boolean {
  return domain === "calls" || String(domain) === "call";
}

function isNavigationDomain(domain: WidgetPayload["domain"]): boolean {
  return domain === "navigation" || String(domain) === "nav";
}

function isAudioDomain(domain: WidgetPayload["domain"]): boolean {
  return domain === "audio" || String(domain) === "music" || String(domain) === "media";
}

function isMessagesDomain(domain: WidgetPayload["domain"]): boolean {
  return domain === "messages" || String(domain) === "message";
}

function isClimateDomain(domain: WidgetPayload["domain"]): boolean {
  return domain === "climate" || String(domain) === "seat_heating" || String(domain) === "seat-heating";
}

function CallPopupWidget({ payload, state }: { payload: WidgetPayload; state: CockpitState }) {
  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const usedModalities = payload.source?.used_modalities;
  const intentText = `${payload.intent ?? ""} ${payload.action ?? ""} ${payload.target ?? ""}`.toLowerCase();
  const isClarify = payload.decision === "clarify";
  const isAccepted = !isClarify && (
    gestureLabel === "Daumen hoch" ||
    payload.decision === "execute" ||
    intentText.includes("accept")
  );
  const isDeclined = !isClarify && (
    gestureLabel === "Swipe" ||
    payload.decision === "cancel" ||
    intentText.includes("reject") ||
    intentText.includes("decline")
  );
  const isGestureMode = payload.condition !== "Voice only" || Boolean(payload.expected_gesture) || Boolean(usedModalities?.includes("gesture"));
  const stageClass = isClarify
    ? "call-popup--clarify"
    : isAccepted
      ? "call-popup--accepted"
      : isDeclined
        ? "call-popup--declined"
        : "call-popup--incoming";
  const badgeText = isClarify
    ? "Klären"
    : isAccepted
      ? "Angenommen"
      : isDeclined
        ? "Abgelehnt"
      : isGestureMode
        ? "Anruf"
        : "Aktiv";
  const title = isClarify
    ? "Eingabe klären"
    : isAccepted
      ? "Anruf angenommen"
      : isDeclined
        ? "Anruf abgelehnt"
        : payload.overlay_title || "Eingehender Anruf";
  const body = isClarify
    ? payload.unclear_text || payload.prompt || "Bitte Eingabe wiederholen."
    : isAccepted
      ? payload.accepted_text || "Anruf angenommen"
      : isDeclined
        ? payload.rejected_text || "Anruf abgelehnt"
        : payload.overlay_body || payload.prompt || "Max Mustermann ruft an.";
  const callStatus = isAccepted ? "Verbunden" : isDeclined ? "Beendet" : "Eingehend";

  return (
    <div className={`interaction-popup call-popup-shell ${payload.event_type || ""}`}>
      <section className={`call-popup ${stageClass}`}>
        <div className="call-popup__header">
          <div>
            <span className="eyebrow call-popup__eyebrow">Anruf</span>
            <h2>{title}</h2>
          </div>
          <span className="call-popup__badge">{badgeText}</span>
        </div>

        <div className="call-popup__content">
          <div className="call-popup__avatar" aria-hidden>
            <span>☎</span>
          </div>

          <div className="call-popup__details">
            <span className="call-popup__label">Max Mustermann</span>
            <strong>{callStatus}</strong>
            <p>{body}</p>
          </div>
        </div>

        {isAccepted ? (
          <div className="call-popup__actions call-popup__actions--connected" aria-label="Anrufstatus">
            <span className="call-popup__success-pill">Verbunden</span>
            <button className="call-popup__button call-popup__button--hangup" type="button">
              Auflegen
            </button>
          </div>
        ) : isGestureMode ? (
          <div className="call-popup__actions" aria-label="Anrufgesten">
            <span className={`call-popup__chip call-popup__chip--accept ${isAccepted ? "call-popup__chip--active" : ""}`}>
              <span aria-hidden>👍</span>Daumen hoch
            </span>
            <span className={`call-popup__chip call-popup__chip--decline ${isDeclined ? "call-popup__chip--active" : ""}`}>
              <span aria-hidden>↔</span>Swipe
            </span>
          </div>
        ) : (
          <div className="call-popup__actions" aria-label="Anrufaktionen">
            <button className={`call-popup__button call-popup__button--accept ${isAccepted ? "call-popup__button--active" : ""}`} type="button">
              Annehmen
            </button>
            <button className={`call-popup__button call-popup__button--decline ${isDeclined ? "call-popup__button--active" : ""}`} type="button">
              Ablehnen
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

function NavigationPopupWidget({ payload, state }: { payload: WidgetPayload; state: CockpitState }) {
  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const usedModalities = payload.source?.used_modalities;
  const isClarify = payload.decision === "clarify";
  const isAccepted = !isClarify && (gestureLabel === "Daumen hoch" || payload.decision === "execute");
  const isDeclined = !isClarify && (gestureLabel === "Swipe" || payload.decision === "cancel");
  const isSelected = !isClarify && gestureLabel === "Zeigen/Tippen";
  const isGestureMode = payload.condition !== "Voice only" || Boolean(payload.expected_gesture) || Boolean(usedModalities?.includes("gesture"));
  const routeName = isSelected
    ? "Alternative Route"
    : isAccepted
      ? "Schnellere Route"
      : isDeclined
        ? "Route abgelehnt"
        : "Schnellere Route";
  const stageClass = isClarify
    ? "navigation-popup--clarify"
    : isAccepted
      ? "navigation-popup--accepted"
      : isDeclined
        ? "navigation-popup--declined"
        : isSelected
          ? "navigation-popup--selected"
          : "navigation-popup--suggested";
  const badgeText = isClarify
    ? "Klärung"
    : isAccepted
      ? "Ausgewählt"
      : isDeclined
        ? "Route"
        : isSelected
          ? "Ausgewählt"
          : "Aktiv";
  const title = isClarify
    ? "Navigation klären"
    : isAccepted
      ? "Route übernommen"
      : isDeclined
        ? "Route abgelehnt"
        : isSelected
          ? "Route ausgewählt"
          : payload.overlay_title || "Route vorgeschlagen";
  const body = isClarify
    ? payload.unclear_text || payload.prompt || "Bitte Auswahl wiederholen."
    : isAccepted
      ? payload.accepted_text || "Route übernommen"
      : isDeclined
        ? payload.rejected_text || "Route abgelehnt"
        : isSelected
          ? payload.accepted_text || "Route ausgewählt"
          : payload.overlay_body || payload.prompt || "Neue Route verfügbar.";

  return (
    <div className={`interaction-popup navigation-popup-shell ${payload.event_type || ""}`}>
      <section className={`navigation-popup ${stageClass}`}>
        <div className="navigation-popup__header">
          <div>
            <span className="eyebrow navigation-popup__eyebrow">Navigation</span>
            <h2>{title}</h2>
          </div>
          <span className="navigation-popup__badge">{badgeText}</span>
        </div>

        <div className="navigation-popup__content">
          <div className="navigation-popup__route-preview" aria-hidden>
            <span className="navigation-popup__route-line navigation-popup__route-line--primary" />
            <span className="navigation-popup__route-line navigation-popup__route-line--secondary" />
            <span className="navigation-popup__pin navigation-popup__pin--start" />
            <span className="navigation-popup__pin navigation-popup__pin--end" />
          </div>

          <div className="navigation-popup__details">
            <span className="navigation-popup__label">{routeName}</span>
            <strong>{body}</strong>
            <div className="navigation-popup__meta" aria-label="Routendetails">
              <span>12 min</span>
              <span>4.2 km</span>
              <span>8 min schneller</span>
            </div>
          </div>
        </div>

        {isGestureMode ? (
          <div className="navigation-popup__actions" aria-label="Navigationsgesten">
            <span className={`navigation-popup__chip navigation-popup__chip--accept ${isAccepted ? "navigation-popup__chip--active" : ""}`}>
              <span aria-hidden>👍</span>Daumen hoch
            </span>
            <span className={`navigation-popup__chip navigation-popup__chip--decline ${isDeclined ? "navigation-popup__chip--active" : ""}`}>
              <span aria-hidden>↔</span>Swipe
            </span>
            <span className={`navigation-popup__chip navigation-popup__chip--select ${isSelected ? "navigation-popup__chip--active" : ""}`}>
              <span aria-hidden>⌾</span>Zeigen/Tippen
            </span>
          </div>
        ) : (
          <div className="navigation-popup__actions" aria-label="Navigationsentscheidung">
            <button className={`navigation-popup__button navigation-popup__button--accept ${isAccepted ? "navigation-popup__button--active" : ""}`} type="button">
              Annehmen
            </button>
            <button className={`navigation-popup__button navigation-popup__button--decline ${isDeclined ? "navigation-popup__button--active" : ""}`} type="button">
              Ablehnen
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

function AudioPopupWidget({ payload, state }: { payload: WidgetPayload; state: CockpitState }) {
  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const usedModalities = payload.source?.used_modalities;
  const isClarify = payload.decision === "clarify";
  const isPlaying = !isClarify && (gestureLabel === "Daumen hoch" || payload.decision === "execute");
  const isSkipped = !isClarify && (gestureLabel === "Swipe" || payload.decision === "cancel");
  const isVolume = !isClarify && gestureLabel === "Handgelenk drehen";
  const isGestureMode = payload.condition !== "Voice only" || Boolean(payload.expected_gesture) || Boolean(usedModalities?.includes("gesture"));
  const volume = Math.max(0, Math.min(100, isVolume ? Math.max(state.volume, 72) : state.volume));
  const progress = isSkipped ? 18 : isPlaying ? 48 : 32;
  const trackTitle = state.track || "Night Drive";
  const stageClass = isClarify
    ? "audio-popup--clarify"
    : isVolume
      ? "audio-popup--volume"
      : isSkipped
        ? "audio-popup--skipped"
        : isPlaying
          ? "audio-popup--playing"
          : "audio-popup--suggested";
  const badgeText = isClarify
    ? "Klärung"
    : isVolume
      ? "Lautstärke"
      : isSkipped
        ? "Übersprungen"
        : isPlaying
          ? "Spielt"
          : "Vorschlag";
  const title = isClarify
    ? "Musik klären"
    : isVolume
      ? "Lautstärke angepasst"
      : isSkipped
        ? "Nächster Song"
        : isPlaying
          ? "Wiedergabe gestartet"
          : payload.overlay_title || "Musikvorschlag";
  const body = isClarify
    ? payload.unclear_text || payload.prompt || "Bitte Eingabe wiederholen."
    : isVolume
      ? payload.accepted_text || "Lautstärke angepasst"
      : isSkipped
        ? payload.rejected_text || "Song übersprungen"
        : isPlaying
          ? payload.accepted_text || "Wiedergabe gestartet"
          : payload.overlay_body || payload.prompt || "Night Drive abspielen?";
  const metaText = isVolume ? `${volume}% Lautstärke` : isPlaying ? "Spielt" : isSkipped ? "Weiter" : "Vorgeschlagen";

  return (
    <div className={`interaction-popup audio-popup-shell ${payload.event_type || ""}`}>
      <section className={`audio-popup ${stageClass}`}>
        <div className="audio-popup__header">
          <div>
            <span className="eyebrow audio-popup__eyebrow">Audio</span>
            <h2>{title}</h2>
          </div>
          <span className="audio-popup__badge">{badgeText}</span>
        </div>

        <div className="audio-popup__content">
          <div className="audio-popup__artwork" aria-hidden>
            <span>ND</span>
          </div>

          <div className="audio-popup__details">
            <span className="audio-popup__label">{metaText}</span>
            <strong className="audio-popup__track">{trackTitle}</strong>
            <p>{body}</p>
            <div className={`audio-popup__progress ${isVolume ? "audio-popup__progress--volume" : ""}`} aria-label={isVolume ? `Lautstärke ${volume}%` : `Wiedergabe ${progress}%`}>
              <span style={{ width: `${isVolume ? volume : progress}%` }} />
            </div>
            <div className="audio-popup__controls" aria-label="Musiksteuerung">
              <span aria-hidden>‹‹</span>
              <span aria-hidden>{state.audioPlaying || isPlaying ? "Ⅱ" : "▶"}</span>
              <span aria-hidden>››</span>
            </div>
          </div>
        </div>

        {isGestureMode ? (
          <div className="audio-popup__actions" aria-label="Audiogesten">
            <span className={`audio-popup__chip audio-popup__chip--accept ${isPlaying ? "audio-popup__chip--active" : ""}`}>
              <span aria-hidden>👍</span>Daumen hoch
            </span>
            <span className={`audio-popup__chip audio-popup__chip--decline ${isSkipped ? "audio-popup__chip--active" : ""}`}>
              <span aria-hidden>↔</span>Swipe
            </span>
            <span className={`audio-popup__chip audio-popup__chip--volume ${isVolume ? "audio-popup__chip--active" : ""}`}>
              <span aria-hidden>↻</span>Drehen
            </span>
          </div>
        ) : (
          <div className="audio-popup__actions" aria-label="Audioaktionen">
            <button className={`audio-popup__button audio-popup__button--accept ${isPlaying ? "audio-popup__button--active" : ""}`} type="button">
              Annehmen
            </button>
            <button className={`audio-popup__button audio-popup__button--decline ${isSkipped ? "audio-popup__button--active" : ""}`} type="button">
              Ablehnen
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

function MessagesPopupWidget({ payload, state }: { payload: WidgetPayload; state: CockpitState }) {
  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const usedModalities = payload.source?.used_modalities;
  const isClarify = payload.decision === "clarify";
  const isConfirmed = !isClarify && gestureLabel === "Daumen hoch";
  const isOpened = !isClarify && !isConfirmed && (gestureLabel === "Zeigen/Tippen" || payload.decision === "execute");
  const isClosed = !isClarify && (gestureLabel === "Swipe" || payload.decision === "cancel");
  const isGestureMode = payload.condition !== "Voice only" || Boolean(payload.expected_gesture) || Boolean(usedModalities?.includes("gesture"));
  const stageClass = isClarify
    ? "messages-popup--clarify"
    : isConfirmed
      ? "messages-popup--confirmed"
      : isOpened
        ? "messages-popup--opened"
        : isClosed
          ? "messages-popup--closed"
          : "messages-popup--new";
  const badgeText = isClarify
    ? "Klärung"
    : isConfirmed
      ? "Bestätigt"
      : isOpened
        ? "Geöffnet"
        : isClosed
          ? "Geschlossen"
          : "Neu";
  const title = isClarify
    ? "Nachricht klären"
    : isConfirmed
      ? "Bestätigt"
      : isOpened
        ? "Nachricht geöffnet"
        : isClosed
          ? "Nachricht geschlossen"
          : payload.overlay_title || "Neue Nachricht";
  const body = isClarify
    ? payload.unclear_text || payload.prompt || "Bitte Eingabe wiederholen."
    : isConfirmed
      ? payload.accepted_text || "Bestätigt"
      : isOpened
        ? payload.accepted_text || "Nachricht geöffnet"
        : isClosed
          ? payload.rejected_text || "Nachricht geschlossen"
          : payload.overlay_body || payload.prompt || "Neue Nachricht von Anna.";
  const messageStatus = isClosed ? "Geschlossen" : isOpened ? "Geöffnet" : isConfirmed ? "Bestätigt" : "Neue Nachricht";

  return (
    <div className={`interaction-popup messages-popup-shell ${payload.event_type || ""}`}>
      <section className={`messages-popup ${stageClass}`}>
        <div className="messages-popup__header">
          <div>
            <span className="eyebrow messages-popup__eyebrow">Nachrichten</span>
            <h2>{title}</h2>
          </div>
          <span className="messages-popup__badge">{badgeText}</span>
        </div>

        <div className="messages-popup__content">
          <div className="messages-popup__icon" aria-hidden>
            <span>✉</span>
          </div>

          <div className="messages-popup__preview">
            <span className="messages-popup__sender">Von: <strong>Anna</strong></span>
            <strong>{messageStatus}</strong>
            <p className="messages-popup__text">{body}</p>
          </div>
        </div>

        {isGestureMode ? (
          <div className="messages-popup__actions" aria-label="Nachrichtengesten">
            <span className={`messages-popup__chip messages-popup__chip--open ${isOpened ? "messages-popup__chip--active" : ""}`}>
              <span aria-hidden>⌾</span>Zeigen/Tippen
            </span>
            <span className={`messages-popup__chip messages-popup__chip--close ${isClosed ? "messages-popup__chip--active" : ""}`}>
              <span aria-hidden>↔</span>Swipe
            </span>
            <span className={`messages-popup__chip messages-popup__chip--confirm ${isConfirmed ? "messages-popup__chip--active" : ""}`}>
              <span aria-hidden>👍</span>Daumen hoch
            </span>
          </div>
        ) : (
          <div className="messages-popup__actions" aria-label="Nachrichtenaktionen">
            <button className={`messages-popup__button messages-popup__button--open ${isOpened ? "messages-popup__button--active" : ""}`} type="button">
              Öffnen
            </button>
            <button className={`messages-popup__button messages-popup__button--close ${isClosed ? "messages-popup__button--active" : ""}`} type="button">
              Schließen
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

function ClimatePopupWidget({ payload, state }: { payload: WidgetPayload; state: CockpitState }) {
  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const usedModalities = payload.source?.used_modalities;
  const isClarify = payload.decision === "clarify";
  const isAdjusting = !isClarify && gestureLabel === "Handgelenk drehen";
  const isSuccess = !isClarify && (gestureLabel === "Daumen hoch" || payload.decision === "execute");
  const isCancelled = !isClarify && (gestureLabel === "Swipe" || payload.decision === "cancel");
  const isGestureMode = payload.condition !== "Voice only" || Boolean(payload.expected_gesture) || Boolean(usedModalities?.includes("gesture"));
  const seatOneLevel = Math.max(1, Math.min(3, isAdjusting || isSuccess ? Math.max(state.seatLevel, 2) : state.seatLevel));
  const seatTwoLevel = 1;
  const stageClass = isClarify
    ? "climate-popup--clarify"
    : isSuccess
      ? "climate-popup--success"
      : isCancelled
        ? "climate-popup--cancelled"
        : isAdjusting
          ? "climate-popup--adjusting"
          : "climate-popup--active";
  const badgeText = isClarify
    ? "Klärung"
    : isSuccess
      ? "Angepasst"
      : isCancelled
        ? "Abgebrochen"
        : isAdjusting
          ? "Wärmer"
          : "Aktiv";
  const title = isClarify
    ? "Sitzheizung klären"
    : isSuccess
      ? "Sitzheizung aktualisiert"
      : isCancelled
        ? "Änderung abgebrochen"
        : isAdjusting
          ? "Sitzheizung angepasst"
          : payload.overlay_title || "Sitzheizung";
  const body = isClarify
    ? payload.unclear_text || payload.prompt || "Bitte Eingabe wiederholen."
    : isSuccess
      ? payload.accepted_text || "Sitzheizung aktualisiert"
      : isCancelled
        ? payload.rejected_text || "Änderung abgebrochen"
        : isAdjusting
          ? payload.accepted_text || "Sitzheizung angepasst"
          : payload.overlay_body || payload.prompt || "Sitz 1 wird wärmer gestellt.";

  const renderHeatLevels = (level: number) => (
    <span className="climate-popup__heat-levels" aria-hidden>
      {[1, 2, 3].map((dot) => (
        <span key={dot} className={`climate-popup__heat-dot ${dot <= level ? "climate-popup__heat-dot--active" : ""}`} />
      ))}
    </span>
  );

  return (
    <div className={`interaction-popup climate-popup-shell ${payload.event_type || ""}`}>
      <section className={`climate-popup ${stageClass}`}>
        <div className="climate-popup__header">
          <div>
            <span className="eyebrow climate-popup__eyebrow">Sitzheizung</span>
            <h2>{title}</h2>
          </div>
          <span className="climate-popup__badge">{badgeText}</span>
        </div>

        <div className="climate-popup__content">
          <div className="climate-popup__icon" aria-hidden>
            <span>♨</span>
          </div>

          <div className="climate-popup__seat-panel">
            <span className="climate-popup__label">{isAdjusting ? "Temperatur erhöht" : "Klimaeinstellung"}</span>
            <strong>{body}</strong>

            <div className="climate-popup__seat-row">
              <div>
                <span>Sitz 1</span>
                <strong>Stufe {seatOneLevel}</strong>
              </div>
              {renderHeatLevels(seatOneLevel)}
            </div>

            <div className="climate-popup__seat-row">
              <div>
                <span>Sitz 2</span>
                <strong>Stufe {seatTwoLevel}</strong>
              </div>
              {renderHeatLevels(seatTwoLevel)}
            </div>
          </div>
        </div>

        {isGestureMode ? (
          <div className="climate-popup__actions" aria-label="Sitzheizungsgesten">
            <span className={`climate-popup__chip climate-popup__chip--adjust ${isAdjusting ? "climate-popup__chip--active" : ""}`}>
              <span aria-hidden>↻</span>Handgelenk drehen
            </span>
            <span className={`climate-popup__chip climate-popup__chip--cancel ${isCancelled ? "climate-popup__chip--active" : ""}`}>
              <span aria-hidden>↔</span>Swipe
            </span>
            <span className={`climate-popup__chip climate-popup__chip--confirm ${isSuccess ? "climate-popup__chip--active" : ""}`}>
              <span aria-hidden>👍</span>Daumen hoch
            </span>
          </div>
        ) : (
          <div className="climate-popup__actions" aria-label="Sitzheizungsentscheidung">
            <button className={`climate-popup__button climate-popup__button--accept ${isSuccess ? "climate-popup__button--active" : ""}`} type="button">
              Annehmen
            </button>
            <button className={`climate-popup__button climate-popup__button--decline ${isCancelled ? "climate-popup__button--active" : ""}`} type="button">
              Ablehnen
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

function AmbientPopupWidget({ payload, state }: { payload: WidgetPayload; state: CockpitState }) {
  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const isSwipe = gestureLabel === "Swipe";
  const isRotate = gestureLabel === "Handgelenk drehen";
  const isConfirmed = payload.decision === "execute" || gestureLabel === "Daumen hoch";
  const brightness = Math.max(0, Math.min(100, state.ambientBrightness));
  const colorPosition = isSwipe ? 72 : state.ambientColor === "Warm" ? 18 : state.ambientColor === "Blau" ? 70 : 45;
  const brightnessPosition = isRotate ? Math.min(100, brightness + 18) : brightness;
  const statusText = isConfirmed
    ? "Ambientebeleuchtung aktualisiert"
    : isSwipe
      ? "Swipe erkannt"
      : isRotate
        ? "Drehen erkannt"
        : "Warte auf Geste";

  return (
    <div className={`interaction-popup ambient-popup-shell ${payload.event_type || ""}`}>
      <section className={`ambient-popup-card ${isConfirmed ? "ambient-popup-card--confirmed" : isSwipe || isRotate ? "ambient-popup-card--detected" : ""}`}>
        <div className="ambient-popup-header">
          <div>
            <span className="eyebrow ambient-popup-eyebrow">Ambientebeleuchtung</span>
            <h2>{statusText}</h2>
          </div>
          <span className={`ambient-popup-state ${isConfirmed ? "confirmed" : isSwipe || isRotate ? "detected" : ""}`}>
            {isConfirmed ? "Ausgeführt" : isSwipe || isRotate ? "Geste erkannt" : "Aktiv"}
          </span>
        </div>

        <div className="ambient-popup-content">
          <div className="ambient-popup-preview" aria-hidden>
            <div className="ambient-popup-glow" />
            <div className="ambient-popup-lamp">
              <span />
            </div>
          </div>

          <div className="ambient-popup-controls">
            <div className="ambient-popup-slider-row" aria-label={`Farbe ${state.ambientColor}`}>
              <span>Farbe</span>
              <div className="ambient-popup-slider rgb">
                <span className="ambient-popup-slider-handle" style={{ left: `${colorPosition}%` }} />
              </div>
            </div>

            <div className="ambient-popup-slider-row" aria-label={`Helligkeit ${brightnessPosition}%`}>
              <span>Helligkeit</span>
              <div className="ambient-popup-slider brightness">
                <span className="ambient-popup-slider-fill" style={{ width: `${brightnessPosition}%` }} />
                <span className="ambient-popup-slider-handle" style={{ left: `${brightnessPosition}%` }} />
              </div>
            </div>
          </div>
        </div>

        <div className="ambient-popup-gesture-row" aria-label="Erwartete Gesten">
          <span className={`ambient-popup-chip ${isSwipe ? "gesture-chip--detected" : ""}`}><span aria-hidden>↔</span>Swipe</span>
          <span className={`ambient-popup-chip ${isRotate ? "gesture-chip--detected" : ""}`}><span aria-hidden>↻</span>Drehen</span>
        </div>
      </section>
    </div>
  );
}

function FeedbackBadge({ decision, feedback }: { decision?: Decision | ""; feedback: string }) {
  return (
    <section className={`feedback ${decision || "idle"}`}>
      <span>{decision || "ready"}</span>
      <p>{feedback}</p>
    </section>
  );
}

function taskText(payload: WidgetPayload | null, completed: boolean, stepLabel: string): string {
  if (!payload) {
    return "Starte einen Trial in der Operator-GUI.";
  }
  if (completed) {
    return "Szenario abgeschlossen. Warte auf die nächste Aufgabe.";
  }
  const prefix = stepLabel ? `${stepLabel}: ` : "";
  return `${prefix}${payload.prompt || payload.overlay_body || "Aktiver Schritt"}`;
}

function guidanceFor(payload: WidgetPayload | null): string {
  if (!payload) {
    return "Der Operator startet die nächste Aufgabe.";
  }
  if (payload.condition === "Voice only") {
    return "Sprache verwenden. Gesten werden nicht gewertet.";
  }
  if (payload.condition === "Gesture only") {
    return "EMG-Gesten verwenden. Sprache wird nicht gewertet.";
  }
  if (payload.condition === "CAN use both") {
    return "Sprache, Geste oder beides möglich.";
  }
  return "Warte auf die aktive Study-Condition.";
}

// --- existing payload application logic preserved below ---
function applyPayload(current: CockpitState, payload: WidgetPayload): CockpitState {
  if (payload.event_type === "scenario_start") {
    return initializeForStep(createIdleState(), payload);
  }

  const decision = payload.decision ?? "";
  const updated = decision
    ? applyDecision(current, decision, current.activePayload?.task_id || payload.task_id)
    : current;

  if (payload.event_type === "trial_completed") {
    return {
      ...updated,
      activePayload: payload,
      completed: true,
      decision,
      feedback: "Szenario abgeschlossen. Warte auf die nächste Aufgabe.",
    };
  }

  if (payload.event_type === "step_update") {
    if (decision === "clarify") {
      return {
        ...updated,
        activePayload: payload,
        completed: false,
        decision,
        feedback: payload.clarification || payload.unclear_text || "Bitte Eingabe wiederholen.",
      };
    }
    return {
      ...initializeForStep(updated, payload),
      decision,
      feedback: payload.prompt || "Nächster Schritt aktiv.",
    };
  }

  return {
    ...updated,
    activePayload: payload,
    completed: false,
    decision,
    feedback: payload.prompt || payload.clarification || current.feedback,
  };
}

function initializeForStep(state: CockpitState, payload: WidgetPayload): CockpitState {
  const taskId = payload.task_id || "";
  return {
    ...state,
    activePayload: payload,
    completed: false,
    callIncoming: taskId === "CALL-INCOMING",
    callActive: taskId === "CALL-END" || taskId === "CALL-VOLUME",
    routeActive: taskId === "NAV-VOLUME-UP",
    routeIndex: taskId === "NAV-SELECT-SECOND" ? 2 : state.routeIndex,
    audioPlaying: taskId !== "AUDIO-RESUME",
    messageOpen: taskId === "MESSAGE-CLOSE",
    feedback: payload.prompt || state.feedback,
  };
}

function applyDecision(state: CockpitState, decision: Decision, taskId?: string): CockpitState {
  if (decision === "clarify") {
    return state;
  }

  if (decision === "cancel") {
    if (taskId === "CALL-INCOMING" || taskId === "CALL-END") {
      return { ...state, callIncoming: false, callActive: false };
    }
    if (taskId === "NAV-REJECT-ROUTE") {
      return { ...state, routeActive: false };
    }
    if (taskId === "MESSAGE-CLOSE") {
      return { ...state, messageOpen: false };
    }
    return state;
  }

  switch (taskId) {
    case "CALL-INCOMING":
      return { ...state, callIncoming: false, callActive: true };
    case "CALL-END":
      return { ...state, callIncoming: false, callActive: false };
    case "CALL-VOLUME":
      return { ...state, callActive: true, volume: Math.min(100, state.volume + 8) };
    case "AUDIO-SUGGESTION":
      return { ...state, audioPlaying: true, track: "Night Drive" };
    case "AUDIO-NEXT":
      return { ...state, audioPlaying: true, track: "City Lights" };
    case "AUDIO-LOUDER":
      return { ...state, volume: Math.min(100, state.volume + 8) };
    case "AUDIO-RESUME":
      return { ...state, audioPlaying: true };
    case "MESSAGE-OPEN":
      return { ...state, messageOpen: true };
    case "MESSAGE-CLOSE":
      return { ...state, messageOpen: false };
    case "NAV-ACCEPT-ROUTE":
      return { ...state, routeActive: true };
    case "NAV-NEXT-ROUTE":
      return { ...state, routeIndex: 2 };
    case "NAV-SELECT-SECOND":
      return { ...state, routeActive: true, routeIndex: 2 };
    case "NAV-VOLUME-UP":
      return { ...state, routeActive: true, volume: Math.min(100, state.volume + 8) };
    case "AMBIENT-COLOR":
      return { ...state, ambientColor: "Warm" };
    case "AMBIENT-BRIGHTER":
      return { ...state, ambientBrightness: Math.min(100, state.ambientBrightness + 15) };
    case "AMBIENT-NIGHTMODE":
      return { ...state, ambientColor: "Warm", ambientBrightness: Math.max(30, state.ambientBrightness - 10) };
    case "CLIMATE-SEAT-HEAT":
      return { ...state, seatLevel: Math.max(1, state.seatLevel) };
    case "CLIMATE-SEAT-WARMER":
      return { ...state, seatLevel: Math.min(3, state.seatLevel + 1) };
    default:
      return state;
  }
}

createRoot(document.getElementById("root") as HTMLElement).render(<App />);
