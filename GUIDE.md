# EMG Gesture Classification — LibEMG + MindRove

Classify hand gestures in real time using surface EMG.
Built on [LibEMG](https://libemg.github.io/libemg/) and the MindRove armband (8-channel, 500 Hz).

> **For students:** follow the steps below in order. Each script has a detailed docstring at the top — read it before running.

---

## Folder structure

```text
LibEMG_workflow/
├── scripts/
│   ├── mindrove_streamer.py   ← connects armband → UDP stream
│   ├── collect_data.py        ← guided gesture recording
│   ├── inspect_data.py        ← signal quality plots
│   ├── live_demo.py           ← real-time prediction
│   └── diagnose_data.py       ← troubleshooting tool
├── Middleware/                ← central integration for Audio & EMG
│   ├── gesture_gui.py         ← Main GUI for multimodal input
│   ├── audio_recorder.py      ← PyAudio recording logic
│   ├── speech_transcriber.py  ← Whisper STT logic
│   └── network_client.py      ← API sockets
├── notebooks/
│   └── 04_train.ipynb         ← feature extraction → training → evaluation
├── data/
│   ├── raw/                   ← your collected data goes here
│   ├── sample/                ← example data (copy to raw/ for a test run)
│   └── inspect/               ← signal plots from inspect_data.py
├── models/                    ← trained classifier saved here
├── requirements.txt
├── GUIDE.md                   ← how to extend and modify the pipeline
└── README.md                  ← you are here

```

---

## Prerequisites & Setup

To ensure all C++ dependencies (like `pygame` and `pyaudio`) compile correctly, this project **strictly requires Python 3.11 or 3.12**. Do *not* use Python 3.13 or 3.14. You also need FFmpeg for the audio transcription pipeline.

### 1. System Requirements (Windows)

Open a new PowerShell (ideally as Administrator) and install the necessary system tools:

```bash
# Install Python 3.12
winget install Python.Python.3.12

# Install FFmpeg (Crucial for Whisper Speech-to-Text)
winget install Gyan.FFmpeg

```

***Important:** Restart Visual Studio Code and your terminal after installing FFmpeg to update your system's PATH variables!*

### 2. Environment Setup (.venv)

Navigate to the project folder and create a clean virtual environment specifically using Python 3.12.

```bash
# Create the virtual environment
# Windows:
py -3.12 -m venv .venv
# macOS/Linux:
python3.12 -m venv .venv

# Activate it
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install all dependencies (make sure your .venv is active!)
pip install -r requirements.txt

```

*(Note: Ensure `pyaudio` is listed in your `requirements.txt`)*

---

## Quick start (5 steps)

### Step 1 — Stream from the armband

Connect to the MindRove WiFi (`MindRove_XXXX`), then in a terminal:

```bash
python scripts/mindrove_streamer.py

```

Keep this terminal open — it bridges the armband to the rest of the pipeline.

### Step 2 — Collect gesture data

In a **second** terminal:

```bash
python scripts/collect_data.py

```

Follow the prompts. The script records 10 repetitions of each gesture (3 seconds each) and saves CSVs to `data/raw/gesture_<id>/`.

> **No armband?** Copy the contents of `data/sample/` into `data/raw/` and skip to step 3. See `data/sample/README.md` for details.

### Step 3 — Inspect signal quality

```bash
python scripts/inspect_data.py

```

Plots all 8 channels for each gesture. Look for:

* Channels with visible activity differences between gestures (good)
* Flat channels with near-zero std (bad — check electrode contact)

### Step 4 — Train the classifier

Open `notebooks/04_train.ipynb` in Jupyter and run all cells top to bottom.

The notebook handles: windowing → DC offset removal → feature extraction (HTD group) → LDA training → evaluation → model save.

### Step 5 — Multimodal Live Demo

Instead of the basic demo, run the multimodal Central Interface:

```bash
python Middleware/gesture_gui.py

```

Hold a gesture, confirm it via the UI, and record your voice commands. The interface handles the rest!

---

## Hardware checklist

1. Power on the MindRove armband (LED blinks)
2. Connect PC to armband WiFi (`MindRove_XXXX`)
3. Verify: `ping 192.168.4.1` should get replies
4. Run `mindrove_streamer.py` — it should report `Stream started OK`

---

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Streamer says "no data" | Is the armband WiFi connected? Is the LED on? |
| 100% training accuracy but live demo predicts one class | DC offset mismatch — make sure the notebook has the `mean(axis=2)` subtraction line. Run `diagnose_data.py` to verify. |
| Low accuracy (<70%) | Check `inspect_data.py` plots. Are gestures visually different? Re-record with firmer contractions. |
| Live demo lags | Reduce `PREDICT_EVERY_N_SAMPLES` in `live_demo.py` |
| `FileNotFoundError` (WinError 2) during audio | FFmpeg is missing from your system PATH. Install it via `winget` (see Setup) and completely restart VS Code. |
| `ModuleNotFoundError` for PyAudio or Pygame | Your terminal is not using the `.venv`. Run `.\.venv\Scripts\Activate.ps1` and `pip install -r requirements.txt`. |

For extending the pipeline (adding gestures, changing classifiers, using different features), see **[GUIDE.md](GUIDE.md)**.

```