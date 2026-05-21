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
    seatLevel: 1
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
  const stepLabel = payload && typeof payload.step_index === "number" && payload.step_count
    ? `${(payload.step_index ?? 0) + 1}/${payload.step_count}`
    : "";

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <h1>Driver Cockpit</h1>
          <p>{bridgeStatus}</p>
        </div>
        <div className="condition">{payload?.condition ?? "Warte auf Aufgabe"}</div>
      </header>

      <section className="taskband">
        <div>
          <span className="eyebrow">Aktuelle Aufgabe</span>
          <h2>{payload ? `${payload.study_ref ?? ""} ${payload.scenario_prompt || payload.overlay_title || "Studienaufgabe"}` : "Kein aktiver Trial"}</h2>
          <p>{taskText(payload, state.completed, stepLabel)}</p>
        </div>
        <div className="guidance">
          <span>{guidance}</span>
          {payload?.expected_voice && <strong>Voice: {payload.expected_voice}</strong>}
          {payload?.expected_gesture && <strong>Geste: {payload.expected_gesture}</strong>}
        </div>
      </section>

      <section className="cockpit-grid">
        <Tile title="Anrufe" active={activeDomain === "calls"}>
          <strong>{state.callActive ? "Call aktiv" : state.callIncoming ? "Eingehender Anruf" : "Kein aktiver Anruf"}</strong>
          <span>{state.callActive || state.callIncoming ? "Alex" : "Bereit"}</span>
          <small>Lautstaerke {state.volume}%</small>
        </Tile>
        <Tile title="Navigation" active={activeDomain === "navigation"}>
          <strong>{state.routeActive ? "Route aktiv" : `Route ${state.routeIndex}`}</strong>
          <span>18 min | 12 km</span>
          <small>{state.routeActive ? "Navigation laeuft" : "Vorschlag"}</small>
        </Tile>
        <Tile title="Audio" active={activeDomain === "audio"}>
          <strong>{state.track}</strong>
          <span>{state.audioPlaying ? "Spielt" : "Pausiert"}</span>
          <small>Lautstaerke {state.volume}%</small>
        </Tile>
        <Tile title="Nachrichten" active={activeDomain === "messages"}>
          <strong>{state.messageOpen ? "Nachricht offen" : "Neue Nachricht"}</strong>
          <span>Mia: Bin in 5 Minuten da.</span>
          <small>{state.messageOpen ? "Geoeffnet" : "Inbox"}</small>
        </Tile>
        <Tile title="Ambientebeleuchtung" active={activeDomain === "ambient_light"}>
          <strong>{state.ambientColor}</strong>
          <span>Helligkeit {state.ambientBrightness}%</span>
          <small>Nachtmodus bereit</small>
        </Tile>
        <Tile title="Klima" active={activeDomain === "climate"}>
          <strong>Sitzheizung {state.seatLevel}</strong>
          <span>21 Grad</span>
          <small>Klima aktiv</small>
        </Tile>
      </section>

      <section className={`feedback ${state.decision || "idle"}`}>
        <span>{state.decision || "ready"}</span>
        <p>{state.feedback}</p>
      </section>
    </main>
  );
}

function Tile({ title, active, children }: { title: string; active?: boolean; children: React.ReactNode }) {
  return (
    <article className={`tile ${active ? "active" : ""}`}>
      <span className="eyebrow">{title}</span>
      {children}
    </article>
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
      feedback: "Szenario abgeschlossen. Warte auf die naechste Aufgabe."
    };
  }

  if (payload.event_type === "step_update") {
    if (decision === "clarify") {
      return {
        ...updated,
        activePayload: payload,
        completed: false,
        decision,
        feedback: payload.clarification || payload.unclear_text || "Bitte Eingabe wiederholen."
      };
    }
    return {
      ...initializeForStep(updated, payload),
      decision,
      feedback: payload.prompt || "Naechster Schritt aktiv."
    };
  }

  return {
    ...updated,
    activePayload: payload,
    completed: false,
    decision,
    feedback: payload.prompt || payload.clarification || current.feedback
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
    feedback: payload.prompt || state.feedback
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
