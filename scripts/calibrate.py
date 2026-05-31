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

try:
    import cv2
    from PIL import Image, ImageTk
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False

# ── Video paths ────────────────────────────────────────────────────────────────

_ANIM_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "animations")

VIDEO_PATHS = {
    0: os.path.join(_ANIM_DIR, "gesture_0_rest.mp4"),
    1: os.path.join(_ANIM_DIR, "gesture_1_daumen.mp4"),
    2: os.path.join(_ANIM_DIR, "gesture_2_swipe.mp4"),
    3: os.path.join(_ANIM_DIR, "gesture_3_drehen.mp4"),
    4: os.path.join(_ANIM_DIR, "gesture_4_zeigen.mp4"),
}

_WIDGET_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "widgets")

# Widget videos per gesture — (video_path, description)
WIDGET_SLIDES = {
    0: [
        (None, "Diese Geste hat keine direkte Funktion — sie signalisiert dem System, dass keine Eingabe gemacht wird."),
    ],
    1: [
        (os.path.join(_WIDGET_DIR, "gesture_1_daumen_1.mp4"), "Musikvorschlag annehmen"),
        (os.path.join(_WIDGET_DIR, "gesture_1_daumen_2.mp4"), "Zum Tagfahrmodus wechseln bestätigen"),
        (os.path.join(_WIDGET_DIR, "gesture_1_daumen_3.mp4"), "Eingehenden Anruf annehmen"),
        (os.path.join(_WIDGET_DIR, "gesture_1_daumen_4.mp4"), "Routenvorschlag annehmen"),
    ],
    2: [
        (os.path.join(_WIDGET_DIR, "gesture_2_swipe_1.mp4"), "Zum nächsten Song springen"),
        (os.path.join(_WIDGET_DIR, "gesture_2_swipe_2.mp4"), "Im Klimamenü navigieren"),
        (os.path.join(_WIDGET_DIR, "gesture_2_swipe_3.mp4"), "Zwischen Routenoptionen wechseln"),
        (os.path.join(_WIDGET_DIR, "gesture_2_swipe_4.mp4"), "Zwischen Farben bei der Ambientebeleuchtung wechseln"),
    ],
    3: [
        (os.path.join(_WIDGET_DIR, "gesture_3_drehen_1.mp4"), "Sitzheizung regulieren"),
        (os.path.join(_WIDGET_DIR, "gesture_3_drehen_2.mp4"), "Helligkeit der Ambientebeleuchtung regulieren"),
        (os.path.join(_WIDGET_DIR, "gesture_3_drehen_3.mp4"), "Lautstärke regulieren"),
    ],
    4: [
        (os.path.join(_WIDGET_DIR, "gesture_4_zeigen_1.mp4"), "Musik abspielen"),
        (os.path.join(_WIDGET_DIR, "gesture_4_zeigen_2.mp4"), "Tankstelle auswählen"),
    ],
}

# ── Video player helper ────────────────────────────────────────────────────────

