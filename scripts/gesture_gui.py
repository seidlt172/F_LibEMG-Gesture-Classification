"""
gesture_gui.py
==============
Real-time EMG gesture prediction GUI.

What it does:
    - Connects to mindrove_streamer.py via UDP (port 12345)
    - Runs continuous predictions in the background
    - Every 2 seconds: shows the most stable gesture (majority vote)
    - "Einloggen" button to confirm the predicted gesture
    - Operator/Wizard buttons for manual fallback during pilot trials
    - Log list showing structured gesture and trial events with timestamp
    - Logged data accessible via get_log() for later interface integration

Usage:
    Terminal 1: python scripts/mindrove_streamer.py
    Terminal 2: python gesture_gui.py

Press the window close button to stop.
"""

import os
import sys
import pickle
import socket
import collections
import json
import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import font as tkfont
from datetime import datetime
import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from Middleware.audio_recorder import AudioRecorder
from Middleware.input_events import build_intent_inputs
from Middleware.input_events import create_gesture_event
from Middleware.input_events import create_voice_event
from Middleware.intent_manager import OllamaIntentClient
from Middleware.intent_manager import OllamaIntentError
from Middleware.speech_transcriber import SpeechTranscriber
from Middleware.widget_bridge import WidgetBridgeClient
from Middleware.widget_bridge import build_scenario_start_payload
from Middleware.widget_bridge import build_trial_completed_payload
from Middleware.widget_bridge import build_widget_payload
from Middleware.widget_bridge import decision_for_step
from Middleware.widget_bridge import decision_from_intent_result
from libemg.feature_extractor import FeatureExtractor
from scripts.gesture_config import GESTURE_DISPLAY_NAMES as GESTURE_NAMES
from scripts.gesture_config import MANUAL_GESTURE_IDS
from scripts.study_config import CONDITION_ORDERS
from scripts.study_config import build_intent_context
from scripts.study_config import infer_multimodal_usage_pattern
from scripts.study_config import make_trial_id
from scripts.study_config import now_iso
from scripts.study_flow import scenario_from_label
from scripts.study_flow import scenario_labels
from scripts.study_flow import scenario_prompt

# ── Settings ──────────────────────────────────────────────────────────────────

GESTURE_ICONS = {
    0: "✋",
    1: "👍",
    2: "👋",
    3: "🔄",
    4: "☝️",
}

# Operator/Wizard buttons. Rest is excluded because it is a neutral state.
MANUAL_BUTTONS = {
    gid: (GESTURE_ICONS[gid], GESTURE_NAMES[gid])
    for gid in MANUAL_GESTURE_IDS
}

WINDOW_SIZE             = 200
FEATURE_GROUP           = 'HTD'
N_CHANNELS              = 8
PREDICT_EVERY_N_SAMPLES = 50    # ~10 predictions/sec at 500 Hz
UPDATE_INTERVAL_MS      = 500   # UI update every 0.5 seconds
VOTE_WINDOW_SECS        = 1.0   # collect predictions for this long, pick majority

UDP_HOST   = '127.0.0.1'
UDP_PORT   = 12345
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'clf')
INTENT_CONTEXT = (
    "Automotive cockpit research prototype. Possible domains are incoming calls, "
    "navigation routes, media playback, ambient light, seat heating, volume, "
    "and received messages."
)

# ── Colors ────────────────────────────────────────────────────────────────────

BG          = "#111318"
BG_CARD     = "#191d24"
BG_CARD2    = "#242a33"
ACCENT      = "#31c7b2"
ACCENT_DIM  = "#239886"
TEXT_PRI    = "#f4f7fb"
TEXT_SEC    = "#a7b0bf"
TEXT_DIM    = "#677083"
DANGER      = "#ef5f75"
BORDER      = "#2a303a"

# ── Shared state ──────────────────────────────────────────────────────────────

class PredictionState:
    def __init__(self):
        self.lock              = threading.Lock()
        self.recent_preds      = collections.deque()  # (timestamp, label, confidence)
        self.current_display   = None   # majority-voted label shown in UI
        self.current_confidence = 0.0
        self.streamer_ok       = False
        self.log               = []     # structured operator/study events
        self.trial_log         = []     # completed pilot trial summaries
        self.live_feed         = []     # raw predictions, pruned to last 10s
        self.battery           = None   # float 0-100 or None

state = PredictionState()

# ── Battery listener thread ───────────────────────────────────────────────────

BATTERY_UDP_PORT = 12346

