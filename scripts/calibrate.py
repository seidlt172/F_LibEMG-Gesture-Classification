"""
calibrate.py
============
Guided calibration with GUI for new sessions or new users.

What it does:
    - Shows a clean onboarding UI guiding the user through each gesture
    - Records N_CALIB_REPS per gesture with countdown + hold timer
    - Shows use-case examples for each gesture while recording
    - Combines calibration data with existing training data
    - Retrains the classifier and saves the updated model

Usage:
    Terminal 1: python scripts/mindrove_streamer.py   (keep running)
    Terminal 2: python scripts/calibrate.py

Press the window close button to abort.
"""

import csv
import os
import pickle
import socket
import time
import glob
import shutil
import random
import threading
import tkinter as tk
from tkinter import font as tkfont
import numpy as np

try:
    import pygame
    pygame.mixer.init()
    _SOUND_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "sounds", "click.mp3")
    _CLICK_SOUND = pygame.mixer.Sound(_SOUND_PATH) if os.path.exists(_SOUND_PATH) else None
except Exception:
    _CLICK_SOUND = None

def play_tick():
    """Play click sound cross-platform via pygame."""
    try:
        if _CLICK_SOUND:
            _CLICK_SOUND.play()
    except Exception:
        pass

from libemg.feature_extractor import FeatureExtractor
from libemg.emg_predictor import EMGClassifier
from libemg.utils import get_windows

try:
    from scripts.gesture_config import GESTURE_DESCRIPTIONS
    from scripts.gesture_config import GESTURE_DISPLAY_NAMES as GESTURES
except ImportError:
    from gesture_config import GESTURE_DESCRIPTIONS
    from gesture_config import GESTURE_DISPLAY_NAMES as GESTURES

# ── Settings ──────────────────────────────────────────────────────────────────

GESTURE_ICONS = {
    0: "✋",
    1: "👍",
    2: "👋",
    3: "🔄",
    4: "☝️",
}

GESTURE_EXAMPLES = {
    0: [
        "Ruhezustand — keine Aktion wird ausgelöst",
        "System wartet auf deine nächste Geste",
        "Keine Eingabe — Hintergrundmodus aktiv",
    ],
    1: [
        "Eingehenden Anruf annehmen",
        "Navigationsziel bestätigen",
        "Musikwiedergabe starten",
    ],
    2: [
        "Zum nächsten Song wechseln",
        "Nächste Route in der Navigation",
        "Benachrichtigung wegwischen",
    ],
    3: [
        "Lautstärke regulieren",
        "Klimaanlage anpassen",
        "Beleuchtung dimmen oder heller stellen",
    ],
    4: [
        "Navigationskarte vergrößern",
        "Menüpunkt auswählen",
        "Details zu einem POI anzeigen",
    ],
}

N_CALIB_REPS   = 5
RECORD_SECS    = 3
REST_BETWEEN   = 5
COUNTDOWN_SECS = 3

WINDOW_SIZE    = 200
WINDOW_INC     = 100
FEATURE_GROUP  = 'HTD'
CLASSIFIER     = 'LDA'

N_CHANNELS     = 8
UDP_HOST       = "127.0.0.1"
UDP_PORT       = 12345
UDP_TIMEOUT    = 5.0

DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
CALIB_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "calibration")
MODEL_DIR  = os.path.join(os.path.dirname(__file__), "..", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "clf")

# ── Colors (light, clean) ─────────────────────────────────────────────────────

BG          = "#f5f5f7"
BG_CARD     = "#ffffff"
BG_TILE     = "#f0f0f2"
ACCENT      = "#1d6f42"
ACCENT_MED  = "#2d9e5f"
ACCENT_LIGHT= "#e8f5ee"
TEXT_PRI    = "#1a1a2e"
TEXT_SEC    = "#6b7280"
TEXT_DIM    = "#b0b8c1"
BORDER      = "#e5e7eb"
BORDER_ACT  = "#1d6f42"
DANGER      = "#ef4444"
WARNING     = "#f59e0b"
TILE_DONE   = "#e8f5ee"
TILE_DIMMED = "#f9f9fb"

# ── Calibration state ─────────────────────────────────────────────────────────

class CalibState:
    def __init__(self):
        self.lock               = threading.Lock()
        self.phase              = "ready"      # ready | countdown | recording | rest | gesture_done | training | done | error
        self.gesture_idx        = 0
        self.rep_idx            = 0
        self.timer_val          = 0.0
        self.completed_gestures = set()
        self.current_example    = ""
        self.error_msg          = ""
        self.training_progress  = ""
        self.battery            = None
        self.button_event       = threading.Event()
        self.example_idx        = 0   # current example index, drives slider

