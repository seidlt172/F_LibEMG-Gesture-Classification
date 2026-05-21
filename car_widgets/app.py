"""Startable participant-facing in-car widget demo.

Run with:
    python -m car_widgets.app
"""

from __future__ import annotations

import json
import os
import queue
import threading
import tkinter as tk
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer

from . import theme
from .components import Fonts
from .components import button
from .components import card
from .components import clear
from .components import render_feedback
from .components import render_guidance
from .components import render_overlay
from .feedback import apply_feedback
from .feedback import build_payload
from .scenarios import SCENARIOS
from .scenarios import get_scenario
from .scenarios import scenario_id_from_title
from .scenarios import scenario_titles
from .state import create_initial_state
from .state import load_scenario


BRIDGE_HOST = os.environ.get("CAR_WIDGET_BRIDGE_HOST", "127.0.0.1")
BRIDGE_PORT = int(os.environ.get("CAR_WIDGET_BRIDGE_PORT", "8765"))
BRIDGE_PATH = "/widget-event"


class WidgetEventHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != BRIDGE_PATH:
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw)
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "Invalid JSON payload")
            return

        self.server.payload_queue.put(payload)  # type: ignore[attr-defined]
        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"received": true}')

    def log_message(self, format: str, *args) -> None:
        return


class CarWidgetApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Car Widgets Prototype")
        self.root.configure(bg=theme.BG)
        self.fonts = Fonts()
        self.state = create_initial_state()
        self.inbound_payloads: queue.Queue[dict] = queue.Queue()
        self.bridge_server: ThreadingHTTPServer | None = None
        self._suppress_scenario_trace = False
        self.condition_var = tk.StringVar(value=SCENARIOS[0].condition)
        self.scenario_var = tk.StringVar(value=scenario_titles()[0])
        self.scenario_var.trace_add("write", lambda *_: self._on_scenario_selection_changed())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._load_selected_scenario()
        self._start_bridge_server()
        self._poll_inbound_payloads()

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg=theme.BG)
        header.pack(fill="x", padx=theme.PAD, pady=(16, 10))
        tk.Label(header, text="In-Car Interaction Prototype", font=self.fonts.title,
                 bg=theme.BG, fg=theme.TEXT).pack(side="left")
        self.condition_badge = tk.Label(header, text="", font=self.fonts.h2,
                                        bg=theme.SURFACE_ALT, fg=theme.ACCENT,
                                        padx=12, pady=6)
        self.condition_badge.pack(side="right")

        top = tk.Frame(self.root, bg=theme.BG)
        top.pack(fill="x", padx=theme.PAD, pady=(0, 12))

        self.task_card = card(top)
        self.task_card.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self.guidance_card = card(top)
        self.guidance_card.pack(side="left", fill="both", expand=True, padx=(12, 0))

        middle = tk.Frame(self.root, bg=theme.BG)
        middle.pack(fill="both", expand=True, padx=theme.PAD)
        middle.grid_columnconfigure(0, weight=2)
        middle.grid_columnconfigure(1, weight=1)
        middle.grid_rowconfigure(0, weight=1)

        cockpit = tk.Frame(middle, bg=theme.BG)
        cockpit.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        cockpit.grid_columnconfigure(0, weight=1)
        cockpit.grid_columnconfigure(1, weight=1)
        cockpit.grid_rowconfigure(0, weight=1)
        cockpit.grid_rowconfigure(1, weight=1)

        self.navigation_card = card(cockpit)
        self.navigation_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        self.audio_card = card(cockpit)
        self.audio_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
        self.message_card = card(cockpit)
        self.message_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(8, 0))
        lower_right = tk.Frame(cockpit, bg=theme.BG)
        lower_right.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))
        lower_right.grid_columnconfigure(0, weight=1)
        lower_right.grid_columnconfigure(1, weight=1)
        self.ambient_card = card(lower_right)
        self.ambient_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.climate_card = card(lower_right)
        self.climate_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        side = tk.Frame(middle, bg=theme.BG)
        side.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        self.overlay_card = card(side)
        self.overlay_card.pack(fill="x")
        self.feedback_card = card(side)
        self.feedback_card.pack(fill="x", pady=(12, 0))
        self.demo_card = card(side)
        self.demo_card.pack(fill="x", pady=(12, 0))
        self.log_card = card(side)
        self.log_card.pack(fill="both", expand=True, pady=(12, 0))

        self._build_demo_controls()

    def _build_demo_controls(self) -> None:
        clear(self.demo_card)
        tk.Label(self.demo_card, text="Demo Control", font=self.fonts.h2,
                 bg=theme.SURFACE, fg=theme.TEXT).pack(anchor="w")

        tk.Label(self.demo_card, text="Study-Flow", font=self.fonts.small,
                 bg=theme.SURFACE, fg=theme.TEXT_DIM).pack(anchor="w", pady=(10, 2))
        scenario_menu = tk.OptionMenu(self.demo_card, self.scenario_var, *scenario_titles())
        self._style_option_menu(scenario_menu)
        scenario_menu.pack(fill="x")

        tk.Label(
            self.demo_card,
            text="Die Condition kommt aus dem gewaehlten Studien-Flow.",
            font=self.fonts.small,
            bg=theme.SURFACE,
            fg=theme.TEXT_DIM,
            wraplength=320,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        tk.Label(self.demo_card, text="Middleware Decision simulieren", font=self.fonts.small,
                 bg=theme.SURFACE, fg=theme.TEXT_DIM).pack(anchor="w", pady=(12, 4))
        row = tk.Frame(self.demo_card, bg=theme.SURFACE)
        row.pack(fill="x")
        button(row, "execute", lambda: self._simulate("execute"), primary=True).pack(side="left", fill="x", expand=True, padx=(0, 4))
        button(row, "cancel", lambda: self._simulate("cancel"), danger=True).pack(side="left", fill="x", expand=True, padx=4)
        button(row, "clarify", lambda: self._simulate("clarify")).pack(side="left", fill="x", expand=True, padx=(4, 0))

    def _style_option_menu(self, menu: tk.OptionMenu) -> None:
        menu.config(bg=theme.SURFACE_ALT, fg=theme.TEXT, activebackground=theme.SURFACE_ACTIVE,
                    activeforeground=theme.TEXT, relief="flat", bd=0, highlightthickness=0)
        menu["menu"].config(bg=theme.SURFACE_ALT, fg=theme.TEXT, activebackground=theme.ACCENT_DARK)

    def _on_scenario_selection_changed(self) -> None:
        if not self._suppress_scenario_trace:
            self._load_selected_scenario()

    def _load_selected_scenario(self) -> None:
        scenario = get_scenario(scenario_id_from_title(self.scenario_var.get()))
        self.condition_var.set(scenario.condition)
        load_scenario(self.state, scenario)
        self._render()

    def _simulate(self, decision: str) -> None:
        scenario = self.state.active_scenario or SCENARIOS[0]
        payload = build_payload(
            condition=scenario.condition,
            scenario=scenario,
            decision=decision,
            clarification=self.state.current_step().unclear_text if decision == "clarify" and self.state.current_step() else "",
        )
        apply_feedback(self.state, payload)
        self._render()

    def _start_bridge_server(self) -> None:
        try:
            self.bridge_server = ThreadingHTTPServer((BRIDGE_HOST, BRIDGE_PORT), WidgetEventHandler)
            self.bridge_server.payload_queue = self.inbound_payloads  # type: ignore[attr-defined]
        except OSError as exc:
            self.state.log(f"Widget bridge nicht gestartet: {exc}")
            return

        thread = threading.Thread(target=self.bridge_server.serve_forever, daemon=True)
        thread.start()
        self.state.log(f"Widget bridge aktiv: http://{BRIDGE_HOST}:{BRIDGE_PORT}{BRIDGE_PATH}")

    def _poll_inbound_payloads(self) -> None:
        handled = False
        while True:
            try:
                payload = self.inbound_payloads.get_nowait()
            except queue.Empty:
                break
            self._handle_bridge_payload(payload)
            handled = True
        if handled:
            self._render()
        self.root.after(100, self._poll_inbound_payloads)

    def _handle_bridge_payload(self, payload: dict) -> None:
        scenario_key = payload.get("study_ref") or payload.get("scenario_id")
        if scenario_key:
            scenario = get_scenario(str(scenario_key))
            if self.state.active_scenario is None or self.state.active_scenario.study_ref != scenario.study_ref:
                self._suppress_scenario_trace = True
                self.scenario_var.set(self._title_for_scenario(scenario.study_ref))
                self._suppress_scenario_trace = False
                self.condition_var.set(scenario.condition)
                load_scenario(self.state, scenario)

        apply_feedback(self.state, payload)
        self.state.log(
            f"Middleware Decision empfangen: {payload.get('decision', payload.get('status', 'clarify'))}."
        )

    def _title_for_scenario(self, study_ref: str) -> str:
        prefix = f"{study_ref} - "
        for title in scenario_titles():
            if title.startswith(prefix):
                return title
        return scenario_titles()[0]

    def _on_close(self) -> None:
        if self.bridge_server is not None:
            self.bridge_server.shutdown()
            self.bridge_server.server_close()
        self.root.destroy()

    def _render(self) -> None:
        self.condition_badge.config(text=self.condition_var.get())
        self._render_task()
        render_guidance(self.guidance_card, self.condition_var.get(), self.fonts)
        self._render_cockpit()
        self._render_overlay()
        render_feedback(self.feedback_card, self.state.feedback_status,
                        self.state.feedback_text, self.fonts)
        self._render_log()

    def _render_task(self) -> None:
        clear(self.task_card)
        scenario = self.state.active_scenario
        tk.Label(self.task_card, text="Aktuelle Aufgabe", font=self.fonts.h2,
                 bg=theme.SURFACE, fg=theme.TEXT).pack(anchor="w")
        if scenario is None:
            return
        step = self.state.current_step()
        step_count = len(scenario.flow_steps)
        step_number = self.state.current_step_index + 1
        tk.Label(self.task_card, text=f"{scenario.study_ref}  {scenario.title}", font=self.fonts.h1,
                 bg=theme.SURFACE, fg=theme.TEXT).pack(anchor="w", pady=(8, 2))
        if step is None:
            return
        tk.Label(self.task_card, text=f"Schritt {step_number}/{step_count}: {step.prompt}", font=self.fonts.body,
                 bg=theme.SURFACE, fg=theme.TEXT_MUTED, wraplength=560,
                 justify="left").pack(anchor="w")
        expected = self._format_expected_input(step)
        tk.Label(self.task_card, text=expected, font=self.fonts.body,
                 bg=theme.SURFACE, fg=theme.ACCENT, wraplength=560,
                 justify="left").pack(anchor="w", pady=(8, 0))
        tk.Label(self.task_card, text=f"{scenario.scenario_id}  |  {scenario.category_name}  |  {scenario.condition}",
                 font=self.fonts.mono, bg=theme.SURFACE, fg=theme.TEXT_DIM).pack(anchor="w", pady=(10, 0))

    def _format_expected_input(self, step) -> str:
        parts = [f"Modalitaet: {step.modality}"]
        if step.voice_input:
            parts.append(f"Voice: '{step.voice_input}'")
        if step.gesture_label:
            gesture = step.gesture_label
            if step.gesture_ref:
                gesture = f"{gesture} ({step.gesture_ref})"
            parts.append(f"Geste: {gesture}")
        parts.append(f"Erwartete Decision: {step.expected_status}")
        return "  |  ".join(parts)

    def _render_cockpit(self) -> None:
        self._render_navigation()
        self._render_audio()
        self._render_messages()
        self._render_ambient()
        self._render_climate()

    def _render_navigation(self) -> None:
        clear(self.navigation_card)
        self._domain_title(self.navigation_card, "Navigation", "Route B17")
        route = f"Route {self.state.route_index}: 18 min | 12 km"
        selected = "aktiv" if self.state.route_selected else "Vorschlag"
        self._big_value(self.navigation_card, route)
        self._muted(self.navigation_card, selected)
        self._progress_line(self.navigation_card, theme.MAP_ROUTE)

    def _render_audio(self) -> None:
        clear(self.audio_card)
        self._domain_title(self.audio_card, "Audio", "Media")
        self._big_value(self.audio_card, self.state.audio_track)
        self._muted(self.audio_card, "Spielt" if self.state.audio_playing else "Pausiert")
        self._muted(self.audio_card, f"Lautstaerke {self.state.volume}%")

    def _render_messages(self) -> None:
        clear(self.message_card)
        self._domain_title(self.message_card, "Nachrichten", "Inbox")
        status = "Geoeffnet" if self.state.message_open else "Neue Nachricht" if self.state.message_available else "Keine neue Nachricht"
        self._big_value(self.message_card, status)
        self._muted(self.message_card, "Mia: Bin in 5 Minuten da.")

    def _render_ambient(self) -> None:
        clear(self.ambient_card)
        self._domain_title(self.ambient_card, "Ambiente", "Licht")
        self._big_value(self.ambient_card, self.state.ambient_color)
        self._muted(self.ambient_card, f"Helligkeit {self.state.ambient_brightness}%")
        color = theme.AMBIENT_WARM if self.state.ambient_color == "Warm" else theme.AMBIENT_BLUE
        self._progress_line(self.ambient_card, color)

    def _render_climate(self) -> None:
        clear(self.climate_card)
        self._domain_title(self.climate_card, "Klima", "Sitz")
        selected = "ausgewaehlt" if self.state.seat_heating_selected else "nicht ausgewaehlt"
        self._big_value(self.climate_card, f"Sitzheizung {self.state.seat_heating_level}")
        self._muted(self.climate_card, selected)

    def _render_overlay(self) -> None:
        if self.state.overlay_visible:
            self.overlay_card.config(bg=theme.SURFACE_ALT)
            render_overlay(
                self.overlay_card,
                self.state.overlay_title,
                self.state.overlay_body,
                self.state.clarification_text,
                self.fonts,
            )
        else:
            self.overlay_card.config(bg=theme.SURFACE)
            clear(self.overlay_card)
            tk.Label(self.overlay_card, text="Kein aktives Overlay", font=self.fonts.h2,
                     bg=theme.SURFACE, fg=theme.TEXT).pack(anchor="w")
            tk.Label(self.overlay_card, text="Aufgaben koennen links eingespielt werden.",
                     font=self.fonts.body, bg=theme.SURFACE, fg=theme.TEXT_DIM).pack(anchor="w", pady=(6, 0))

    def _render_log(self) -> None:
        clear(self.log_card)
        tk.Label(self.log_card, text="Event Log", font=self.fonts.h2,
                 bg=theme.SURFACE, fg=theme.TEXT).pack(anchor="w")
        for item in self.state.event_log[-8:]:
            tk.Label(self.log_card, text=item, font=self.fonts.mono,
                     bg=theme.SURFACE, fg=theme.TEXT_MUTED, anchor="w").pack(fill="x", pady=2)

    def _domain_title(self, parent: tk.Misc, title: str, subtitle: str) -> None:
        tk.Label(parent, text=title, font=self.fonts.h2, bg=theme.SURFACE, fg=theme.TEXT).pack(anchor="w")
        tk.Label(parent, text=subtitle, font=self.fonts.small, bg=theme.SURFACE, fg=theme.TEXT_DIM).pack(anchor="w")

    def _big_value(self, parent: tk.Misc, value: str) -> None:
        tk.Label(parent, text=value, font=self.fonts.h1, bg=theme.SURFACE,
                 fg=theme.TEXT, wraplength=260, justify="left").pack(anchor="w", pady=(14, 4))

    def _muted(self, parent: tk.Misc, value: str) -> None:
        tk.Label(parent, text=value, font=self.fonts.body, bg=theme.SURFACE,
                 fg=theme.TEXT_MUTED, wraplength=260, justify="left").pack(anchor="w", pady=1)

    def _progress_line(self, parent: tk.Misc, color: str) -> None:
        line = tk.Frame(parent, bg=color, height=5)
        line.pack(fill="x", pady=(16, 0))


def main() -> None:
    root = tk.Tk()
    root.geometry("1280x760")
    root.minsize(1100, 680)
    app = CarWidgetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
