"""
collect_data.py
===============
Guided EMG data collection script for the LibEMG teaching pipeline.

What it does:
    - Listens on UDP port 12345 (where mindrove_streamer.py sends data)
    - Guides the student through a countdown before each trial
    - Records EMG for a fixed duration while the student holds a gesture
    - Saves each trial as a CSV to data/raw/gesture_<id>/rep_<n>.csv

Gesture IDs are defined centrally in scripts/gesture_config.py.

Usage:
    Make sure mindrove_streamer.py is running in another terminal first.
    Then run:
        python scripts/collect_data.py

    Follow the on-screen prompts. Press Ctrl+C at any time to stop early.
"""

import csv
import os
import pickle
import socket
import time

try:
    from scripts.gesture_config import COLLECTION_GESTURES as GESTURES
except ImportError:
    from gesture_config import COLLECTION_GESTURES as GESTURES

# ── Settings ──────────────────────────────────────────────────────────────────

N_REPS = 10          # number of repetitions per gesture
RECORD_SECS = 3      # seconds of EMG recorded per rep
REST_BETWEEN = 2     # seconds of rest between reps (no recording)
COUNTDOWN_SECS = 3   # countdown before each rep starts

UDP_HOST = "127.0.0.1"
UDP_PORT = 12345
UDP_TIMEOUT = 5.0    # seconds to wait for first packet before giving up

N_CHANNELS = 8

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

# ── Helpers ───────────────────────────────────────────────────────────────────


def make_output_path(gesture_id, rep_idx):
    folder = os.path.join(DATA_DIR, f"gesture_{gesture_id}")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"rep_{rep_idx}.csv")


def next_rep_index(gesture_id):
    """Find the next unused rep index so we never overwrite existing data."""
    folder = os.path.join(DATA_DIR, f"gesture_{gesture_id}")
    if not os.path.exists(folder):
        return 0
    existing = [
        f for f in os.listdir(folder)
        if f.startswith("rep_") and f.endswith(".csv")
    ]
    if not existing:
        return 0
    indices = []
    for f in existing:
        try:
            indices.append(int(f.replace("rep_", "").replace(".csv", "")))
        except ValueError:
            pass
    return max(indices) + 1 if indices else 0


def countdown(label, secs):
    print(f"\n  >>> Prepare for: {label}")
    for i in range(secs, 0, -1):
        print(f"      {i}...", flush=True)
        time.sleep(1)
    print("  *** GO! Hold the gesture now. ***\n", flush=True)


def record_trial(sock, duration_secs):
    """
    Drain the socket and collect samples for `duration_secs` seconds.
    Returns a list of rows, each row is a list of N_CHANNELS floats.
    """
    samples = []
    deadline = time.time() + duration_secs

    # Drain any stale packets that built up during the countdown
    sock.setblocking(False)
    while True:
        try:
            sock.recvfrom(4096)
        except BlockingIOError:
            break
    sock.setblocking(True)
    sock.settimeout(0.5)

    while time.time() < deadline:
        try:
            data, _ = sock.recvfrom(4096)
            sample = pickle.loads(data)
            if len(sample) == N_CHANNELS:
                samples.append(sample)
        except socket.timeout:
            continue

    return samples


def save_csv(samples, path):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        header = [f"ch{i}" for i in range(N_CHANNELS)]
        writer.writerow(header)
        writer.writerows(samples)


def wait_for_stream(sock):
    """Block until we receive the first UDP packet or time out."""
    print(f"  Waiting for streamer on {UDP_HOST}:{UDP_PORT} ...", flush=True)
    sock.settimeout(UDP_TIMEOUT)
    try:
        sock.recvfrom(4096)
        print("  Streamer detected. Starting collection.\n")
    except socket.timeout:
        print(
            f"\n[ERROR] No data received after {UDP_TIMEOUT}s.\n"
            "  Is mindrove_streamer.py running in another terminal?\n"
            "  Is the armband connected?\n"
        )
        raise SystemExit(1)


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    print("=" * 55)
    print("  EMG Data Collection")
    print("=" * 55)
    print(f"  Gestures   : {len(GESTURES)}")
    print(f"  Reps each  : {N_REPS}")
    print(f"  Duration   : {RECORD_SECS}s per rep")
    print(f"  Saving to  : data/raw/")
    print()
    print("  Gestures to collect:")
    for gid, glabel in GESTURES.items():
        print(f"    [{gid}] {glabel}")
    print()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_HOST, UDP_PORT))

    try:
        wait_for_stream(sock)

        for gesture_id, gesture_label in GESTURES.items():
            print("─" * 55)
            print(f"  GESTURE {gesture_id}: {gesture_label}")
            print("─" * 55)

            start_rep = next_rep_index(gesture_id)

            for rep in range(N_REPS):
                rep_idx = start_rep + rep
                print(f"\n  Rep {rep + 1} of {N_REPS} (saving as rep_{rep_idx}.csv)")

                countdown(gesture_label, COUNTDOWN_SECS)

                samples = record_trial(sock, RECORD_SECS)

                if len(samples) == 0:
                    print("  [WARN] No samples recorded for this rep. Check streamer.")
                    continue

                path = make_output_path(gesture_id, rep_idx)
                save_csv(samples, path)

                expected = RECORD_SECS * 500  # ~500 Hz
                print(f"  Saved {len(samples)} samples to {path}")
                if len(samples) < expected * 0.8:
                    print(
                        f"  [WARN] Expected ~{expected} samples, got {len(samples)}. "
                        "Packet loss? Check streamer terminal."
                    )

                if rep < N_REPS - 1:
                    print(f"\n  Rest for {REST_BETWEEN}s...")
                    time.sleep(REST_BETWEEN)

            print(f"\n  Gesture {gesture_id} complete.\n")

        print("=" * 55)
        print("  All gestures collected successfully.")
        print("  Run inspect_data.py next to check signal quality.")
        print("=" * 55)

    except KeyboardInterrupt:
        print("\n[Stopped by user]")

    finally:
        sock.close()


if __name__ == "__main__":
    main()
