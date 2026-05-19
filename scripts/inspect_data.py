"""
inspect_data.py
===============
Signal quality check for collected EMG data.

What it does:
    - Loads all reps for each gesture
    - Plots all 8 channels with all reps overlaid in different colours
    - Prints per-channel stats: RMS, std, min, max
    - Flags channels that look dead (flat signal)
    - Saves each plot to data/inspect/gesture_X.png

Usage:
    python scripts/inspect_data.py

Run this after collect_data.py has produced files in data/raw/.
No armband or streamer needed — works purely from saved CSVs.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

try:
    from scripts.gesture_config import GESTURE_DISPLAY_NAMES as GESTURES
except ImportError:
    from gesture_config import GESTURE_DISPLAY_NAMES as GESTURES

# ── Settings ──────────────────────────────────────────────────────────────────

SAMPLING_RATE = 500      # Hz — used for x-axis time labels
FLAT_STD_THRESHOLD = 10  # channels with std below this are flagged as dead

DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
SAVE_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "inspect")

# ── Helpers ───────────────────────────────────────────────────────────────────


def load_all_reps(gesture_id):
    folder = os.path.join(DATA_DIR, f"gesture_{gesture_id}")
    if not os.path.exists(folder):
        raise FileNotFoundError(f"Folder not found: {folder}")

    reps = []
    for fname in sorted(os.listdir(folder)):
        if fname.startswith("rep_") and fname.endswith(".csv"):
            path = os.path.join(folder, fname)
            data = np.loadtxt(path, delimiter=",", skiprows=1)  # (n_samples, 8)
            reps.append((fname, data))

    if not reps:
        raise FileNotFoundError(f"No rep CSVs found in {folder}")
    return reps  # list of (filename, ndarray)


def print_stats(reps, gesture_label):
    print(f"\n  Gesture : {gesture_label}  ({len(reps)} reps)")

    # Aggregate stats across all reps
    all_data = np.vstack([d for _, d in reps])
    n_channels = all_data.shape[1]

    print(f"  {'Channel':<10} {'RMS':>10} {'Std':>10} {'Min':>12} {'Max':>12}  Status")
    print("  " + "-" * 65)

    for ch in range(n_channels):
        col = all_data[:, ch]
        rms  = float(np.sqrt(np.mean(col ** 2)))
        std  = float(np.std(col))
        cmin = float(np.min(col))
        cmax = float(np.max(col))
        status = "⚠ FLAT — check electrode" if std < FLAT_STD_THRESHOLD else "OK"
        print(f"  ch{ch:<8} {rms:>10.1f} {std:>10.1f} {cmin:>12.1f} {cmax:>12.1f}  {status}")


def plot_gesture(gesture_id, gesture_label, reps):
    n_channels = reps[0][1].shape[1]
    n_reps = len(reps)

    # One distinct colour per rep
    colours = [cm.tab10(i / max(n_reps, 1)) for i in range(n_reps)]

    fig, axes = plt.subplots(n_channels, 1, figsize=(13, 11), sharex=True)
    fig.suptitle(
        f"EMG Signal — Gesture {gesture_id}: {gesture_label}  "
        f"({n_reps} reps overlaid)",
        fontsize=12,
    )

    for ch in range(n_channels):
        ax = axes[ch]
        for rep_idx, (fname, data) in enumerate(reps):
            n_samples = data.shape[0]
            time_axis = np.arange(n_samples) / SAMPLING_RATE
            ax.plot(
                time_axis,
                data[:, ch],
                linewidth=0.7,
                color=colours[rep_idx],
                alpha=0.85,
                label=fname.replace(".csv", "") if ch == 0 else "_nolegend_",
            )
        ax.set_ylabel(f"ch{ch}", fontsize=8, rotation=0, labelpad=28)
        ax.tick_params(labelsize=7)
        ax.grid(True, linestyle="--", alpha=0.4)

    # Single legend at the top
    axes[0].legend(
        loc="upper right",
        fontsize=7,
        ncol=n_reps,
        framealpha=0.7,
    )
    axes[-1].set_xlabel("Time (s)")
    plt.tight_layout()

    # Save
    os.makedirs(SAVE_DIR, exist_ok=True)
    save_path = os.path.join(SAVE_DIR, f"gesture_{gesture_id}.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"\n  Plot saved → {save_path}")

    plt.show()
    plt.close(fig)


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    print("=" * 55)
    print("  EMG Data Inspector")
    print("=" * 55)

    all_ok = True

    for gesture_id, gesture_label in GESTURES.items():
        try:
            reps = load_all_reps(gesture_id)
        except FileNotFoundError as e:
            print(f"\n[ERROR] {e}")
            all_ok = False
            continue

        print_stats(reps, gesture_label)
        plot_gesture(gesture_id, gesture_label, reps)

    if all_ok:
        print("\n" + "=" * 55)
        print("  Inspection complete.")
        print("  Plots saved to data/inspect/")
        print("  If signals look reasonable and no FLAT warnings,")
        print("  you are ready for notebooks/04_train.ipynb.")
        print("=" * 55)


if __name__ == "__main__":
    main()
