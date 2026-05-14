"""
gesture_gui.py
==============
Real-time EMG gesture prediction GUI.

What it does:
    - Connects to mindrove_streamer.py via UDP (port 12345)
    - Runs continuous predictions in the background
    - Every 2 seconds: shows the most stable gesture (majority vote)
    - "Einloggen" button to confirm the predicted gesture
    - Manual buttons for all 5 gestures (fallback)
    - Log list showing all confirmed gestures with timestamp
    - Logged data accessible via get_log() for later interface integration

Usage:
    Terminal 1: python scripts/mindrove_streamer.py
    Terminal 2: python scripts/gesture_gui.py

Press the window close button to stop.
"""

import os
import pickle
import socket
import collections
import threading
import time
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
import numpy as np

from libemg.feature_extractor import FeatureExtractor

# ── Settings ──────────────────────────────────────────────────────────────────

GESTURE_NAMES = {
    0: "Rest",
    1: "Daumen hoch",
    2: "Swipe",
    3: "Handgelenk drehen",
    4: "Zeigen / Tippen",
}

GESTURE_ICONS = {
    0: "✋",
    1: "👍",
    2: "👋",
    3: "🔄",
    4: "☝️",
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

# ── Colors ────────────────────────────────────────────────────────────────────

BG          = "#0f0f13"
BG_CARD     = "#1a1a22"
BG_CARD2    = "#22222e"
ACCENT      = "#00e5a0"
ACCENT_DIM  = "#00a870"
TEXT_PRI    = "#f0f0f0"
TEXT_SEC    = "#888899"
TEXT_DIM    = "#444455"
DANGER      = "#ff4466"
BORDER      = "#2a2a38"

# ── Shared state ──────────────────────────────────────────────────────────────

class PredictionState:
    def __init__(self):
        self.lock              = threading.Lock()
        self.recent_preds      = collections.deque()  # (timestamp, label, confidence)
        self.current_display   = None   # majority-voted label shown in UI
        self.current_confidence = 0.0
        self.streamer_ok       = False
        self.log               = []     # list of (datetime, label_str)
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
    """Returns list of (datetime, gesture_name) — call this from your interface."""
    with state.lock:
        return list(state.log)


# ── GUI ───────────────────────────────────────────────────────────────────────

class GestureGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EMG Gesture Recognition")
        self.root.configure(bg=BG)

        self._build_fonts()
        self._build_ui()
        self._start_update_loop()

    def _build_fonts(self):
        self.font_title    = tkfont.Font(family="Courier New", size=13, weight="bold")
        self.font_gesture  = tkfont.Font(family="Courier New", size=22, weight="bold")
        self.font_icon     = tkfont.Font(family="Courier New", size=22)
        self.font_conf     = tkfont.Font(family="Courier New", size=11)
        self.font_btn      = tkfont.Font(family="Courier New", size=12, weight="bold")
        self.font_btn_sm   = tkfont.Font(family="Courier New", size=11, weight="bold")
        self.font_log      = tkfont.Font(family="Courier New", size=12)
        self.font_feed     = tkfont.Font(family="Courier New", size=11)
        self.font_status   = tkfont.Font(family="Courier New", size=9)
        self.font_header   = tkfont.Font(family="Courier New", size=12, weight="bold")

    def _build_ui(self):
        root = self.root
        pad  = 16

        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(root, bg=BG, pady=pad)
        header.pack(fill="x", padx=pad)

        tk.Label(header, text="EMG GESTURE RECOGNITION",
                 font=self.font_title, bg=BG, fg=ACCENT).pack(side="left")

        self.battery_label = tk.Label(header, text="🔋 —",
                                      font=self.font_header, bg=BG, fg=TEXT_SEC)
        self.battery_label.pack(side="left", padx=(24, 0))

        self.status_dot = tk.Label(header, text="● NO STREAM",
                                   font=self.font_header, bg=BG, fg=DANGER)
        self.status_dot.pack(side="right")

        tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=pad)

        # ── Main content ──────────────────────────────────────────────────────
        content = tk.Frame(root, bg=BG)
        content.pack(fill="both", expand=True, padx=pad, pady=(pad, 0))

        # Left column — fixed width to avoid jumping
        left = tk.Frame(content, bg=BG, width=320)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        # Prediction card
        pred_card = tk.Frame(left, bg=BG_CARD, padx=16, pady=6,
                             relief="flat", bd=0)
        pred_card.pack(fill="x", pady=(0, 5))
        self._add_border(pred_card)

        tk.Label(pred_card, text="AKTUELLE GESTE",
                 font=self.font_status, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w")

        self.icon_label = tk.Label(pred_card, text="—",
                                   font=self.font_icon, bg=BG_CARD, fg=TEXT_PRI)
        self.icon_label.pack(pady=(2, 0))

        # Fixed-width gesture label — anchored to longest gesture name
        self.gesture_label = tk.Label(pred_card,
                                      text="Zeigen / Tippen",
                                      font=self.font_gesture, bg=BG_CARD,
                                      fg=TEXT_DIM, width=18, anchor="center")
        self.gesture_label.pack(pady=(1, 4))

        # Confidence bar
        conf_frame = tk.Frame(pred_card, bg=BG_CARD)
        conf_frame.pack(fill="x")

        tk.Label(conf_frame, text="KONFIDENZ",
                 font=self.font_status, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w")

        self.conf_bar_bg = tk.Frame(conf_frame, bg=BG_CARD2, height=8)
        self.conf_bar_bg.pack(fill="x", pady=(4, 0))
        self.conf_bar_bg.pack_propagate(False)

        self.conf_bar = tk.Frame(self.conf_bar_bg, bg=ACCENT_DIM, height=8, width=0)
        self.conf_bar.place(x=0, y=0, relheight=1.0)

        # Conf % and countdown timer in one row
        conf_row = tk.Frame(pred_card, bg=BG_CARD)
        conf_row.pack(fill="x", pady=(4, 0))

        self.countdown_label = tk.Label(conf_row, text="2.00s",
                                        font=self.font_status, bg=BG_CARD, fg=TEXT_DIM)
        self.countdown_label.pack(side="left")

        self.conf_label = tk.Label(conf_row, text="—",
                                   font=self.font_conf, bg=BG_CARD, fg=TEXT_SEC)
        self.conf_label.pack(side="right")

        self._countdown_start = time.time()
        self._update_countdown()

        # Einloggen button — Label-based for reliable macOS styling
        self.log_btn = tk.Label(
            left,
            text="✓  EINLOGGEN",
            font=self.font_btn,
            bg=ACCENT_DIM, fg=BG,
            pady=7, cursor="hand2",
            anchor="center",
        )
        self.log_btn.pack(fill="x", pady=(0, 5))
        self.log_btn.bind("<Button-1>", lambda e: self._log_predicted())
        self.log_btn.bind("<Enter>", lambda e: self.log_btn.config(bg=ACCENT))
        self.log_btn.bind("<Leave>", lambda e: self.log_btn.config(bg=ACCENT_DIM))
        self._log_btn_enabled = False

        # Manual gesture buttons
        manual_card = tk.Frame(left, bg=BG_CARD, padx=12, pady=6)
        manual_card.pack(fill="both", expand=True, pady=(0, 5))
        self._add_border(manual_card)

        tk.Label(manual_card, text="MANUELL EINLOGGEN",
                 font=self.font_status, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", pady=(0, 4))

        btn_grid = tk.Frame(manual_card, bg=BG_CARD)
        btn_grid.pack(fill="both", expand=True)

        for gid, gname in GESTURE_NAMES.items():
            icon = GESTURE_ICONS.get(gid, "")
            lbl = tk.Label(
                btn_grid,
                text=f"{icon}  {gname}",
                font=self.font_btn_sm,
                bg="#1a1a1a", fg="#ffffff",
                pady=6, cursor="hand2",
                anchor="center",
            )
            lbl.pack(fill="both", expand=True, pady=2)
            lbl.bind("<Button-1>", lambda e, g=gid: self._log_manual(g))
            lbl.bind("<Enter>",    lambda e, w=lbl: w.config(bg=ACCENT_DIM, fg="#000000"))
            lbl.bind("<Leave>",    lambda e, w=lbl: w.config(bg="#1a1a1a",  fg="#ffffff"))

        # Right column — Log
        right = tk.Frame(content, bg=BG)
        right.pack(side="right", fill="both", expand=True, padx=(12, 0))

        log_card = tk.Frame(right, bg=BG_CARD, padx=16, pady=16)
        log_card.pack(fill="both", expand=True)
        self._add_border(log_card)

        log_header = tk.Frame(log_card, bg=BG_CARD)
        log_header.pack(fill="x", pady=(0, 10))

        tk.Label(log_header, text="LOG",
                 font=self.font_status, bg=BG_CARD, fg=TEXT_SEC).pack(side="left")

        tk.Button(log_header, text="LEEREN",
                  font=self.font_status, bg=BG_CARD, fg=TEXT_DIM,
                  activebackground=BG_CARD, activeforeground=DANGER,
                  relief="flat", bd=0, cursor="hand2",
                  command=self._clear_log).pack(side="right")

        # Scrollable log list
        log_scroll_frame = tk.Frame(log_card, bg=BG_CARD)
        log_scroll_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(log_scroll_frame, bg=BG_CARD2,
                                 troughcolor=BG_CARD, width=6)
        scrollbar.pack(side="right", fill="y")

        self.log_listbox = tk.Listbox(
            log_scroll_frame,
            font=self.font_log,
            bg=BG_CARD, fg=TEXT_PRI,
            selectbackground=ACCENT_DIM, selectforeground=BG,
            relief="flat", bd=0,
            highlightthickness=0,
            yscrollcommand=scrollbar.set,
            width=28, height=20,
        )
        self.log_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.log_listbox.yview)

        self.log_count = tk.Label(log_card, text="0 Einträge",
                                  font=self.font_status, bg=BG_CARD, fg=TEXT_DIM)
        self.log_count.pack(anchor="e", pady=(8, 0))

        # Far right column — Live Feed
        far_right = tk.Frame(content, bg=BG)
        far_right.pack(side="right", fill="both", expand=True, padx=(12, 0))

        feed_card = tk.Frame(far_right, bg=BG_CARD, padx=16, pady=16)
        feed_card.pack(fill="both", expand=True)
        self._add_border(feed_card)

        feed_header = tk.Frame(feed_card, bg=BG_CARD)
        feed_header.pack(fill="x", pady=(0, 10))

        tk.Label(feed_header, text="LIVE FEED",
                 font=self.font_status, bg=BG_CARD, fg=TEXT_SEC).pack(side="left")

        self.feed_count = tk.Label(feed_header, text="~10 Hz",
                                   font=self.font_status, bg=BG_CARD, fg=TEXT_DIM)
        self.feed_count.pack(side="right")

        feed_scroll_frame = tk.Frame(feed_card, bg=BG_CARD)
        feed_scroll_frame.pack(fill="both", expand=True)

        feed_scrollbar = tk.Scrollbar(feed_scroll_frame, bg=BG_CARD2,
                                      troughcolor=BG_CARD, width=6)
        feed_scrollbar.pack(side="right", fill="y")

        self.feed_listbox = tk.Listbox(
            feed_scroll_frame,
            font=self.font_feed,
            bg=BG_CARD, fg=TEXT_SEC,
            selectbackground=ACCENT_DIM, selectforeground=BG,
            relief="flat", bd=0,
            highlightthickness=0,
            yscrollcommand=feed_scrollbar.set,
            width=32, height=20,
        )
        self.feed_listbox.pack(side="left", fill="both", expand=True)
        feed_scrollbar.config(command=self.feed_listbox.yview)

        self._last_feed_ts = 0.0

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
        else:
            self.gesture_label.config(text="Warte auf Daten...", fg=TEXT_DIM)
            self.icon_label.config(text="—")
            self.conf_label.config(text="—")
            self.log_btn.config(bg="#333333")
            self._log_btn_enabled = False
            self._current_label = None

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

    def _log_entry(self, label):
        """Add a gesture to the log."""
        name = GESTURE_NAMES.get(label, f"class_{label}")
        icon = GESTURE_ICONS.get(label, "")
        now  = datetime.now()
        ts   = now.strftime("%H:%M:%S")

        with state.lock:
            state.log.append((now, name))

        entry = f"{ts}  {icon} {name}"
        self.log_listbox.insert(tk.END, entry)
        self.log_listbox.see(tk.END)

        # Alternate row colors
        idx = self.log_listbox.size() - 1
        bg  = BG_CARD2 if idx % 2 == 0 else BG_CARD
        self.log_listbox.itemconfig(idx, bg=bg)

        count = self.log_listbox.size()
        self.log_count.config(text=f"{count} Einträge")

        # Flash the log button briefly
        self.log_btn.config(bg=ACCENT)
        self.root.after(300, lambda: self.log_btn.config(bg=ACCENT_DIM))

    def _log_predicted(self):
        if self._log_btn_enabled and hasattr(self, '_current_label') and self._current_label is not None:
            self._log_entry(self._current_label)

    def _log_manual(self, gesture_id):
        self._log_entry(gesture_id)

    def _clear_log(self):
        self.log_listbox.delete(0, tk.END)
        with state.lock:
            state.log.clear()
        self.log_count.config(text="0 Einträge")


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
    root.geometry("1150x600")
    root.minsize(1150, 600)
    root.resizable(True, True)
    app  = GestureGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()