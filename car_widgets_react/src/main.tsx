import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import type { Decision, LatestResponse, WidgetPayload } from "./types";
import { AudioWidget as AudioPopupDomainWidget } from "./widgets/AudioWidget";
import { CallWidget as CallPopupDomainWidget } from "./widgets/CallWidget";
import { MessageWidget as MessagePopupDomainWidget } from "./widgets/MessageWidget";
import { NavigationWidget as NavigationPopupDomainWidget } from "./widgets/NavigationWidget";
import {
  normalizeGestureLabel,
  popupModalityVisibility,
  previewChipProps,
  type CockpitState,
  type PreviewGesture,
} from "./widgets/shared";
import "./styles.css";

const bridgeUrl = import.meta.env.VITE_WIDGET_EVENT_URL ?? "http://127.0.0.1:8765/latest";

type PreviewScenario =
  | "off"
  | "study-1-1"
  | "study-2-1"
  | "study-3-1"
  | "study-4-1"
  | "study-1-2"
  | "study-2-2"
  | "study-3-2"
  | "study-4-2"
  | "study-1-3"
  | "study-2-3"
  | "study-3-3"
  | "study-4-3";


function createIdleState(): CockpitState {
  return {
    activePayload: null,
    completed: false,
    feedback: "Warte auf nächste Aufgabe.",
    decision: "",
    callActive: false,
    callIncoming: false,
    callEnded: false,
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
  const [previewGesture, setPreviewGesture] = useState<PreviewGesture | null>(null);
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

  useEffect(() => {
    setPreviewGesture(null);
  }, [previewScenario]);

  const livePayload = state.activePayload;
  // Temporary UI preview helper for popup/widget design. Remove or disable before final study run.
  const previewBasePayload = useMemo(() => createPreviewPayload(previewScenario), [previewScenario]);
  const previewPayload = useMemo(
    () => applyPreviewGesture(previewBasePayload, previewGesture),
    [previewBasePayload, previewGesture],
  );
  const previewModeActive = previewScenario !== "off";
  const isTerminalLivePayload = livePayload?.event_type === "trial_completed" && livePayload.success === false;
  const visibleLivePayload = isTerminalLivePayload ? null : livePayload;
  const displayPayload = previewModeActive ? previewPayload : visibleLivePayload;
  const displayState = useMemo(() => createPreviewState(state, previewScenario, previewPayload), [state, previewScenario, previewPayload]);
  const shouldShowPopup = Boolean(
    (previewModeActive && previewPayload) ||
    (!previewModeActive && visibleLivePayload && (
      visibleLivePayload.event_type === "scenario_start" ||
      visibleLivePayload.event_type === "step_update" ||
      visibleLivePayload.event_type === "trial_completed"
    ))
  );
  const previewControlLabel = previewPayload ? previewScenarioDisplayLabel(previewScenario) : liveScenarioLabel(visibleLivePayload);
  const handlePreviewGesture = (gesture: PreviewGesture) => {
    setPreviewGesture(gesture);
  };
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

      {shouldShowPopup && (
        <InteractionPopup
          payload={displayPayload}
          state={displayState}
          onPreviewGesture={previewModeActive ? handlePreviewGesture : undefined}
        />
      )}

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
          <optgroup label="Voice only">
            <option value="study-1-1">1.1 Voice · Call</option>
            <option value="study-2-1">2.1 Voice · Audio</option>
            <option value="study-3-1">3.1 Voice · Messages</option>
            <option value="study-4-1">4.1 Voice · Navigation</option>
          </optgroup>
          <optgroup label="Gesture only">
            <option value="study-1-2">1.2 Gesture · Audio</option>
            <option value="study-2-2">2.2 Gesture · Climate</option>
            <option value="study-3-2">3.2 Gesture · Navigation</option>
            <option value="study-4-2">4.2 Gesture · Ambient Light</option>
          </optgroup>
          <optgroup label="CAN use both">
            <option value="study-1-3">1.3 Both · Navigation</option>
            <option value="study-2-3">2.3 Both · Ambient Light</option>
            <option value="study-3-3">3.3 Both · Audio</option>
            <option value="study-4-3">4.3 Both · Call</option>
          </optgroup>
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

  if (payload.domain === "calls" && (payload.task_id === "CALL-INCOMING" || payload.task_id === "CALL-ACTIVE" || payload.task_id === "CALL-ENDED")) {
    return `Live · ${domainLabel} · ${confirmedStateLabel(payload)}`;
  }

  if (payload.decision === "clarify") {
    return `Live · ${domainLabel} · Clarify`;
  }
  if (payload.decision === "execute" || payload.event_type === "trial_completed" || gestureLabel === "Daumen hoch") {
    return `Live · ${domainLabel} · ${confirmedStateLabel(payload)}`;
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

function confirmedStateLabel(payload: WidgetPayload): string {
  if (payload.domain === "calls") {
    if (payload.task_id === "CALL-ENDED") {
      return "Ended";
    }
    if (payload.task_id === "CALL-ACTIVE") {
      return "Ongoing";
    }
    if (payload.task_id === "CALL-INCOMING") {
      return "Incoming";
    }
  }

  switch (payload.domain) {
    case "navigation":
      return "Accepted";
    case "audio":
      if (payload.task_id === "AUDIO-VOLUME-UP") {
        return "Lautstärke erhöht";
      }
      return "Playing";
    case "messages":
      return "Opened";
    default:
      return "Confirmed";
  }
}

function previewScenarioDisplayLabel(previewScenario: PreviewScenario): string {
  switch (previewScenario) {
    case "study-1-1": return "1.1 Voice · Call";
    case "study-2-1": return "2.1 Voice · Audio";
    case "study-3-1": return "3.1 Voice · Messages";
    case "study-4-1": return "4.1 Voice · Navigation";
    case "study-1-2": return "1.2 Gesture · Audio";
    case "study-2-2": return "2.2 Gesture · Climate";
    case "study-3-2": return "3.2 Gesture · Navigation";
    case "study-4-2": return "4.2 Gesture · Ambient Light";
    case "study-1-3": return "1.3 Both · Navigation";
    case "study-2-3": return "2.3 Both · Ambient Light";
    case "study-3-3": return "3.3 Both · Audio";
    case "study-4-3": return "4.3 Both · Call";
    case "off":
    default:
      return "Off / Live middleware";
  }
}

function createPreviewPayload(previewScenario: PreviewScenario): WidgetPayload | null {
  const scenarioPayload = (
    studyRef: string,
    condition: WidgetPayload["condition"],
    fields: WidgetPayload,
  ): WidgetPayload => ({
    step_index: 0,
    step_count: studyRef === "1.1" ? 3 : 2,
    event_type: "scenario_start",
    study_ref: studyRef,
    scenario_id: `STUDY-${studyRef}`,
    condition,
    source: { used_modalities: "none" },
    ...fields,
  });

  switch (previewScenario) {
    case "study-1-1":
      return scenarioPayload("1.1", "Voice only", {
        domain: "calls",
        scenario_prompt: "Anruf annehmen und beenden. Steps: Anruf kommt rein. -> Call läuft. -> Anruf beendet.",
        task_id: "CALL-INCOMING",
        prompt: "Anruf kommt rein.",
        overlay_title: "Eingehender Anruf",
        overlay_body: "Alex ruft an.",
        modality: "voice",
        expected_decision: "execute",
        expected_voice: "Annehmen",
        accepted_text: "Anruf angenommen.",
        unclear_text: "Möchtest du den Anruf annehmen?",
      });
    case "study-2-1":
      return scenarioPayload("2.1", "Voice only", {
        domain: "audio",
        scenario_prompt: "Nächster Song und lauter. Steps: Song läuft. -> Nächstes Lied spielt.",
        task_id: "AUDIO-NEXT",
        prompt: "Song läuft.",
        overlay_title: "Audio",
        overlay_body: "Low Beam wird abgespielt.",
        modality: "voice",
        expected_decision: "execute",
        expected_voice: "Nächstes Lied",
        accepted_text: "Nächstes Lied spielt.",
        unclear_text: "Soll das nächste Lied abgespielt werden?",
      });
    case "study-3-1":
      return scenarioPayload("3.1", "Voice only", {
        domain: "messages",
        scenario_prompt: "Nachricht öffnen und schließen. Steps: Nachricht kommt rein. -> Nachricht ist geöffnet.",
        task_id: "MESSAGE-OPEN",
        prompt: "Nachricht kommt rein.",
        overlay_title: "Neue Nachricht",
        overlay_body: "Mia: Bin in 5 Minuten da.",
        modality: "voice",
        expected_decision: "execute",
        expected_voice: "Öffnen",
        accepted_text: "Nachricht geöffnet.",
        unclear_text: "Soll die Nachricht geöffnet werden?",
      });
    case "study-4-1":
      return scenarioPayload("4.1", "Voice only", {
        domain: "navigation",
        scenario_prompt: "Navigation annehmen und Ansagen lauter. Steps: Navigation wird vorgeschlagen. -> Navigation läuft.",
        task_id: "NAV-ACCEPT-ROUTE",
        prompt: "Navigation wird vorgeschlagen.",
        overlay_title: "Navigationsvorschlag",
        overlay_body: "Zielroute ist verfügbar.",
        modality: "voice",
        expected_decision: "execute",
        expected_voice: "Annehmen",
        accepted_text: "Navigation läuft.",
        unclear_text: "Soll die Navigation gestartet werden?",
      });
    case "study-1-2":
      return scenarioPayload("1.2", "Gesture only", {
        domain: "audio",
        scenario_prompt: "Musikvorschlag annehmen und nächster Titel. Steps: Songvorschlag wird angezeigt. -> Wiedergabe läuft.",
        task_id: "AUDIO-SUGGESTION",
        prompt: "Songvorschlag wird angezeigt.",
        overlay_title: "Musikvorschlag",
        overlay_body: "Vorgeschlagen: Night Drive.",
        modality: "gesture",
        expected_decision: "execute",
        expected_gesture: "Daumen hoch",
        gesture_ref: "1",
        accepted_text: "Musikvorschlag angenommen.",
        unclear_text: "Soll der Musikvorschlag angenommen werden?",
      });
    case "study-2-2":
      return scenarioPayload("2.2", "Gesture only", {
        domain: "climate",
        scenario_prompt: "Sitzheizung auswählen und erhöhen. Steps: Beide Sitze sind niedrig. -> Beifahrersitz wird ausgewählt. -> Beifahrersitzheizung wird erhöht.",
        task_id: "CLIMATE-SEAT-HEAT",
        prompt: "Beide Sitze sind niedrig.",
        overlay_title: "Sitzheizung",
        overlay_body: "Fahrer: niedrig. Beifahrer: niedrig.",
        modality: "gesture",
        expected_decision: "execute",
        expected_gesture: "Swipe",
        gesture_ref: "3",
        accepted_text: "Sitzheizung ausgewählt.",
        unclear_text: "Soll die Sitzheizung ausgewählt werden?",
      });
    case "study-3-2":
      return scenarioPayload("3.2", "Gesture only", {
        domain: "navigation",
        scenario_prompt: "Route auswählen. Steps: 2 Routenvorschläge werden angezeigt. -> Route 2 wird ausgewählt. -> Route 2 startet.",
        task_id: "NAV-NEXT-ROUTE",
        prompt: "Route auswählen.",
        overlay_title: "Route auswählen",
        overlay_body: "Route 1: Schnellste Route · 18 min. Route 2: Ruhigere Route · 21 min.",
        modality: "gesture",
        expected_decision: "execute",
        expected_gesture: "Swipe",
        gesture_ref: "3",
        accepted_text: "Route 2 ausgewählt.",
        unclear_text: "Soll Route 2 ausgewählt werden?",
      });
    case "study-4-2":
      return scenarioPayload("4.2", "Gesture only", {
        domain: "ambient_light",
        scenario_prompt: "Nachtmodus annehmen und Ambientelicht heller. Steps: Popup: zu Nachtmodus wechseln. -> Ambientebeleuchtung ist aktiv.",
        task_id: "AMBIENT-NIGHTMODE",
        prompt: "Popup: zu Nachtmodus wechseln.",
        overlay_title: "Nachtmodus",
        overlay_body: "Das System schlägt Nachtmodus vor.",
        modality: "gesture",
        expected_decision: "execute",
        expected_gesture: "Daumen hoch",
        gesture_ref: "1",
        accepted_text: "Nachtmodus angenommen.",
        unclear_text: "Soll der Nachtmodus aktiviert werden?",
      });
    case "study-1-3":
      return scenarioPayload("1.3", "CAN use both", {
        domain: "navigation",
        scenario_prompt: "Route annehmen und Routenänderung ablehnen. Steps: Route wird vorgeschlagen. -> Routenänderung wird vorgeschlagen.",
        task_id: "NAV-ACCEPT-ROUTE",
        prompt: "Route wird vorgeschlagen.",
        overlay_title: "Routenvorschlag",
        overlay_body: "Schnellste Route: 18 Minuten.",
        modality: "voice+gesture",
        expected_decision: "execute",
        expected_voice: "Annehmen",
        expected_gesture: "Daumen hoch",
        gesture_ref: "1",
        accepted_text: "Route übernommen.",
        unclear_text: "Soll diese Route übernommen werden?",
      });
    case "study-2-3":
      return scenarioPayload("2.3", "CAN use both", {
        domain: "ambient_light",
        scenario_prompt: "Ambientefarbe wechseln und heller machen. Steps: Ambientebeleuchtung ist aktiv. -> Neue Farbe ist aktiv.",
        task_id: "AMBIENT-COLOR",
        prompt: "Ambientebeleuchtung ist aktiv.",
        overlay_title: "Ambientebeleuchtung",
        overlay_body: "Aktuelle Farbe: Blau.",
        modality: "voice+gesture",
        expected_decision: "execute",
        expected_voice: "Farbe wechseln",
        expected_gesture: "Swipe",
        gesture_ref: "3",
        accepted_text: "Farbe gewechselt.",
        unclear_text: "Soll die Lichtfarbe gewechselt werden?",
      });
    case "study-3-3":
      return scenarioPayload("3.3", "CAN use both", {
        domain: "audio",
        scenario_prompt: "Wiedergabe fortsetzen und nächster Song. Steps: Song ist pausiert. -> Song läuft.",
        task_id: "AUDIO-RESUME",
        prompt: "Song ist pausiert.",
        overlay_title: "Audio pausiert",
        overlay_body: "Low Beam ist pausiert.",
        modality: "voice+gesture",
        expected_decision: "execute",
        expected_voice: "Wiedergabe fortsetzen",
        expected_gesture: "Zeigen / Tippen",
        gesture_ref: "5",
        accepted_text: "Song wird abgespielt.",
        unclear_text: "Soll die Wiedergabe fortgesetzt werden?",
      });
    case "study-4-3":
      return scenarioPayload("4.3", "CAN use both", {
        domain: "calls",
        scenario_prompt: "Anruf annehmen und Lautstärke regeln. Steps: Anruf kommt rein. -> Call läuft.",
        task_id: "CALL-INCOMING",
        prompt: "Anruf kommt rein.",
        overlay_title: "Eingehender Anruf",
        overlay_body: "Alex ruft an.",
        modality: "voice+gesture",
        expected_decision: "execute",
        expected_voice: "Annehmen",
        expected_gesture: "Daumen hoch",
        gesture_ref: "1",
        accepted_text: "Anruf angenommen.",
        unclear_text: "Möchtest du den Anruf annehmen?",
      });
    default:
      return null;
  }
}

function voiceStepPayload(payload: WidgetPayload, fields: Partial<WidgetPayload>): WidgetPayload {
  return {
    ...payload,
    ...fields,
    event_type: "step_update",
    source: {
      ...payload.source,
      used_modalities: "voice",
      gesture_event: undefined,
    },
  };
}

function applyPreviewGesture(payload: WidgetPayload | null, gesture: PreviewGesture | null): WidgetPayload | null {
  if (!payload || !gesture) {
    return payload;
  }

  if (payload.study_ref === "1.1" || payload.scenario_id === "STUDY-1.1") {
    if (payload.task_id === "CALL-ACTIVE") {
      return voiceStepPayload(payload, {
        task_id: "CALL-ENDED",
        prompt: "Anruf beendet.",
        overlay_title: "Anruf beendet",
        overlay_body: "Gespräch beendet.",
        expected_voice: "",
        accepted_text: "Anruf beendet.",
        unclear_text: "",
        decision: "execute",
        step_index: 2,
      });
    }

    if (payload.task_id === "CALL-ENDED") {
      return voiceStepPayload(payload, {
        task_id: "CALL-ENDED",
        prompt: "Anruf beendet.",
        overlay_title: "Anruf beendet",
        overlay_body: "Gespräch beendet.",
        expected_voice: "",
        accepted_text: "Anruf beendet.",
        unclear_text: "",
        decision: "execute",
        step_index: 2,
      });
    }

    const isReject = gesture === "Ablehnen" || gesture === "Swipe";
    const isAccept = gesture === "Annehmen" || gesture === "Daumen hoch";
    return voiceStepPayload(payload, {
      task_id: isAccept ? "CALL-ACTIVE" : isReject ? "CALL-ENDED" : "CALL-INCOMING",
      prompt: isAccept ? "Call läuft." : isReject ? "Anruf beendet." : "Anruf kommt rein.",
      overlay_title: isAccept ? "Aktiver Anruf" : isReject ? "Anruf beendet" : "Eingehender Anruf",
      overlay_body: isAccept ? "Anruf mit Alex läuft." : isReject ? "Alex hat aufgelegt." : "Alex ruft an.",
      expected_voice: isAccept ? "Beenden" : isReject ? "Ablehnen" : "Annehmen",
      accepted_text: isAccept ? "Anruf angenommen." : isReject ? "Anruf beendet." : "Anruf angenommen.",
      rejected_text: "Anruf beendet.",
      unclear_text: isAccept ? "Soll der Anruf beendet werden?" : isReject ? "Möchtest du den Anruf ablehnen?" : "Möchtest du den Anruf annehmen?",
      decision: isReject ? "cancel" : "execute",
      step_index: isAccept ? 1 : isReject ? 2 : 0,
    });
  }

  if (payload.study_ref === "2.1" || payload.scenario_id === "STUDY-2.1") {
    const isLouder = gesture === "Lauter" || gesture === "Lauter machen" || gesture === "Handgelenk drehen";
    return voiceStepPayload(payload, {
      task_id: isLouder ? "AUDIO-VOLUME-UP" : "AUDIO-NEXT",
      event_type: isLouder ? "trial_completed" : "step_update",
      prompt: isLouder ? "Lautstärke erhöht." : "Nächstes Lied spielt.",
      overlay_title: "Audio",
      overlay_body: isLouder ? "City Lights wird lauter abgespielt." : "City Lights wird abgespielt.",
      expected_voice: isLouder ? "Lauter" : "Lauter",
      accepted_text: isLouder ? "Lautstärke erhöht." : "Nächstes Lied spielt.",
      unclear_text: isLouder ? "Soll die Musik lauter werden?" : "Soll das nächste Lied abgespielt werden?",
      decision: "execute",
      step_index: isLouder ? 1 : 0,
    });
  }

  if (payload.study_ref === "3.1" || payload.scenario_id === "STUDY-3.1") {
    const isClose = gesture === "Schließen" || gesture === "Swipe";
    return voiceStepPayload(payload, {
      task_id: isClose ? "MESSAGE-CLOSE" : "MESSAGE-OPEN",
      prompt: isClose ? "Nachricht ist geöffnet." : "Nachricht kommt rein.",
      overlay_title: isClose ? "Nachricht" : "Neue Nachricht",
      overlay_body: "Mia: Bin in 5 Minuten da.",
      expected_voice: isClose ? "Schließen" : "Nachricht öffnen",
      accepted_text: isClose ? "Nachricht geschlossen." : "Nachricht geöffnet.",
      unclear_text: isClose ? "Soll die Nachricht geschlossen werden?" : "Soll die Nachricht geöffnet werden?",
      decision: "execute",
      step_index: isClose ? 1 : 0,
    });
  }

  if (payload.study_ref === "4.1" || payload.scenario_id === "STUDY-4.1") {
    const isLouder = gesture === "Lauter" || gesture === "Lauter machen" || gesture === "Handgelenk drehen";
    const isDecline = gesture === "Ablehnen" || gesture === "Swipe";
    const isAccept = gesture === "Annehmen" || gesture === "Daumen hoch";
    return voiceStepPayload(payload, {
      task_id: isLouder ? "NAV-VOLUME-UP" : isAccept ? "NAV-ACTIVE" : "NAV-ACCEPT-ROUTE",
      prompt: isLouder || isAccept ? "Navigation läuft." : "Navigation wird vorgeschlagen.",
      overlay_title: isLouder ? "Navigationsansagen" : isAccept ? "Navigation aktiv" : "Navigationsvorschlag",
      overlay_body: isLouder ? "Ansagelautstärke: 40 Prozent." : isAccept ? "Route ist aktiv. Ansagelautstärke: normal." : "Zielroute ist verfügbar.",
      expected_voice: isLouder || isAccept ? "Lauter" : isDecline ? "Ablehnen" : "Annehmen",
      accepted_text: isLouder ? "Navigationsansagen lauter gemacht." : "Navigation läuft.",
      rejected_text: "Navigation abgelehnt.",
      unclear_text: isLouder ? "Sollen die Navigationsansagen lauter werden?" : "Soll die Navigation gestartet werden?",
      decision: isDecline ? "cancel" : isAccept || isLouder ? "execute" : undefined,
      step_index: isLouder ? 2 : isAccept ? 1 : 0,
    });
  }

  if (payload.study_ref === "1.3" || payload.scenario_id === "STUDY-1.3") {
    if (payload.task_id === "NAV-ACCEPT-ROUTE") {
      const isAccept = gesture === "Annehmen" || gesture === "Daumen hoch";
      return voiceStepPayload(payload, {
        task_id: "NAV-ACCEPT-ROUTE",
        prompt: "Route wird vorgeschlagen.",
        overlay_title: "Routenvorschlag",
        overlay_body: "Schnellste Route: 18 Minuten.",
        expected_voice: "Annehmen",
        expected_gesture: "Daumen hoch",
        gesture_ref: "1",
        accepted_text: "Route übernommen.",
        unclear_text: "Soll diese Route übernommen werden?",
        decision: isAccept ? "execute" : "execute",
        step_index: 0,
      });
    }

    const isReject = gesture === "Ablehnen" || gesture === "Swipe";
    return voiceStepPayload(payload, {
      task_id: "NAV-REJECT-ROUTE",
      prompt: "Routenänderung wird vorgeschlagen.",
      overlay_title: "Routenänderung",
      overlay_body: "Alternative Route spart 2 Minuten.",
      expected_voice: "Ablehnen",
      expected_gesture: "Swipe",
      gesture_ref: "2",
      accepted_text: "Route abgelehnt.",
      rejected_text: "Route abgelehnt.",
      unclear_text: "Soll die Routenänderung abgelehnt werden?",
      decision: isReject ? "cancel" : "execute",
      step_index: 1,
    });
  }

  const nextPayload: WidgetPayload = {
    ...payload,
    source: {
      ...payload.source,
      used_modalities: "gesture",
      gesture_event: {
        gesture_label: gesture,
        gesture_id: gesture === "Daumen hoch" ? 1 : gesture === "Swipe" ? 3 : gesture === "Handgelenk drehen" ? 4 : 5,
        source: "preview",
        confidence: null,
      },
    },
  };

  if (payload.study_ref === "3.2" || payload.scenario_id === "STUDY-3.2") {
    const isTap = gesture === "Zeigen / Tippen" || gesture === "Zeigen/Tippen" || gesture === "Zeigen" || gesture === "Tippen";
    const isSecondStep = payload.step_index === 1 || payload.task_id === "NAV-SELECT-SECOND";
    const isConfirmed = isTap || (isSecondStep && payload.decision === "execute");
    const nextTaskId = isConfirmed ? "NAV-SELECT-SECOND" : "NAV-NEXT-ROUTE";
    return {
      ...nextPayload,
      task_id: nextTaskId,
      prompt: isConfirmed ? "Route 2 ist ausgewählt." : "Route auswählen.",
      overlay_title: "Route auswählen",
      overlay_body: "Route 1: Schnellste Route · 18 min. Route 2: Ruhigere Route · 21 min.",
      expected_decision: "execute",
      expected_gesture: isConfirmed ? "Zeigen / Tippen" : "Swipe",
      gesture_ref: isConfirmed ? "5" : "3",
      accepted_text: isConfirmed ? "Route 2 gestartet." : "Route 2 ausgewählt.",
      unclear_text: "Bitte Route 2 auswählen und dann bestätigen.",
      decision: isConfirmed ? "execute" : nextPayload.decision,
      step_index: isConfirmed ? 1 : 0,
      source: {
        ...nextPayload.source,
        used_modalities: "gesture",
        gesture_event: {
          gesture_label: gesture,
          gesture_id: gesture === "Swipe" ? 3 : 5,
          source: "preview",
          confidence: null,
        },
      },
    };
  }

  if (payload.study_ref === "2.2" || payload.scenario_id === "STUDY-2.2") {
    const isSwipe = gesture === "Swipe";
    const isRotate = gesture === "Handgelenk drehen";
    const isHeatingStep = normalizeGestureLabel(payload.expected_gesture) === "handgelenkdrehen" || payload.task_id === "CLIMATE-SEAT-WARMER";
    const isPassengerSelected = isSwipe || (!isHeatingStep && payload.task_id === "CLIMATE-SEAT-HEAT") || (payload.task_id === "CLIMATE-SEAT-WARMER" && !isRotate);
    const isHeatIncreased = isRotate;
    return {
      ...nextPayload,
      task_id: isHeatIncreased ? "CLIMATE-SEAT-WARMER" : "CLIMATE-SEAT-HEAT",
      prompt: isHeatIncreased ? "Beifahrersitzheizung erhöht." : isPassengerSelected ? "Beifahrersitz ausgewählt." : "Beide Sitze sind niedrig.",
      overlay_title: "Sitzheizung",
      overlay_body: isHeatIncreased
        ? "Beifahrersitzheizung ist auf mittel."
        : isPassengerSelected
          ? "Beifahrersitz ist ausgewählt."
          : "Fahrer: niedrig. Beifahrer: niedrig.",
      expected_decision: "execute",
      expected_gesture: isHeatIncreased ? "Handgelenk drehen" : "Swipe",
      gesture_ref: isHeatIncreased ? "4" : "3",
      accepted_text: isHeatIncreased ? "Beifahrersitzheizung erhöht." : "Beifahrersitz ausgewählt.",
      unclear_text: isHeatIncreased ? "Soll die Beifahrersitzheizung erhöht werden?" : "Soll der Beifahrersitz ausgewählt werden?",
      decision: isHeatIncreased ? "execute" : nextPayload.decision,
      step_index: isHeatIncreased ? 1 : 0,
      source: {
        ...nextPayload.source,
        used_modalities: "gesture",
        gesture_event: {
          gesture_label: gesture,
          gesture_id: gesture === "Swipe" ? 3 : 4,
          source: "preview",
          confidence: null,
        },
      },
    };
  }

  if (payload.study_ref === "1.2" || payload.scenario_id === "STUDY-1.2") {
    if (gesture === "Daumen hoch") {
      return {
        ...nextPayload,
        task_id: "AUDIO-SUGGESTION",
        prompt: "Songvorschlag wird angezeigt.",
        overlay_title: "Musikvorschlag",
        overlay_body: "Vorgeschlagen: Night Drive.",
        expected_gesture: "Daumen hoch",
        gesture_ref: "1",
        accepted_text: "Musikvorschlag angenommen.",
        unclear_text: "Soll der Musikvorschlag angenommen werden?",
        decision: "execute",
        step_index: 0,
      };
    }

    return {
      ...nextPayload,
      task_id: "AUDIO-NEXT",
      prompt: "Wiedergabe läuft.",
      overlay_title: "Audio",
      overlay_body: "Night Drive wird abgespielt.",
      expected_gesture: "Swipe",
      gesture_ref: "3",
      accepted_text: "Nächster Titel wird abgespielt.",
      unclear_text: "Soll der nächste Titel abgespielt werden?",
      decision: "execute",
      step_index: 1,
    };
  }

  if (payload.task_id === "CLIMATE-SEAT-HEAT" && gesture === "Handgelenk drehen") {
    return {
      ...nextPayload,
      task_id: "CLIMATE-SEAT-WARMER",
      prompt: "Sitzheizung ist ausgewählt.",
      overlay_title: "Sitzheizung",
      overlay_body: "Aktuelle Stufe: 1.",
      expected_gesture: "Handgelenk drehen",
      gesture_ref: "4",
      step_index: 1,
    };
  }

  if (payload.task_id === "AUDIO-RESUME" && gesture === "Swipe") {
    return {
      ...nextPayload,
      task_id: "AUDIO-NEXT",
      prompt: "Song läuft.",
      overlay_title: "Audio",
      overlay_body: "Low Beam wird abgespielt.",
      expected_gesture: "Swipe",
      gesture_ref: "3",
      step_index: 1,
    };
  }

  return nextPayload;
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
    case "study-1-1":
      if (previewPayload.task_id === "CALL-ACTIVE") {
        return { ...previewState, callIncoming: false, callActive: true, callEnded: false };
      }
      if (previewPayload.task_id === "CALL-ENDED") {
        return { ...previewState, callIncoming: false, callActive: false, callEnded: true };
      }
      return { ...previewState, callIncoming: true, callActive: false, callEnded: false };
    case "study-4-3":
      return { ...previewState, callIncoming: true, callActive: false, callEnded: false };
    case "study-2-1":
      return { ...previewState, audioPlaying: true, track: "Low Beam" };
    case "study-3-1":
      return { ...previewState, messageOpen: false };
    case "study-4-1":
    case "study-1-3":
      return { ...previewState, routeActive: true, routeIndex: 1 };
    case "study-1-2":
      return { ...previewState, audioPlaying: false, track: "Night Drive" };
    case "study-2-2":
      return { ...previewState, seatLevel: 1 };
    case "study-3-2":
      return { ...previewState, routeActive: true, routeIndex: 1 };
    case "study-4-2":
      return { ...previewState, ambientColor: "Warm", ambientBrightness: 35 };
    case "study-2-3":
      return { ...previewState, ambientColor: "Blau", ambientBrightness: 45 };
    case "study-3-3":
      return { ...previewState, audioPlaying: false, track: "Low Beam" };
    case "off":
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

function InteractionPopup({
  payload,
  state,
  onPreviewGesture,
}: {
  payload: WidgetPayload | null;
  state: CockpitState;
  onPreviewGesture?: (gesture: PreviewGesture) => void;
}) {
  if (!payload) return null;

  if (payload.domain === "ambient_light") {
    return <AmbientPopupWidget payload={payload} state={state} onPreviewGesture={onPreviewGesture} />;
  }

  if (isCallDomain(payload.domain)) {
    return <CallPopupDomainWidget payload={payload} state={state} onPreviewGesture={onPreviewGesture} />;
  }

  if (isNavigationDomain(payload.domain)) {
    return <NavigationPopupDomainWidget payload={payload} state={state} onPreviewGesture={onPreviewGesture} />;
  }

  if (isAudioDomain(payload.domain)) {
    return <AudioPopupDomainWidget payload={payload} state={state} onPreviewGesture={onPreviewGesture} />;
  }

  if (isMessagesDomain(payload.domain)) {
    return <MessagePopupDomainWidget payload={payload} state={state} onPreviewGesture={onPreviewGesture} />;
  }

  if (isClimateDomain(payload.domain)) {
    return <ClimatePopupWidget payload={payload} state={state} onPreviewGesture={onPreviewGesture} />;
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
            <button className="pill accept" aria-label="Annehmen" onClick={onPreviewGesture ? () => onPreviewGesture("Daumen hoch") : undefined}>✔ Annehmen</button>
            <button className="pill decline" aria-label="Ablehnen" onClick={onPreviewGesture ? () => onPreviewGesture("Swipe") : undefined}>✖ Ablehnen</button>
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










function ClimatePopupWidget({ payload, state, onPreviewGesture }: { payload: WidgetPayload; state: CockpitState; onPreviewGesture?: (gesture: PreviewGesture) => void }) {
  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const normalizedGesture = normalizeGestureLabel(gestureLabel);
  const isClarify = payload.decision === "clarify";
  const isWaiting = !isClarify && !payload.decision && !gestureLabel;
  const clarifyText = payload.unclear_text || payload.prompt || "Bitte Eingabe wiederholen.";
  const isScenario22 = isClimateScenario22(payload);
  const scenario22Stage = isScenario22 ? climateScenario22Stage(payload) : "standard";
  const isPassengerSelectedStage = scenario22Stage === "passenger_selected";
  const isHeatIncreasedStage = scenario22Stage === "heat_increased";
  const isCompletedStage = scenario22Stage === "completed";
  const hasRotatedToIncreaseHeat = isScenario22 && (normalizedGesture === "handgelenkdrehen" || isHeatIncreasedStage || isCompletedStage);
  const hasSwipeSelectedPassenger = isScenario22 && !hasRotatedToIncreaseHeat && (normalizedGesture === "swipe" || isPassengerSelectedStage || (payload.task_id === "CLIMATE-SEAT-WARMER" && !gestureLabel));
  const isSeatSelectTask = payload.task_id === "CLIMATE-SEAT-HEAT";
  const isIncreaseTask = payload.task_id === "CLIMATE-SEAT-WARMER" || payload.task_id === "CLIMATE-INCREASE";
  const isSwipe = normalizedGesture === "swipe";
  const isAdjusting = !isClarify && isIncreaseTask && gestureLabel === "Handgelenk drehen";
  const isSelectingSeatHeat = !isClarify && isSeatSelectTask && (isSwipe || payload.decision === "execute");
  const isSuccess = !isClarify && !isSeatSelectTask && (gestureLabel === "Daumen hoch" || payload.decision === "execute");
  const isCancelled = !isClarify && !isSeatSelectTask && (isSwipe || payload.decision === "cancel");
  const { showVoiceActions, showGestureActions } = popupModalityVisibility(payload);
  const driverSeatLevel = 1;
  const passengerSeatLevel = hasRotatedToIncreaseHeat ? 2 : 1;
  const selectedSeat = isScenario22
    ? hasSwipeSelectedPassenger || hasRotatedToIncreaseHeat
      ? 2
      : 1
    : isSeatSelectTask && isSelectingSeatHeat
      ? 2
      : 1;
  const stageClass = isClarify
    ? "climate-popup--clarify"
    : isScenario22
      ? isCompletedStage
        ? "climate-popup--scenario22-completed"
        : isHeatIncreasedStage
          ? "climate-popup--scenario22-heat"
          : isPassengerSelectedStage
            ? "climate-popup--scenario22-selected"
            : "climate-popup--scenario22-waiting"
    : isSelectingSeatHeat
      ? "climate-popup--selecting"
      : isSuccess
        ? "climate-popup--success"
      : isCancelled
        ? "climate-popup--cancelled"
        : isAdjusting
          ? "climate-popup--adjusting"
          : "climate-popup--active";
  const body = isClarify
    ? payload.overlay_body || "Sitzheizung einstellen."
    : isScenario22
      ? hasRotatedToIncreaseHeat
        ? "Beifahrersitzheizung erhöht."
        : hasSwipeSelectedPassenger
          ? "Beifahrersitz ausgewählt."
          : "Fahrer: niedrig. Beifahrer: niedrig."
    : isSelectingSeatHeat
      ? payload.accepted_text || "Sitzheizung ausgewählt."
      : isSuccess
        ? payload.accepted_text || "Sitzheizung aktualisiert"
        : isCancelled
          ? payload.rejected_text || "Änderung abgebrochen"
          : isAdjusting
            ? payload.accepted_text || "Sitzheizung angepasst"
            : payload.overlay_body || payload.prompt || "Sitz 1 wird wärmer gestellt.";
  const statusBadge = isScenario22
    ? hasRotatedToIncreaseHeat
      ? "Drehen erkannt"
      : hasSwipeSelectedPassenger
        ? "Swipe erkannt"
        : "Swipe zum Wechseln / Auswählen"
    : isAdjusting
      ? "Drehen erkannt"
      : isSelectingSeatHeat
        ? "Swipe erkannt"
        : "";
  const stageHint = isScenario22
    ? hasRotatedToIncreaseHeat
      ? "Stufe 2"
      : hasSwipeSelectedPassenger
        ? "Jetzt drehen zum Erhöhen"
        : "Swipe zum Wechseln / Auswählen"
    : isSelectingSeatHeat
      ? "Sitzheizung auswählen"
      : isAdjusting
        ? "Temperatur erhöht"
        : "";
  const scenario22SwipeActive = hasSwipeSelectedPassenger || hasRotatedToIncreaseHeat;
  const scenario22RotateActive = hasRotatedToIncreaseHeat;
  const renderHeatDots = (level: number) => (
    <span className="climate-popup__heat-levels" aria-hidden>
      {[1, 2, 3].map((dot) => (
        <span key={dot} className={`climate-popup__heat-dot ${dot <= level ? "climate-popup__heat-dot--active" : ""}`} />
      ))}
    </span>
  );
  const renderHeatLabel = (level: number) => (level === 1 ? "niedrig" : level === 2 ? "mittel" : "hoch");
  const renderSeatCard = (seat: 1 | 2, label: string, level: number) => (
    <div className={`climate-popup__seat-card ${selectedSeat === seat ? "climate-popup__seat-card--selected" : ""} ${isScenario22 && selectedSeat === seat ? "climate-popup__seat-card--scenario22" : ""}`}>
      <span className="climate-popup__seat-icon" aria-hidden>
        <span />
        <span />
        <span />
      </span>
      <div>
        <span>{label}</span>
        <strong>{renderHeatLabel(level)}</strong>
      </div>
      {renderHeatDots(level)}
    </div>
  );

  return (
    <div className={`interaction-popup climate-popup-shell ${payload.event_type || ""}`}>
      <section className={`climate-popup ${stageClass}`}>
        <div className="climate-popup__header">
          <div>
            <span className="eyebrow climate-popup__eyebrow">Sitzheizung</span>
          </div>
        </div>

        <div className="climate-popup__content">
          <div className="climate-popup__seat-panel">
            <span className="climate-popup__label">{isScenario22 ? "Sitzheizung" : isAdjusting ? "Temperatur erhöht" : isSeatSelectTask ? "Sitzheizung auswählen" : "Klimaeinstellung"}</span>
            <strong>{body}</strong>
            <div className="climate-popup__stage-strip">
              <span className={`climate-popup__stage-badge ${isScenario22 && isCompletedStage ? "climate-popup__stage-badge--success" : isScenario22 && (isPassengerSelectedStage || isHeatIncreasedStage) ? "climate-popup__stage-badge--active" : ""}`}>
                {statusBadge || (isClarify ? "Eingabe prüfen" : "Bereit")}
              </span>
              {stageHint && <span className="climate-popup__stage-hint">{stageHint}</span>}
            </div>

            <div className="climate-popup__seat-grid" aria-label="Sitzauswahl">
              {renderSeatCard(1, "Fahrer", driverSeatLevel)}
              {renderSeatCard(2, "Beifahrer", passengerSeatLevel)}
            </div>
          </div>
        </div>



        {!isClarify && showGestureActions && (
          <div className="climate-popup__actions" aria-label="Sitzheizungsgesten">
            {isScenario22 ? (
              <>
                <span className={`climate-popup__chip climate-popup__chip--cancel ${scenario22SwipeActive ? "climate-popup__chip--active" : ""}`} {...previewChipProps("Swipe", onPreviewGesture)}>
                  <span aria-hidden>↔</span>Swipe
                </span>
                <span className={`climate-popup__chip climate-popup__chip--adjust ${scenario22RotateActive ? "climate-popup__chip--active" : ""} ${!scenario22RotateActive ? "climate-popup__chip--secondary" : ""}`} {...previewChipProps("Handgelenk drehen", onPreviewGesture)}>
                  <span aria-hidden>↻</span>Drehen
                </span>
              </>
            ) : (
              <>
                <span className={`climate-popup__chip climate-popup__chip--cancel ${isCancelled || isSelectingSeatHeat ? "climate-popup__chip--active" : ""}`} {...previewChipProps("Swipe", onPreviewGesture)}>
                  <span aria-hidden>↔</span>Swipe
                </span>
                <span className={`climate-popup__chip climate-popup__chip--adjust ${isAdjusting ? "climate-popup__chip--active" : ""}`} {...previewChipProps("Handgelenk drehen", onPreviewGesture)}>
                  <span aria-hidden>↻</span>Handgelenk drehen
                </span>
              </>
            )}
          </div>
        )}
        {!isClarify && showVoiceActions && !isScenario22 && (
          <div className="climate-popup__actions" aria-label="Sitzheizungsentscheidung">
            <button className={`climate-popup__button climate-popup__button--accept ${isSuccess ? "climate-popup__button--active" : ""}`} type="button" onClick={onPreviewGesture ? () => onPreviewGesture("Handgelenk drehen") : undefined}>
              Annehmen
            </button>
            <button className={`climate-popup__button climate-popup__button--decline ${isCancelled ? "climate-popup__button--active" : ""}`} type="button" onClick={onPreviewGesture ? () => onPreviewGesture("Swipe") : undefined}>
              Ablehnen
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

function isClimateScenario22(payload: WidgetPayload): boolean {
  return payload.domain === "climate" && (payload.study_ref === "2.2" || payload.scenario_id === "STUDY-2.2" || payload.task_id === "CLIMATE-SEAT-HEAT" || payload.task_id === "CLIMATE-SEAT-WARMER" || payload.task_id === "CLIMATE-INCREASE");
}

function climateScenario22Stage(payload: WidgetPayload): "waiting" | "passenger_selected" | "heat_increased" | "completed" {
  if (!isClimateScenario22(payload)) {
    return "waiting";
  }

  if (payload.event_type === "trial_completed" && payload.success !== false) {
    return "completed";
  }

  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const normalizedGesture = normalizeGestureLabel(gestureLabel);
  const isSwipe = normalizedGesture === "swipe";
  const isRotate = normalizedGesture === "handgelenkdrehen";
  const isHeatStep = payload.task_id === "CLIMATE-SEAT-WARMER" || payload.task_id === "CLIMATE-INCREASE" || normalizeGestureLabel(payload.expected_gesture) === "handgelenkdrehen";

  if (isHeatStep && isRotate) {
    return "heat_increased";
  }

  if (isSwipe) {
    return "passenger_selected";
  }

  if (isHeatStep) {
    return "passenger_selected";
  }

  return "waiting";
}

function AmbientPopupWidget({ payload, state, onPreviewGesture }: { payload: WidgetPayload; state: CockpitState; onPreviewGesture?: (gesture: PreviewGesture) => void }) {
  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const { showVoiceActions, showGestureActions } = popupModalityVisibility(payload);
  const isClarify = payload.decision === "clarify";
  const isWaiting = !isClarify && !payload.decision && !gestureLabel;
  const isSwipe = !isClarify && gestureLabel === "Swipe";
  const isThumbsUp = !isClarify && gestureLabel === "Daumen hoch";
  const isRotate = !isClarify && gestureLabel === "Handgelenk drehen";
  const isCancelled = !isClarify && (payload.success === false || payload.decision === "cancel");
  const isConfirmed = !isClarify && (payload.decision === "execute" || gestureLabel === "Daumen hoch");
  const isNightModeTask = payload.task_id === "AMBIENT-NIGHTMODE";
  const isColorTask = payload.task_id === "AMBIENT-COLOR";
  const isBrighterTask = payload.task_id === "AMBIENT-BRIGHTER";
  const isScenario42 = payload.study_ref === "4.2" || payload.scenario_id === "STUDY-4.2";
  const isScenario23 = payload.study_ref === "2.3" || payload.scenario_id === "STUDY-2.3";
  const brightness = Math.max(0, Math.min(100, state.ambientBrightness));
  const isBrightnessAdjusted = isBrighterTask && (isRotate || payload.decision === "execute" || payload.event_type === "trial_completed");
  const isColorChanged = isColorTask && (isSwipe || payload.decision === "execute");
  const colorPresets = [
    { id: "violet", label: "Violett", hex: "#a855f7" },
    { id: "blue", label: "Blau", hex: "#3b82f6" },
    { id: "green", label: "Gruen", hex: "#22c55e" },
    { id: "yellow", label: "Gelb", hex: "#facc15" },
    { id: "orange", label: "Orange", hex: "#f97316" },
    { id: "red", label: "Rot", hex: "#ef4444" },
  ] as const;
  const baseColorIndex = state.ambientColor === "Warm" ? 3 : state.ambientColor === "Blau" ? 1 : 0;
  const activeColorIndex = isScenario23 && (isColorChanged || isBrighterTask) ? 4 : (baseColorIndex + (isSwipe ? 1 : 0)) % colorPresets.length;
  const brightnessPosition = isBrightnessAdjusted ? Math.min(100, brightness + 22) : brightness;
  const statusLabel = isClarify
      ? "Klärung"
    : isCancelled
      ? "Abgebrochen"
      : isBrightnessAdjusted
        ? "Erhöht"
        : isColorChanged
          ? "Gewechselt"
        : isNightModeTask && isConfirmed
          ? "Angenommen"
          : isNightModeTask
            ? "Vorschlag"
            : isBrighterTask
              ? "Aktiv"
              : isConfirmed
                ? "Erkannt"
                : "Bereit";
  const title = isClarify
    ? "Eingabe prüfen"
    : isNightModeTask
      ? isConfirmed
        ? "Nachtmodus angenommen"
        : "Nachtmodus aktivieren?"
      : isBrighterTask
        ? isBrightnessAdjusted
          ? isScenario23 ? "Neue Farbe heller" : "Helligkeit erhöht"
          : isScenario23 ? "Neue Farbe ist aktiv" : "Nachtmodus ist aktiv"
        : isColorTask
          ? isColorChanged ? "Farbe gewechselt" : "Farbe wechseln"
          : payload.overlay_title || "Ambientebeleuchtung";
  const description = isClarify
    ? payload.unclear_text || payload.prompt || "Bitte Eingabe wiederholen."
    : isNightModeTask
      ? isConfirmed
        ? payload.accepted_text || "Nachtmodus wird aktiviert."
        : payload.overlay_body || payload.prompt || "Das System schlaegt Nachtmodus vor."
      : isBrighterTask
        ? isBrightnessAdjusted
          ? payload.accepted_text || "Ambientebeleuchtung ist jetzt heller."
          : isScenario23
            ? "Die neue Farbe ist aktiv. Als nächstes kann sie heller gemacht werden."
            : payload.overlay_body || payload.prompt || "Nachtmodus ist aktiv. Helligkeit kann angepasst werden."
        : isColorTask
          ? isColorChanged
            ? payload.accepted_text || "Neue Farbe ist aktiv."
            : payload.overlay_body || payload.prompt || "Aktuelle Farbe: Blau."
        : payload.overlay_body || payload.prompt || "Ambientebeleuchtung ist aktiv.";
  const sceneLabel = isNightModeTask ? "Nachtmodus" : isColorTask ? "Farbe" : isBrighterTask ? "Ambientebeleuchtung" : "Lichtszene";
  const sceneValue = isBrightnessAdjusted
    ? isScenario23 ? `Neue Farbe · ${brightnessPosition}%` : `${brightnessPosition}% Helligkeit`
    : isNightModeTask
      ? "Warm gedimmt"
      : isScenario23 && (isColorChanged || isBrighterTask)
        ? "Neue Farbe"
      : state.ambientColor === "Warm"
        ? "Warm"
        : state.ambientColor;
  return (
    <div className={`interaction-popup ambient-popup-shell ${payload.event_type || ""}`}>
      <section className={`ambient-popup-card ${isClarify ? "ambient-popup-card--clarify" : isCancelled ? "ambient-popup-card--cancelled" : isBrightnessAdjusted ? "ambient-popup-card--brightness-done" : isColorChanged ? "ambient-popup-card--color-done" : isConfirmed ? "ambient-popup-card--confirmed" : isSwipe || isRotate ? "ambient-popup-card--detected" : ""} ${isScenario42 ? "ambient-popup-card--scenario42" : ""} ${isScenario23 ? "ambient-popup-card--scenario23" : ""} ${isNightModeTask ? "ambient-popup-card--nightmode" : ""} ${isBrighterTask ? "ambient-popup-card--brighter" : ""}`}>
        <div className="ambient-popup-header">
          <div>
            <span className="eyebrow ambient-popup-eyebrow">Ambientebeleuchtung</span>
            <strong className="ambient-popup-title">{title}</strong>
          </div>
          <span className="ambient-popup-status">{statusLabel}</span>
        </div>

        <div className="ambient-popup-content">
          <div className="ambient-popup-scene" aria-label={`${sceneLabel}: ${sceneValue}`}>
            <div className="ambient-popup-light-preview" aria-hidden>
              <span />
            </div>
            <div>
              <span>{sceneLabel}</span>
              <strong>{sceneValue}</strong>
              <p>{description}</p>
            </div>
          </div>

          <div className="ambient-popup-controls">
            <div className="ambient-popup-slider-row" aria-label={`Farbe ${state.ambientColor}`}>
              <span>Farbe</span>
              <div className="ambient-popup-color-dots" role="list" aria-label="Farbauswahl">
                {colorPresets.map((preset, index) => (
                  <span
                    key={preset.id}
                    className={`ambient-popup-color-dot ${index === activeColorIndex ? "ambient-popup-color-dot--active" : ""}`}
                    role="listitem"
                    aria-label={preset.label}
                    style={{ background: preset.hex }}
                  />
                ))}
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

        {!isClarify && (showVoiceActions || showGestureActions) && (
          <div className="ambient-popup-gesture-row" aria-label="Interaktionen">
            {showGestureActions && (
              <>
                {isNightModeTask && (
                  <span className={`ambient-popup-chip ${isThumbsUp || isConfirmed ? "gesture-chip--detected" : ""}`} {...previewChipProps("Daumen hoch", onPreviewGesture)}><span aria-hidden>👍</span>Annehmen</span>
                )}
                {isColorTask && (
                  <>
                    {showVoiceActions && (
                      <span className={`ambient-popup-chip ${isColorChanged && !isSwipe ? "gesture-chip--detected" : ""}`} {...previewChipProps("Swipe", onPreviewGesture)}><span aria-hidden>↔</span>Farbe wechseln</span>
                    )}
                    <span className={`ambient-popup-chip ${isSwipe ? "gesture-chip--detected" : ""}`} {...previewChipProps("Swipe", onPreviewGesture)}><span aria-hidden>↔</span>Swipe</span>
                  </>
                )}
                {!isNightModeTask && !isBrighterTask && !isColorTask && (
                  <span className={`ambient-popup-chip ${isSwipe ? "gesture-chip--detected" : ""}`} {...previewChipProps("Swipe", onPreviewGesture)}><span aria-hidden>↔</span>Swipe</span>
                )}
                {!isNightModeTask && (
                  <span className={`ambient-popup-chip ${isRotate ? "gesture-chip--detected" : ""}`} {...previewChipProps("Handgelenk drehen", onPreviewGesture)}><span aria-hidden>↻</span>{isBrighterTask ? "Heller machen" : "Drehen"}</span>
                )}
              </>
            )}
          </div>
        )}
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
  if (payload.event_type === "trial_completed" && payload.success === false) {
    return createIdleState();
  }
  if (payload.finalized_by_operator === true) {
    return current;
  }

  if (payload.event_type === "scenario_start") {
    return initializeForStep(createIdleState(), payload);
  }

  const decision = payload.decision ?? "";
  const shouldApplyDecision =
    Boolean(decision) &&
    !(payload.event_type === "trial_completed" && payload.task_id === "AUDIO-VOLUME-UP");
  const updated = shouldApplyDecision
    ? applyDecision(current, decision as Decision, current.activePayload?.task_id || payload.task_id)
    : current;

  if (payload.event_type === "trial_completed") {
    if (
      (payload.study_ref === "2.1" || payload.scenario_id === "STUDY-2.1") &&
      payload.task_id === "AUDIO-NEXT"
    ) {
      return {
        ...updated,
        activePayload: payload,
        completed: false,
        decision,
        feedback: "Nächstes Lied spielt. Warte auf Lautstärke-Befehl.",
      };
    }

    return {
      ...updated,
      activePayload: payload,
      completed: true,
      decision,
      feedback: payload.success === false
        ? "Trial abgebrochen. Warte auf die nächste Aufgabe."
        : "Szenario abgeschlossen. Warte auf die nächste Aufgabe.",
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
    if (payload.task_id === "AUDIO-VOLUME-UP") {
      return {
        ...initializeForStep(updated, payload),
        volume: Math.min(100, updated.volume + 20),
        decision,
        feedback: payload.prompt || "Lautstärke erhöht.",
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
    callActive: taskId === "CALL-ACTIVE" || taskId === "CALL-VOLUME",
    callEnded: taskId === "CALL-ENDED",
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
    if (taskId === "CALL-INCOMING") {
      return { ...state, callIncoming: false, callActive: false, callEnded: true };
    }
    if (taskId === "CALL-ACTIVE") {
      return { ...state, callIncoming: false, callActive: false, callEnded: true };
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
      return { ...state, callIncoming: false, callActive: true, callEnded: false };
    case "CALL-ACTIVE":
      return { ...state, callIncoming: false, callActive: false, callEnded: true };
    case "CALL-ENDED":
      return { ...state, callIncoming: false, callActive: false, callEnded: true };
    case "CALL-VOLUME":
      return { ...state, callActive: true, volume: Math.min(100, state.volume + 8) };
    case "AUDIO-SUGGESTION":
      return { ...state, audioPlaying: true, track: "Night Drive" };
    case "AUDIO-NEXT":
      return { ...state, audioPlaying: true, track: "City Lights" };
    case "AUDIO-VOLUME-UP":
      return { ...state, volume: Math.min(100, state.volume + 20) };
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
