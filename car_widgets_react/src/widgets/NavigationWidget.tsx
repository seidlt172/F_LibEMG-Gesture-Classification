import type { WidgetPayload } from "../types";
import {
  normalizeGestureLabel,
  popupModalityVisibility,
  previewChipProps,
  previewGestureForVoiceTask,
  voiceActionLabel,
  voicePreviewActions,
} from "./shared";
import type { CockpitState, PreviewGesture } from "./shared";

export function NavigationWidget({ payload, state, onPreviewGesture }: { payload: WidgetPayload; state: CockpitState; onPreviewGesture?: (gesture: PreviewGesture) => void }) {
  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const normalizedGesture = normalizeGestureLabel(gestureLabel);
  const isClarify = payload.decision === "clarify";
  const isWaiting = !isClarify && !payload.decision && !gestureLabel;
  const clarifyText = payload.unclear_text || payload.prompt || "Bitte Auswahl wiederholen.";
  const isRouteSelectionScenario = isNavigationScenario32(payload);
  const isRejectRouteScenario = isNavigationRejectScenario13(payload);
  const isNextRouteTask = payload.task_id === "NAV-NEXT-ROUTE";
  const isSelectRouteTask = payload.task_id === "NAV-SELECT-SECOND";
  const isActiveTask = payload.task_id === "NAV-ACTIVE";
  const isVolumeTask = payload.task_id === "NAV-VOLUME-UP";
  const isVoiceNavScenario41 = payload.condition === "Voice only" && (payload.study_ref === "4.1" || payload.scenario_id === "STUDY-4.1");
  const isRouteBrowseSelectTask = isNextRouteTask || isSelectRouteTask;
  const isSwipe = normalizedGesture === "swipe";
  const isTap = normalizedGesture === "tap";
  const routeSelectionStage = isRouteSelectionScenario ? navigationScenario32Stage(payload) : "standard";
  const rejectRouteStage = isRejectRouteScenario ? navigationScenario13Stage(payload) : "waiting";
  const isRouteSelectionWaiting = routeSelectionStage === "waiting";
  const isRouteSelectionSwiped = routeSelectionStage === "swiped";
  const isRouteSelectionConfirmed = routeSelectionStage === "confirmed";
  const isRouteSelectionCompleted = routeSelectionStage === "completed";
  const isRejectRouteWaiting = rejectRouteStage === "waiting";
  const isRejectRouteDetected = rejectRouteStage === "detected";
  const isRejectRouteCompleted = rejectRouteStage === "completed";
  const rejectRouteDetectedBySwipe = normalizedGesture === "swipe";
  const rejectRouteDetectedByVoice = !rejectRouteDetectedBySwipe && `${payload.intent ?? ""} ${payload.action ?? ""} ${payload.target ?? ""} ${payload.expected_voice ?? ""} ${payload.prompt ?? ""} ${payload.overlay_body ?? ""}`.toLowerCase().includes("ablehnen");
  const isBrowsingNextRoute = !isClarify && isNextRouteTask && (isSwipe || payload.decision === "execute");
  const isSelected = !isClarify && (isSelectRouteTask ? (isTap || payload.decision === "execute") : isTap);
  const isNavigationActive = !isClarify && isActiveTask;
  const isAccepted = !isClarify && !isNextRouteTask && !isSelectRouteTask && !isActiveTask && !isVolumeTask && (gestureLabel === "Daumen hoch" || payload.decision === "execute");
  const isDeclined = !isClarify && !isNextRouteTask && (isSwipe || payload.decision === "cancel");
  const isVolumeUp = !isClarify && isVolumeTask && (payload.decision === "execute" || normalizedGesture === "handgelenkdrehen");
  const { showVoiceActions, showGestureActions } = popupModalityVisibility(payload);
  const showVoiceDecline = payload.condition !== "Voice only" || payload.task_id === "NAV-ACCEPT-ROUTE";
  const previewActions = onPreviewGesture ? voicePreviewActions(payload) : null;
  const shouldShowVoiceControls = !isVoiceNavScenario41 || (payload.task_id === "NAV-ACCEPT-ROUTE" && !isAccepted && !isDeclined) || isActiveTask;
  const routeName = isRouteSelectionScenario
    ? isRouteSelectionCompleted
      ? "Route gestartet"
      : isRouteSelectionConfirmed
        ? "Route 2 ausgewählt"
        : isRouteSelectionSwiped
          ? "Swipe erkannt"
          : "Route auswählen"
    : isRejectRouteScenario
      ? isRejectRouteCompleted
        ? "Route abgelehnt"
        : isRejectRouteDetected
          ? rejectRouteDetectedBySwipe
            ? "Swipe erkannt"
            : rejectRouteDetectedByVoice
              ? "Sprachbefehl erkannt"
              : "Ablehnung erkannt"
          : "Routenänderung"
    : isSelected
      ? "Alternative Route"
      : isBrowsingNextRoute
        ? "Nächster Vorschlag"
      : isNavigationActive
        ? "Navigation läuft"
      : isVolumeTask
        ? "Navigation läuft"
      : isAccepted
        ? "Schnellere Route"
      : isDeclined
        ? "Route abgelehnt"
        : "Schnellere Route";
  const stageClass = isRejectRouteScenario
    ? isRejectRouteCompleted || isRejectRouteDetected
      ? "navigation-popup--route-rejected"
      : "navigation-popup--route-waiting"
    : isClarify
      ? "navigation-popup--clarify"
    : isRouteSelectionCompleted
      ? "navigation-popup--route-completed"
    : isRouteSelectionConfirmed
      ? "navigation-popup--route-confirmed"
    : isRouteSelectionSwiped
      ? "navigation-popup--route-swiped"
    : isRouteSelectionWaiting
      ? "navigation-popup--route-waiting"
    : isVolumeUp
      ? "navigation-popup--accepted"
    : isNavigationActive
      ? "navigation-popup--accepted"
    : isVolumeTask
      ? "navigation-popup--suggested"
    : isBrowsingNextRoute
      ? "navigation-popup--browsing"
    : isAccepted
      ? "navigation-popup--accepted"
      : isDeclined
        ? "navigation-popup--declined"
      : isSelected
          ? "navigation-popup--selected"
          : "navigation-popup--suggested";
  const body = isRejectRouteScenario
    ? isRejectRouteCompleted
      ? "Route wird abgelehnt."
      : isRejectRouteDetected
        ? "Route wurde angenommen."
        : payload.overlay_body || payload.prompt || "Neue Route verfügbar."
    : isClarify
      ? payload.overlay_body || "Route verfügbar."
    : isRouteSelectionCompleted
      ? "Route 2 gestartet."
    : isRouteSelectionConfirmed
      ? "Route 2 ist ausgewählt."
    : isRouteSelectionSwiped
      ? "Route 2 ausgewählt."
    : isRouteSelectionWaiting
      ? "Route 1 oder Route 2?"
    : isVolumeUp
      ? "Route ist aktiv."
    : isNavigationActive
      ? payload.overlay_body || "Route ist aktiv. Ansagelautstärke: normal."
    : isVolumeTask
      ? payload.overlay_body || payload.prompt || "Ansagelautstärke: 40 Prozent."
    : isBrowsingNextRoute
      ? payload.accepted_text || "Nächster Routenvorschlag angezeigt."
    : isAccepted
      ? payload.accepted_text || "Route übernommen"
      : isDeclined
        ? payload.rejected_text || "Route abgelehnt"
    : isSelected
          ? payload.accepted_text || "Route ausgewählt"
          : payload.overlay_body || payload.prompt || "Neue Route verfügbar.";
  const routeCards = [
    {
      id: 1,
      title: "Route 1",
      summary: "Schnellste Route",
      detail: "18 min",
    },
    {
      id: 2,
      title: "Route 2",
      summary: "Ruhigere Route",
      detail: "21 min",
    },
  ] as const;
  const selectedRouteId = isRouteSelectionScenario && !isRouteSelectionWaiting ? 2 : isSelectRouteTask && isSelected ? 2 : 1;
  const rejectRouteLabel = isRejectRouteCompleted
    ? "Route abgelehnt"
    : isRejectRouteDetected
      ? rejectRouteDetectedBySwipe
        ? "Swipe erkannt"
        : rejectRouteDetectedByVoice
          ? "Sprachbefehl erkannt"
          : "Ablehnung erkannt"
      : "Neue Route vorgeschlagen";
  const rejectRouteTitle = isRejectRouteCompleted ? "Route abgelehnt" : "Neue Route vorgeschlagen";
  const rejectRouteSubline = isRejectRouteCompleted
    ? "Die alternative Route wird nicht übernommen."
    : "Schnellste Route · 18 min";

  return (
    <div className={`interaction-popup navigation-popup-shell ${payload.event_type || ""}`}>
      <section className={`navigation-popup ${stageClass}`}>
        <div className="navigation-popup__header">
          <div>
            <span className="eyebrow navigation-popup__eyebrow">Navigation</span>
          </div>
        </div>

        <div className="navigation-popup__content">
          <div className="navigation-popup__details">
            <span className="navigation-popup__label">{routeName}</span>
            <strong>{body}</strong>
            {isRouteSelectionScenario ? (
              isRouteSelectionCompleted ? (
                <div className="navigation-popup__final-view" aria-label="Navigation gestartet">
                  <div className="navigation-popup__route-preview navigation-popup__route-preview--final">
                    <div className="navigation-mini-map navigation-mini-map--final" aria-hidden>
                      <span className="navigation-map-line primary" />
                      <span className="navigation-map-line secondary" />
                      <span className="navigation-map-pin start" />
                      <span className="navigation-map-pin end" />
                    </div>
                    <div className="navigation-popup__route-summary">
                      <span className="navigation-popup__route-badge navigation-popup__route-badge--success">✓ Auswahl bestätigt</span>
                      <strong>Route 2 gestartet</strong>
                      <p>Ruhigere Route · 21 min</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="navigation-popup__route-grid" aria-label="Route auswählen">
                  {routeCards.map((route) => {
                    const selected = route.id === selectedRouteId;
                    return (
                      <button
                        key={route.id}
                        className={`navigation-popup__route-card ${selected ? "navigation-popup__route-card--selected" : ""}`}
                        type="button"
                        onClick={onPreviewGesture ? () => onPreviewGesture(route.id === 1 ? "Swipe" : "Zeigen / Tippen") : undefined}
                      >
                        <div className="navigation-popup__route-card-head">
                          <span className="navigation-popup__route-name">{route.title}</span>
                          <span className={`navigation-popup__route-badge ${selected ? "navigation-popup__route-badge--selected" : ""}`}>
                            {selected ? "Ausgewählt" : "Option"}
                          </span>
                        </div>
                        <strong>{route.summary}</strong>
                        <div className="navigation-popup__route-card-meta">
                          <span>{route.detail}</span>
                          {route.id === 1 ? <span>Direkt</span> : <span>Leiser</span>}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )
            ) : isRejectRouteScenario ? (
              <div className="navigation-popup__reject-view" aria-label="Route ablehnen">
                <div className="navigation-popup__route-preview navigation-popup__route-preview--reject">
                  <div className="navigation-mini-map" aria-hidden>
                    <span className="navigation-map-line primary" />
                    <span className="navigation-map-line secondary" />
                    <span className="navigation-map-pin start" />
                    <span className="navigation-map-pin end" />
                  </div>
                  <div className="navigation-popup__route-summary navigation-popup__route-summary--reject">
                    <span className="navigation-popup__route-badge navigation-popup__route-badge--danger">{rejectRouteLabel}</span>
                    <strong>{rejectRouteTitle}</strong>
                    <p>{rejectRouteSubline}</p>
                  </div>
                </div>
              </div>
            ) : isNavigationActive || isVolumeTask ? (
              <div className="navigation-popup__route-preview navigation-popup__route-preview--final" aria-label="Navigation aktiv">
                <div className="navigation-mini-map navigation-mini-map--final" aria-hidden>
                  <span className="navigation-map-line primary" />
                  <span className="navigation-map-line secondary" />
                  <span className="navigation-map-pin start" />
                  <span className="navigation-map-pin end" />
                </div>
                <div className="navigation-popup__route-summary">
                  <span className="navigation-popup__route-badge navigation-popup__route-badge--success">Route aktiv</span>
                  <strong>Navigation läuft</strong>
                  <p>Statische Kartenansicht</p>
                </div>
              </div>
            ) : (
              <div className="navigation-popup__standard-view" aria-label="Routendetails">
                <div className="navigation-popup__route-preview navigation-popup__route-preview--suggest">
                  <div className="navigation-mini-map" aria-hidden>
                    <span className="navigation-map-line primary" />
                    <span className="navigation-map-line secondary" />
                    <span className="navigation-map-pin start" />
                    <span className="navigation-map-pin end" />
                  </div>
                </div>
                <div className="navigation-popup__meta">
                  {isVoiceNavScenario41 && (isActiveTask || isVolumeTask) ? (
                    <>
                      <span className="navigation-popup__speaker" aria-hidden>🔊</span>
                      <span className="navigation-popup__volume-label">Ansagen</span>
                      <span className="navigation-popup__volume" aria-label={`Ansagelautstärke ${isVolumeUp ? 55 : 40} Prozent`}>
                        <span className={`navigation-popup__volume-bar ${isVolumeUp ? "on" : ""}`} />
                        <span className={`navigation-popup__volume-bar ${isVolumeUp ? "on" : ""}`} />
                        <span className={`navigation-popup__volume-bar ${isVolumeUp ? "on" : ""}`} />
                        <span className={`navigation-popup__volume-bar ${isVolumeUp ? "on" : ""}`} />
                        <span className={`navigation-popup__volume-bar ${isVolumeUp ? "on" : ""}`} />
                      </span>
                    </>
                  ) : (
                    <>
                      <span>12 min</span>
                      <span>4.2 km</span>
                      <span>8 min schneller</span>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>



        {!isClarify && showVoiceActions && shouldShowVoiceControls && !isRejectRouteCompleted && (
          <div className="navigation-popup__actions" aria-label="Navigationsentscheidung">
            {isRejectRouteScenario ? (
              <button
                className={`navigation-popup__button navigation-popup__button--decline ${isRejectRouteDetected && !rejectRouteDetectedBySwipe ? "navigation-popup__button--active" : ""}`}
                type="button"
                onClick={onPreviewGesture ? () => onPreviewGesture("Ablehnen") : undefined}
              >
                Route ablehnen
              </button>
            ) : previewActions ? previewActions.map((action) => (
              <button
                key={action.label}
                className={`navigation-popup__button navigation-popup__button--${action.kind === "decline" ? "decline" : "accept"} ${(action.action === "Annehmen" && isAccepted) || (action.action === "Ablehnen" && isDeclined) || (action.action === "Lauter" && isNavigationActive) ? "navigation-popup__button--active" : ""}`}
                type="button"
                onClick={() => onPreviewGesture?.(action.action)}
              >
                {action.label}
              </button>
            )) : (
              <>
                <button className={`navigation-popup__button navigation-popup__button--accept ${isAccepted || isVolumeUp ? "navigation-popup__button--active" : ""}`} type="button" onClick={onPreviewGesture ? () => onPreviewGesture(previewGestureForVoiceTask(payload)) : undefined}>
                  {voiceActionLabel(payload)}
                </button>
                {showVoiceDecline && (
                  <button className={`navigation-popup__button navigation-popup__button--decline ${isDeclined ? "navigation-popup__button--active" : ""}`} type="button" onClick={onPreviewGesture ? () => onPreviewGesture("Swipe") : undefined}>
                    Ablehnen
                  </button>
                )}
              </>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

function isNavigationScenario32(payload: WidgetPayload): boolean {
  return payload.domain === "navigation" && (payload.study_ref === "3.2" || payload.scenario_id === "STUDY-3.2" || payload.task_id === "NAV-NEXT-ROUTE" || payload.task_id === "NAV-SELECT-SECOND");
}

function navigationScenario32Stage(payload: WidgetPayload): "waiting" | "swiped" | "confirmed" | "completed" {
  if (!isNavigationScenario32(payload)) {
    return "waiting";
  }

  if (payload.event_type === "trial_completed" && payload.decision === "execute") {
    return "completed";
  }

  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const normalizedGesture = normalizeGestureLabel(gestureLabel);
  const expectedGesture = normalizeGestureLabel(payload.expected_gesture);
  const isSwipe = normalizedGesture === "swipe";
  const isTap = normalizedGesture === "tap";
  const isSecondStep = payload.step_index === 1 || payload.task_id === "NAV-SELECT-SECOND" || expectedGesture === "tap";
  const isConfirmed = isTap || (isSecondStep && payload.decision === "execute") || gestureLabel === "Zeigen / Tippen" || gestureLabel === "Zeigen/Tippen";

  if (isConfirmed) {
    return "confirmed";
  }

  if (isSwipe) {
    return "swiped";
  }

  return "waiting";
}

function isNavigationRejectScenario13(payload: WidgetPayload): boolean {
  return payload.domain === "navigation" && (payload.study_ref === "1.3" || payload.scenario_id === "STUDY-1.3") && payload.task_id === "NAV-REJECT-ROUTE";
}

function navigationScenario13Stage(payload: WidgetPayload): "waiting" | "detected" | "completed" {
  if (!isNavigationRejectScenario13(payload)) {
    return "waiting";
  }

  if (payload.event_type === "trial_completed" || payload.decision === "cancel") {
    return "completed";
  }

  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const normalizedGesture = normalizeGestureLabel(gestureLabel);
  const voiceText = `${payload.intent ?? ""} ${payload.action ?? ""} ${payload.target ?? ""} ${payload.expected_voice ?? ""} ${payload.prompt ?? ""} ${payload.overlay_body ?? ""}`.toLowerCase();
  const detectedByGesture = normalizedGesture === "swipe";
  const detectedByVoice = voiceText.includes("ablehnen") || voiceText.includes("reject");

  if (detectedByGesture || detectedByVoice) {
    return "detected";
  }

  return "waiting";
}