class VideoPlayer:
    """
    Plays an MP4 once on a tkinter Canvas, then holds the last frame.
    Call start(gesture_id) to begin playback.
    Call stop() to release resources.
    """
    def __init__(self, canvas, placeholder_text_id, icon_id, root, fixed_ratio=None):
        self.canvas           = canvas
        self.placeholder_id   = placeholder_text_id
        self.icon_id          = icon_id
        self.root             = root
        self._cap             = None
        self._photo           = None   # must keep reference to avoid GC
        self._image_id        = None
        self._playing         = False
        self._fps             = 30
        self._frame_delay_ms  = 33
        self._token           = 0     # invalidates stale after() callbacks
        self._fixed_ratio     = fixed_ratio  # None=use canvas size, float=enforce ratio

    def start(self, gesture_id):
        """Start playing the video for gesture_id. Safe to call from any thread."""
        self.root.after(0, lambda: self._start_on_main(gesture_id))

    def start_path(self, path):
        """Start playing a video directly from a file path."""
        self.root.after(0, lambda: self._start_on_main_path(path))

    def _start_on_main(self, gesture_id):
        if not _CV2_AVAILABLE:
            return
        path = VIDEO_PATHS.get(gesture_id, "")
        if not path or not os.path.exists(path):
            return
        self._load_and_play(path)

    def _start_on_main_path(self, path):
        if not _CV2_AVAILABLE:
            return
        if not path or not os.path.exists(path):
            return
        self._load_and_play(path)

    def _load_and_play(self, path):
        # Stop any running playback
        self._playing = False
        self._token  += 1
        if self._cap:
            self._cap.release()

        self._cap = cv2.VideoCapture(path)
        if not self._cap.isOpened():
            return

        fps = self._cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 24
        self._frame_delay_ms = int(1000 / fps)

        # Hide placeholder and icon text
        self.canvas.itemconfig(self.placeholder_id, text="")
        self.canvas.itemconfig(self.icon_id, text="")

        self._playing = True
        token = self._token

        if self._fixed_ratio is not None:
            # Delay 100ms so canvas has correct width after pack
            self.root.after(100, lambda: self._apply_ratio_then_play(token))
        else:
            self._schedule_frame(token)

    def _apply_ratio_then_play(self, token):
        """Called after a short delay so winfo_width() is accurate."""
        if token != self._token or not self._playing:
            return
        self.canvas.update_idletasks()
        w = self.canvas.winfo_width()
        if w < 10:
            w = 600
        h = int(w / self._fixed_ratio)
        self.canvas.config(width=w, height=h)
        self.canvas.update_idletasks()
        self._schedule_frame(token)

    def _schedule_frame(self, token):
        if token != self._token or not self._playing:
            return
        self.root.after(self._frame_delay_ms,
                        lambda: self._show_frame(token))

    def _show_frame(self, token):
        if token != self._token:
            return

        if self._cap is None or not self._cap.isOpened():
            return

        ret, frame = self._cap.read()

        if not ret:
            # Video finished — hold last frame, stop scheduling
            self._playing = False
            return

        # Get canvas dimensions
        if self._fixed_ratio is not None:
            # ratio-enforced canvas: width dynamic, height = width / ratio
            w = self.canvas.winfo_width()
            if w < 10:
                w = 700
            h = int(w / self._fixed_ratio)
        else:
            # fixed square canvas: use configured width/height
            try:
                w = int(self.canvas.cget("width"))
                h = int(self.canvas.cget("height"))
            except Exception:
                w, h = 320, 320
            if w < 10:
                w = 320
            if h < 10:
                h = 320

        frame_rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (w, h),
                                   interpolation=cv2.INTER_LINEAR)

        img   = Image.fromarray(frame_resized)
        photo = ImageTk.PhotoImage(image=img)
        self._photo = photo  # keep reference

        if self._image_id is None:
            self._image_id = self.canvas.create_image(
                0, 0, anchor="nw", image=photo)
        else:
            self.canvas.itemconfig(self._image_id, image=photo)

        # Schedule next frame
        self._schedule_frame(token)

    def stop(self):
        self._playing = False
        self._token  += 1
        if self._cap:
            self._cap.release()
            self._cap = None

    def reset(self):
        """Stop and clear canvas back to placeholder."""
        self.stop()
        if self._image_id is not None:
            self.canvas.delete(self._image_id)
            self._image_id = None
        self._photo = None
        self.canvas.itemconfig(self.placeholder_id,
                               text="[ Gesten-Anim\n   1 : 1 ]")
        self.canvas.itemconfig(self.icon_id, text="")

from libemg.feature_extractor import FeatureExtractor
from libemg.emg_predictor import EMGClassifier
from libemg.utils import get_windows

# ── Settings ──────────────────────────────────────────────────────────────────

GESTURES = {
    0: "Rest",
    1: "Daumen hoch",
    2: "Swipe",
    3: "Handgelenk drehen",
    4: "Zeigen / Tippen",
}

GESTURE_ICONS = {
    0: "",
    1: "",
    2: "",
    3: "",
    4: "",
}

GESTURE_DESCRIPTIONS = {
    0: "Alle Finger locker eingeklappt,\nHand entspannt am Lenkrad",
    1: "Faust schließen,\nnur Daumen gestreckt nach oben",
    2: "Alle Finger zusammen,\nHandgelenk zügig seitlich schwenken",
    3: "Unterarm rotieren (Pro/Supination),\nFinger locker gestreckt",
    4: "Nur Zeigefinger gestreckt,\nrestliche Finger eingekrallt",
}