cal = CalibState()

# ── Battery listener ──────────────────────────────────────────────────────────

BATTERY_UDP_PORT = 12346

def battery_thread():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((UDP_HOST, BATTERY_UDP_PORT))
    except Exception:
        return
    sock.settimeout(2.0)
    while True:
        try:
            data, _ = sock.recvfrom(4096)
            msg = pickle.loads(data)
            if isinstance(msg, dict) and msg.get('type') == 'battery':
                with cal.lock:
                    cal.battery = float(msg['value'])
        except socket.timeout:
            continue
        except Exception:
            continue

# ── Data helpers ──────────────────────────────────────────────────────────────

def record_trial(sock, duration_secs):
    samples  = []
    deadline = time.time() + duration_secs
    sock.setblocking(False)
    while True:
        try:
            sock.recvfrom(4096)
        except BlockingIOError:
            break
    sock.setblocking(True)
    sock.settimeout(0.1)
    while time.time() < deadline:
        with cal.lock:
            cal.timer_val = max(deadline - time.time(), 0.0)
        try:
            data, _ = sock.recvfrom(4096)
            sample  = pickle.loads(data)
            if len(sample) == N_CHANNELS:
                samples.append(sample)
        except socket.timeout:
            continue
    return samples


def save_csv(samples, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([f"ch{i}" for i in range(N_CHANNELS)])
        writer.writerows(samples)


def load_all_data(data_dir):
    all_files = sorted(glob.glob(
        os.path.join(data_dir, '**', '*.csv'), recursive=True))
    data_list, classes_list = [], []
    for f in all_files:
        parts = f.replace('\\', '/').split('/')
        gf = [p for p in parts if p.startswith('gesture_')]
        if not gf:
            continue
        class_id = int(gf[0].replace('gesture_', ''))
        arr = np.loadtxt(f, delimiter=',', skiprows=1)
        if arr.ndim == 2 and arr.shape[0] > WINDOW_SIZE:
            data_list.append(arr)
            classes_list.append(class_id)
    return data_list, np.array(classes_list)


def make_windows_and_labels(data_list, classes_arr):
    all_windows, all_labels = [], []
    for i, arr in enumerate(data_list):
        wins = get_windows(arr, WINDOW_SIZE, WINDOW_INC)
        all_windows.append(wins)
        all_labels.extend([classes_arr[i]] * len(wins))
    windows = np.vstack(all_windows)
    labels  = np.array(all_labels)
    windows = windows - windows.mean(axis=2, keepdims=True)
    return windows, labels

# ── Worker thread ─────────────────────────────────────────────────────────────

def calibration_worker():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_HOST, UDP_PORT))
    sock.settimeout(UDP_TIMEOUT)

    # Wait for stream
    with cal.lock:
        cal.phase = "waiting"
    try:
        sock.recvfrom(4096)
    except socket.timeout:
        with cal.lock:
            cal.phase     = "error"
            cal.error_msg = "Kein Stream gefunden.\nIst mindrove_streamer.py gestartet?"
        sock.close()
        return

    sock.settimeout(0.5)

    # Wait for user to press Start
    with cal.lock:
        cal.phase = "ready"
    cal.button_event.clear()
    cal.button_event.wait()  # blocks until GUI sets the event

    if os.path.exists(CALIB_DIR):
        shutil.rmtree(CALIB_DIR)

    gesture_ids = list(GESTURES.keys())

    for g_idx, gesture_id in enumerate(gesture_ids):
        with cal.lock:
            cal.gesture_idx     = g_idx
            cal.rep_idx         = 0
            cal.current_example = random.choice(GESTURE_EXAMPLES[gesture_id])

        for rep in range(N_CALIB_REPS):
            with cal.lock:
                cal.rep_idx = rep

            # Countdown with reliable tick at each second
            with cal.lock:
                cal.phase     = "countdown"
                cal.timer_val = float(COUNTDOWN_SECS)
            start    = time.time()
            deadline = start + COUNTDOWN_SECS
            ticked   = set()  # which seconds we already ticked
            while time.time() < deadline:
                remaining = max(deadline - time.time(), 0.0)
                with cal.lock:
                    cal.timer_val = remaining
                # Fire tick at the START of each countdown second (3, 2, 1)
                sec = int(remaining) + 1
                if sec <= COUNTDOWN_SECS and sec not in ticked:
                    ticked.add(sec)
                    threading.Thread(target=play_tick, daemon=True).start()
                time.sleep(0.02)

            # Recording
            n_examples = len(GESTURE_EXAMPLES[gesture_id])
            with cal.lock:
                cal.phase       = "recording"
                cal.timer_val   = float(RECORD_SECS)
                cal.example_idx = (rep) % n_examples  # advance one per rep

            samples = record_trial(sock, RECORD_SECS)
            if samples:
                path = os.path.join(
                    CALIB_DIR, f"gesture_{gesture_id}", f"rep_{rep}.csv")
                save_csv(samples, path)

            # Short auto-rest between reps (not after last rep of gesture)
            if rep < N_CALIB_REPS - 1:
                with cal.lock:
                    cal.phase     = "rest"
                    cal.timer_val = float(REST_BETWEEN)
                deadline = time.time() + REST_BETWEEN
                while time.time() < deadline:
                    with cal.lock:
                        cal.timer_val = max(deadline - time.time(), 0.0)
                    time.sleep(0.05)

        # Mark gesture done, wait for button before next gesture
        with cal.lock:
            cal.completed_gestures.add(gesture_id)

        is_last_gesture = (g_idx == len(gesture_ids) - 1)
        if not is_last_gesture:
            with cal.lock:
                cal.phase = "gesture_done"
            cal.button_event.clear()
            cal.button_event.wait()  # wait for "Weiter" button

    sock.close()

    # Retrain
    with cal.lock:
        cal.phase             = "training"
        cal.training_progress = "Trainingsdaten laden..."

    train_data,  train_classes = load_all_data(DATA_DIR)
    calib_data,  calib_classes = load_all_data(CALIB_DIR)

    with cal.lock:
        cal.training_progress = "Features berechnen..."

    all_data    = train_data + calib_data
    all_classes = (np.concatenate([train_classes, calib_classes])
                   if len(train_data) > 0 else calib_classes)

    windows, labels = make_windows_and_labels(all_data, all_classes)

    with cal.lock:
        cal.training_progress = f"LDA trainieren ({len(windows)} Fenster)..."

    fe       = FeatureExtractor()
    features = fe.extract_feature_group(FEATURE_GROUP, windows)
    dataset  = {'training_features': features, 'training_labels': labels}
    clf      = EMGClassifier(CLASSIFIER)
    clf.fit(dataset)

    os.makedirs(MODEL_DIR, exist_ok=True)
    clf.save(MODEL_PATH)

    with cal.lock:
        cal.phase = "done"

