import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import type { Decision, Domain, LatestResponse, WidgetPayload } from "./types";
import "./styles.css";

const bridgeUrl = import.meta.env.VITE_WIDGET_EVENT_URL ?? "http://127.0.0.1:8765/latest";

type PreviewScenario =
  | "off"
  | "ambient-waiting"
  | "ambient-swipe"
  | "ambient-rotate"
  | "ambient-confirmed"
  | "call-incoming"
  | "navigation-route"
  | "music-suggestion"
  | "message-open"
  | "climate-seat";

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
    feedback: "Warte auf naechste Aufgabe.",
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
  const guidance = useMemo(() => guidanceFor(displayPayload), [displayPayload]);
  const activeDomain = displayPayload?.domain !== "unknown" ? displayPayload?.domain : undefined;
  const detectedGesture = displayPayload?.source?.gesture_event?.gesture_label ?? undefined;
  const detectedGestureConfidence = displayPayload?.source?.gesture_event?.confidence ?? undefined;
  const usedModalities = displayPayload?.source?.used_modalities;
  const stepLabel = displayPayload && typeof displayPayload.step_index === "number" && displayPayload.step_count
    ? `${(displayPayload.step_index ?? 0) + 1}/${displayPayload.step_count}`
    : "";
  const previewActive = previewScenario !== "off";

  return (
    <main className="shell cockpit-shell">
      <header className="topbar">
        <div>
          <h1>Driver Cockpit</h1>
          <p className="bridge-status">{bridgeStatus}</p>
        </div>
        <div className="topbar-tools">
          <PreviewScenarioControl value={previewScenario} onChange={setPreviewScenario} />
          <ModeBadge condition={displayPayload?.condition} />
        </div>
      </header>

      {previewActive && <div className="preview-mode-note">Preview mode · not study data</div>}

      <div className="core">
        <MapPanel>
          <div className="taskband inside-map">
            <div>
              <span className="eyebrow">Aktuelle Aufgabe</span>
              <h2>{displayPayload ? `${displayPayload.study_ref ?? ""} ${displayPayload.scenario_prompt || displayPayload.overlay_title || "Studienaufgabe"}` : "Kein aktiver Trial"}</h2>
              <p>{taskText(displayPayload, displayState.completed, stepLabel)}</p>
            </div>
            <div className="guidance guidance-inline">
              <span>{guidance}</span>
              {displayPayload?.expected_voice && <strong className="pill voice">{displayPayload.expected_voice}</strong>}
              {displayPayload?.expected_gesture && <strong className="pill gesture">{displayPayload.expected_gesture}{displayPayload.gesture_ref ? ` (${displayPayload.gesture_ref})` : ""}</strong>}
            </div>
          </div>
        </MapPanel>

        <aside className="sidebar">
          <SideWidgets
            activeDomain={activeDomain}
            state={displayState}
            detectedGesture={detectedGesture}
            detectedGestureConfidence={detectedGestureConfidence}
            usedModalities={usedModalities}
            condition={displayPayload?.condition}
          />
        </aside>
      </div>

      <BottomControls state={displayState} />

      <InteractionPopup payload={displayPayload} state={displayState} />

      <FeedbackBadge decision={displayState.decision} feedback={displayState.feedback} />
    </main>
  );
}

