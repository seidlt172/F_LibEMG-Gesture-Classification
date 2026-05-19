import threading
import tkinter as tk
from tkinter import font as tkfont

import scripts.gesture_gui as backend
from Middleware.audio_recorder import AudioRecorder
from Middleware.network_client import send_gesture_to_middleware


# UI appearance constants
BG = "#0f0f13"
BG_CARD = "#1a1a22"
BG_BUTTON = "#00a870"
BG_BUTTON_HOVER = "#00e5a0"
TEXT_PRI = "#f0f0f0"
TEXT_SEC = "#c0c0c0"
DANGER = "#ff4466"
BORDER = "#2a2a38"


class GestureGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EMG & Sprach-Pipeline")
        self.root.configure(bg=BG)

        self.last_logged_gesture = "NONE"
        self.is_recording = False
        self.recorder = AudioRecorder(output_filename="temp_voice.wav")

        self._build_fonts()
        self._build_ui()
        self._start_update_loop()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_fonts(self):
        self.font_title = tkfont.Font(family="Arial", size=16, weight="bold")
        self.font_label = tkfont.Font(family="Arial", size=12)
        self.font_button = tkfont.Font(family="Arial", size=12, weight="bold")
        self.font_status = tkfont.Font(family="Arial", size=11)

    def _build_ui(self):
        pad = 14
        header = tk.Frame(self.root, bg=BG, pady=pad)
        header.pack(fill="x")

        tk.Label(header, text="EMG + Sprachaufnahme", font=self.font_title,
                 bg=BG, fg=TEXT_PRI).pack(side="left")

        self.api_status_label = tk.Label(header, text="", font=self.font_status,
                                         bg=BG, fg=TEXT_SEC)
        self.api_status_label.pack(side="right")

        content = tk.Frame(self.root, bg=BG)
        content.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

        left = tk.Frame(content, bg=BG)
        left.pack(side="left", fill="both", expand=True)

        self.gesture_frame = self._build_card(left, "Aktuelle erkannte EMG-Geste")
        self.current_gesture_value = tk.Label(self.gesture_frame, text="NONE",
                                             font=self.font_button, bg=BG_CARD,
                                             fg=TEXT_PRI, pady=8)
        self.current_gesture_value.pack(fill="x")

        self.log_button = tk.Button(left, text="Geste einloggen",
                                    font=self.font_button, bg=BG_BUTTON,
                                    fg=BG, activebackground=BG_BUTTON_HOVER,
                                    activeforeground=BG, relief="flat",
                                    command=self._on_log_gesture)
        self.log_button.pack(fill="x", pady=(12, 6))

        self.logged_gesture_frame = self._build_card(left, "Zuletzt eingeloggt")
        self.logged_gesture_value = tk.Label(self.logged_gesture_frame, text=self.last_logged_gesture,
                                             font=self.font_button, bg=BG_CARD,
                                             fg=TEXT_PRI, pady=8)
        self.logged_gesture_value.pack(fill="x")

        middle = tk.Frame(content, bg=BG)
        middle.pack(side="left", fill="both", expand=True, padx=(12, 12))

        self.record_frame = self._build_card(middle, "Audioaufnahme")
        self.recording_state_label = tk.Label(self.record_frame, text="Stopped",
                                              font=self.font_label, bg=BG_CARD,
                                              fg=TEXT_SEC, pady=8)
        self.recording_state_label.pack(fill="x")

        self.record_button = tk.Button(self.record_frame, text="Sprachaufnahme starten",
                                       font=self.font_button, bg=BG_BUTTON,
                                       fg=BG, activebackground=BG_BUTTON_HOVER,
                                       activeforeground=BG, relief="flat",
                                       command=self._on_toggle_recording)
        self.record_button.pack(fill="x", pady=(8, 0))

        self.api_button = tk.Button(middle, text="An API abschicken",
                                    font=self.font_button, bg=BG_BUTTON,
                                    fg=BG, activebackground=BG_BUTTON_HOVER,
                                    activeforeground=BG, relief="flat",
                                    command=self._on_send_to_api)
        self.api_button.pack(fill="x", pady=(18, 0))

        self.last_action_label = tk.Label(middle, text="Bereit.", font=self.font_status,
                                          bg=BG, fg=TEXT_SEC, pady=8)
        self.last_action_label.pack(fill="x", pady=(10, 0))

        right = tk.Frame(content, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self.help_frame = self._build_card(right, "Hinweise")
        tk.Label(self.help_frame, text="1) EMG-Geste einloggen\n"
                                      "2) Sprachaufnahme starten/stoppen\n"
                                      "3) An API abschicken",
                 font=self.font_label, bg=BG_CARD, fg=TEXT_SEC, justify="left").pack(fill="x")

    def _build_card(self, parent, title):
        frame = tk.Frame(parent, bg=BG_CARD, bd=1, relief="solid",
                         highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="x", pady=(0, 8))
        tk.Label(frame, text=title, font=self.font_label,
                 bg=BG_CARD, fg=TEXT_SEC, anchor="w").pack(fill="x", padx=10, pady=(8, 0))
        return frame

    def _start_update_loop(self):
        self._update_current_gesture()

    def _update_current_gesture(self):
        gesture_name = self._get_current_emg_gesture()
        self.current_gesture_value.config(text=gesture_name)
        self.root.after(500, self._update_current_gesture)

    def _get_current_emg_gesture(self):
        label, confidence = backend.get_majority_vote()
        if label is None:
            return "NONE"
        return backend.GESTURE_NAMES.get(label, f"class_{label}")

    def _on_log_gesture(self):
        gesture_name = self._get_current_emg_gesture()
        if gesture_name == "NONE":
            self.last_action_label.config(text="Keine EMG-Geste verfügbar.", fg=DANGER)
            return

        self.last_logged_gesture = gesture_name
        self.logged_gesture_value.config(text=self.last_logged_gesture)
        self.last_action_label.config(text=f"Geste eingeloggt: {gesture_name}", fg=TEXT_PRI)

    def _on_toggle_recording(self):
        if not self.is_recording:
            try:
                self.recorder.start_recording()
                self.is_recording = True
                self.record_button.config(text="Sprachaufnahme stoppen")
                self.recording_state_label.config(text="Aufnahme läuft…", fg=BG_BUTTON_HOVER)
                self.last_action_label.config(text="Audioaufnahme gestartet.", fg=TEXT_PRI)
            except Exception as exc:
                self.last_action_label.config(text=f"Aufnahmefehler: {exc}", fg=DANGER)
        else:
            try:
                self.recorder.stop_recording()
                self.is_recording = False
                self.record_button.config(text="Sprachaufnahme starten")
                self.recording_state_label.config(text="Aufnahme beendet", fg=TEXT_SEC)
                self.last_action_label.config(text="Audio in temp_voice.wav gespeichert.", fg=TEXT_PRI)
            except Exception as exc:
                self.last_action_label.config(text=f"Stop-Fehler: {exc}", fg=DANGER)

    def _on_send_to_api(self):
        if self.is_recording:
            try:
                self.recorder.stop_recording()
                self.is_recording = False
                self.record_button.config(text="Sprachaufnahme starten")
                self.recording_state_label.config(text="Aufnahme beendet", fg=TEXT_SEC)
                self.last_action_label.config(text="Aufnahme zwischengespeichert.", fg=TEXT_PRI)
            except Exception as exc:
                self.last_action_label.config(text=f"Stop-Fehler: {exc}", fg=DANGER)
                return

        payload = self.last_logged_gesture or "NONE"
        self.api_status_label.config(text="Sende an Middleware…", fg=TEXT_SEC)
        success = send_gesture_to_middleware(payload)

        if success:
            self.api_status_label.config(text=f"Erfolg: {payload}", fg=BG_BUTTON_HOVER)
            self.last_action_label.config(text="Payload an Middleware gesendet.", fg=TEXT_PRI)
        else:
            self.api_status_label.config(text="Fehler: Middleware nicht erreichbar", fg=DANGER)
            self.last_action_label.config(text="Verbindung zur Middleware fehlgeschlagen.", fg=DANGER)

        self.root.after(5000, lambda: self.api_status_label.config(text=""))

    def _on_close(self):
        if self.is_recording:
            try:
                self.recorder.stop_recording()
            except Exception:
                pass
        try:
            self.recorder.close()
        except Exception:
            pass
        self.root.destroy()


def main():
    prediction_thread = threading.Thread(target=backend.prediction_thread, daemon=True)
    prediction_thread.start()

    battery_thread = threading.Thread(target=backend.battery_thread, daemon=True)
    battery_thread.start()

    root = tk.Tk()
    root.geometry("640x420")
    root.minsize(640, 420)
    app = GestureGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