# ── GUI ───────────────────────────────────────────────────────────────────────

# ── GUI ───────────────────────────────────────────────────────────────────────

class CalibGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EMG Kalibrierung")
        self.root.configure(bg=BG)
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w    = min(1200, screen_w - 40)
        win_h    = min(900,  screen_h - 80)   # leave room for macOS menubar+dock
        self.root.geometry(f"{win_w}x{win_h}")
        self.root.minsize(1000, win_h)
        self.root.resizable(True, True)

        self._pulse_val  = 0
        self._pulse_up   = True
        self._anim_phase = 0
        self._spinner    = ["◐", "◓", "◑", "◒"]
        self._btn_visible  = False
        self._dialog_shown = False

        self._build_fonts()
        self._build_ui()
        self._update()

    def _build_fonts(self):
        self.f_title   = tkfont.Font(family="Helvetica Neue", size=14, weight="bold")
        self.f_sub     = tkfont.Font(family="Helvetica Neue", size=10)
        self.f_tile    = tkfont.Font(family="Helvetica Neue", size=13, weight="bold")
        self.f_gesture = tkfont.Font(family="Helvetica Neue", size=30, weight="bold")
        self.f_anim    = tkfont.Font(family="Helvetica Neue", size=52)
        self.f_action  = tkfont.Font(family="Helvetica Neue", size=18, weight="bold")
        self.f_timer   = tkfont.Font(family="Helvetica Neue", size=52, weight="bold")
        self.f_example = tkfont.Font(family="Helvetica Neue", size=18, weight="bold")
        self.f_exlabel = tkfont.Font(family="Helvetica Neue", size=9)
        self.f_rep     = tkfont.Font(family="Helvetica Neue", size=10)
        self.f_btn     = tkfont.Font(family="Helvetica Neue", size=13, weight="bold")
        self.f_header  = tkfont.Font(family="Helvetica Neue", size=11, weight="bold")

    def _build_ui(self):
        pad = 20

        # Header
        header = tk.Frame(self.root, bg=BG, pady=14)
        header.pack(fill="x", padx=pad)
        tk.Label(header, text="EMG Kalibrierung",
                 font=self.f_title, bg=BG, fg=TEXT_PRI).pack(side="left")
        self.battery_lbl = tk.Label(header, text="🔋 —",
                                    font=self.f_header, bg=BG, fg=TEXT_SEC)
        self.battery_lbl.pack(side="left", padx=(20, 0))
        self.step_label = tk.Label(header, text="",
                                   font=self.f_sub, bg=BG, fg=TEXT_SEC)
        self.step_label.pack(side="right")

        # Progress bar
        prog_bg = tk.Frame(self.root, bg=BORDER, height=6)
        prog_bg.pack(fill="x", padx=pad)
        prog_bg.pack_propagate(False)
        self.prog_bar = tk.Frame(prog_bg, bg=ACCENT, height=6)
        self.prog_bar.place(x=0, y=0, relheight=1.0, relwidth=0.0)

        tk.Frame(self.root, bg=BG, height=14).pack()

        # Gesture tiles
        tiles_row = tk.Frame(self.root, bg=BG)
        tiles_row.pack(fill="x", padx=pad)
        self.tiles = {}
        for gid, gname in GESTURES.items():
            tile = tk.Frame(tiles_row, bg=TILE_DIMMED,
                            highlightbackground=BORDER,
                            highlightthickness=1, padx=10, pady=8)
            tile.pack(side="left", expand=True, fill="x",
                      padx=(0, 8 if gid < 4 else 0))
            ilbl = tk.Label(tile, text=GESTURE_ICONS[gid],
                            font=self.f_sub, bg=TILE_DIMMED, fg=TEXT_DIM)
            ilbl.pack()
            nlbl = tk.Label(tile, text=gname, font=self.f_tile,
                            bg=TILE_DIMMED, fg=TEXT_DIM,
                            wraplength=130, justify="center")
            nlbl.pack(pady=(2, 4))
            dots_f = tk.Frame(tile, bg=TILE_DIMMED)
            dots_f.pack()
            dots = []
            for _ in range(N_CALIB_REPS):
                d = tk.Frame(dots_f, bg=BORDER, width=8, height=8)
                d.pack(side="left", padx=2)
                d.pack_propagate(False)
                dots.append(d)
            self.tiles[gid] = {"frame": tile, "icon": ilbl,
                                "name": nlbl, "dots": dots}

        tk.Frame(self.root, bg=BG, height=14).pack()
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=pad)
        tk.Frame(self.root, bg=BG, height=14).pack()

        # Main area — two equal columns via grid
        self._main = tk.Frame(self.root, bg=BG)
        self._main.pack(fill="both", expand=True, padx=pad, pady=(0, pad))
        self._main.columnconfigure(0, weight=2, uniform="col")
        self._main.columnconfigure(1, weight=3, uniform="col")
        self._main.rowconfigure(0, weight=1)
        main = self._main

        # Left card
        left = tk.Frame(main, bg=BG_CARD,
                        highlightbackground=BORDER,
                        highlightthickness=1, padx=24, pady=18)
        left.grid(row=0, column=0, sticky="nsew")

        self.phase_lbl = tk.Label(left, text="",
                                  font=self.f_exlabel, bg=BG_CARD,
                                  fg=TEXT_SEC, anchor="w")
        self.phase_lbl.pack(fill="x")

        tk.Frame(left, bg=BG_CARD, height=6).pack()

        # 1:1 animation placeholder — square canvas
        self.anim_canvas = tk.Canvas(left, bg=BG_TILE,
                                     highlightbackground=BORDER,
                                     highlightthickness=1,
                                     width=160, height=160)
        self.anim_canvas.pack(pady=(0, 4))
        self._anim_canvas_text = self.anim_canvas.create_text(
            80, 80, text="[ Gesten-Animation\n      1 : 1 ]",
            font=self.f_sub, fill=TEXT_DIM, justify="center")
        self.anim_icon_id = self.anim_canvas.create_text(
            80, 80, text="", font=self.f_anim, fill=ACCENT)
        # Keep canvas square on resize
        left.bind("<Configure>", self._on_left_resize)

        self.gname_lbl = tk.Label(left, text="—",
                                  font=self.f_gesture, bg=BG_CARD,
                                  fg=TEXT_PRI, anchor="center")
        self.gname_lbl.pack(fill="x")

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=12)

        # Action label + big timer, centered
        action_area = tk.Frame(left, bg=BG_CARD)
        action_area.pack()
        self.action_lbl = tk.Label(action_area, text="",
                                   font=self.f_action, bg=BG_CARD, fg=TEXT_SEC)
        self.action_lbl.pack()
        self.tval_lbl = tk.Label(action_area, text="",
                                 font=self.f_timer, bg=BG_CARD, fg=TEXT_PRI)
        self.tval_lbl.pack(pady=(2, 0))

        self.rep_lbl = tk.Label(left, text="",
                                font=self.f_rep, bg=BG_CARD, fg=TEXT_DIM)
        self.rep_lbl.pack(pady=(8, 0))

        # Start / Weiter button
        self.action_btn = tk.Label(left,
                                   text="▶  Kalibrierung starten",
                                   font=self.f_btn,
                                   bg=ACCENT, fg="#ffffff",
                                   pady=12, cursor="hand2",
                                   anchor="center")
        self.action_btn.bind("<Button-1>", lambda e: self._on_button())
        self.action_btn.bind("<Enter>",
                             lambda e: self.action_btn.config(bg=ACCENT_MED))
        self.action_btn.bind("<Leave>",
                             lambda e: self.action_btn.config(bg=ACCENT))

        # Right card
        right_outer = tk.Frame(main, bg=BG)
        right_outer.grid(row=0, column=1, sticky="nsew", padx=(16, 0))

        ex_card = tk.Frame(right_outer, bg=BG_CARD,
                           highlightbackground=BORDER,
                           highlightthickness=1, padx=20, pady=18)
        ex_card.pack(fill="both", expand=True)

        tk.Label(ex_card, text="ANWENDUNGSBEISPIEL",
                 font=self.f_exlabel, bg=BG_CARD,
                 fg=TEXT_SEC, anchor="w").pack(fill="x")
        tk.Frame(ex_card, bg=BORDER, height=1).pack(fill="x", pady=10)

        # 16:9 canvas — width fills card, height = width * 9/16
        self.preview_canvas = tk.Canvas(ex_card, bg=BG_TILE,
                                        highlightbackground=BORDER,
                                        highlightthickness=1,
                                        width=300, height=169)
        self.preview_canvas.pack(fill="x")
        self._preview_text_id = self.preview_canvas.create_text(
            150, 84, text="[ Anwendungs-Preview\n       16 : 9 ]",
            font=self.f_sub, fill=TEXT_DIM, justify="center")
        ex_card.bind("<Configure>", self._on_right_resize)

        tk.Frame(ex_card, bg=BG_CARD, height=14).pack()

        self.example_lbl = tk.Label(ex_card, text="",
                                    font=self.f_example, bg=BG_CARD,
                                    fg=TEXT_PRI, wraplength=380,
                                    justify="left")
        self.example_lbl.pack(anchor="w", fill="x")

        tk.Frame(ex_card, bg=BG_CARD, height=12).pack()

        # Slider controls: ← dots →
        slider_row = tk.Frame(ex_card, bg=BG_CARD)
        slider_row.pack(fill="x")

        self._prev_btn = tk.Label(slider_row, text="←",
                                  font=tkfont.Font(family="Helvetica Neue", size=27),
                                  bg=BG_CARD, fg=TEXT_SEC, cursor="hand2")
        self._prev_btn.pack(side="left")
        self._prev_btn.bind("<Button-1>", lambda e: self._slider_prev())
        self._prev_btn.bind("<Enter>", lambda e: self._prev_btn.config(fg=ACCENT))
        self._prev_btn.bind("<Leave>", lambda e: self._prev_btn.config(fg=TEXT_SEC))

        self._dots_frame = tk.Frame(slider_row, bg=BG_CARD)
        self._dots_frame.pack(side="left", expand=True)

        self._next_btn = tk.Label(slider_row, text="→",
                                  font=tkfont.Font(family="Helvetica Neue", size=27),
                                  bg=BG_CARD, fg=TEXT_SEC, cursor="hand2")
        self._next_btn.pack(side="right")
        self._next_btn.bind("<Button-1>", lambda e: self._slider_next())
        self._next_btn.bind("<Enter>", lambda e: self._next_btn.config(fg=ACCENT))
        self._next_btn.bind("<Leave>", lambda e: self._next_btn.config(fg=TEXT_SEC))

        # Dot labels — rebuilt when gesture changes
        self._slider_dots = []
        self._slider_idx  = 0
        self._slider_gid  = None
        self._dots_frame  = self._dots_frame  # already set above
        self._rebuild_dots(0)  # start with gesture 0

    # ── Button ────────────────────────────────────────────────────────────────

    def _on_button(self):
        cal.button_event.set()
        self._hide_btn()

    def _show_btn(self, text):
        self.action_btn.config(text=text)
        if not self._btn_visible:
            self.action_btn.pack(fill="x", pady=(16, 0))
            self._btn_visible = True

    def _hide_btn(self):
        if self._btn_visible:
            self.action_btn.pack_forget()
            self._btn_visible = False

    def _show_keep_dialog(self):
        """Overlay dialog asking whether to keep calibration data."""
        overlay = tk.Frame(self._main, bg="#ffffffee")
        overlay.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)

        dialog = tk.Frame(overlay, bg=BG_CARD,
                          highlightbackground=BORDER,
                          highlightthickness=1,
                          padx=40, pady=36)
        dialog.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(dialog,
                 text="Kalibrierungsdaten behalten?",
                 font=tkfont.Font(family="Helvetica Neue", size=16, weight="bold"),
                 bg=BG_CARD, fg=TEXT_PRI).pack()

        tk.Frame(dialog, bg=BG_CARD, height=8).pack()

        tk.Label(dialog,
                 text="Wenn du die Daten behältst, werden sie bei der\n"
                      "nächsten Kalibrierung als zusätzliche Trainingsdaten\n"
                      "verwendet und nicht gelöscht.",
                 font=tkfont.Font(family="Helvetica Neue", size=12),
                 bg=BG_CARD, fg=TEXT_SEC, justify="center").pack()

        tk.Frame(dialog, bg=BG_CARD, height=24).pack()

        btn_row = tk.Frame(dialog, bg=BG_CARD)
        btn_row.pack()

        def keep():
            # Move calibration data into raw/ so it persists
            calib_path = os.path.abspath(CALIB_DIR)
            raw_path   = os.path.abspath(DATA_DIR)
            if os.path.exists(calib_path):
                for gfolder in os.listdir(calib_path):
                    src = os.path.join(calib_path, gfolder)
                    if not os.path.isdir(src):
                        continue
                    dst = os.path.join(raw_path, gfolder)
                    os.makedirs(dst, exist_ok=True)
                    # Find next free rep index in dst
                    existing = [f for f in os.listdir(dst)
                                if f.startswith("rep_") and f.endswith(".csv")]
                    next_idx = max(
                        [int(f.replace("rep_","").replace(".csv",""))
                         for f in existing], default=-1) + 1
                    for fname in sorted(os.listdir(src)):
                        if fname.endswith(".csv"):
                            old_path = os.path.join(src, fname)
                            new_name = f"rep_{next_idx}.csv"
                            shutil.copy2(old_path,
                                        os.path.join(dst, new_name))
                            next_idx += 1
            overlay.destroy()

        def discard():
            overlay.destroy()

        keep_btn = tk.Label(btn_row,
                            text="✓  Daten behalten",
                            font=tkfont.Font(family="Helvetica Neue",
                                             size=13, weight="bold"),
                            bg=ACCENT, fg="#ffffff",
                            padx=24, pady=12, cursor="hand2")
        keep_btn.pack(side="left", padx=(0, 12))
        keep_btn.bind("<Button-1>", lambda e: keep())
        keep_btn.bind("<Enter>",
                      lambda e: keep_btn.config(bg=ACCENT_MED))
        keep_btn.bind("<Leave>",
                      lambda e: keep_btn.config(bg=ACCENT))

        discard_btn = tk.Label(btn_row,
                               text="✗  Verwerfen",
                               font=tkfont.Font(family="Helvetica Neue",
                                                size=13, weight="bold"),
                               bg=BG_TILE, fg=TEXT_SEC,
                               padx=24, pady=12, cursor="hand2")
        discard_btn.pack(side="left")
        discard_btn.bind("<Button-1>", lambda e: discard())
        discard_btn.bind("<Enter>",
                         lambda e: discard_btn.config(bg=BORDER))
        discard_btn.bind("<Leave>",
                         lambda e: discard_btn.config(bg=BG_TILE))

    def _rebuild_dots(self, gesture_id):
        """Rebuild dot indicators when gesture changes."""
        for w in self._slider_dots:
            w.destroy()
        self._slider_dots = []
        n = len(GESTURE_EXAMPLES.get(gesture_id, []))
        for i in range(n):
            dot = tk.Label(self._dots_frame, text="●",
                           font=tkfont.Font(family="Helvetica Neue", size=15),
                           bg=BG_CARD,
                           fg=ACCENT if i == self._slider_idx else TEXT_DIM)
            dot.pack(side="left", padx=2)
            self._slider_dots.append(dot)

    def _update_dots(self):
        for i, dot in enumerate(self._slider_dots):
            dot.config(fg=ACCENT if i == self._slider_idx else TEXT_DIM)

    def _slider_prev(self):
        with cal.lock:
            gid = list(GESTURES.keys())[min(cal.gesture_idx, len(GESTURES)-1)]
        n = len(GESTURE_EXAMPLES.get(gid, []))
        self._slider_idx = (self._slider_idx - 1) % n
        self._show_current_example(gid)

    def _slider_next(self):
        with cal.lock:
            gid = list(GESTURES.keys())[min(cal.gesture_idx, len(GESTURES)-1)]
        n = len(GESTURE_EXAMPLES.get(gid, []))
        self._slider_idx = (self._slider_idx + 1) % n
        self._show_current_example(gid)

    def _show_current_example(self, gesture_id):
        examples = GESTURE_EXAMPLES.get(gesture_id, [""])
        self._slider_idx = self._slider_idx % len(examples)
        self.example_lbl.config(text=examples[self._slider_idx])
        self._update_dots()

    # ── Update loop ───────────────────────────────────────────────────────────

    def _update(self):
        with cal.lock:
            phase      = cal.phase
            g_idx      = cal.gesture_idx
            rep_idx    = cal.rep_idx
            timer_val  = cal.timer_val
            completed  = set(cal.completed_gestures)
            error_msg  = cal.error_msg
            t_prog     = cal.training_progress
            battery    = cal.battery
            ex_idx_cal = cal.example_idx

        gesture_id = list(GESTURES.keys())[min(g_idx, len(GESTURES) - 1)]
        n_gestures = len(GESTURES)

        # Battery
        if battery is not None:
            pct = int(battery)
            col = ACCENT if pct > 60 else (WARNING if pct > 25 else DANGER)
            self.battery_lbl.config(text=f"🔋 {pct}%", fg=col)

        # Progress
        total = n_gestures * N_CALIB_REPS
        done  = len(completed) * N_CALIB_REPS
        if phase not in ("training", "done", "error", "ready", "waiting"):
            done += rep_idx
        self.prog_bar.place(relwidth=min(done / total, 1.0))
        self.step_label.config(
            text=f"Geste {min(g_idx + 1, n_gestures)} von {n_gestures}"
            if phase not in ("ready", "waiting", "done", "training") else "")

        # Tiles
        for gid in GESTURES:
            t      = self.tiles[gid]
            active = (gid == gesture_id and
                      phase not in ("training", "done", "error",
                                    "ready", "waiting"))
            done_g = gid in completed
            if done_g:
                bg, fg, border = TILE_DONE, ACCENT, ACCENT_MED
            elif active:
                bg, fg, border = "#ffffff", TEXT_PRI, BORDER_ACT
            else:
                bg, fg, border = TILE_DIMMED, TEXT_DIM, BORDER
            t["frame"].config(bg=bg, highlightbackground=border)
            t["icon"].config(bg=bg, fg=fg)
            t["name"].config(bg=bg, fg=fg)
            for i, dot in enumerate(t["dots"]):
                if done_g or (active and i < rep_idx):
                    dot.config(bg=ACCENT)
                elif active and i == rep_idx and phase == "recording":
                    dot.config(bg=ACCENT_MED)
                else:
                    dot.config(bg=BORDER)

        # Reset slider when gesture changes
        if gesture_id != self._slider_gid:
            self._slider_gid = gesture_id
            self._slider_idx = 0
            self._rebuild_dots(gesture_id)
            self._show_current_example(gesture_id)
        elif phase == "recording" and ex_idx_cal != self._slider_idx:
            # Worker advanced the example — sync slider unless user just clicked
            self._slider_idx = ex_idx_cal
            self._show_current_example(gesture_id)

        # Phase content
        if phase == "waiting":
            self._set("VERBINDE...", TEXT_SEC, "Bitte warten", TEXT_DIM,
                      "", "", TEXT_DIM)
            self._anim_placeholder()
            self._hide_btn()

        elif phase == "ready":
            self._set("BEREIT", ACCENT, "Kalibrierung", TEXT_PRI,
                      "Platziere das Armband und drücke Start.", "", TEXT_SEC)
            self._anim_placeholder()
            self._show_btn("▶  Kalibrierung starten")

        elif phase == "countdown":
            self._set("GLEICH GEHT ES LOS", WARNING,
                      GESTURES[gesture_id], TEXT_PRI,
                      "Vorbereiten...", f"{int(timer_val)+1}s", WARNING)
            self.rep_lbl.config(
                text=f"Wiederholung {rep_idx + 1} von {N_CALIB_REPS}")
            self._tick_anim(gesture_id)
            self._hide_btn()

        elif phase == "recording":
            self._set("▶  AUFNAHME LÄUFT", ACCENT,
                      GESTURES[gesture_id], TEXT_PRI,
                      "Geste halten!", f"{int(timer_val)+1}s", ACCENT)
            self.rep_lbl.config(
                text=f"Wiederholung {rep_idx + 1} von {N_CALIB_REPS}")
            self._tick_anim(gesture_id)
            self._hide_btn()

        elif phase == "rest":
            self._set("PAUSE", TEXT_SEC,
                      GESTURES[gesture_id], TEXT_DIM,
                      "Kurze Pause", f"{int(timer_val)+1}s", TEXT_SEC)
            self._anim_placeholder()
            self._hide_btn()

        elif phase == "gesture_done":
            next_idx  = g_idx + 1
            next_name = GESTURES.get(next_idx, "")
            self._set("✓  GESTE ABGESCHLOSSEN", ACCENT,
                      GESTURES[gesture_id], ACCENT,
                      f"Weiter zu: {next_name}", "", ACCENT)
            self._anim_placeholder()
            self._show_btn(f"▶  Weiter zu {next_name}")

        elif phase == "training":
            self._set("MODELL WIRD TRAINIERT", ACCENT,
                      "Fast fertig!", TEXT_PRI, t_prog, "", TEXT_SEC)
            self.prog_bar.place(relwidth=0.95)
            spin = self._spinner[self._anim_phase % 4]
            self.anim_canvas.itemconfig(self._anim_canvas_text, text="")
            self.anim_canvas.itemconfig(self.anim_icon_id, text=spin,
                font=tkfont.Font(family="Helvetica Neue", size=52))
            self._anim_phase += 1
            self._hide_btn()

        elif phase == "done":
            self._set("✓  KALIBRIERUNG ABGESCHLOSSEN", ACCENT,
                      "Fertig!", ACCENT,
                      "Modell gespeichert.", "", ACCENT)
            self.prog_bar.place(relwidth=1.0)
            self.anim_canvas.itemconfig(self._anim_canvas_text, text="")
            self.anim_canvas.itemconfig(self.anim_icon_id, text="✓",
                font=tkfont.Font(family="Helvetica Neue", size=52))
            for gid in GESTURES:
                t = self.tiles[gid]
                t["frame"].config(bg=TILE_DONE,
                                  highlightbackground=ACCENT_MED)
                t["icon"].config(bg=TILE_DONE, fg=ACCENT)
                t["name"].config(bg=TILE_DONE, fg=ACCENT)
                for dot in t["dots"]:
                    dot.config(bg=ACCENT)
            self._hide_btn()
            if not self._dialog_shown:
                self._dialog_shown = True
                self._show_keep_dialog()

        elif phase == "error":
            self._set("⚠  FEHLER", DANGER,
                      "Verbindungsfehler", DANGER, error_msg, "", DANGER)
            self._hide_btn()

        self.root.after(100, self._update)

    def _on_left_resize(self, event):
        """Keep animation canvas square."""
        w = event.width - 48  # subtract padx
        if w > 0:
            self.anim_canvas.config(width=w, height=w)
            cx, cy = w // 2, w // 2
            self.anim_canvas.coords(self._anim_canvas_text, cx, cy)
            self.anim_canvas.coords(self.anim_icon_id, cx, cy)

    def _on_right_resize(self, event):
        """Keep preview canvas 16:9."""
        w = event.width - 40  # subtract padx
        if w > 0:
            h = int(w * 9 / 16)
            self.preview_canvas.config(width=w, height=h)
            self.preview_canvas.coords(
                self._preview_text_id, w // 2, h // 2)

    def _set(self, phase_text, phase_color,
             gname, gname_color, action_text, tval, action_color):
        self.phase_lbl.config(text=phase_text, fg=phase_color)
        self.gname_lbl.config(text=gname, fg=gname_color)
        self.action_lbl.config(text=action_text, fg=action_color)
        self.tval_lbl.config(text=tval, fg=action_color)

    def _anim_placeholder(self):
        self.anim_canvas.itemconfig(self.anim_icon_id, text="")
        self.anim_canvas.itemconfig(
            self._anim_canvas_text,
            text="[ Gesten-Animation\n      1 : 1 ]")

    def _tick_anim(self, gesture_id):
        if self._pulse_up:
            self._pulse_val += 3
            if self._pulse_val >= 14:
                self._pulse_up = False
        else:
            self._pulse_val -= 3
            if self._pulse_val <= 0:
                self._pulse_up = True
        size = 52 + self._pulse_val
        self.anim_canvas.itemconfig(self._anim_canvas_text, text="")
        self.anim_canvas.itemconfig(
            self.anim_icon_id,
            text=GESTURE_ICONS.get(gesture_id, ""),
            font=tkfont.Font(family="Helvetica Neue", size=size))


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    app  = CalibGUI(root)
    t    = threading.Thread(target=calibration_worker, daemon=True)
    t.start()
    tb   = threading.Thread(target=battery_thread, daemon=True)
    tb.start()
    root.mainloop()


if __name__ == "__main__":
    main()