function PreviewScenarioControl({
  value,
  onChange,
}: {
  value: PreviewScenario;
  onChange: (value: PreviewScenario) => void;
}) {
  return (
    <label className="preview-control">
      <span>Preview scenario</span>
      <select value={value} onChange={(event) => onChange(event.target.value as PreviewScenario)}>
        <option value="off">Off / Live middleware</option>
        <option value="ambient-waiting">Ambient · Waiting</option>
        <option value="ambient-swipe">Ambient · Swipe detected</option>
        <option value="ambient-rotate">Ambient · Drehen detected</option>
        <option value="ambient-confirmed">Ambient · Confirmed</option>
        <option value="call-incoming">Call · Incoming</option>
        <option value="navigation-route">Navigation · Route suggestion</option>
        <option value="music-suggestion">Music · Suggestion</option>
        <option value="message-open">Message · Open message</option>
        <option value="climate-seat">Climate · Seat heating</option>
      </select>
    </label>
  );
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
    case "navigation-route":
      return { ...previewState, routeActive: true, routeIndex: 1 };
    case "music-suggestion":
      return { ...previewState, audioPlaying: true, track: "Night Drive" };
    case "message-open":
      return { ...previewState, messageOpen: true };
    case "climate-seat":
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

function MapPanel({ children }: { children?: React.ReactNode }) {
  return (
    <section className="map-panel">
      <div className="fake-map">{children || <div className="map-placeholder">Karte / Navigation</div>}</div>
    </section>
  );
}

function SideWidgets({
  activeDomain,
  state,
  detectedGesture,
  detectedGestureConfidence,
  usedModalities,
  condition,
}: {
  activeDomain?: Domain;
  state: CockpitState;
  detectedGesture?: string | null;
  detectedGestureConfidence?: number | null;
  usedModalities?: string;
  condition?: string | null;
}) {
  return (
    <div className="side-widgets">
      <MusicWidget active={activeDomain === "audio"} state={state} />
      <MessageWidget active={activeDomain === "messages"} state={state} />
      <NavigationWidget
        active={activeDomain === "navigation"}
        state={state}
        condition={condition}
        detectedGesture={detectedGesture}
      />
      <CallWidget
        active={activeDomain === "calls"}
        state={state}
        condition={condition}
        detectedGesture={detectedGesture}
      />
      <AmbientWidget
        state={state}
        isActive={activeDomain === "ambient_light"}
        detectedGesture={detectedGesture}
        detectedGestureConfidence={detectedGestureConfidence}
        usedModalities={usedModalities}
        condition={condition}
      />
      <ClimateWidget state={state} />
    </div>
  );
}

function NavigationWidget({
  active,
  state,
  condition,
  detectedGesture,
}: {
  active: boolean;
  state: CockpitState;
  condition?: string | null;
  detectedGesture?: string | null;
}) {
  const isGesture = condition === "Gesture only";
  const isCombined = condition === "CAN use both";
  const progress = state.routeActive ? 75 : 35;
  const routeAActive = state.routeIndex !== 2;
  const routeBActive = state.routeIndex === 2;
  const swipeDetected = active && detectedGesture === "Swipe";
  const tapDetected = active && (detectedGesture === "Zeigen/Tippen" || detectedGesture === "Zeigen / Tippen");
  const thumbDetected = active && detectedGesture === "Daumen hoch";

  return (
    <div className={`widget-card navigation-widget ${active ? "active" : ""} ${isGesture ? "gesture" : isCombined ? "combined" : "voice"}`}>
      <div className="navigation-widget-main">
        <div className="navigation-widget-header">
          <span className="eyebrow navigation-widget-title">Navigation</span>
          {active && <span className="widget-mini-badge">{isCombined ? "Voice + Geste" : isGesture ? "Geste" : "Voice"}</span>}
        </div>

        {isGesture ? (
          <div className="navigation-route-list" aria-label="Routenauswahl">
            <div className={`navigation-route-row ${routeAActive ? "selected" : ""}`}>
              <span>Route A</span>
              <strong>24 min</strong>
            </div>
            <div className={`navigation-route-row ${routeBActive ? "selected" : ""}`}>
              <span>Route B</span>
              <strong>29 min</strong>
            </div>
          </div>
        ) : isCombined ? (
          <>
            <div className="navigation-route-alert">Neue Route <strong>8 min schneller</strong></div>
            <div className="navigation-mini-map" aria-hidden>
              <span className="navigation-map-line primary" />
              <span className="navigation-map-line secondary" />
              <span className="navigation-map-pin start" />
              <span className="navigation-map-pin end" />
            </div>
            <div className="navigation-action-row" aria-label="Navigationsentscheidung">
              <button className="navigation-action accept" type="button">Annehmen</button>
              <button className="navigation-action decline" type="button">Ablehnen</button>
            </div>
          </>
        ) : (
          <>
            <div className="navigation-prompt-row">
              <span className="navigation-icon" aria-hidden>⌖</span>
              <strong>Navigation Route starten?</strong>
            </div>
            <div className="navigation-progress-row" aria-label={`Navigation ${progress}%`}>
              <div className="navigation-progress-track">
                <span style={{ width: `${progress}%` }} />
              </div>
              <em>{progress}%</em>
            </div>
            <button className="navigation-voice-action" type="button">Annehmen</button>
          </>
        )}
      </div>

      <div className="navigation-gesture-panel" aria-label="Navigationsgesten">
        {isCombined ? (
          <>
            <span className={`navigation-gesture-chip accept ${thumbDetected ? "gesture-chip--detected" : ""}`}><span aria-hidden>👍</span>Daumen hoch</span>
            <span className={`navigation-gesture-chip reject ${swipeDetected ? "gesture-chip--detected" : ""}`}><span aria-hidden>↔</span>Swipe</span>
          </>
        ) : isGesture ? (
          <>
            <span className={`navigation-gesture-chip ${swipeDetected ? "gesture-chip--detected" : ""}`}><span aria-hidden>↔</span>Swipe</span>
            <span className={`navigation-gesture-chip ${tapDetected ? "gesture-chip--detected" : ""}`}><span aria-hidden>⌾</span>Tippen</span>
          </>
        ) : null}
      </div>
    </div>
  );
}

function CallWidget({
  active,
  state,
  condition,
  detectedGesture,
}: {
  active: boolean;
  state: CockpitState;
  condition?: string | null;
  detectedGesture?: string | null;
}) {
  const isCombined = condition === "CAN use both";
  const callStatus = state.callIncoming ? "Eingehend" : state.callActive ? "Aktiv" : "Mobil";
  const progress = state.callActive ? Math.min(100, Math.max(30, state.volume)) : 60;
  const thumbDetected = active && detectedGesture === "Daumen hoch";
  const rotateDetected = active && detectedGesture === "Handgelenk drehen";

  return (
    <div className={`widget-card call-widget ${active ? "active" : ""} ${isCombined ? "combined" : "voice"}`}>
      <div className="call-widget-main">
        <div className="call-widget-header">
          <span className="eyebrow call-widget-title">{state.callIncoming ? "Eingehender Anruf" : "Anruf"}</span>
          {active && <span className="widget-mini-badge">{isCombined ? "Voice + Geste" : "Voice"}</span>}
        </div>

        <div className="call-info-row">
          <span className="call-phone-circle" aria-hidden>☎</span>
          <div className="call-copy">
            <strong>Max Mustermann</strong>
            <span>{callStatus}</span>
          </div>
        </div>

        {isCombined && (
          <div className="call-progress-row" aria-label={`Anrufpegel ${progress}%`}>
            <div className="call-progress-track">
              <span style={{ width: `${progress}%` }} />
            </div>
            <em>{progress}%</em>
          </div>
        )}
      </div>

      {isCombined ? (
        <div className="call-gesture-panel" aria-label="Anrufgesten">
          <span className={`call-gesture-chip ${thumbDetected ? "gesture-chip--detected" : ""}`}><span aria-hidden>👍</span>Daumen hoch</span>
          <span className={`call-gesture-chip ${rotateDetected ? "gesture-chip--detected" : ""}`}><span aria-hidden>↻</span>Drehen</span>
        </div>
      ) : (
        <div className="call-action-row" aria-label="Anrufaktionen">
          <button className="call-action-button accept" type="button">Annehmen</button>
          <button className="call-action-button decline" type="button">Ablehnen</button>
        </div>
      )}
    </div>
  );
}

function MusicWidget({ active, state }: { active: boolean; state: CockpitState }) {
  const volume = Math.max(0, Math.min(100, state.volume));
  const trackInitials = state.track
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase())
    .join("") || "M";

  return (
    <div className={`widget-card music-widget ${active ? "active" : ""}`}>
      <div className="music-widget-frame">
        <div className="music-widget-main">
          <span className="eyebrow music-widget-title">Musik</span>
          <div className="music-widget-track">
            <div className="music-album-art" aria-hidden>
              <span>{trackInitials}</span>
            </div>
            <div className="music-track-copy">
              <strong className="widget-title music-track-title">{state.track}</strong>
              <span className="music-track-meta">{state.audioPlaying ? "Spielt" : "Pausiert"} · Voice</span>
            </div>
          </div>
        </div>

        <div className="music-widget-controls">
          <div className="music-volume-row" aria-label={`Lautstaerke ${volume}%`}>
            <div className="music-volume-track">
              <span className="music-volume-fill" style={{ width: `${volume}%` }} />
            </div>
            <span className="music-volume-value">{volume}%</span>
          </div>

          <div className="music-control-row" aria-label="Musiksteuerung">
            <button className="music-control-button" type="button" aria-label="Vorheriger Titel">
              <span aria-hidden>‹</span>
            </button>
            <button className="music-control-button play" type="button" aria-label={state.audioPlaying ? "Pause" : "Abspielen"}>
              <span aria-hidden>{state.audioPlaying ? "Ⅱ" : "▶"}</span>
            </button>
            <button className="music-control-button" type="button" aria-label="Naechster Titel">
              <span aria-hidden>›</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function MessageWidget({ active, state }: { active: boolean; state: CockpitState }) {
  return (
    <div className={`widget-card message-widget ${active ? "active" : ""}`}>
      <span className="eyebrow message-widget-title">Nachrichten</span>

      <div className="message-preview-panel">
        <strong className="message-preview-title">{state.messageOpen ? "Nachricht offen" : "Neue Nachricht"}</strong>
        <span className="message-preview-sender">Von: <strong>Anna</strong></span>
      </div>

      <div className="message-action-row" aria-label="Nachrichtenaktionen">
        <button className="message-action-button" type="button">Öffnen</button>
        <button className="message-action-button" type="button">Schließen</button>
      </div>
    </div>
  );
}

function AmbientWidget({
  state,
  isActive,
  detectedGesture,
  detectedGestureConfidence,
  usedModalities,
  condition,
}: {
  state: CockpitState;
  isActive: boolean;
  detectedGesture?: string | null;
  detectedGestureConfidence?: number | null;
  usedModalities?: string;
  condition?: string | null;
}) {
  const brightness = Math.max(0, Math.min(100, state.ambientBrightness));
  const colorPosition = state.ambientColor === "Warm" ? 18 : state.ambientColor === "Blau" ? 70 : 45;
  const isCombined = condition === "CAN use both";
  const gestureDetected = isActive && (detectedGesture === "Swipe" || detectedGesture === "Handgelenk drehen");
  const confidenceLabel = typeof detectedGestureConfidence === "number"
    ? `${Math.round(detectedGestureConfidence * 100)}%`
    : "";

  return (
    <div className={`widget-card ambient-widget ${isCombined ? "combined" : "gesture"} ${isActive ? "ambient-widget--active" : ""} ${gestureDetected ? "ambient-widget--gesture-detected" : ""}`}>
      <div className="ambient-widget-main">
        <div className="ambient-widget-header">
          <span className="eyebrow ambient-widget-title">Ambientebeleuchtung</span>
          {gestureDetected ? (
            <span className="ambient-status-badge detected">Geste erkannt</span>
          ) : isActive ? (
            <span className="ambient-status-badge">Aktiv</span>
          ) : null}
        </div>

        <div className="ambient-slider-panel">
          <div className="ambient-slider-row" aria-label={`Farbe ${state.ambientColor}`}>
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

        {gestureDetected && (
          <div className="ambient-detected-readout">
            <strong>{detectedGesture}</strong>
            <span>{[usedModalities, confidenceLabel].filter(Boolean).join(" · ")}</span>
          </div>
        )}
      </div>

      <div className="ambient-gesture-panel" aria-label="Gesten">
        <span className={`ambient-gesture-chip ${gestureDetected && detectedGesture === "Swipe" ? "gesture-chip--detected" : ""}`}><span aria-hidden>↔</span>Swipe</span>
        <span className={`ambient-gesture-chip ${gestureDetected && detectedGesture === "Handgelenk drehen" ? "gesture-chip--detected" : ""}`}><span aria-hidden>↻</span>Drehen</span>
      </div>
    </div>
  );
}

function ClimateWidget({ state }: { state: CockpitState }) {
  const seatOneLevel = Math.max(1, Math.min(3, state.seatLevel));

  return (
    <div className="widget-card climate-widget">
      <div className="climate-widget-main">
        <span className="eyebrow climate-widget-title">Klimamenü</span>

        <div className="climate-seat-list">
          <div className="climate-seat-row">
            <div className="climate-seat-label">
              <span>Sitz 1:</span>
              <span className="climate-seat-icon" aria-hidden>▰</span>
            </div>
            <div className="climate-seat-control">
              <strong>Stufe {seatOneLevel}</strong>
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

function BottomControls({ state }: { state: CockpitState }) {
  return (
    <nav className="bottom-bar" aria-label="Bottom controls">
      <button className="pill" aria-label="Sitzheizung">🔥 Sitzheizung</button>
      <button className="pill" aria-label="Ambiente">💡 Ambiente</button>
      <button className="pill" aria-label="Anruf">📞 Anruf</button>
      <button className="pill" aria-label="Apps">⋯ Apps</button>
    </nav>
  );
}

function InteractionPopup({ payload, state }: { payload: WidgetPayload | null; state: CockpitState }) {
  if (!payload) return null;

  if (payload.domain === "ambient_light") {
    return <AmbientPopupWidget payload={payload} state={state} />;
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
        <div className="popup-footer">
          <span className="muted">Erwartet: {payload.expected_voice ?? payload.expected_gesture ?? "-"}</span>
        </div>
      </div>
    </div>
  );
}

function AmbientPopupWidget({ payload, state }: { payload: WidgetPayload; state: CockpitState }) {
  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const usedModalities = payload.source?.used_modalities;
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

        <footer className="ambient-popup-footer">
          <span>Erwartet: {payload.expected_gesture ?? "-"}</span>
          {usedModalities && <span>{usedModalities}</span>}
          {payload.condition && <span>{payload.condition}</span>}
        </footer>
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
    return "Szenario abgeschlossen. Warte auf die naechste Aufgabe.";
  }
  const prefix = stepLabel ? `${stepLabel}: ` : "";
  return `${prefix}${payload.prompt || payload.overlay_body || "Aktiver Schritt"}`;
}

function guidanceFor(payload: WidgetPayload | null): string {
  if (!payload) {
    return "Der Operator startet die naechste Aufgabe.";
  }
  if (payload.condition === "Voice only") {
    return "Sprache verwenden. Gesten werden nicht gewertet.";
  }
  if (payload.condition === "Gesture only") {
    return "EMG-Gesten verwenden. Sprache wird nicht gewertet.";
  }
  if (payload.condition === "CAN use both") {
    return "Sprache, Geste oder beides moeglich.";
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
      feedback: "Szenario abgeschlossen. Warte auf die naechste Aufgabe.",
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
      feedback: payload.prompt || "Naechster Schritt aktiv.",
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
