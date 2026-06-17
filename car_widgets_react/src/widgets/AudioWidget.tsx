import type { WidgetPayload } from "../types";
import {
  normalizeGestureLabel,
  popupModalityVisibility,
  PopupProcessNotice,
  previewChipProps,
  previewGestureForVoiceTask,
  voiceActionLabel,
  voicePreviewActions,
  waitingTextFor,
} from "./shared";
import type { CockpitState, PreviewGesture } from "./shared";

export function AudioWidget({ payload, state, onPreviewGesture }: { payload: WidgetPayload; state: CockpitState; onPreviewGesture?: (gesture: PreviewGesture) => void }) {
  const gestureLabel = payload.source?.gesture_event?.gesture_label ?? "";
  const normalizedGesture = normalizeGestureLabel(gestureLabel);
  const isClarify = payload.decision === "clarify";
  const isWaiting = !isClarify && !payload.decision && !gestureLabel;
  const clarifyText = payload.unclear_text || payload.prompt || "Bitte Eingabe wiederholen.";
  const isScenario21 = payload.study_ref === "2.1" || payload.scenario_id === "STUDY-2.1";
  const isResumeTask = payload.task_id === "AUDIO-RESUME";
  const isNextTask = payload.task_id === "AUDIO-NEXT";
  const isLouderTask = payload.task_id === "AUDIO-VOLUME-UP";
  const isAudioResumeNextScenario = payload.study_ref === "3.3" || payload.scenario_id === "STUDY-3.3";
  const isAudioSuggestionNextScenario = payload.study_ref === "1.2" || payload.scenario_id === "STUDY-1.2";
  const isAudioBothScenario = payload.study_ref === "3.3" || payload.scenario_id === "STUDY-3.3";
  const isTap = normalizedGesture === "tap";
  const isPlaying = !isClarify && !isNextTask && (gestureLabel === "Daumen hoch" || isTap || payload.decision === "execute");
  const isSkipped = !isClarify && isNextTask && (gestureLabel === "Swipe" || payload.decision === "execute" || payload.decision === "cancel");
  const isVolume = !isClarify && (gestureLabel === "Handgelenk drehen" || isLouderTask);
  const { showVoiceActions, showGestureActions } = popupModalityVisibility(payload);
  const previewActions = onPreviewGesture ? voicePreviewActions(payload) : null;
  const volume = Math.max(0, Math.min(100, state.volume));
  const trackTitle = state.track || "Night Drive";
  const isScenario21NextSongPlaying = isScenario21 && isNextTask && (payload.decision === "execute" || payload.event_type === "trial_completed");
  const isScenario21VolumeFinal = isScenario21 && isLouderTask && payload.event_type === "trial_completed";
  const isScenario21VolumeWaiting = isScenario21 && isLouderTask && !isScenario21VolumeFinal;

  if (isScenario21) {
    const scenario21Track = isNextTask && !isScenario21NextSongPlaying ? "Low Beam" : "City Lights";
    const scenario21Volume = isScenario21VolumeFinal ? 62 : 42;
    const scenario21StageClass = isClarify
      ? "audio-popup--clarify"
      : isScenario21VolumeFinal
        ? "audio-popup--volume audio-popup--success"
        : isScenario21VolumeWaiting
          ? "audio-popup--volume"
          : isScenario21NextSongPlaying
            ? "audio-popup--playing"
            : "audio-popup--suggested";
    const scenario21Meta = isClarify
      ? "Nicht erkannt"
      : isScenario21VolumeFinal
        ? "Lautstärke erhöht"
        : isScenario21VolumeWaiting
          ? "Bereit für Sprachbefehl"
          : isScenario21NextSongPlaying
            ? "Nächstes Lied spielt"
            : "Aktive Wiedergabe";
    const scenario21Body = isClarify
      ? payload.overlay_body || "Audiowiedergabe"
      : isScenario21VolumeFinal
        ? "Lautstärke erhöht."
        : isScenario21VolumeWaiting
          ? "City Lights wird abgespielt."
          : isScenario21NextSongPlaying
            ? "City Lights wird abgespielt."
            : "Low Beam wird abgespielt.";
    const scenario21ActionLabel = isScenario21NextSongPlaying || isScenario21VolumeWaiting ? "Lauter" : "Nächstes Lied";
    const scenario21Action = isScenario21NextSongPlaying || isScenario21VolumeWaiting ? "Lauter" : "Nächstes Lied";

    return (
      <div className={`interaction-popup audio-popup-shell ${payload.event_type || ""}`}>
        <section className={`audio-popup ${scenario21StageClass}`}>
          <div className="audio-popup__header">
            <div>
              <span className="eyebrow audio-popup__eyebrow">Audio</span>
            </div>
          </div>

          <div className="audio-popup__content">
            <div className="audio-popup__details">
              <span className="audio-popup__label">{scenario21Meta}</span>
              <strong className="audio-popup__track">{scenario21Track}</strong>
              <p>{scenario21Body}</p>
              <div className={`audio-popup__volume ${isScenario21VolumeWaiting || isScenario21VolumeFinal ? "audio-popup__volume--active" : ""}`} aria-label={`Lautstärke ${scenario21Volume}%`}>
                <div className="audio-popup__volume-label">
                  <span>Lautstärke</span>
                  <strong>{scenario21Volume}%</strong>
                </div>
                <div className="audio-popup__volume-track">
                  <span style={{ width: `${scenario21Volume}%` }} />
                </div>
              </div>
            </div>
          </div>

          <PopupProcessNotice
            isWaiting={!isClarify && !payload.decision && !gestureLabel}
            isClarify={isClarify}
            waitingText={waitingTextFor(payload)}
            clarifyText={clarifyText}
          />

          {!isClarify && !isScenario21VolumeFinal && showVoiceActions && (
            <div className="audio-popup__actions" aria-label="Audioaktionen">
              <button
                className={`audio-popup__button audio-popup__button--accept ${isScenario21NextSongPlaying || isScenario21VolumeWaiting ? "" : ""}`}
                type="button"
                onClick={onPreviewGesture ? () => onPreviewGesture(scenario21Action) : undefined}
              >
                {scenario21ActionLabel}
              </button>
            </div>
          )}
        </section>
      </div>
    );
  }

  if (isAudioResumeNextScenario) {
    const resumeDetected = isResumeTask && (isTap || payload.decision === "execute");
    const audioIntentText = `${payload.intent ?? ""} ${payload.action ?? ""} ${payload.target ?? ""}`.toLowerCase();
    const nextDetected = isNextTask && (
      gestureLabel === "Swipe" ||
      payload.event_type === "trial_completed" ||
      audioIntentText.includes("next_track") ||
      audioIntentText.includes(" next ") ||
      audioIntentText.includes("skip")
    );
    const scenario33StageClass = isClarify
      ? "audio-popup--clarify"
      : nextDetected
        ? "audio-popup--scenario33-next"
        : isNextTask
          ? "audio-popup--scenario33-running"
          : resumeDetected
            ? "audio-popup--scenario33-resumed"
            : "audio-popup--scenario33-paused";
    const scenario33Badge = isClarify
      ? "KLÄRUNG"
      : nextDetected
        ? "NÄCHSTER SONG"
        : isNextTask
          ? "LÄUFT"
          : resumeDetected
            ? "FORTGESETZT"
            : "PAUSIERT";
    const scenario33Title = nextDetected
      ? "Nächster Song"
      : isNextTask
        ? "Song läuft"
        : resumeDetected
          ? "Wiedergabe fortgesetzt"
          : "Song pausiert";
    const scenario33Track = nextDetected ? "City Lights" : "Low Beam";
    const scenario33Status = nextDetected
      ? "City Lights wird abgespielt."
      : isNextTask
        ? "Low Beam läuft. Du kannst zum nächsten Song wechseln."
        : resumeDetected
          ? "Low Beam wird abgespielt."
          : "Low Beam ist pausiert.";
    const scenario33Progress = nextDetected ? 18 : isNextTask || resumeDetected ? 42 : 0;

    return (
      <div className={`interaction-popup audio-popup-shell ${payload.event_type || ""}`}>
        <section className={`audio-popup audio-popup--scenario33 ${scenario33StageClass}`}>
          <div className="audio-popup__header">
            <div>
              <span className="eyebrow audio-popup__eyebrow">Audio</span>
              <strong className="audio-popup__title">{scenario33Title}</strong>
            </div>
            <span className="audio-popup__badge">{scenario33Badge}</span>
          </div>

          <div className="audio-popup__content audio-popup__content--player">
            <div className="audio-popup__artwork" aria-hidden>
              <span className={resumeDetected || isNextTask || nextDetected ? "audio-popup__play-indicator" : "audio-popup__pause-indicator"} />
            </div>
            <div className="audio-popup__details">
              <span className="audio-popup__label">{resumeDetected || isNextTask || nextDetected ? "Aktive Wiedergabe" : "Pausierte Wiedergabe"}</span>
              <strong className="audio-popup__track">{scenario33Track}</strong>
              <p>{scenario33Status}</p>
              <div className={`audio-popup__progress ${resumeDetected || isNextTask || nextDetected ? "audio-popup__progress--active" : ""}`} aria-label={`Fortschritt ${scenario33Progress}%`}>
                <div className="audio-popup__progress-label">
                  <span>{nextDetected ? "Neuer Titel" : "Fortschritt"}</span>
                  <strong>{scenario33Progress}%</strong>
                </div>
                <div className="audio-popup__progress-track">
                  <span style={{ width: `${scenario33Progress}%` }} />
                </div>
              </div>
            </div>
          </div>

          {!isClarify && showGestureActions && (
            <div className="audio-popup__actions" aria-label="Audio 3.3 Gesten">
              {isResumeTask && (
                <span className={`audio-popup__chip audio-popup__chip--accept ${resumeDetected ? "audio-popup__chip--active" : ""}`} {...previewChipProps("Zeigen / Tippen", onPreviewGesture)}>
                  <span aria-hidden>⌾</span>Tippen zum Fortsetzen
                </span>
              )}
              {isNextTask && (
                <span className={`audio-popup__chip audio-popup__chip--decline ${nextDetected ? "audio-popup__chip--active" : ""}`} {...previewChipProps("Swipe", onPreviewGesture)}>
                  <span aria-hidden>↔</span>Swipe zum nächsten Song
                </span>
              )}
            </div>
          )}
          {!isClarify && showVoiceActions && (
            <div className="audio-popup__actions" aria-label="Audio 3.3 Sprachaktionen">
              {previewActions ? previewActions.map((action) => (
                <button
                  key={action.label}
                  className={`audio-popup__button audio-popup__button--accept ${(action.action === "Nächstes Lied" && nextDetected) || (action.action === "Zeigen / Tippen" && resumeDetected) ? "audio-popup__button--active" : ""}`}
                  type="button"
                  onClick={() => onPreviewGesture?.(action.action)}
                >
                  {isResumeTask ? "Wiedergabe fortsetzen" : action.label}
                </button>
              )) : (
                <button className={`audio-popup__button audio-popup__button--accept ${resumeDetected || nextDetected ? "audio-popup__button--active" : ""}`} type="button" onClick={onPreviewGesture ? () => onPreviewGesture(isResumeTask ? "Zeigen / Tippen" : "Swipe") : undefined}>
                  {isResumeTask ? "Wiedergabe fortsetzen" : "Nächster Song"}
                </button>
              )}
            </div>
          )}
        </section>
      </div>
    );
  }

  const stageClass = isClarify
    ? "audio-popup--clarify"
    : isVolume
      ? "audio-popup--volume"
    : isSkipped
      ? "audio-popup--skipped"
      : isResumeTask && !isPlaying
        ? "audio-popup--paused"
        : isPlaying
          ? "audio-popup--playing"
          : "audio-popup--suggested";
  const body = isClarify
    ? payload.overlay_body || "Audiowiedergabe"
    : isVolume && payload.decision === "execute"
      ? payload.accepted_text || "Lautstärke angepasst"
    : isVolume
      ? payload.overlay_body || payload.prompt || "Lautstärke erhöhen."
    : isSkipped
      ? payload.accepted_text || "Nächster Song wird abgespielt"
      : isPlaying
        ? payload.accepted_text || "Wiedergabe gestartet"
        : isResumeTask
          ? payload.overlay_body || payload.prompt || "Song ist pausiert."
        : payload.overlay_body || payload.prompt || "Night Drive abspielen?";
  const metaText = isVolume ? `${volume}% Lautstärke` : isResumeTask && !isPlaying ? "Pausiert" : isPlaying ? "Spielt" : isSkipped ? "Nächster Titel" : isNextTask ? "Aktive Wiedergabe" : "Vorgeschlagen";

  return (
    <div className={`interaction-popup audio-popup-shell ${payload.event_type || ""}`}>
      <section className={`audio-popup ${stageClass}`}>
        <div className="audio-popup__header">
          <div>
            <span className="eyebrow audio-popup__eyebrow">Audio</span>
          </div>
        </div>

        <div className="audio-popup__content">
          <div className="audio-popup__details">
            <span className="audio-popup__label">{metaText}</span>
            <strong className="audio-popup__track">{trackTitle}</strong>
            <p>{body}</p>
            <div className={`audio-popup__volume ${isVolume ? "audio-popup__volume--active" : ""}`} aria-label={`Lautstärke ${volume}%`}>
              <div className="audio-popup__volume-label">
                <span>Lautstärke</span>
                <strong>{volume}%</strong>
              </div>
              <div className="audio-popup__volume-track">
                <span style={{ width: `${volume}%` }} />
              </div>
            </div>
          </div>
        </div>

        {!isClarify && showGestureActions && (
          <div className="audio-popup__actions" aria-label="Audiogesten">
            <span
              className={`audio-popup__chip audio-popup__chip--accept ${isPlaying ? "audio-popup__chip--active" : ""}`}
              {...previewChipProps(isAudioBothScenario ? "Zeigen / Tippen" : isResumeTask ? "Zeigen / Tippen" : "Daumen hoch", onPreviewGesture)}
            >
              <span aria-hidden>{isAudioBothScenario || isResumeTask ? "⌾" : "👍"}</span>{isAudioBothScenario || isResumeTask ? "Tippen" : "Daumen hoch"}
            </span>
            <span className={`audio-popup__chip audio-popup__chip--decline ${isSkipped ? "audio-popup__chip--active" : ""}`} {...previewChipProps("Swipe", onPreviewGesture)}>
              <span aria-hidden>↔</span>{isNextTask ? "Swipe" : "Swipe"}
            </span>
            {!isAudioResumeNextScenario && !isAudioSuggestionNextScenario && (
              <span className={`audio-popup__chip audio-popup__chip--volume ${isVolume ? "audio-popup__chip--active" : ""}`} {...previewChipProps("Handgelenk drehen", onPreviewGesture)}>
                <span aria-hidden>↻</span>Drehen
              </span>
            )}
          </div>
        )}
        {!isClarify && showVoiceActions && (
          <div className="audio-popup__actions" aria-label="Audioaktionen">
            {previewActions ? previewActions.map((action) => (
              <button
                key={action.label}
                className={`audio-popup__button audio-popup__button--accept ${(action.action === "Nächstes Lied" && isSkipped) || (action.action === "Lauter" && isVolume) ? "audio-popup__button--active" : ""}`}
                type="button"
                onClick={() => onPreviewGesture?.(action.action)}
              >
                {action.label}
              </button>
            )) : (
              <>
                <button className={`audio-popup__button audio-popup__button--accept ${isPlaying || isSkipped || isVolume ? "audio-popup__button--active" : ""}`} type="button" onClick={onPreviewGesture ? () => onPreviewGesture(previewGestureForVoiceTask(payload)) : undefined}>
                  {voiceActionLabel(payload)}
                </button>
                {payload.condition !== "Voice only" && (
                  <button className={`audio-popup__button audio-popup__button--decline ${isSkipped ? "audio-popup__button--active" : ""}`} type="button" onClick={onPreviewGesture ? () => onPreviewGesture("Swipe") : undefined}>
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