def battery_thread():
    """Listens on UDP 12346 for battery packets from mindrove_streamer.py."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_HOST, BATTERY_UDP_PORT))
    sock.settimeout(2.0)
    while True:
        try:
            data, _ = sock.recvfrom(4096)
            msg = pickle.loads(data)
            if isinstance(msg, dict) and msg.get('type') == 'battery':
                with state.lock:
                    state.battery = float(msg['value'])
        except socket.timeout:
            continue
        except Exception:
            continue

# ── Prediction thread ─────────────────────────────────────────────────────────

def prediction_thread():
    """Runs in background: receives UDP, predicts, stores in state.recent_preds."""
    try:
        import libemg
        from libemg.emg_predictor import EMGClassifier
        with open(MODEL_PATH, 'rb') as f:
            clf = pickle.load(f)
        fe = FeatureExtractor()
    except Exception as e:
        print(f"[ERROR] Could not load model: {e}")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_HOST, UDP_PORT))
    sock.settimeout(1.0)

    buffer = collections.deque(maxlen=WINDOW_SIZE)
    samples_since_pred = 0

    while True:
        try:
            data, _ = sock.recvfrom(4096)
            sample = pickle.loads(data)
            buffer.append(sample)
            samples_since_pred += 1
            with state.lock:
                state.streamer_ok = True
        except socket.timeout:
            with state.lock:
                state.streamer_ok = False
            continue

        if samples_since_pred < PREDICT_EVERY_N_SAMPLES:
            continue
        if len(buffer) < WINDOW_SIZE:
            continue

        samples_since_pred = 0

        window_arr = np.array(buffer, dtype=float).T[np.newaxis, :, :]
        window_arr = window_arr - window_arr.mean(axis=2, keepdims=True)

        features   = fe.extract_feature_group(FEATURE_GROUP, window_arr)
        feat_vec   = np.hstack(list(features.values()))

        pred       = clf.model.predict(feat_vec)
        label      = int(pred[0])

        # Confidence via predict_proba if available
        confidence = 0.0
        if hasattr(clf.model, 'predict_proba'):
            proba      = clf.model.predict_proba(feat_vec)
            confidence = float(proba.max())

        with state.lock:
            now = time.time()
            state.recent_preds.append((now, label, confidence))
            state.live_feed.append((now, label, confidence))
            # Prune live_feed to last 10 seconds
            cutoff_feed = now - 10.0
            state.live_feed = [(t, l, c) for (t, l, c) in state.live_feed if t >= cutoff_feed]
            # Keep only last VOTE_WINDOW_SECS seconds in recent_preds
            cutoff = now - VOTE_WINDOW_SECS
            while state.recent_preds and state.recent_preds[0][0] < cutoff:
                state.recent_preds.popleft()


def get_majority_vote():
    """From recent predictions, return (majority_label, avg_confidence)."""
    with state.lock:
        preds = list(state.recent_preds)

    if not preds:
        return None, 0.0

    counts = collections.Counter(p[1] for p in preds)
    majority_label = counts.most_common(1)[0][0]

    # Average confidence of the winning label
    winning = [p[2] for p in preds if p[1] == majority_label]
    avg_conf = sum(winning) / len(winning) if winning else 0.0

    return majority_label, avg_conf


# ── Log access (for later interface integration) ──────────────────────────────

def get_log():
    """Returns structured operator/study events — call this from your interface."""
    with state.lock:
        return list(state.log)


# ── GUI ───────────────────────────────────────────────────────────────────────

class GestureGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pilot Operator Console")
        self.root.configure(bg=BG)

        self.last_logged_gesture = "NONE"
        self.last_logged_gesture_source = "none"
        self.last_logged_gesture_confidence = None
        self.last_voice_event = None
        self.last_gesture_event = None
        self.last_widget_payload = None
        self.last_recognition_outcome = "none"
        self.last_wizard_intervention = False
        self.last_intent_result = None
        self.is_recording = False
        self.recording_state = "idle"
        self.recording_start_time = 0.0
        self._recording_token = 0
        self._ui_queue = queue.Queue()
        self.trial_counter = 0
        self.current_trial = None
        self.current_trial_events = []
        self.participant_id_var = tk.StringVar(value="P001")
        self.condition_order_var = tk.StringVar(value=CONDITION_ORDERS[0])
        self.scenario_choice_var = tk.StringVar(value=scenario_labels()[0])
        self.condition_display_var = tk.StringVar(value="")
        self.category_display_var = tk.StringVar(value="")
        self.scenario_id_var = tk.StringVar(value="")
        self.scenario_prompt_var = tk.StringVar(value="")
        self.notes_var = tk.StringVar(value="")
        self.scenario_choice_var.trace_add("write", lambda *_: self._update_scenario_from_selection())
        # Use absolute path for audio file
        audio_file_path = os.path.join(ROOT_DIR, "temp_voice.wav")
        self.recorder = AudioRecorder(output_filename=audio_file_path)
        self.transcriber = SpeechTranscriber(model_name="base")
        self.intent_client = OllamaIntentClient.from_env()
        self.widget_bridge = WidgetBridgeClient()
        self.transcribed_text = ""
        self.intent_in_progress = False
        self._update_scenario_from_selection()

        self._build_fonts()
        self._build_ui()
        self._start_update_loop()
        self._process_ui_queue()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_fonts(self):
        family = "Helvetica"
        mono = "Menlo"
        self.font_title    = tkfont.Font(family=family, size=17, weight="bold")
        self.font_gesture  = tkfont.Font(family=family, size=25, weight="bold")
        self.font_icon     = tkfont.Font(family=family, size=28)
        self.font_conf     = tkfont.Font(family=family, size=11)
        self.font_btn      = tkfont.Font(family=family, size=12, weight="bold")
        self.font_btn_sm   = tkfont.Font(family=family, size=11, weight="bold")
        self.font_log      = tkfont.Font(family=mono, size=11)
        self.font_feed     = tkfont.Font(family=mono, size=10)
        self.font_status   = tkfont.Font(family=family, size=10)
        self.font_header   = tkfont.Font(family=family, size=12, weight="bold")

    def _build_ui(self):
        root = self.root
        pad = 18
        root.configure(bg=BG)

        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", padx=pad, pady=(16, 10))

        title_group = tk.Frame(header, bg=BG)
        title_group.pack(side="left")
        tk.Label(
            title_group,
            text="Pilot Operator Console",
            font=self.font_title,
            bg=BG,
            fg=TEXT_PRI,
        ).pack(anchor="w")
        tk.Label(
            title_group,
            text="EMG + Voice in-car interaction study",
            font=self.font_status,
            bg=BG,
            fg=TEXT_SEC,
        ).pack(anchor="w", pady=(2, 0))

        status_group = tk.Frame(header, bg=BG)
        status_group.pack(side="right")
        self.status_dot = tk.Label(
            status_group,
            text="NO STREAM",
            font=self.font_header,
            bg=BG,
            fg=DANGER,
        )
        self.status_dot.pack(side="right")
        self.battery_label = tk.Label(
            status_group,
            text="Battery —",
            font=self.font_header,
            bg=BG,
            fg=TEXT_DIM,
        )
        self.battery_label.pack(side="right", padx=(0, 24))

        study_card = tk.Frame(root, bg=BG_CARD, padx=16, pady=14)
        study_card.pack(fill="x", padx=pad, pady=(0, 14))
        self._add_border(study_card)

        study_header = tk.Frame(study_card, bg=BG_CARD)
        study_header.pack(fill="x", pady=(0, 10))
        tk.Label(
            study_header,
            text="Study Setup",
            font=self.font_header,
            bg=BG_CARD,
            fg=TEXT_PRI,
        ).pack(side="left")
        self.trial_status_label = tk.Label(
            study_header,
            text="Kein aktiver Trial",
            font=self.font_status,
            bg=BG_CARD,
            fg=TEXT_DIM,
        )
        self.trial_status_label.pack(side="right")

        setup_row = tk.Frame(study_card, bg=BG_CARD)
        setup_row.pack(fill="x")
        self._build_labeled_entry(setup_row, "Participant", self.participant_id_var, width=9)
        self._build_labeled_option(setup_row, "Order", self.condition_order_var, CONDITION_ORDERS, width=5)
        self.scenario_menu = self._build_labeled_option(
            setup_row,
            "Scenario",
            self.scenario_choice_var,
            scenario_labels(),
            width=48,
        )
        self._build_labeled_entry(setup_row, "Notes", self.notes_var, width=24)

        scenario_row = tk.Frame(study_card, bg=BG_CARD)
        scenario_row.pack(fill="x", pady=(10, 0))
        tk.Label(
            scenario_row,
            textvariable=self.scenario_id_var,
            font=self.font_header,
            bg=BG_CARD2,
            fg=ACCENT,
            padx=10,
            pady=6,
        ).pack(side="left")
        tk.Label(
            scenario_row,
            textvariable=self.condition_display_var,
            font=self.font_status,
            bg=BG_CARD2,
            fg=TEXT_PRI,
            padx=10,
            pady=6,
        ).pack(side="left", padx=(8, 0))
        tk.Label(
            scenario_row,
            textvariable=self.category_display_var,
            font=self.font_status,
            bg=BG_CARD2,
            fg=TEXT_PRI,
            padx=10,
            pady=6,
        ).pack(side="left", padx=(8, 0))
        self.scenario_prompt_label = tk.Label(
            scenario_row,
            textvariable=self.scenario_prompt_var,
            font=self.font_status,
            bg=BG_CARD,
            fg=TEXT_SEC,
            wraplength=620,
            justify="left",
            anchor="w",
        )
        self.scenario_prompt_label.pack(side="left", fill="x", expand=True, padx=(12, 12))

        trial_buttons = tk.Frame(scenario_row, bg=BG_CARD)
        trial_buttons.pack(side="right")
        self.start_trial_button = self._make_button(
            trial_buttons,
            "Trial starten",
            self._start_trial,
            primary=True,
        )
        self.start_trial_button.pack(side="left", padx=(0, 6))
        self.finish_trial_button = self._make_button(
            trial_buttons,
            "Erfolgreich beenden",
            lambda: self._finish_trial(True),
        )
        self.finish_trial_button.pack(side="left", padx=6)
        self.abort_trial_button = self._make_button(
            trial_buttons,
            "Abbrechen",
            lambda: self._finish_trial(False),
            danger=True,
        )
        self.abort_trial_button.pack(side="left", padx=(6, 0))

        content = tk.Frame(root, bg=BG)
        content.pack(fill="both", expand=True, padx=pad, pady=(0, pad))
        content.grid_columnconfigure(0, weight=1, minsize=330)
        content.grid_columnconfigure(1, weight=1, minsize=330)
        content.grid_columnconfigure(2, weight=2, minsize=430)
        content.grid_rowconfigure(0, weight=1)

        input_col = tk.Frame(content, bg=BG)
        input_col.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        operator_col = tk.Frame(content, bg=BG)
        operator_col.grid(row=0, column=1, sticky="nsew", padx=12)
        log_col = tk.Frame(content, bg=BG)
        log_col.grid(row=0, column=2, sticky="nsew", padx=(12, 0))

        pred_card = self._make_card(input_col)
        pred_card.pack(fill="x")
        self._section_title(pred_card, "Participant Input", "Live EMG")

        self.icon_label = tk.Label(pred_card, text="—", font=self.font_icon, bg=BG_CARD, fg=TEXT_PRI)
        self.icon_label.pack(pady=(8, 0))

        self.gesture_label = tk.Label(
            pred_card,
            text="Warte auf Daten...",
            font=self.font_gesture,
            bg=BG_CARD,
            fg=TEXT_DIM,
            width=18,
            anchor="center",
        )
        self.gesture_label.pack(pady=(2, 10))

        conf_row = tk.Frame(pred_card, bg=BG_CARD)
        conf_row.pack(fill="x")
        tk.Label(conf_row, text="Confidence", font=self.font_status, bg=BG_CARD, fg=TEXT_DIM).pack(side="left")
        self.conf_label = tk.Label(conf_row, text="—", font=self.font_conf, bg=BG_CARD, fg=TEXT_SEC)
        self.conf_label.pack(side="right")

        self.conf_bar_bg = tk.Frame(pred_card, bg=BG_CARD2, height=8)
        self.conf_bar_bg.pack(fill="x", pady=(6, 6))
        self.conf_bar_bg.pack_propagate(False)
        self.conf_bar = tk.Frame(self.conf_bar_bg, bg=ACCENT_DIM, height=8, width=0)
        self.conf_bar.place(x=0, y=0, relheight=1.0)

        timer_row = tk.Frame(pred_card, bg=BG_CARD)
        timer_row.pack(fill="x", pady=(0, 10))
        tk.Label(timer_row, text="Vote window", font=self.font_status, bg=BG_CARD, fg=TEXT_DIM).pack(side="left")
        self.countdown_label = tk.Label(timer_row, text="2.00s", font=self.font_status, bg=BG_CARD, fg=TEXT_SEC)
        self.countdown_label.pack(side="right")
        self._countdown_start = time.time()
        self._update_countdown()

        self.log_btn = tk.Label(
            pred_card,
            text="Einloggen",
            font=self.font_btn,
            bg=ACCENT_DIM,
            fg=BG,
            pady=10,
            cursor="hand2",
            anchor="center",
        )
        self.log_btn.pack(fill="x", pady=(4, 8))
        self.log_btn.bind("<Button-1>", lambda e: self._log_predicted())
        self.log_btn.bind("<Enter>", lambda e: self.log_btn.config(bg=ACCENT))
        self.log_btn.bind("<Leave>", lambda e: self.log_btn.config(bg=ACCENT_DIM))
        self._log_btn_enabled = False

        self.last_gesture_label = tk.Label(
            pred_card,
            text=f"Letzte Geste: {self.last_logged_gesture}",
            font=self.font_status,
            bg=BG_CARD,
            fg=TEXT_SEC,
            anchor="w",
        )
        self.last_gesture_label.pack(fill="x")

        audio_card = self._make_card(input_col)
        audio_card.pack(fill="x", pady=(14, 0))
        self._section_title(audio_card, "Voice", "Recording")

        self.record_button = self._make_button(
            audio_card,
            "Sprachaufnahme starten",
            self._on_toggle_recording,
            primary=True,
        )
        self.record_button.pack(fill="x", pady=(10, 8))

        self.recording_status = tk.Label(audio_card, text="Aufnahme gestoppt",
                                         font=self.font_status, bg=BG_CARD, fg=TEXT_DIM)
        self.recording_status.pack(fill="x")

        self.transcription_label = tk.Label(
            audio_card,
            text="Transkript: —",
            font=self.font_status,
            bg=BG_CARD,
            fg=TEXT_DIM,
            wraplength=300,
            justify="left",
            anchor="w",
        )
        self.transcription_label.pack(fill="x", pady=(10, 0))

        wizard_card = self._make_card(operator_col)
        wizard_card.pack(fill="x")
        self._section_title(wizard_card, "Operator / Wizard", "Fallback controls")
        tk.Label(
            wizard_card,
            text="Nur durch die Durchführenden bedienen. Klicks werden als Wizard-Eingriff geloggt.",
            font=self.font_status,
            bg=BG_CARD,
            fg=TEXT_DIM,
            wraplength=300,
            justify="left",
        ).pack(fill="x", pady=(4, 10))

        btn_grid = tk.Frame(wizard_card, bg=BG_CARD)
        btn_grid.pack(fill="x")
        for idx, (gid, (icon, gname)) in enumerate(MANUAL_BUTTONS.items()):
            lbl = tk.Label(
                btn_grid,
                text=f"{icon}  {gname}",
                font=self.font_btn_sm,
                bg=BG_CARD2,
                fg=TEXT_PRI,
                pady=9,
                cursor="hand2",
                anchor="center",
            )
            lbl.grid(row=idx // 2, column=idx % 2, sticky="ew", padx=4, pady=4)
            lbl.bind("<Button-1>", lambda e, g=gid: self._log_manual(g))
            lbl.bind("<Enter>", lambda e, w=lbl: w.config(bg=ACCENT_DIM, fg=BG))
            lbl.bind("<Leave>", lambda e, w=lbl: w.config(bg=BG_CARD2, fg=TEXT_PRI))
        btn_grid.grid_columnconfigure(0, weight=1)
        btn_grid.grid_columnconfigure(1, weight=1)

        unknown_lbl = tk.Label(
            wizard_card,
            text="No recognition",
            font=self.font_btn_sm,
            bg="#3a2028",
            fg="#ffffff",
            pady=9,
            cursor="hand2",
            anchor="center",
        )
        unknown_lbl.pack(fill="x", pady=(10, 0))
        unknown_lbl.bind("<Button-1>", lambda e: self._log_no_recognition())
        unknown_lbl.bind("<Enter>", lambda e: unknown_lbl.config(bg=DANGER, fg="#ffffff"))
        unknown_lbl.bind("<Leave>", lambda e: unknown_lbl.config(bg="#3a2028", fg="#ffffff"))

        intent_card = self._make_card(operator_col)
        intent_card.pack(fill="x", pady=(14, 0))
        self._section_title(intent_card, "Intent", "Local Ollama")

        self.api_button = self._make_button(
            intent_card,
            "Intent auswerten",
            self._on_evaluate_intent,
            primary=True,
        )
        self.api_button.pack(fill="x", pady=(10, 8))

        self.action_status_label = tk.Label(
            intent_card,
            text="Bereit.",
            font=self.font_status,
            bg=BG_CARD,
            fg=TEXT_SEC,
            wraplength=300,
            justify="left",
            anchor="w",
        )
        self.action_status_label.pack(fill="x")

        self.intent_label = tk.Label(
            intent_card,
            text="Intent: —",
            font=self.font_status,
            bg=BG_CARD,
            fg=TEXT_DIM,
            wraplength=300,
            justify="left",
            anchor="w",
        )
        self.intent_label.pack(fill="x", pady=(10, 0))

        log_card = self._make_card(log_col)
        log_card.pack(fill="both", expand=True)
        log_header = tk.Frame(log_card, bg=BG_CARD)
        log_header.pack(fill="x", pady=(0, 10))
        log_title = tk.Frame(log_header, bg=BG_CARD)
        log_title.pack(side="left")
        tk.Label(log_title, text="Session Log", font=self.font_header,
                 bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(log_title, text="Events", font=self.font_status,
                 bg=BG_CARD, fg=TEXT_DIM).pack(anchor="w", pady=(2, 0))

        tk.Button(log_header, text="EXPORT JSONL",
                  font=self.font_status, bg=BG_CARD, fg=ACCENT,
                  activebackground=BG_CARD, activeforeground=TEXT_PRI,
                  relief="flat", bd=0, cursor="hand2",
                  command=self._export_trial_log).pack(side="right")
        tk.Button(log_header, text="LEEREN",
                  font=self.font_status, bg=BG_CARD, fg=TEXT_DIM,
                  activebackground=BG_CARD, activeforeground=DANGER,
                  relief="flat", bd=0, cursor="hand2",
                  command=self._clear_log).pack(side="right", padx=(0, 12))

        log_scroll_frame = tk.Frame(log_card, bg=BG_CARD)
        log_scroll_frame.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(log_scroll_frame, bg=BG_CARD2, troughcolor=BG_CARD, width=6)
        scrollbar.pack(side="right", fill="y")
        self.log_listbox = tk.Listbox(
            log_scroll_frame,
            font=self.font_log,
            bg=BG_CARD,
            fg=TEXT_PRI,
            selectbackground=ACCENT_DIM,
            selectforeground=BG,
            relief="flat",
            bd=0,
            highlightthickness=0,
            yscrollcommand=scrollbar.set,
            width=48,
            height=12,
        )
        self.log_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.log_listbox.yview)

        log_footer = tk.Frame(log_card, bg=BG_CARD)
        log_footer.pack(fill="x", pady=(8, 0))
        self.log_count = tk.Label(log_footer, text="0 Einträge",
                                  font=self.font_status, bg=BG_CARD, fg=TEXT_DIM)
        self.log_count.pack(side="left")

        feed_card = self._make_card(log_col)
        feed_card.pack(fill="both", expand=True, pady=(14, 0))
        feed_header = tk.Frame(feed_card, bg=BG_CARD)
        feed_header.pack(fill="x", pady=(0, 10))
        feed_title = tk.Frame(feed_header, bg=BG_CARD)
        feed_title.pack(side="left")
        tk.Label(feed_title, text="Live Feed", font=self.font_header,
                 bg=BG_CARD, fg=TEXT_PRI).pack(anchor="w")
        tk.Label(feed_title, text="Raw EMG", font=self.font_status,
                 bg=BG_CARD, fg=TEXT_DIM).pack(anchor="w", pady=(2, 0))
        self.feed_count = tk.Label(feed_header, text="~10 Hz",
                                   font=self.font_status, bg=BG_CARD, fg=TEXT_DIM)
        self.feed_count.pack(side="right")

        feed_scroll_frame = tk.Frame(feed_card, bg=BG_CARD)
        feed_scroll_frame.pack(fill="both", expand=True)
        feed_scrollbar = tk.Scrollbar(feed_scroll_frame, bg=BG_CARD2, troughcolor=BG_CARD, width=6)
        feed_scrollbar.pack(side="right", fill="y")
        self.feed_listbox = tk.Listbox(
            feed_scroll_frame,
            font=self.font_feed,
            bg=BG_CARD,
            fg=TEXT_SEC,
            selectbackground=ACCENT_DIM,
            selectforeground=BG,
            relief="flat",
            bd=0,
            highlightthickness=0,
            yscrollcommand=feed_scrollbar.set,
            width=48,
            height=8,
        )
        self.feed_listbox.pack(side="left", fill="both", expand=True)
        feed_scrollbar.config(command=self.feed_listbox.yview)

        self._last_feed_ts = 0.0

    def _process_ui_queue(self):
        """Apply UI updates that were requested by worker threads."""
        try:
            while True:
                callback, args, kwargs = self._ui_queue.get_nowait()
                try:
                    callback(*args, **kwargs)
                except Exception as exc:
                    logger.error(f"Queued UI update failed: {exc}", exc_info=True)
        except queue.Empty:
            pass

        self.root.after(50, self._process_ui_queue)

    def _post_ui(self, callback, *args, **kwargs):
        self._ui_queue.put((callback, args, kwargs))

    def _make_card(self, parent):
        card = tk.Frame(parent, bg=BG_CARD, padx=16, pady=14, relief="flat", bd=0)
        self._add_border(card)
        return card

    def _section_title(self, parent, title, subtitle=None):
        bg = parent.cget("bg")
        title_frame = tk.Frame(parent, bg=bg)
        title_frame.pack(fill="x", anchor="w")
        tk.Label(
            title_frame,
            text=title,
            font=self.font_header,
            bg=bg,
            fg=TEXT_PRI,
        ).pack(anchor="w")
        if subtitle:
            tk.Label(
                title_frame,
                text=subtitle,
                font=self.font_status,
                bg=bg,
                fg=TEXT_DIM,
            ).pack(anchor="w", pady=(2, 0))

    def _make_button(self, parent, text, command, *, primary=False, danger=False):
        bg = ACCENT_DIM if primary else BG_CARD2
        fg = BG if primary else TEXT_PRI
        active_bg = ACCENT if primary else BG_CARD
        if danger:
            bg = "#3a2028"
            fg = "#ffffff"
            active_bg = DANGER
        return tk.Button(
            parent,
            text=text,
            font=self.font_btn_sm,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            cursor="hand2",
            command=command,
        )

    def _build_labeled_entry(self, parent, label, variable, width):
        group = tk.Frame(parent, bg=BG_CARD)
        group.pack(side="left", padx=(0, 10))
        tk.Label(group, text=label,
                 font=self.font_status, bg=BG_CARD, fg=TEXT_DIM).pack(anchor="w")
        tk.Entry(
            group,
            textvariable=variable,
            width=width,
            font=self.font_status,
            bg=BG_CARD2,
            fg=TEXT_PRI,
            insertbackground=TEXT_PRI,
            relief="flat",
        ).pack(anchor="w", pady=(2, 0))

    def _build_labeled_option(self, parent, label, variable, values, width):
        group = tk.Frame(parent, bg=BG_CARD)
        group.pack(side="left", padx=(0, 10))
        tk.Label(group, text=label,
                 font=self.font_status, bg=BG_CARD, fg=TEXT_DIM).pack(anchor="w")
        menu = tk.OptionMenu(group, variable, *values)
        menu.config(
            width=width,
            font=self.font_status,
            bg=BG_CARD2,
            fg=TEXT_PRI,
            activebackground=BG_CARD2,
            activeforeground=ACCENT,
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        menu["menu"].config(bg=BG_CARD2, fg=TEXT_PRI, activebackground=ACCENT_DIM)
        menu.pack(anchor="w", pady=(2, 0))
        return menu

    def _update_scenario_from_selection(self):
        scenario = scenario_from_label(self.scenario_choice_var.get())
        self.scenario_id_var.set(scenario.scenario_id)
        self.condition_display_var.set(scenario.condition)
        self.category_display_var.set(scenario.category_name)
        self.scenario_prompt_var.set(scenario_prompt(scenario))

    def _current_study_context(self):
        scenario = scenario_from_label(self.scenario_choice_var.get())
        return {
            "participant_id": self.participant_id_var.get().strip() or "P000",
            "condition_order": self.condition_order_var.get(),
            "condition": scenario.condition,
            "category": scenario.category_name,
            "scenario_id": scenario.scenario_id,
            "study_ref": scenario.study_ref,
            "scenario_prompt": scenario_prompt(scenario),
            "notes": self.notes_var.get().strip(),
        }

    def _trial_study_context(self):
        if self.current_trial:
            return {
                key: self.current_trial[key]
                for key in (
                    "participant_id",
                    "condition_order",
                    "condition",
                    "category",
                    "scenario_id",
                    "study_ref",
                    "scenario_prompt",
                    "notes",
                    "trial_id",
                )
                if key in self.current_trial
            }
        return self._current_study_context()

    def _current_widget_scenario(self):
        context = self._trial_study_context()
        return scenario_from_label(context.get("study_ref") or context.get("scenario_id", ""))

    def _current_widget_step(self):
        scenario = self._current_widget_scenario()
        step_index = int((self.current_trial or {}).get("current_step_index", 0))
        step_index = max(0, min(step_index, len(scenario.flow_steps) - 1))
        return scenario.flow_steps[step_index], step_index, len(scenario.flow_steps)

    def _is_call_flow_1_1(self):
        context = self._trial_study_context()
        return context.get("study_ref") == "1.1" or context.get("scenario_id") == "STUDY-1.1"

    def _is_audio_flow_2_1(self):
        context = self._trial_study_context()
        return context.get("study_ref") == "2.1" or context.get("scenario_id") == "STUDY-2.1"

    def _set_trial_step_status(self):
        if not self.current_trial:
            return
        step, step_index, step_count = self._current_widget_step()
        self.trial_status_label.config(
            text=(
                f"Aktiv: {self.current_trial['trial_id']} | "
                f"Schritt {step_index + 1}/{step_count} | {step.task_id}"
            ),
            fg=ACCENT,
        )

    def _record_study_event(self, event_type, **fields):
        context = (
            {k: self.current_trial[k] for k in (
                "participant_id",
                "condition_order",
                "condition",
                "category",
                "scenario_id",
                "study_ref",
                "scenario_prompt",
                "notes",
            )}
            if self.current_trial else self._current_study_context()
        )
        event = {
            "event_type": event_type,
            "timestamp": now_iso(),
            **context,
            **fields,
        }
        if self.current_trial:
            event["trial_id"] = self.current_trial["trial_id"]
            self.current_trial_events.append(event)
        with state.lock:
            state.log.append(event)
        return event

    def _set_recording_state(
        self,
        state,
        *,
        button_text,
        button_enabled=True,
        status_text=None,
        status_color=None,
        action_text=None,
        action_color=None,
        transcription_text=None,
        transcription_color=None,
    ):
        self.recording_state = state
        self.is_recording = state in {"starting", "recording", "stopping"}

        if state == "recording":
            button_bg = DANGER
            button_fg = "#ffffff"
            active_bg = "#ff6b85"
        elif button_enabled:
            button_bg = ACCENT_DIM
            button_fg = BG
            active_bg = ACCENT
        else:
            button_bg = TEXT_DIM
            button_fg = BG_CARD
            active_bg = TEXT_DIM

        self.record_button.config(
            text=button_text,
            state=tk.NORMAL if button_enabled else tk.DISABLED,
            bg=button_bg,
            fg=button_fg,
            activebackground=active_bg,
            activeforeground=button_fg,
        )

        if status_text is not None:
            self.recording_status.config(text=status_text, fg=status_color or TEXT_SEC)
        if action_text is not None:
            self.action_status_label.config(text=action_text, fg=action_color or TEXT_SEC)
        if transcription_text is not None:
            self.transcription_label.config(
                text=transcription_text,
                fg=transcription_color or TEXT_SEC,
            )

    def _add_border(self, widget):
        widget.config(highlightbackground=BORDER, highlightthickness=1,
                      highlightcolor=ACCENT)

    def _start_update_loop(self):
        self._update_ui()
        self._update_feed()

    def _update_ui(self):
        """Called every UPDATE_INTERVAL_MS ms — updates prediction display."""
        self._countdown_start = time.time()  # reset countdown

        # Status dot
        with state.lock:
            ok   = state.streamer_ok
            batt = state.battery

        if ok:
            self.status_dot.config(text="● STREAM OK", fg=ACCENT)
        else:
            self.status_dot.config(text="● NO STREAM", fg=DANGER)

        # Battery
        if batt is not None:
            pct = int(batt)
            if pct > 60:
                color = ACCENT
            elif pct > 25:
                color = "#f0c040"
            else:
                color = DANGER
            self.battery_label.config(text=f"🔋 {pct}%", fg=color)
        else:
            self.battery_label.config(text="🔋 —", fg=TEXT_DIM)

        # Majority vote
        label, conf = get_majority_vote()

        if label is not None:
            name = GESTURE_NAMES.get(label, f"class_{label}")
            icon = GESTURE_ICONS.get(label, "?")
            self.gesture_label.config(text=name, fg=TEXT_PRI)
            self.icon_label.config(text=icon)
            self.conf_label.config(text=f"{conf*100:.0f}%")

            # Update confidence bar
            bar_width = int(self.conf_bar_bg.winfo_width() * conf)
            self.conf_bar.place(x=0, y=0, relheight=1.0, width=max(bar_width, 0))

            # Color bar by confidence
            if conf >= 0.80:
                self.conf_bar.config(bg=ACCENT)
            elif conf >= 0.60:
                self.conf_bar.config(bg="#f0c040")
            else:
                self.conf_bar.config(bg=DANGER)

            self.log_btn.config(bg=ACCENT_DIM)
            self._log_btn_enabled = True
            self._current_label = label
            self._current_confidence = conf
        else:
            self.gesture_label.config(text="Warte auf Daten...", fg=TEXT_DIM)
            self.icon_label.config(text="—")
            self.conf_label.config(text="—")
            self.log_btn.config(bg="#333333")
            self._log_btn_enabled = False
            self._current_label = None
            self._current_confidence = None

        self.root.after(UPDATE_INTERVAL_MS, self._update_ui)

    def _update_countdown(self):
        """Updates the countdown timer text every 50ms."""
        elapsed   = time.time() - self._countdown_start
        remaining = max((UPDATE_INTERVAL_MS / 1000.0) - elapsed, 0.0)
        self.countdown_label.config(text=f"{remaining:.2f}s", fg=TEXT_PRI)
        self.root.after(50, self._update_countdown)

    def _update_feed(self):
        """Called every 200ms — pushes new raw predictions into the live feed listbox."""
        with state.lock:
            feed = list(state.live_feed)

        # Only show entries newer than what we last displayed
        new_entries = [e for e in feed if e[0] > self._last_feed_ts]
        if new_entries:
            self._last_feed_ts = new_entries[-1][0]

        for (ts, label, conf) in new_entries:
            name = GESTURE_NAMES.get(label, f"class_{label}")
            icon = GESTURE_ICONS.get(label, "")
            conf_str = f"{conf*100:.0f}%" if conf > 0 else "  —"
            entry = f">> {icon}  {name:<20} {conf_str}"

            self.feed_listbox.insert(tk.END, entry)

            # Color by confidence
            idx = self.feed_listbox.size() - 1
            if conf >= 0.80:
                self.feed_listbox.itemconfig(idx, fg=ACCENT)
            elif conf >= 0.60:
                self.feed_listbox.itemconfig(idx, fg="#f0c040")
            else:
                self.feed_listbox.itemconfig(idx, fg=DANGER)

            # Keep listbox max 200 entries
            if self.feed_listbox.size() > 200:
                self.feed_listbox.delete(0, 1)

        if new_entries:
            self.feed_listbox.see(tk.END)

        self.root.after(200, self._update_feed)

    def _log_entry(self, label, source="EMG"):
        """Confirm a displayed gesture as a structured middleware event."""
        name = GESTURE_NAMES.get(label, f"class_{label}")
        icon = GESTURE_ICONS.get(label, "")
        now  = datetime.now()
        ts   = now.strftime("%H:%M:%S")
        normalized_source = "emg" if str(source).lower() == "emg" else source
        confidence = getattr(self, "_current_confidence", None) if normalized_source == "emg" else None
        gesture_event = create_gesture_event(
            name,
            source=normalized_source,
            gesture_id=label,
            confidence=confidence,
        )
        metadata = {
            "gesture_label": gesture_event["gesture_label"],
            "gesture_source": gesture_event["source"],
            "gesture_confidence": gesture_event["confidence"],
            "recognition_outcome": gesture_event["recognition_outcome"],
            "wizard_intervention": gesture_event["recognition_outcome"] == "wizard_intervention",
            "gesture_event": gesture_event,
        }

        self.last_logged_gesture = gesture_event["gesture_label"] or "NONE"
        self.last_logged_gesture_source = gesture_event["source"]
        self.last_logged_gesture_confidence = confidence
        self.last_gesture_event = gesture_event
        self.last_recognition_outcome = metadata["recognition_outcome"]
        self.last_wizard_intervention = metadata["wizard_intervention"]
        self.last_gesture_label.config(
            text=f"Letzte Geste: {self.last_logged_gesture} [{self.last_logged_gesture_source}]"
        )

        self._record_study_event(
            "gesture",
            **metadata,
        )

        entry = f"{ts}  {icon} {name}  [{self.last_logged_gesture_source}]"
        self._append_log_row(entry)

        if self.last_logged_gesture_source in {"manual", "wizard"}:
            self.action_status_label.config(
                text=f"Wizard-Geste gesetzt: {name} [{self.last_logged_gesture_source}]",
                fg="#f0c040",
            )

        # Flash the log button briefly
        self.log_btn.config(bg=ACCENT)
        self.root.after(300, lambda: self.log_btn.config(bg=ACCENT_DIM))

    def _log_predicted(self):
        if self._log_btn_enabled and hasattr(self, '_current_label') and self._current_label is not None:
            self._log_entry(self._current_label, source="emg")

    def _append_log_row(self, entry):
        self.log_listbox.insert(tk.END, entry)
        self.log_listbox.see(tk.END)

        idx = self.log_listbox.size() - 1
        bg  = BG_CARD2 if idx % 2 == 0 else BG_CARD
        self.log_listbox.itemconfig(idx, bg=bg)

        count = self.log_listbox.size()
        self.log_count.config(text=f"{count} Einträge")

    def _on_toggle_recording(self):
        if self.recording_state == "idle":
            self._start_recording()
        elif self.recording_state == "recording":
            self._stop_recording()
        elif self.recording_state == "starting":
            self.action_status_label.config(text="Mikrofon wird noch geöffnet…", fg=TEXT_PRI)
        elif self.recording_state in {"stopping", "transcribing"}:
            self.action_status_label.config(text="Bitte kurz warten, Aufnahme wird verarbeitet…", fg=TEXT_PRI)

    def _start_recording(self):
        logger.info("Starting recording...")
        self._recording_token += 1
        token = self._recording_token
        self.recording_start_time = time.time()
        self._set_recording_state(
            "starting",
            button_text="Mikrofon wird geöffnet…",
            button_enabled=False,
            status_text="Mikrofon wird geöffnet…",
            status_color=TEXT_PRI,
            action_text="Aufnahme startet. Bitte kurz warten.",
            action_color=TEXT_PRI,
            transcription_text="Transkript: —",
            transcription_color=TEXT_DIM,
        )

        def start_in_thread():
            try:
                logger.info("Opening audio stream...")
                self.recorder.start_recording()
                logger.info("Recording started successfully")
                self._post_ui(self._on_recording_started, token)
            except Exception as exc:
                logger.error(f"Recording start error: {exc}", exc_info=True)
                self._post_ui(self._on_recording_start_failed, token, str(exc))

        thread = threading.Thread(target=start_in_thread, daemon=True)
        thread.start()
        self.root.after(15000, lambda: self._check_recording_start_timeout(token, thread))

    def _on_recording_started(self, token):
        if token != self._recording_token or self.recording_state != "starting":
            logger.warning("Recording start finished after UI state changed; stopping stale stream")
            threading.Thread(target=self.recorder.stop_recording, daemon=True).start()
            return

        self._set_recording_state(
            "recording",
            button_text="Aufnahme stoppen",
            button_enabled=True,
            status_text="Aufnahme läuft",
            status_color=ACCENT,
            action_text="Aufnahme läuft. Erneut klicken zum Stoppen.",
            action_color=ACCENT,
        )

    def _on_recording_start_failed(self, token, message):
        if token != self._recording_token:
            return

        self._set_recording_state(
            "idle",
            button_text="Sprachaufnahme starten",
            button_enabled=True,
            status_text="Aufnahme fehlgeschlagen",
            status_color=DANGER,
            action_text=f"Aufnahmefehler: {message}",
            action_color=DANGER,
        )

    def _check_recording_start_timeout(self, token, thread):
        if token != self._recording_token or self.recording_state != "starting":
            return
        if not thread.is_alive():
            return

        logger.warning("Audio thread stuck for 15+ seconds, likely PyAudio issue")
        self._recording_token += 1
        self._set_recording_state(
            "idle",
            button_text="Sprachaufnahme starten",
            button_enabled=True,
            status_text="Audio-Timeout",
            status_color=DANGER,
            action_text="Audio-Init Fehler nach 15s. Prüfe Mikrofonberechtigung.",
            action_color=DANGER,
        )

    def _stop_recording(self):
        logger.info("Stopping recording...")
        if self.recording_state != "recording":
            self.action_status_label.config(text="Keine laufende Aufnahme zum Stoppen.", fg=TEXT_PRI)
            return

        token = self._recording_token
        self._set_recording_state(
            "stopping",
            button_text="Speichere Aufnahme…",
            button_enabled=False,
            status_text="Stoppe Aufnahme…",
            status_color=TEXT_PRI,
            action_text="Stoppe Aufnahme und speichere Audio…",
            action_color=TEXT_PRI,
        )

        def stop_in_thread():
            try:
                self.recorder.stop_recording()
                file_size = (
                    os.path.getsize(self.recorder.output_filename)
                    if os.path.exists(self.recorder.output_filename)
                    else 0
                )
                logger.info("Recording stopped and saved")
                self._post_ui(self._on_recording_stopped, token, file_size)
            except Exception as exc:
                logger.error(f"Recording stop error: {exc}", exc_info=True)
                self._post_ui(self._on_recording_stop_failed, token, str(exc))

        thread = threading.Thread(target=stop_in_thread, daemon=True)
        thread.start()

    def _on_recording_stopped(self, token, file_size):
        if token != self._recording_token:
            return

        if file_size < 100:
            self._set_recording_state(
                "idle",
                button_text="Sprachaufnahme starten",
                button_enabled=True,
                status_text="Aufnahme leer",
                status_color=DANGER,
                action_text="Keine Audioframes gespeichert. Prüfe Mikrofon und Berechtigung.",
                action_color=DANGER,
            )
            return

        self._set_recording_state(
            "transcribing",
            button_text="Transkribiere…",
            button_enabled=False,
            status_text="Aufnahme gespeichert",
            status_color=ACCENT,
            action_text="Audio gespeichert. Transkribiere…",
            action_color=ACCENT,
            transcription_text="Transkript: (wird transkribiert…)",
            transcription_color=TEXT_SEC,
        )
        self._transcribe_async(token)

    def _on_recording_stop_failed(self, token, message):
        if token != self._recording_token:
            return

        self._set_recording_state(
            "idle",
            button_text="Sprachaufnahme starten",
            button_enabled=True,
            status_text="Stop-Fehler",
            status_color=DANGER,
            action_text=f"Stop-Fehler: {message}",
            action_color=DANGER,
        )

    def _transcribe_async(self, token):
        """Transcribe audio file in background thread."""
        def transcribe_in_thread():
            try:
                logger.info("Starting speech-to-text transcription...")
                output_file = os.path.join(ROOT_DIR, "temp_voice.wav")
                logger.info(f"Transcribing file: {output_file}")
                text = self.transcriber.transcribe(output_file)
                self._post_ui(self._on_transcription_finished, token, text)
            except Exception as exc:
                logger.error(f"Transcription error: {exc}", exc_info=True)
                self._post_ui(self._on_transcription_failed, token, str(exc))

        thread = threading.Thread(target=transcribe_in_thread, daemon=True)
        thread.start()

    def _on_transcription_finished(self, token, text):
        if token != self._recording_token:
            return

        self.transcribed_text = text or ""
        if text:
            self.last_voice_event = create_voice_event(text, source="whisper")
            logger.info(f"Transcription complete: {text}")
            self._record_study_event(
                "voice_transcription",
                voice_transcript=text,
                recognition_outcome="correct",
                voice_event=self.last_voice_event,
            )
            self._set_recording_state(
                "idle",
                button_text="Sprachaufnahme starten",
                button_enabled=True,
                status_text="Aufnahme beendet",
                status_color=TEXT_SEC,
                action_text="Transkription erfolgreich.",
                action_color=ACCENT,
                transcription_text=f"Transkript: {text}",
                transcription_color=ACCENT,
            )
        else:
            self.last_voice_event = create_voice_event(
                "",
                source="whisper",
                recognition_outcome="no_recognition",
            )
            logger.warning("Transcription returned empty text")
            self._record_study_event(
                "voice_transcription",
                voice_transcript="",
                recognition_outcome="no recognition",
                voice_event=self.last_voice_event,
            )
            self._set_recording_state(
                "idle",
                button_text="Sprachaufnahme starten",
                button_enabled=True,
                status_text="Aufnahme beendet",
                status_color=TEXT_SEC,
                action_text="Transkription fehlgeschlagen.",
                action_color=DANGER,
                transcription_text="Transkript: (konnte nicht transkribieren)",
                transcription_color=DANGER,
            )

    def _on_transcription_failed(self, token, message):
        if token != self._recording_token:
            return

        self.last_voice_event = create_voice_event(
            "",
            source="whisper",
            recognition_outcome="no_recognition",
        )
        self._record_study_event(
            "voice_transcription",
            voice_transcript="",
            recognition_outcome="no recognition",
            voice_event=self.last_voice_event,
            error=message,
        )
        self._set_recording_state(
            "idle",
            button_text="Sprachaufnahme starten",
            button_enabled=True,
            status_text="Aufnahme beendet",
            status_color=TEXT_SEC,
            action_text=f"Transkriptionsfehler: {message}",
            action_color=DANGER,
            transcription_text=f"Transkript: Fehler - {message}",
            transcription_color=DANGER,
        )

    def _on_evaluate_intent(self):
        if self.recording_state == "recording":
            self.action_status_label.config(text="Beende zuerst die Aufnahme. Danach erneut auswerten.", fg=TEXT_PRI)
            self._stop_recording()
            return
        if self.recording_state in {"starting", "stopping", "transcribing"}:
            self.action_status_label.config(text="Bitte warten, Audio wird noch verarbeitet.", fg=TEXT_PRI)
            return
        if self.intent_in_progress:
            self.action_status_label.config(text="Intent-Auswertung läuft bereits.", fg=TEXT_PRI)
            return
        if not self.current_trial:
            self.action_status_label.config(
                text="Starte zuerst einen Trial, damit Widgets Szenario und Schritt kennen.",
                fg="#f0c040",
            )
            return
        if self.current_trial.get("flow_completed"):
            self.action_status_label.config(
                text="Dieser Trial ist abgeschlossen. Bitte speichern oder abbrechen.",
                fg="#f0c040",
            )
            return

        study_context = self._trial_study_context()
        transcript = (self.transcribed_text or "").strip()
        voice_event = self.last_voice_event
        if not voice_event or voice_event.get("transcript", "") != transcript:
            voice_event = create_voice_event(transcript, source="whisper")
            self.last_voice_event = voice_event

        gesture_event = self.last_gesture_event
        if not gesture_event:
            gesture_event = create_gesture_event(
                self.last_logged_gesture,
                source=self.last_logged_gesture_source or "none",
                confidence=self.last_logged_gesture_confidence,
            )
            self.last_gesture_event = gesture_event

        intent_inputs = build_intent_inputs(
            condition=study_context["condition"],
            voice_event=voice_event,
            gesture_event=gesture_event,
        )
        operator_gesture = (
            intent_inputs["gesture"]
            if intent_inputs["gesture_source"] in {"manual", "wizard"}
            else None
        )
        intent_context = build_intent_context(
            base_context=INTENT_CONTEXT,
            condition=study_context["condition"],
            category=study_context["category"],
            scenario_id=study_context["scenario_id"],
            scenario_prompt=study_context["scenario_prompt"],
            gesture_source=intent_inputs["gesture_source"],
            operator_gesture=operator_gesture,
        )
        self.intent_in_progress = True
        self.api_button.config(
            text="Werte Intent aus…",
            state=tk.DISABLED,
            bg=TEXT_DIM,
            fg=BG_CARD,
            activebackground=TEXT_DIM,
            activeforeground=BG_CARD,
        )
        self.intent_label.config(text="Intent: (wird ausgewertet…)", fg=TEXT_SEC)
        self.action_status_label.config(
            text=(
                f"Lokale Ollama-Auswertung: {study_context['scenario_id']} "
                f"({intent_inputs['gesture'] or 'keine Geste'}, "
                f"{intent_inputs['gesture_source']})"
            ),
            fg=TEXT_PRI,
        )

        def interpret_in_thread():
            try:
                result = self.intent_client.interpret(
                    transcript=intent_inputs["transcript"],
                    gesture=intent_inputs["gesture"],
                    context=intent_context,
                    gesture_source=intent_inputs["gesture_source"],
                )
                self._post_ui(self._on_intent_result, result, intent_inputs)
            except OllamaIntentError as exc:
                self._post_ui(self._on_intent_error, str(exc))
            except Exception as exc:
                logger.error(f"Intent parsing failed: {exc}", exc_info=True)
                self._post_ui(self._on_intent_error, f"Intent-Fehler: {exc}")

        threading.Thread(target=interpret_in_thread, daemon=True).start()

    def _on_intent_result(self, result, intent_inputs=None):
        self.intent_in_progress = False
        intent_inputs = intent_inputs or {}
        self.last_intent_result = result
        study_context = self._trial_study_context()
        current_step, current_step_index, step_count = self._current_widget_step()
        scenario = self._current_widget_scenario()
        raw_decision = decision_from_intent_result(result)
        step_decision = decision_for_step(current_step.task_id, raw_decision, result)

        if step_decision == "clarify":
            payload_step = current_step
            payload_step_index = current_step_index
            widget_payload = build_widget_payload(
                intent_result=result,
                study_context=study_context,
                voice_event=intent_inputs.get("voice_event"),
                gesture_event=intent_inputs.get("gesture_event"),
                step=payload_step,
                step_index=payload_step_index,
                step_count=step_count,
                trial_id=study_context.get("trial_id"),
                used_modalities=intent_inputs.get("used_modalities"),
                event_type="step_update",
                decision_override=step_decision,
            )
        elif self._is_call_flow_1_1() and current_step.task_id == "CALL-INCOMING" and step_decision in {"execute", "cancel"}:
            next_step_index = 1 if step_decision == "execute" else 2
            if self.current_trial:
                self.current_trial["current_step_index"] = next_step_index
            payload_step = scenario.flow_steps[next_step_index]
            payload_step_index = next_step_index
            widget_payload = build_widget_payload(
                intent_result=result,
                study_context=study_context,
                voice_event=intent_inputs.get("voice_event"),
                gesture_event=intent_inputs.get("gesture_event"),
                step=payload_step,
                step_index=payload_step_index,
                step_count=step_count,
                trial_id=study_context.get("trial_id"),
                used_modalities=intent_inputs.get("used_modalities"),
                event_type="step_update",
                decision_override=step_decision,
            )
        elif self._is_call_flow_1_1() and current_step.task_id == "CALL-ACTIVE" and step_decision in {"execute", "cancel"}:
            if self.current_trial:
                self.current_trial["current_step_index"] = 2
            payload_step = scenario.flow_steps[2]
            payload_step_index = 2
            widget_payload = build_widget_payload(
                intent_result=result,
                study_context=study_context,
                voice_event=intent_inputs.get("voice_event"),
                gesture_event=intent_inputs.get("gesture_event"),
                step=payload_step,
                step_index=payload_step_index,
                step_count=step_count,
                trial_id=study_context.get("trial_id"),
                used_modalities=intent_inputs.get("used_modalities"),
                event_type="step_update",
                decision_override=step_decision,
            )
        elif self._is_audio_flow_2_1() and current_step.task_id == "AUDIO-VOLUME-UP" and step_decision in {"execute", "cancel"}:
            if self.current_trial:
                self.current_trial["current_step_index"] = 1
            payload_step = current_step
            payload_step_index = current_step_index
            widget_payload = build_widget_payload(
                intent_result=result,
                study_context=study_context,
                voice_event=intent_inputs.get("voice_event"),
                gesture_event=intent_inputs.get("gesture_event"),
                step=payload_step,
                step_index=payload_step_index,
                step_count=step_count,
                trial_id=study_context.get("trial_id"),
                used_modalities=intent_inputs.get("used_modalities"),
                event_type="step_update",
                decision_override=step_decision,
            )
        elif current_step_index >= step_count - 1:
            if self.current_trial:
                self.current_trial["flow_completed"] = True
            payload_step = current_step
            payload_step_index = current_step_index
            widget_payload = build_trial_completed_payload(
                intent_result=result,
                study_context=study_context,
                voice_event=intent_inputs.get("voice_event"),
                gesture_event=intent_inputs.get("gesture_event"),
                step=payload_step,
                step_index=payload_step_index,
                step_count=step_count,
                trial_id=study_context.get("trial_id"),
                success=True,
                decision_override=step_decision,
                used_modalities=intent_inputs.get("used_modalities"),
            )
        else:
            next_step_index = current_step_index + 1
            if self.current_trial:
                self.current_trial["current_step_index"] = next_step_index
            scenario = self._current_widget_scenario()
            payload_step = scenario.flow_steps[next_step_index]
            payload_step_index = next_step_index
            widget_payload = build_widget_payload(
                intent_result=result,
                study_context=study_context,
                voice_event=intent_inputs.get("voice_event"),
                gesture_event=intent_inputs.get("gesture_event"),
                step=payload_step,
                step_index=payload_step_index,
                step_count=step_count,
                trial_id=study_context.get("trial_id"),
                used_modalities=intent_inputs.get("used_modalities"),
                event_type="step_update",
                decision_override=step_decision,
            )
        self.last_widget_payload = widget_payload
        self._record_study_event(
            "intent",
            voice_transcript=intent_inputs.get("transcript", ""),
            gesture_label=intent_inputs.get("gesture") or None,
            gesture_source=intent_inputs.get("gesture_source", "none"),
            ignored_voice=bool(intent_inputs.get("ignored_voice")),
            ignored_gesture=bool(intent_inputs.get("ignored_gesture")),
            intent=result.get("intent", "unknown"),
            action=result.get("action", "unknown"),
            target=result.get("target", "unknown"),
            value=result.get("value") or "",
            used_modalities=result.get("used_modalities", "none"),
            needs_clarification=bool(result.get("needs_clarification")),
            clarification=result.get("clarification") or "",
            llm_confidence_estimate=result.get("llm_confidence_estimate"),
            widget_decision=widget_payload["decision"],
            widget_event_type=widget_payload["event_type"],
            step_index=current_step_index,
            step_count=step_count,
            task_id=current_step.task_id,
            widget_payload=widget_payload,
            error=result.get("error") or "",
        )
        threading.Thread(
            target=self._send_widget_payload,
            args=(widget_payload,),
            daemon=True,
        ).start()
        if (
            self._is_call_flow_1_1()
            and widget_payload["event_type"] == "step_update"
            and widget_payload.get("task_id") == "CALL-ENDED"
        ):
            if self.current_trial:
                self.current_trial["flow_completed"] = True

            def finalize_call_trial():
                if not self.current_trial or self.current_trial.get("flow_completed") is not True:
                    return
                self._finish_trial(True, finalized_by_operator=False)

            threading.Timer(0.35, finalize_call_trial).start()
        if (
            self._is_audio_flow_2_1()
            and widget_payload["event_type"] == "step_update"
            and widget_payload.get("task_id") == "AUDIO-VOLUME-UP"
        ):
            if self.current_trial:
                self.current_trial["flow_completed"] = True

            def finalize_audio_trial():
                if not self.current_trial or self.current_trial.get("flow_completed") is not True:
                    return
                self._finish_trial(True, finalized_by_operator=False)

            threading.Timer(0.45, finalize_audio_trial).start()
        self.api_button.config(
            text="Intent auswerten",
            state=tk.NORMAL,
            bg=ACCENT_DIM,
            fg=BG,
            activebackground=ACCENT,
            activeforeground=BG,
        )
        self.intent_label.config(text=f"Intent: {self._format_intent_result(result)}", fg=ACCENT)
        if result.get("error"):
            self.action_status_label.config(text=result["error"], fg=DANGER)
        elif step_decision == "clarify":
            clarification = result.get("clarification") or "Bitte Eingabe wiederholen."
            self.action_status_label.config(text=f"Rückfrage: {clarification}", fg="#f0c040")
            self._set_trial_step_status()
        elif widget_payload["event_type"] == "trial_completed":
            self.action_status_label.config(
                text="Szenario abgeschlossen. Bitte Trial speichern oder abbrechen.",
                fg=ACCENT,
            )
            self.trial_status_label.config(
                text=f"Trial abgeschlossen: {study_context.get('trial_id', '')}",
                fg=ACCENT,
            )
        else:
            self.action_status_label.config(text="Intent erfolgreich ausgewertet. Nächster Schritt aktiv.", fg=ACCENT)
            self._set_trial_step_status()

    def _send_widget_payload(self, payload):
        result = self.widget_bridge.send(payload)
        self._post_ui(self._on_widget_bridge_result, result, payload)

    def _on_widget_bridge_result(self, result, payload):
        self._record_study_event(
            "widget_bridge",
            widget_event_type=payload.get("event_type", "decision"),
            widget_decision=payload.get("decision", ""),
            widget_bridge_sent=result.sent,
            widget_bridge_error=result.error,
            widget_bridge_status=result.response_status,
        )
        if result.sent:
            label = payload.get("event_type") or payload.get("decision")
            self._append_log_row(
                f"{datetime.now().strftime('%H:%M:%S')}  WIDGET {label} sent"
            )
        else:
            logger.info("Widget bridge not connected: %s", result.error)

    def _on_intent_error(self, message):
        self.intent_in_progress = False
        self._record_study_event("intent_error", error=message)
        self.api_button.config(
            text="Intent auswerten",
            state=tk.NORMAL,
            bg=ACCENT_DIM,
            fg=BG,
            activebackground=ACCENT,
            activeforeground=BG,
        )
        self.intent_label.config(text="Intent: —", fg=TEXT_DIM)
        self.recording_status.config(text="Ollama nicht erreichbar", fg=DANGER)
        self.action_status_label.config(text=message, fg=DANGER)

    def _format_intent_result(self, result):
        intent = result.get("intent", "unknown")
        action = result.get("action", "unknown")
        target = result.get("target", "unknown")
        value = result.get("value") or "-"
        modalities = result.get("used_modalities", "-")
        confidence = result.get("llm_confidence_estimate", 0.0)
        return (
            f"{intent} | action={action}, target={target}, value={value}, "
            f"modalities={modalities}, llm_conf={confidence:.2f}"
        )

    def _start_trial(self):
        if self.current_trial:
            self.trial_status_label.config(text="Trial läuft bereits.", fg="#f0c040")
            return

        self.trial_counter += 1
        context = self._current_study_context()
        trial_id = make_trial_id(context["participant_id"], self.trial_counter)
        self.current_trial = {
            **context,
            "trial_id": trial_id,
            "start_timestamp": now_iso(),
            "_start_monotonic": time.monotonic(),
            "current_step_index": 0,
            "flow_completed": False,
        }
        self.current_trial_events = []
        self._reset_trial_inputs()
        self._record_study_event("trial_start")
        step, step_index, step_count = self._current_widget_step()
        start_context = {**context, "trial_id": trial_id}
        start_payload = build_scenario_start_payload(
            study_context=start_context,
            step=step,
            step_index=step_index,
            step_count=step_count,
            trial_id=trial_id,
        )
        self.last_widget_payload = start_payload
        threading.Thread(
            target=self._send_widget_payload,
            args=(start_payload,),
            daemon=True,
        ).start()
        self._set_trial_step_status()
        self.scenario_menu.config(state=tk.DISABLED)
        self._append_log_row(f"{datetime.now().strftime('%H:%M:%S')}  START {trial_id}")

    def _build_final_trial_widget_payload(self, success):
        study_context = self._trial_study_context()
        step, step_index, step_count = self._current_widget_step()
        prompt = "Trial erfolgreich beendet." if success else "Trial abgebrochen."
        decision = "execute" if success else "cancel"
        intent = {
            **(self.last_intent_result or {}),
            "intent": (self.last_intent_result or {}).get("intent", "trial_completed" if success else "trial_aborted"),
            "action": (self.last_intent_result or {}).get("action", "complete" if success else "abort"),
            "target": (self.last_intent_result or {}).get("target", step.domain),
            "used_modalities": (self.last_intent_result or {}).get("used_modalities", "none"),
        }
        payload = build_trial_completed_payload(
            intent_result=intent,
            study_context=study_context,
            voice_event=self.last_voice_event,
            gesture_event=self.last_gesture_event,
            step=step,
            step_index=step_index,
            step_count=step_count,
            trial_id=study_context.get("trial_id"),
            success=success,
            decision_override=decision,
            used_modalities=intent.get("used_modalities", "none"),
        )
        payload["prompt"] = prompt
        payload["overlay_title"] = "Trial beendet" if success else "Trial abgebrochen"
        payload["overlay_body"] = prompt
        payload["finalized_by_operator"] = True
        if success:
            payload["accepted_text"] = prompt
        else:
            payload["rejected_text"] = prompt
        return payload

    def _finish_trial(self, success):
        if not self.current_trial:
            self.trial_status_label.config(text="Kein aktiver Trial.", fg=TEXT_PRI)
            return

        final_widget_payload = self._build_final_trial_widget_payload(success)
        end_timestamp = now_iso()
        duration_ms = int((time.monotonic() - self.current_trial["_start_monotonic"]) * 1000)
        events = list(self.current_trial_events)
        intent = self.last_intent_result or {}
        gesture_label = (
            self.last_logged_gesture
            if self.last_logged_gesture not in {"", "NONE", "Unknown"}
            else None
        )
        wizard_intervention = any(e.get("wizard_intervention") for e in events)
        transcript = self.transcribed_text.strip()
        recognition_outcome = self._derive_trial_recognition_outcome(events, intent)
        clarification_cycles = sum(
            1 for e in events
            if e.get("event_type") == "intent" and e.get("needs_clarification")
        )
        recognition_failures = sum(
            1 for e in events
            if e.get("recognition_outcome") in {"no recognition", "no_recognition"}
        )
        wrong_recognitions = sum(
            1 for e in events
            if e.get("recognition_outcome") == "wrong"
        )

        trial_summary = {
            "participant_id": self.current_trial["participant_id"],
            "trial_id": self.current_trial["trial_id"],
            "condition": self.current_trial["condition"],
            "category": self.current_trial["category"],
            "scenario_id": self.current_trial["scenario_id"],
            "study_ref": self.current_trial["study_ref"],
            "scenario_prompt": self.current_trial["scenario_prompt"],
            "condition_order": self.current_trial["condition_order"],
            "start_timestamp": self.current_trial["start_timestamp"],
            "end_timestamp": end_timestamp,
            "task_completion_time_ms": duration_ms,
            "success": bool(success),
            "interaction_steps": len([e for e in events if e.get("event_type") != "trial_start"]),
            "repetitions": 0,
            "corrections": 0,
            "clarification_cycles": clarification_cycles,
            "recognition_failures": recognition_failures,
            "wrong_recognitions": wrong_recognitions,
            "recognition_outcome": recognition_outcome,
            "wizard_intervention": wizard_intervention,
            "voice_transcript": transcript,
            "gesture_label": gesture_label,
            "gesture_source": self.last_logged_gesture_source if gesture_label else "none",
            "gesture_confidence": self.last_logged_gesture_confidence,
            "intent": intent.get("intent", "unknown"),
            "action": intent.get("action", "unknown"),
            "target": intent.get("target", "unknown"),
            "value": intent.get("value") or "",
            "used_modalities": intent.get("used_modalities", "none"),
            "multimodal_usage_pattern": infer_multimodal_usage_pattern(
                self.current_trial["condition"],
                transcript,
                gesture_label or "",
            ),
            "notes": self.notes_var.get().strip(),
            "events": events,
        }

        with state.lock:
            state.trial_log.append(trial_summary)
            state.log.append({
                "event_type": "trial_end",
                "timestamp": end_timestamp,
                "trial_id": trial_summary["trial_id"],
                "success": trial_summary["success"],
                "task_completion_time_ms": duration_ms,
            })

        status = "OK" if success else "ABORT"
        self._append_log_row(
            f"{datetime.now().strftime('%H:%M:%S')}  {status} {trial_summary['trial_id']}  {duration_ms} ms"
        )
        self.trial_status_label.config(
            text=f"Trial gespeichert: {trial_summary['trial_id']}",
            fg=ACCENT if success else "#f0c040",
        )
        self.last_widget_payload = final_widget_payload
        threading.Thread(
            target=self._send_widget_payload,
            args=(final_widget_payload,),
            daemon=True,
        ).start()
        self.current_trial = None
        self.current_trial_events = []
        self.scenario_menu.config(state=tk.NORMAL)

    def _derive_trial_recognition_outcome(self, events, intent):
        outcomes = {e.get("recognition_outcome") for e in events if e.get("recognition_outcome")}
        if any(e.get("wizard_intervention") for e in events):
            return "Wizard intervention"
        if "wrong" in outcomes:
            return "wrong"
        if ("no recognition" in outcomes or "no_recognition" in outcomes) and len(outcomes) > 1:
            return "mixed"
        if "no recognition" in outcomes or "no_recognition" in outcomes:
            return "none"
        if intent.get("intent") and intent.get("intent") != "unknown":
            return "correct"
        if "correct" in outcomes:
            return "correct"
        return "none"

    def _reset_trial_inputs(self):
        self.transcribed_text = ""
        self.last_logged_gesture = "NONE"
        self.last_logged_gesture_source = "none"
        self.last_logged_gesture_confidence = None
        self.last_voice_event = None
        self.last_gesture_event = None
        self.last_widget_payload = None
        self.last_recognition_outcome = "none"
        self.last_wizard_intervention = False
        self.last_intent_result = None
        self.last_gesture_label.config(text="Letzte Geste: NONE")
        self.transcription_label.config(text="Transkript: —", fg=TEXT_DIM)
        self.intent_label.config(text="Intent: —", fg=TEXT_DIM)
        self.action_status_label.config(text="Trial bereit.", fg=TEXT_SEC)

    def _export_trial_log(self):
        with state.lock:
            trials = list(state.trial_log)

        if not trials:
            self.action_status_label.config(text="Noch keine abgeschlossenen Trials zum Exportieren.", fg=TEXT_PRI)
            return

        path = filedialog.asksaveasfilename(
            title="Trial-Log exportieren",
            defaultextension=".jsonl",
            filetypes=[("JSON Lines", "*.jsonl"), ("All files", "*.*")],
            initialfile=f"study_trials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl",
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as handle:
                for trial in trials:
                    handle.write(json.dumps(trial, ensure_ascii=False) + "\n")
        except OSError as exc:
            self.action_status_label.config(text=f"Export fehlgeschlagen: {exc}", fg=DANGER)
            return

        self.action_status_label.config(text=f"Trial-Log exportiert: {path}", fg=ACCENT)

    def _log_manual(self, gesture_id):
        self._log_entry(gesture_id, source="manual")

    def _log_no_recognition(self):
        gesture_event = create_gesture_event(
            None,
            source="manual",
            recognition_outcome="no_recognition",
        )
        self.last_logged_gesture = "NONE"
        self.last_logged_gesture_source = "none"
        self.last_logged_gesture_confidence = None
        self.last_gesture_event = gesture_event
        self.last_recognition_outcome = "no_recognition"
        self.last_wizard_intervention = True
        self.last_gesture_label.config(text="Letzte Geste: NONE [no recognition]")
        self._record_study_event(
            "gesture",
            gesture_label=None,
            gesture_source="manual",
            gesture_confidence=None,
            recognition_outcome="no_recognition",
            wizard_intervention=True,
            gesture_event=gesture_event,
        )
        self._append_log_row(f"{datetime.now().strftime('%H:%M:%S')}  ? No recognition  [manual]")
        self.action_status_label.config(
            text="No recognition als Wizard-/Operator-Ereignis geloggt.",
            fg="#f0c040",
        )

    def _clear_log(self):
        self.log_listbox.delete(0, tk.END)
        with state.lock:
            state.log.clear()
        if not self.current_trial:
            self.current_trial_events.clear()
        self.log_count.config(text="0 Einträge")
        self.action_status_label.config(
            text="Log-Anzeige geleert. Abgeschlossene Trials bleiben exportierbar.",
            fg=TEXT_SEC,
        )

    def _on_close(self):
        try:
            self.recorder.close()
        except Exception as exc:
            logger.error(f"Recorder cleanup failed: {exc}", exc_info=True)
        self.root.destroy()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    # Start prediction thread
    t = threading.Thread(target=prediction_thread, daemon=True)
    t.start()

    # Start battery thread
    tb = threading.Thread(target=battery_thread, daemon=True)
    tb.start()

    # Start GUI
    root = tk.Tk()
    root.geometry("1320x780")
    root.minsize(1180, 720)
    root.resizable(True, True)
    app  = GestureGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
