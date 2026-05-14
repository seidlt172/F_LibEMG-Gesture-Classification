# EMG Gesture Classification — LibEMG + MindRove

Classify hand gestures in real time using surface EMG.
Built on [LibEMG](https://libemg.github.io/libemg/) and the MindRove armband (8-channel, 500 Hz).

> **For students:** follow the steps below in order. Each script has a detailed docstring at the top — read it before running.

---

## Folder structure

```
LibEMG_workflow/
├── scripts/
│   ├── mindrove_streamer.py   ← connects armband → UDP stream
│   ├── collect_data.py        ← guided gesture recording
│   ├── inspect_data.py        ← signal quality plots
│   ├── live_demo.py           ← real-time prediction
│   └── diagnose_data.py       ← troubleshooting tool
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

## Prerequisites

- Python 3.9+
- MindRove armband (powered on, PC connected to its WiFi network)

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

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

- Channels with visible activity differences between gestures (good)
- Flat channels with near-zero std (bad — check electrode contact)

### Step 4 — Train the classifier

Open `notebooks/04_train.ipynb` in Jupyter and run all cells top to bottom.

The notebook handles: windowing → DC offset removal → feature extraction (HTD group) → LDA training → evaluation → model save.

### Step 5 — Live demo

```bash
python scripts/live_demo.py
```

Hold a gesture and watch the predictions print in real time.

---

## Hardware checklist

1. Power on the MindRove armband (LED blinks)
2. Connect PC to armband WiFi (`MindRove_XXXX`)
3. Verify: `ping 192.168.4.1` should get replies
4. Run `mindrove_streamer.py` — it should report `Stream started OK`

---

## Troubleshooting

| Problem                                                 | What to check                                                                                                          |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Streamer says "no data"                                 | Is the armband WiFi connected? Is the LED on?                                                                          |
| 100% training accuracy but live demo predicts one class | DC offset mismatch — make sure the notebook has the `mean(axis=2)` subtraction line. Run `diagnose_data.py` to verify. |
| Low accuracy (<70%)                                     | Check `inspect_data.py` plots. Are gestures visually different? Re-record with firmer contractions.                    |
| Live demo lags                                          | Reduce `PREDICT_EVERY_N_SAMPLES` in `live_demo.py`                                                                     |

For extending the pipeline (adding gestures, changing classifiers, using different features), see **[GUIDE.md](GUIDE.md)**.
