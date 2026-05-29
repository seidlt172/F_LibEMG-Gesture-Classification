import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import type { Decision, Domain, LatestResponse, WidgetPayload } from "./types";
import "./styles.css";

const bridgeUrl = import.meta.env.VITE_WIDGET_EVENT_URL ?? "http://127.0.0.1:8765/latest";

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

  const payload = state.activePayload;
  const guidance = useMemo(() => guidanceFor(payload), [payload]);
  const activeDomain = payload?.domain !== "unknown" ? payload?.domain : undefined;
  const detectedGesture = payload?.source?.gesture_event?.gesture_label ?? undefined;
  const detectedGestureConfidence = payload?.source?.gesture_event?.confidence ?? undefined;
  const usedModalities = payload?.source?.used_modalities;
  const stepLabel = payload && typeof payload.step_index === "number" && payload.step_count
    ? `${(payload.step_index ?? 0) + 1}/${payload.step_count}`
    : "";

  return (
    <main className="shell cockpit-shell">
      <header className="topbar">
        <div>
          <h1>Driver Cockpit</h1>
          <p className="bridge-status">{bridgeStatus}</p>
        </div>
        <ModeBadge condition={payload?.condition} />
      </header>

      <div className="core">
        <MapPanel>
          <div className="taskband inside-map">
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
        </MapPanel>

        <aside className="sidebar">
          <SideWidgets
            activeDomain={activeDomain}
            state={state}
            detectedGesture={detectedGesture}
            detectedGestureConfidence={detectedGestureConfidence}
            usedModalities={usedModalities}
            condition={payload?.condition}
          />
        </aside>
      </div>

      <BottomControls state={state} />

      <InteractionPopup payload={payload} state={state} />

      <FeedbackBadge decision={state.decision} feedback={state.feedback} />
    </main>
  );
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
