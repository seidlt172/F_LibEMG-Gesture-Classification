"""State model for the provisional in-car widget interface."""

from __future__ import annotations

from dataclasses import dataclass, field

from .scenarios import FlowStep
from .scenarios import StudyScenario


@dataclass
class CarState:
    condition: str = "CAN use both"
    active_scenario: StudyScenario | None = None
    current_step_index: int = 0
    scenario_complete: bool = False
    active_domain: str = "navigation"
    overlay_visible: bool = False
    overlay_title: str = ""
    overlay_body: str = ""
    feedback_status: str = ""
    feedback_text: str = "Bereit."
    clarification_text: str = ""
    event_log: list[str] = field(default_factory=list)
    call_incoming: bool = False
    call_active: bool = False
    message_available: bool = False
    message_open: bool = False
    route_suggestion_visible: bool = True
    route_index: int = 1
    route_selected: bool = False
    nav_volume: int = 40
    audio_track: str = "Low Beam"
    audio_playing: bool = True
    volume: int = 42
    ambient_color: str = "Blau"
    ambient_brightness: int = 45
    night_mode: bool = False
    seat_heating_selected: bool = False
    seat_heating_level: int = 1
    climate_temperature: int = 21

    def log(self, message: str) -> None:
        self.event_log.append(message)
        if len(self.event_log) > 80:
            self.event_log = self.event_log[-80:]

    def current_step(self) -> FlowStep | None:
        if self.active_scenario is None:
            return None
        return self.active_scenario.flow_steps[self.current_step_index]


def create_initial_state() -> CarState:
    state = CarState()
    state.log("Interface bereit.")
    return state


def load_scenario(state: CarState, scenario: StudyScenario) -> CarState:
    state.condition = scenario.condition
    state.active_scenario = scenario
    state.current_step_index = 0
    state.scenario_complete = False
    state.feedback_status = ""
    state.clarification_text = ""
    _reset_domain_state_for_scenario(state, scenario)
    set_step_overlay(state)
    first_step = state.current_step()
    state.feedback_text = first_step.prompt if first_step else scenario.title
    state.log(f"Study-Flow geladen: {scenario.study_ref} ({scenario.condition}).")
    return state


def set_step_overlay(state: CarState) -> None:
    step = state.current_step()
    if step is None:
        state.overlay_visible = False
        state.overlay_title = ""
        state.overlay_body = ""
        return

    state.active_domain = step.domain
    state.overlay_visible = True
    state.overlay_title = step.overlay_title
    state.overlay_body = step.overlay_body
    state.clarification_text = ""


def advance_step_or_complete(state: CarState) -> bool:
    if state.active_scenario is None:
        return False
    if state.current_step_index < len(state.active_scenario.flow_steps) - 1:
        state.current_step_index += 1
        set_step_overlay(state)
        next_step = state.current_step()
        if next_step:
            state.log(f"Naechster Schritt: {next_step.task_id}.")
        return True

    state.scenario_complete = True
    state.overlay_visible = False
    state.clarification_text = ""
    state.log(f"Study-Flow abgeschlossen: {state.active_scenario.study_ref}.")
    return False


def _reset_domain_state_for_scenario(state: CarState, scenario: StudyScenario) -> None:
    task_ids = {step.task_id for step in scenario.flow_steps}
    state.call_incoming = "CALL-INCOMING" in task_ids
    state.call_active = "CALL-END" in task_ids or "CALL-VOLUME" in task_ids
    state.message_available = any(task_id.startswith("MESSAGE") for task_id in task_ids)
    state.message_open = "MESSAGE-CLOSE" in task_ids
    state.route_suggestion_visible = any(task_id.startswith("NAV") for task_id in task_ids)
    state.route_selected = False
    state.route_index = 1
    state.audio_playing = "AUDIO-RESUME" not in task_ids
    state.audio_track = "Low Beam"
    state.volume = 42
    state.nav_volume = 40
    state.ambient_color = "Blau"
    state.ambient_brightness = 45
    state.night_mode = False
    state.seat_heating_selected = any(task_id.startswith("CLIMATE") for task_id in task_ids)
    state.seat_heating_level = 1
    state.climate_temperature = 21
