export type Condition = "Voice only" | "Gesture only" | "CAN use both";
export type Decision = "execute" | "cancel" | "clarify";
export type Domain = "calls" | "navigation" | "audio" | "messages" | "ambient_light" | "climate";
export type WidgetEventType = "scenario_start" | "step_update" | "trial_completed";

export interface GestureEventPayload {
  gesture_label?: string | null;
  gesture_id?: number | null;
  confidence?: number | null;
  source?: string;
}

export interface WidgetPayloadSource {
  gesture_event?: GestureEventPayload | null;
  used_modalities?: string;
}

export interface WidgetPayload {
  event_type?: WidgetEventType;
  trial_id?: string;
  decision?: Decision;
  condition?: Condition;
  category?: string;
  scenario_id?: string;
  study_ref?: string;
  scenario_prompt?: string;
  domain?: Domain | "unknown";
  step_index?: number;
  step_count?: number;
  task_id?: string;
  prompt?: string;
  overlay_title?: string;
  overlay_body?: string;
  modality?: string;
  expected_decision?: Decision;
  expected_voice?: string;
  expected_gesture?: string;
  gesture_ref?: string;
  accepted_text?: string;
  rejected_text?: string;
  unclear_text?: string;
  intent?: string;
  action?: string;
  target?: string;
  value?: string | null;
  clarification?: string;
  success?: boolean;
  source?: WidgetPayloadSource;
}

export interface LatestResponse {
  event_id: number;
  payload: WidgetPayload | null;
}
