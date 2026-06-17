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

export function MessageWidget({ payload, state, onPreviewGesture }: { payload: WidgetPayload; state: CockpitState; onPreviewGesture?: (gesture: PreviewGesture) => void }) {
  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const normalizedGesture = normalizeGestureLabel(gestureLabel);
  const isClarify = payload.decision === "clarify";
  const isConfirmed = !isClarify && gestureLabel === "Daumen hoch";
  const isIncomingTask = payload.task_id === "MESSAGE-INCOMING";
  const isOpenTask = payload.task_id === "MESSAGE-OPEN";
  const isOpenedTask = payload.task_id === "MESSAGE-OPENED";
  const isCloseTask = payload.task_id === "MESSAGE-CLOSE";
  const isClosedTask = payload.task_id === "MESSAGE-CLOSED";
  const isCompletedClose = payload.event_type === "trial_completed" && isCloseTask && payload.success !== false;
  const isMessageClosed = !isClarify && (isClosedTask || isCompletedClose);
  const isCloseInstruction = !isClarify && isCloseTask && !isCompletedClose;
  const isOpened = !isClarify && !isConfirmed && !isCloseInstruction && !isMessageClosed && (
    isOpenedTask ||
    normalizedGesture === "tap"
  );
  const isIncoming = !isClarify && !isConfirmed && !isOpened && !isCloseInstruction && !isMessageClosed && (isIncomingTask || isOpenTask || !payload.task_id);
  const { showVoiceActions, showGestureActions } = popupModalityVisibility(payload);
  const previewActions = onPreviewGesture ? voicePreviewActions(payload) : null;
  const showMessageActions = !isMessageClosed && !isOpenedTask;
  const stageClass = isClarify
    ? "messages-popup--clarify"
    : isConfirmed
      ? "messages-popup--confirmed"
      : isMessageClosed
        ? "messages-popup--closed"
        : isCloseInstruction
          ? "messages-popup--readable"
        : isOpened
          ? "messages-popup--opened"
          : "messages-popup--new";
  const body = isClarify
    ? payload.overlay_body || "Neue Nachricht von Anna."
    : isConfirmed
      ? payload.accepted_text || "Bestätigt"
    : isMessageClosed
        ? payload.accepted_text || "Nachricht geschlossen."
        : isCloseInstruction
          ? payload.overlay_body || "Nachricht ist geöffnet und lesbar."
        : isOpened
          ? payload.overlay_body || payload.accepted_text || "Nachricht ist geöffnet und lesbar."
          : payload.overlay_body || payload.prompt || "Neue Nachricht von Anna.";
  const messageStatus = isMessageClosed
    ? "Nachricht geschlossen"
    : isCloseInstruction
      ? "Nachricht geöffnet"
      : isOpened
        ? "Nachricht geöffnet"
        : isConfirmed
          ? "Bestätigt"
          : isIncoming
            ? "Neue Nachricht"
            : "Nachricht";

  return (
    <div className={`interaction-popup messages-popup-shell ${payload.event_type || ""}`}>
      <section className={`messages-popup ${stageClass}`}>
        <div className="messages-popup__header">
          <div>
            <span className="eyebrow messages-popup__eyebrow">Nachrichten</span>
          </div>
        </div>

        <div className="messages-popup__content">
          <div className={`messages-popup__preview ${isMessageClosed ? "messages-popup__preview--closed" : ""}`}>
            {isMessageClosed ? (
              <>
                <span className="messages-popup__closed-icon" aria-hidden>✓</span>
                <strong>{messageStatus}</strong>
                <p className="messages-popup__text">{body}</p>
              </>
            ) : (
              <>
                <span className="messages-popup__sender">Von: <strong>Anna</strong></span>
                <strong>{messageStatus}</strong>
                <p className="messages-popup__text">{body}</p>
              </>
            )}
          </div>
        </div>

        {!isClarify && showGestureActions && showMessageActions && (
          <div className="messages-popup__actions" aria-label="Nachrichtengesten">
            <span className={`messages-popup__chip messages-popup__chip--open ${isOpened ? "messages-popup__chip--active" : ""}`} {...previewChipProps("Zeigen / Tippen", onPreviewGesture)}>
              <span aria-hidden>⌾</span>Tippen
            </span>
            <span className={`messages-popup__chip messages-popup__chip--close ${isCloseInstruction ? "messages-popup__chip--active" : ""}`} {...previewChipProps("Swipe", onPreviewGesture)}>
              <span aria-hidden>↔</span>Swipe
            </span>
            <span className={`messages-popup__chip messages-popup__chip--confirm ${isConfirmed ? "messages-popup__chip--active" : ""}`} {...previewChipProps("Daumen hoch", onPreviewGesture)}>
              <span aria-hidden>👍</span>Daumen hoch
            </span>
          </div>
        )}
        {!isClarify && showVoiceActions && showMessageActions && (
          <div className="messages-popup__actions" aria-label="Nachrichtenaktionen">
            {previewActions ? previewActions.map((action) => (
              <button
                key={action.label}
                className={`messages-popup__button messages-popup__button--${action.kind === "decline" ? "close" : "open"} ${(action.action === "Nachricht öffnen" && isIncoming) || (action.action === "Schließen" && isCloseInstruction) ? "messages-popup__button--active" : ""}`}
                type="button"
                onClick={() => onPreviewGesture?.(action.action)}
              >
                {action.label}
              </button>
            )) : (
              <>
                <button className={`messages-popup__button messages-popup__button--open ${isIncoming || isCloseInstruction ? "messages-popup__button--active" : ""}`} type="button" onClick={onPreviewGesture ? () => onPreviewGesture(previewGestureForVoiceTask(payload)) : undefined}>
                  {voiceActionLabel(payload)}
                </button>
                {payload.condition !== "Voice only" && (
                  <button className={`messages-popup__button messages-popup__button--close ${isCloseInstruction ? "messages-popup__button--active" : ""}`} type="button" onClick={onPreviewGesture ? () => onPreviewGesture("Swipe") : undefined}>
                    Schließen
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
