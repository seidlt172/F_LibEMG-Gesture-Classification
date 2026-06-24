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
      <section className={`audio-popup ${stageClass} music-widget`} style={{ height: 'auto', padding: 0 }}>
        <div className="music-widget-frame" style={{ height: 'auto' }}>
          <div className="music-widget-main">
            <div className="side-widget-header">
              <span className="eyebrow music-widget-title">Audio</span>
              <span className="side-widget-badge voice">{metaText}</span>
            </div>
            <div className="music-widget-track">
              <div className="music-album-art" aria-hidden>
                <span>{trackTitle.substring(0, 2).toUpperCase()}</span>
              </div>
              <div className="music-track-copy">
                <strong className="widget-title music-track-title">{trackTitle}</strong>
                <span className="music-track-meta">{body}</span>
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
                <span aria-hidden>{"<"}</span>
              </button>
              <button className="music-control-button play" type="button" aria-label="Abspielen">
                <span aria-hidden>{isPlaying ? "||" : "▶"}</span>
              </button>
              <button className={`music-control-button ${isSkipped ? 'active' : ''}`} type="button" aria-label="Nächster Titel">
                <span aria-hidden>{">"}</span>
              </button>
            </div>

          </div>
        </div>
      </section>
    </div>
  );
}