GESTURE_EXAMPLES = {
    0: [
        "Diese Geste hat keine direkte Funktion — sie signalisiert dem System, dass keine Eingabe gemacht wird.",
    ],
    1: [
        "Daumen hoch — Anwendungsfall 1",
        "Daumen hoch — Anwendungsfall 2",
        "Daumen hoch — Anwendungsfall 3",
        "Daumen hoch — Anwendungsfall 4",
    ],
    2: [
        "Zum nächsten Song springen",
        "Im Klimamenü navigieren",
        "Zwischen Routenoptionen wechseln",
        "Zwischen Farben bei der Ambientebeleuchtung wechseln",
    ],
    3: [
        "Handgelenk drehen — Anwendungsfall 1",
        "Handgelenk drehen — Anwendungsfall 2",
        "Handgelenk drehen — Anwendungsfall 3",
    ],
    4: [
        "Zeigen / Tippen — Anwendungsfall 1",
        "Zeigen / Tippen — Anwendungsfall 2",
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
        self.root.geometry("1000x800")
        self.root.minsize(1000, 800)
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
        self.f_title   = tkfont.Font(family="Helvetica Neue", size=12, weight="bold")
        self.f_sub     = tkfont.Font(family="Helvetica Neue", size=9)
        self.f_tile    = tkfont.Font(family="Helvetica Neue", size=10, weight="bold")
        self.f_gesture = tkfont.Font(family="Helvetica Neue", size=18, weight="bold")
        self.f_anim    = tkfont.Font(family="Helvetica Neue", size=30)
        self.f_action  = tkfont.Font(family="Helvetica Neue", size=12, weight="bold")
        self.f_timer   = tkfont.Font(family="Helvetica Neue", size=30, weight="bold")
        self.f_example = tkfont.Font(family="Helvetica Neue", size=12, weight="bold")
        self.f_exlabel = tkfont.Font(family="Helvetica Neue", size=9)
        self.f_rep     = tkfont.Font(family="Helvetica Neue", size=9)
        self.f_btn     = tkfont.Font(family="Helvetica Neue", size=11, weight="bold")
        self.f_header  = tkfont.Font(family="Helvetica Neue", size=10, weight="bold")

    def _build_ui(self):
        CONTENT_W = 840  # fixed content width, centered regardless of window size

        def centered(parent, **kwargs):
            """Returns a fixed-width centered frame inside parent."""
            outer = tk.Frame(parent, bg=BG)
            outer.pack(fill="x", **kwargs)
            inner = tk.Frame(outer, bg=BG, width=CONTENT_W)
            inner.pack(anchor="center")
            inner.pack_propagate(False)
            return inner

        # Header
        h_outer = tk.Frame(self.root, bg=BG, pady=8)
        h_outer.pack(fill="x")
        header = tk.Frame(h_outer, bg=BG, width=CONTENT_W)
        header.pack(anchor="center")
        tk.Label(header, text="EMG Kalibrierung",
                 font=self.f_title, bg=BG, fg=TEXT_PRI).pack(side="left")
        self.battery_lbl = tk.Label(header, text="🔋 —",
                                    font=self.f_header, bg=BG, fg=TEXT_SEC)
        self.battery_lbl.pack(side="left", padx=(20, 0))

        # Progress bar
        pb_outer = tk.Frame(self.root, bg=BG)
        pb_outer.pack(fill="x")
        pb_inner = tk.Frame(pb_outer, bg=BG, width=CONTENT_W)
        pb_inner.pack(anchor="center")
        prog_bg = tk.Frame(pb_inner, bg=BORDER, height=4)
        prog_bg.pack(fill="x")
        prog_bg.pack_propagate(False)
        self.prog_bar = tk.Frame(prog_bg, bg=ACCENT, height=4)
        self.prog_bar.place(x=0, y=0, relheight=1.0, relwidth=0.0)

        tk.Frame(self.root, bg=BG, height=8).pack()

        # Gesture tiles — centered at 840px, equal width
        tiles_outer = tk.Frame(self.root, bg=BG)
        tiles_outer.pack(fill="x")

        # Use a centering trick: left+right spacers with equal weight
        tiles_center = tk.Frame(tiles_outer, bg=BG)
        tiles_center.pack(fill="x")
        tiles_center.columnconfigure(0, weight=1)
        tiles_center.columnconfigure(1, weight=0, minsize=CONTENT_W)
        tiles_center.columnconfigure(2, weight=1)

        tiles_fixed = tk.Frame(tiles_center, bg=BG)
        tiles_fixed.grid(row=0, column=1, sticky="ew")
        tiles_fixed.columnconfigure(tuple(range(5)), weight=1, uniform="tile")

        self.tiles = {}
        for gid, gname in GESTURES.items():
            tile = tk.Frame(tiles_fixed, bg=TILE_DIMMED,
                            highlightbackground=BORDER,
                            highlightthickness=1, padx=8, pady=18)
            tile.grid(row=0, column=gid, sticky="nsew",
                      padx=(0, 6 if gid < 4 else 0))
            ilbl = tk.Label(tile, text="", bg=TILE_DIMMED)
            nlbl = tk.Label(tile, text=gname, font=self.f_tile,
                            bg=TILE_DIMMED, fg=TEXT_DIM,
                            wraplength=200, justify="center", anchor="center")
            nlbl.pack(expand=True, fill="x", pady=(2, 2))
            dots_f = tk.Frame(tile, bg=TILE_DIMMED)
            dots_f.pack()
            dots = []
            for _ in range(N_CALIB_REPS):
                d = tk.Frame(dots_f, bg=BORDER, width=7, height=7)
                d.pack(side="left", padx=2)
                d.pack_propagate(False)
                dots.append(d)
            self.tiles[gid] = {"frame": tile, "icon": ilbl,
                                "name": nlbl, "dots": dots}

        tk.Frame(self.root, bg=BG, height=8).pack()
        div_container = tk.Frame(self.root, bg=BG)
        div_container.pack(fill="x")
        div_inner = tk.Frame(div_container, bg=BG, width=CONTENT_W)
        div_inner.pack(anchor="center")
        tk.Frame(div_inner, bg=BORDER, height=1).pack(fill="x")
        tk.Frame(self.root, bg=BG, height=8).pack()

        # Scrollable main area
        scroll_container = tk.Frame(self.root, bg=BG)
        scroll_container.pack(fill="both", expand=True)

        self._canvas_scroll = tk.Canvas(scroll_container, bg=BG,
                                        highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical",
                                 command=self._canvas_scroll.yview,
                                 width=0)
        self._canvas_scroll.configure(yscrollcommand=scrollbar.set)
        self._canvas_scroll.pack(side="left", fill="both", expand=True)

        # Fixed-width centered content frame inside scroll canvas
        self._main_outer = tk.Frame(self._canvas_scroll, bg=BG)
        self._scroll_window = self._canvas_scroll.create_window(
            (0, 0), window=self._main_outer, anchor="nw")

        def _on_frame_configure(e):
            self._canvas_scroll.configure(
                scrollregion=self._canvas_scroll.bbox("all"))

        def _on_canvas_configure(e):
            self._canvas_scroll.itemconfig(
                self._scroll_window, width=e.width)

        self._main_outer.bind("<Configure>", _on_frame_configure)
        self._canvas_scroll.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(e):
            self._canvas_scroll.yview_scroll(int(-1*(e.delta/120)), "units")
        self._canvas_scroll.bind_all("<MouseWheel>", _on_mousewheel)

        # Center the actual content at fixed 840px
        self._main = tk.Frame(self._main_outer, bg=BG, width=CONTENT_W)
        self._main.pack(anchor="center", pady=(0, 20))
        self._main.pack_propagate(False)

        self._main.columnconfigure(0, weight=0, minsize=352)   # left: fixed
        self._main.columnconfigure(1, weight=0, minsize=476)   # right: 840-352-12=476
        self._main.rowconfigure(0, weight=1)
        main = self._main

        # Left card
        left = tk.Frame(main, bg=BG_CARD,
                        highlightbackground=BORDER,
                        highlightthickness=1, padx=16, pady=10)
        left.grid(row=0, column=0, sticky="nsew")

        self.phase_lbl = tk.Label(left, text="",
                                  font=self.f_exlabel, bg=BG_CARD,
                                  fg=TEXT_SEC, anchor="w")
        self.phase_lbl.pack(fill="x")

        tk.Frame(left, bg=BG_CARD, height=2).pack()

        # 1:1 animation canvas — fixed 280x280, no resize
        self.anim_canvas = tk.Canvas(left, bg=BG_TILE,
                                     highlightbackground=BORDER,
                                     highlightthickness=1,
                                     width=320, height=320)
        self.anim_canvas.pack(pady=(0, 3), expand=False)
        self._anim_canvas_text = self.anim_canvas.create_text(
            160, 160, text="",
            font=self.f_sub, fill=TEXT_DIM, justify="center")
        self.anim_icon_id = self.anim_canvas.create_text(
            160, 160, text="", font=self.f_anim, fill=ACCENT)
        # no resize binding — fixed size

        # Video player — plays once per gesture, holds last frame
        self._video = VideoPlayer(
            self.anim_canvas,
            self._anim_canvas_text,
            self.anim_icon_id,
            self.root,
        )
        self._video_gesture = None

        self.gname_lbl = tk.Label(left, text="—",
                                  font=self.f_gesture, bg=BG_CARD,
                                  fg=TEXT_PRI, anchor="center")
        self.gname_lbl.pack(fill="x")

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=5)

        # Action label + timer inline in same row
        action_area = tk.Frame(left, bg=BG_CARD)
        action_area.pack(pady=(4, 0))
        self.tval_lbl = tk.Label(action_area, text="",
                                 font=self.f_timer, bg=BG_CARD, fg=TEXT_PRI)
        self.tval_lbl.pack(side="left", padx=(0, 10))
        self.action_lbl = tk.Label(action_area, text="",
                                   font=self.f_action, bg=BG_CARD, fg=TEXT_SEC)
        self.action_lbl.pack(side="left")

        self.rep_lbl = tk.Label(left, text="",
                                font=self.f_rep, bg=BG_CARD, fg=TEXT_DIM)
        self.rep_lbl.pack(pady=(3, 0))

        # Start / Weiter button
        self.action_btn = tk.Label(left,
                                   text="▶  Kalibrierung starten",
                                   font=self.f_btn,
                                   bg=ACCENT, fg="#ffffff",
                                   pady=7, cursor="hand2",
                                   anchor="center")
        self.action_btn.bind("<Button-1>", lambda e: self._on_button())
        self.action_btn.bind("<Enter>",
                             lambda e: self.action_btn.config(bg=ACCENT_MED))
        self.action_btn.bind("<Leave>",
                             lambda e: self.action_btn.config(bg=ACCENT))

        # Right card
        right_outer = tk.Frame(main, bg=BG)
        right_outer.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        ex_card = tk.Frame(right_outer, bg=BG_CARD,
                           highlightbackground=BORDER,
                           highlightthickness=1, padx=16, pady=10)
        ex_card.pack(fill="both", expand=True)

        tk.Label(ex_card, text="ANWENDUNGSBEISPIEL",
                 font=self.f_exlabel, bg=BG_CARD,
                 fg=TEXT_SEC, anchor="w").pack(fill="x")
        tk.Frame(ex_card, bg=BORDER, height=1).pack(fill="x", pady=6)

        # 16:9 canvas — fixed width 444px (476 - 2*16 padx), height set by ratio
        self.preview_canvas = tk.Canvas(ex_card, bg=BG_TILE,
                                        highlightbackground=BORDER,
                                        highlightthickness=1,
                                        width=444, height=250)
        # Don't pack here — shown/hidden by _show_current_example
        self._preview_text_id = self.preview_canvas.create_text(
            240, 200, text="",
            font=self.f_sub, fill=TEXT_DIM, justify="center")
        self._preview_icon_id = self.preview_canvas.create_text(
            240, 200, text="", font=self.f_sub, fill=TEXT_DIM)
        # no resize binding — fixed canvas sizes

        # Widget video player — plays on slider change (16:9 ratio enforced)
        self._widget_video = VideoPlayer(
            self.preview_canvas,
            self._preview_text_id,
            self._preview_icon_id,
            self.root,
            fixed_ratio=1.78,
        )

        # Slider controls: ← dots → (BELOW video)
        slider_row = tk.Frame(ex_card, bg=BG_CARD)
        slider_row.pack(fill="x", pady=(6, 0))

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

        # Description text (BELOW slider)
        tk.Frame(ex_card, bg=BG_CARD, height=8).pack()
        self.example_lbl = tk.Label(ex_card, text="",
                                    font=self.f_example, bg=BG_CARD,
                                    fg=TEXT_PRI, wraplength=360,
                                    justify="left")
        self.example_lbl.pack(anchor="w", fill="x", padx=50)

        # Dot labels — rebuilt when gesture changes
        self._slider_dots = []
        self._slider_idx  = 0
        self._slider_gid  = None
        self._rebuild_dots(0)

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
        n = len(WIDGET_SLIDES.get(gesture_id, []))
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
        n = len(WIDGET_SLIDES.get(gid, []))
        self._slider_idx = (self._slider_idx - 1) % n
        self._show_current_example(gid)

    def _slider_next(self):
        with cal.lock:
            gid = list(GESTURES.keys())[min(cal.gesture_idx, len(GESTURES)-1)]
        n = len(WIDGET_SLIDES.get(gid, []))
        self._slider_idx = (self._slider_idx + 1) % n
        self._show_current_example(gid)

    def _show_current_example(self, gesture_id):
        slides = WIDGET_SLIDES.get(gesture_id, [(None, "")])
        self._slider_idx = self._slider_idx % len(slides)
        path, description = slides[self._slider_idx]
        self.example_lbl.config(text=description)
        self._update_dots()
        # Rest has no preview video
        if gesture_id == 0:
            self._widget_video.reset()
            self.preview_canvas.pack_forget()
        else:
            # Pack canvas right after the divider (position 2 = after label + divider)
            self.preview_canvas.pack(fill="x", pady=(0, 0), before=self._prev_btn.master)
            if path and os.path.exists(path):
                self._widget_video.start_path(path)
            else:
                self._widget_video.reset()

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
            n = len(WIDGET_SLIDES.get(gesture_id, []))
            self._slider_idx = ex_idx_cal % n
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
            self._video.reset()
            self._video_gesture = None
            self._show_btn("▶  Kalibrierung starten")

        elif phase == "countdown":
            self._set("GLEICH GEHT ES LOS", WARNING,
                      GESTURES[gesture_id], TEXT_PRI,
                      "Vorbereiten...", f"{int(timer_val)+1}s", WARNING)
            self.rep_lbl.config(
                text=f"Wiederholung {rep_idx + 1} von {N_CALIB_REPS}")
            # Restart video + advance slider on every new countdown (once per rep)
            vid_key = (gesture_id, rep_idx)
            if self._video_gesture != vid_key:
                self._video_gesture = vid_key
                self._video.start(gesture_id)
                # Advance slider index parallel with countdown start
                slides = WIDGET_SLIDES.get(gesture_id, [(None, "")])
                self._slider_idx = rep_idx % len(slides)
                self._show_current_example(gesture_id)
            self._hide_btn()

        elif phase == "recording":
            self._set("▶  AUFNAHME LÄUFT", ACCENT,
                      GESTURES[gesture_id], TEXT_PRI,
                      "Geste halten!", f"{int(timer_val)+1}s", ACCENT)
            self.rep_lbl.config(
                text=f"Wiederholung {rep_idx + 1} von {N_CALIB_REPS}")
            # Video holds last frame — no action needed
            self._hide_btn()

        elif phase == "rest":
            self._set("PAUSE", TEXT_SEC,
                      GESTURES[gesture_id], TEXT_DIM,
                      "Kurze Pause", f"{int(timer_val)+1}s", TEXT_SEC)
            # Hold last frame — no reset
            self._hide_btn()

        elif phase == "gesture_done":
            next_idx  = g_idx + 1
            next_name = GESTURES.get(next_idx, "")
            self._set("✓  GESTE ABGESCHLOSSEN", ACCENT,
                      GESTURES[gesture_id], ACCENT,
                      f"Weiter zu: {next_name}", "", ACCENT)
            # Hold last frame — no reset
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
        pass  # canvas is fixed 280x280

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