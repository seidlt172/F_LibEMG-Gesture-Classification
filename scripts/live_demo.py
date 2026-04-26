"""
live_demo.py
============
Real-time EMG gesture prediction in the terminal.

What it does:
    - Loads the trained classifier from models/clf
    - Listens on UDP port 12345 (where mindrove_streamer.py sends data)
    - Buffers incoming samples into a sliding window
    - Extracts features and predicts the gesture at ~2 Hz
    - Prints the predicted gesture to the terminal

IMPORTANT: The preprocessing here (DC offset removal) MUST match
what was done during training in 04_train.ipynb.

Usage:
    Terminal 1: python scripts/mindrove_streamer.py
    Terminal 2: python scripts/live_demo.py

Press Ctrl+C to stop.
"""

import os
import pickle
import socket
import collections
import numpy as np

from libemg.feature_extractor import FeatureExtractor
from libemg.emg_predictor import EMGClassifier

# ── Settings ──────────────────────────────────────────────────────────────────

GESTURE_NAMES = {0: 'Fist', 1: 'Open Hand', 2: 'Index Point'}

WINDOW_SIZE             = 200   # must match training notebook
FEATURE_GROUP           = 'HTD' # must match training notebook
N_CHANNELS              = 8
PREDICT_EVERY_N_SAMPLES = 50    # predict every 50 new samples (~10 Hz at 500 Hz)
                                # Was 500 (1 Hz) — too slow for usable feedback

UDP_HOST = '127.0.0.1'
UDP_PORT = 12345

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'clf')

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print('=' * 45)
    print('  EMG Live Demo')
    print('=' * 45)

    print(f'Loading model from {os.path.abspath(MODEL_PATH)} ...')
    with open(MODEL_PATH, 'rb') as f:
        clf = pickle.load(f)
    fe  = FeatureExtractor()
    print('Model loaded OK.')
    print()
    print('Connecting to streamer...')

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_HOST, UDP_PORT))
    sock.settimeout(5.0)

    # Rolling buffer — keeps last WINDOW_SIZE samples
    buffer = collections.deque(maxlen=WINDOW_SIZE)

    # Wait for first packet
    try:
        data, _ = sock.recvfrom(4096)
        sample = pickle.loads(data)
        print(f'Streamer detected ({len(sample)} channels). Starting prediction.')
        print('-' * 45)
        buffer.append(sample)
    except socket.timeout:
        print('[ERROR] No data received. Is mindrove_streamer.py running?')
        return

    sock.settimeout(0.5)

    samples_since_last_pred = 0

    try:
        while True:
            try:
                data, _ = sock.recvfrom(4096)
                sample = pickle.loads(data)
                buffer.append(sample)
                samples_since_last_pred += 1
            except socket.timeout:
                continue

            if samples_since_last_pred < PREDICT_EVERY_N_SAMPLES:
                continue

            if len(buffer) < WINDOW_SIZE:
                continue

            samples_since_last_pred = 0

            # Build window: (1, n_channels, window_size)
            # Shape convention: libemg expects (n_windows, n_channels, n_samples)
            window_arr  = np.array(buffer, dtype=float).T[np.newaxis, :, :]
            # window_arr shape: (1, 8, 200)

            # ── CRITICAL: DC offset removal ──
            # This MUST match what was done during training.
            # Subtract per-channel mean across the time axis (axis=2).
            window_arr  = window_arr - window_arr.mean(axis=2, keepdims=True)

            features    = fe.extract_feature_group(FEATURE_GROUP, window_arr)
            feature_vec = np.hstack(list(features.values()))
            pred        = clf.model.predict(feature_vec)
            label       = int(pred[0])
            gesture     = GESTURE_NAMES.get(label, f'class_{label}')

            print(f'  >> {gesture}')

    except KeyboardInterrupt:
        print('\n[Stopped by user]')

    finally:
        sock.close()
        print('Done.')


if __name__ == '__main__':
    main()
