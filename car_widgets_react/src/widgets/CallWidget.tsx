import type { WidgetPayload } from "../types";
import {
  normalizeGestureLabel,
  popupModalityVisibility,
  previewChipProps,
  voicePreviewActions,
} from "./shared";
import type { CockpitState, PreviewGesture } from "./shared";

export function CallWidget({ payload, state, onPreviewGesture }: { payload: WidgetPayload; state: CockpitState; onPreviewGesture?: (gesture: PreviewGesture) => void }) {
  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const normalizedGesture = normalizeGestureLabel(gestureLabel);
  const intentText = `${payload.intent ?? ""} ${payload.action ?? ""} ${payload.target ?? ""}`.toLowerCase();
  const isClarify = payload.decision === "clarify";
  const isWaiting = !isClarify && !payload.decision && !gestureLabel;
  const clarifyText = payload.unclear_text || payload.prompt || "Bitte Eingabe wiederholen.";
  const isIncomingTask = payload.task_id === "CALL-INCOMING";
  const isActiveTask = payload.task_id === "CALL-ACTIVE";
  const isEndedTask = payload.task_id === "CALL-ENDED";
  const isVolumeTask = payload.task_id === "CALL-VOLUME";
  const isRotate = normalizedGesture === "handgelenkdrehen";
  const isVolumeIntent = intentText.includes("volume") || intentText.includes("laut") || intentText.includes("increase");
  const isVolumeAdjusting = !isClarify && isVolumeTask && (isRotate || isVolumeIntent || payload.event_type === "trial_completed");
  const showEndedView = isEndedTask || (payload.event_type === "trial_completed" && !isVolumeTask);
  const { showVoiceActions, showGestureActions } = popupModalityVisibility(payload);
  const previewActions = onPreviewGesture ? voicePreviewActions(payload) : null;
  const stageClass = isClarify
    ? "call-popup--clarify"
    : showEndedView
      ? "call-popup--ended"
      : isActiveTask
        ? "call-popup--active"
        : isVolumeAdjusting
          ? "call-popup--volume call-popup--volume-adjusted"
          : isVolumeTask
            ? "call-popup--volume"
            : "call-popup--incoming";
  const body = isClarify
    ? payload.overlay_body || "Anruf mit Alex."
    : showEndedView
      ? payload.accepted_text || payload.overlay_body || "Anruf beendet."
      : isActiveTask
        ? payload.overlay_body || payload.prompt || "Anruf mit Alex läuft."
        : isVolumeTask
          ? isVolumeAdjusting
            ? payload.accepted_text || "Anruflautstärke geregelt."
            : payload.overlay_body || payload.prompt || "Anruf mit Alex läuft."
          : payload.overlay_body || payload.prompt || "Max Mustermann ruft an.";
  const callVolume = Math.max(0, Math.min(100, isVolumeAdjusting ? Math.max(state.volume, 72) : state.volume));
  const callStatus = showEndedView
    ? "Anruf beendet"
    : isVolumeAdjusting
      ? "Lautstärke erhöht"
    : isActiveTask || isVolumeTask
      ? "Gespräch aktiv"
      : "Eingehender Anruf";
  const contactLabel = isActiveTask || isVolumeTask || showEndedView ? "Alex · 00:42" : "Max Mustermann";

  return (
    <div className={`interaction-popup call-popup-shell ${payload.event_type || ""}`}>
      <section className={`call-popup ${stageClass}`}>
        {showEndedView ? (
          <div className="call-popup__ended-anim" style={{ textAlign: "center", padding: "20px" }}>
            <div className="success-checkmark">
              <div className="check-icon">
                <span className="icon-line line-tip"></span>
                <span className="icon-line line-long"></span>
                <div className="icon-circle"></div>
                <div className="icon-fix"></div>
              </div>
            </div>
            <h2 style={{ margin: "1rem 0 0 0", fontSize: "1.5rem", fontWeight: "600" }}>{body}</h2>
          </div>
        ) : (
          <>
            <div className="call-popup__content" style={{ textAlign: "center", padding: "10px 0 20px 0" }}>
              <h2 style={{ margin: 0, fontSize: "1.5rem", fontWeight: "600" }}>
                {isIncomingTask ? "Alex ruft an" : body}
              </h2>
              {isVolumeTask && (
                <div className="call-popup__volume-panel" style={{ marginTop: "20px", textAlign: "left" }}>
                  <div className="call-popup__volume-row">
                    <span>Anruflautstärke</span>
                    <strong>{callVolume}%</strong>
                  </div>
                  <div className="call-popup__volume" aria-label={`Anruflautstärke ${callVolume}%`}>
                    <span style={{ width: `${callVolume}%` }} />
                  </div>
                </div>
              )}
            </div>


          </>
        )}

        {!isClarify && (isVolumeTask ? (
          <>
            {showVoiceActions && (
              <div className="call-popup__actions" aria-label="Anruflautstärke per Sprache">
                <button className={`call-popup__button call-popup__button--accept ${isVolumeAdjusting ? "call-popup__button--active" : ""}`} type="button" onClick={onPreviewGesture ? () => onPreviewGesture("Handgelenk drehen") : undefined}>
                  {payload.expected_voice || "Mach lauter"}
                </button>
              </div>
            )}
          </>
        ) : (
          <>
            {showVoiceActions && (
              <div className="call-popup__actions" aria-label="Anrufaktionen">
                {previewActions ? previewActions.map((action) => (
                  <button
                    key={action.label}
                    className={`call-popup__button call-popup__button--${action.kind === "decline" ? "decline" : "accept"}`}
                    type="button"
                    onClick={() => onPreviewGesture?.(action.action)}
                  >
                    {action.label}
                  </button>
                )) : isIncomingTask ? (
                  <>
                    <button className={`call-popup__button call-popup__button--accept ${payload.decision === "execute" && (payload.task_id === "CALL-INCOMING" || payload.task_id === "CALL-ACTIVE") ? "call-popup__button--active" : ""}`} type="button" onClick={onPreviewGesture ? () => onPreviewGesture("Annehmen") : undefined}>
                      Annehmen
                    </button>
                    <button className={`call-popup__button call-popup__button--decline ${payload.decision === "cancel" ? "call-popup__button--active" : ""}`} type="button" onClick={onPreviewGesture ? () => onPreviewGesture("Ablehnen") : undefined}>
                      Ablehnen
                    </button>
                  </>
                ) : isActiveTask ? (
                  <>
                    <button className={`call-popup__button call-popup__button--decline ${gestureLabel === "Auflegen" ? "call-popup__button--active" : ""}`} type="button" onClick={onPreviewGesture ? () => onPreviewGesture("Auflegen") : undefined}>
                      Auflegen
                    </button>
                  </>
                ) : null}
              </div>
            )}
          </>
        ))}
      </section>
    </div>
  );
}
