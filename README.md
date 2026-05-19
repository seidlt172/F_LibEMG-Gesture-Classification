# EMG + Voice In-Car Interaction Prototype

Research prototype for real-time EMG micro-gesture recognition and voice input in an automotive interaction context. The system uses a MindRove armband for EMG input, LibEMG for feature extraction/classification, local Whisper transcription for speech input, and local Ollama-based intent parsing.

The user-facing GUI command is:

```bash
python gesture_gui.py
```

The implementation lives in `scripts/gesture_gui.py`, but normal users do not need to call that path directly.

The pilot study design remains separate in [STUDY_DESIGN.md](STUDY_DESIGN.md).

## What The Prototype Does

- Streams EMG data from the MindRove armband over local UDP.
- Records, inspects, and calibrates five EMG micro-gesture classes.
- Trains a LibEMG classifier for live gesture prediction.
- Records microphone input and transcribes German speech with local Whisper.
- Combines the latest transcript and confirmed gesture through a local Ollama intent parser.
- Provides manual gesture buttons for fallback/Wizard-of-Oz support during pilot sessions.

## Current Gesture Vocabulary

Gesture IDs are defined centrally in `scripts/gesture_config.py`. Keep these IDs stable because collected data, trained models, live prediction, and the study design depend on them.

| ID | Gesture | Intended use |
| --- | --- | --- |
| 0 | Rest | no action / neutral state |
| 1 | Daumen hoch | accept, confirm, start |
| 2 | Swipe | reject, dismiss, skip, next option |
| 3 | Handgelenk drehen | adjust continuous values such as volume, brightness, or heating |
| 4 | Zeigen / Tippen | select, point, tap |

When changing the gesture vocabulary:

1. Update `scripts/gesture_config.py`.
2. Re-record or migrate `data/raw/gesture_<id>/` if IDs changed.
3. Retrain the model with `scripts/calibrate.py` or `notebooks/04_train.ipynb`.
4. Update `STUDY_DESIGN.md` if the study vocabulary changes.

## Repository Structure

```text
.
├── scripts/
│   ├── gesture_config.py      # shared gesture names and cues
│   ├── mindrove_streamer.py   # MindRove armband to local UDP stream
│   ├── collect_data.py        # guided EMG recording
│   ├── calibrate.py           # GUI calibration and model retraining
│   ├── inspect_data.py        # signal-quality plots
│   ├── diagnose_data.py       # data/model troubleshooting
│   ├── diagnose_audio.py      # microphone/PyAudio troubleshooting
│   ├── live_demo.py           # terminal EMG prediction demo
│   └── gesture_gui.py         # multimodal GUI implementation
├── Middleware/
│   ├── audio_recorder.py      # microphone recording
│   ├── intent_manager.py      # local Ollama intent parser
│   ├── speech_transcriber.py  # local Whisper transcription
│   └── network_client.py      # legacy socket helper
├── notebooks/
│   └── 04_train.ipynb         # offline training workflow
├── data/
│   ├── raw/                   # collected training data
│   ├── calibration/           # calibration recordings
│   ├── inspect/               # generated signal plots
│   └── sample/                # placeholder for optional sample data
├── models/                    # trained classifier output
├── tests/                     # intent-manager tests
├── gesture_gui.py             # user-facing GUI launcher
├── STUDY_DESIGN.md            # pilot study design
└── requirements.txt
```

## Requirements

Recommended runtime:

- macOS on Apple Silicon with 16GB+ RAM
- Python 3.11 or 3.12
- MindRove armband for live EMG input
- FFmpeg for Whisper audio decoding
- PortAudio/PyAudio for microphone access
- Tkinter for the calibration and multimodal GUIs
- Ollama for local LLM intent parsing

The project does not require a cloud LLM API key.

## macOS Setup

Install system dependencies with Homebrew:

```bash
brew install python@3.12 ffmpeg portaudio ollama
```

The GUIs use Tkinter. If your Homebrew Python does not include it, install the matching Tk package:

```bash
brew install python-tk@3.12
```

If command-line build tools are missing:

```bash
xcode-select --install
```

Create and activate the virtual environment from the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If `PyAudio` fails with `portaudio.h file not found`, reinstall it with explicit Homebrew paths:

```bash
CPPFLAGS="-I$(brew --prefix portaudio)/include" LDFLAGS="-L$(brew --prefix portaudio)/lib" python -m pip install PyAudio
```

## Local Ollama Intent Parsing

Pull the default local model:

```bash
ollama pull qwen3.5:4b
```

Quick test:

```bash
ollama run qwen3.5:4b --think=false
```

Optional quality upgrade for faster Macs:

```bash
ollama pull qwen3.5:9b
export OLLAMA_MODEL=qwen3.5:9b
```

Ollama normally runs in the background when the macOS app is open. If the GUI reports that Ollama is not reachable, start it manually in a separate terminal:

```bash
ollama serve
```

Default runtime configuration:

```bash
OLLAMA_MODEL=qwen3.5:4b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT_SECONDS=120
```

The app disables Qwen thinking mode for intent parsing and caps the response length. The first intent request can still take longer because Ollama may need to load the model into memory. The app keeps the model warm for later requests. If the first request still times out, use the smaller `qwen3.5:2b` model:

```bash
ollama pull qwen3.5:2b
export OLLAMA_MODEL=qwen3.5:2b
```

`Middleware/intent_manager.py` is intentionally constrained to structured intent parsing, not free-form chatbot behavior. It sends the latest Whisper transcript, the last confirmed EMG gesture, and a short cockpit context to Ollama. The normalized result contains:

| Field | Meaning |
| --- | --- |
| `intent` | structured in-car intent such as `accept_call`, `adjust_volume`, `select_route`, or `unknown` |
| `action` | normalized action such as `accept`, `reject`, `increase`, `select`, or `unknown` |
| `target` | target domain such as `call`, `route`, `volume`, `ambient_light`, or `media` |
| `value` | optional value such as `louder`, `brighter`, `blue`, or `next` |
| `needs_clarification` | whether the system should ask the user to clarify |
| `clarification` | short German clarification question if needed |
| `used_modalities` | `voice`, `gesture`, `voice+gesture`, or `none` |
| `llm_confidence_estimate` | LLM estimate only; not recognition ground truth |

The LLM output is an interpretation layer for the prototype and should not be treated as recognition ground truth in study data.

## Quick Start

1. Connect the Mac to the MindRove WiFi network, usually named `MindRove_XXXX`.
2. Optional connectivity check:

```bash
ping 192.168.4.1
```

Stop the ping with `Ctrl+C`.

3. Start the EMG streamer in one terminal and keep it open:

```bash
source .venv/bin/activate
python scripts/mindrove_streamer.py
```

4. Calibrate for the current user/session in a second terminal:

```bash
source .venv/bin/activate
python scripts/calibrate.py
```

This records the configured gestures and saves a classifier under `models/`.

5. Start the multimodal GUI:

```bash
source .venv/bin/activate
python gesture_gui.py
```

The first GUI start can take longer because Whisper may download and load the local speech model. macOS may ask for microphone permission; allow it for the terminal app you are using.

Use `Intent auswerten` in the GUI after recording speech and/or confirming a gesture. This calls the local Ollama model and shows a structured in-car intent.

## Maintained Commands

| Purpose | Command |
| --- | --- |
| MindRove UDP bridge | `python scripts/mindrove_streamer.py` |
| Guided data collection | `python scripts/collect_data.py` |
| GUI calibration and retraining | `python scripts/calibrate.py` |
| Signal inspection | `python scripts/inspect_data.py` |
| Data/model diagnosis | `python scripts/diagnose_data.py` |
| Microphone diagnosis | `python scripts/diagnose_audio.py` |
| Terminal live prediction | `python scripts/live_demo.py` |
| Multimodal EMG + voice GUI | `python gesture_gui.py` |

## Data And Training Workflow

Collected recordings are stored as CSV files:

```text
data/raw/
├── gesture_0/
│   ├── rep_0.csv
│   └── ...
├── gesture_1/
└── ...
```

Each CSV contains 8 MindRove EMG channels sampled at 500 Hz. `data/calibration/` is used by the calibration workflow, and `data/inspect/` contains generated plots.

For the offline workflow:

```bash
python scripts/collect_data.py
python scripts/inspect_data.py
jupyter lab notebooks/04_train.ipynb
```

`data/sample/` is currently a placeholder only. It does not contain sample gesture CSVs in this repository.

## Multimodal GUI

The GUI launched by `python gesture_gui.py` combines:

- live EMG prediction from the MindRove UDP stream
- manual gesture confirmation buttons for fallback/Wizard support
- microphone recording through PyAudio
- local German speech transcription through Whisper
- local Ollama intent parsing for voice + gesture

The GUI expects a trained model under `models/clf` and a running streamer on UDP port `12345`. Battery updates are read from UDP port `12346` when available.

The root-level `gesture_gui.py` is the maintained user-facing launcher. Treat `scripts/gesture_gui.py` as an internal implementation detail.

## Tests And Checks

Run the current unit tests:

```bash
python -m unittest discover -s tests
```

Useful local checks:

```bash
python scripts/diagnose_audio.py
python scripts/diagnose_data.py
python scripts/live_demo.py
```

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `portaudio.h` missing during `PyAudio` install | Install PortAudio first with `brew install portaudio`, then use the explicit `CPPFLAGS`/`LDFLAGS` install command above. |
| Whisper or audio transcription fails | Install FFmpeg and restart the terminal. |
| `_tkinter` is missing on macOS | Install `python-tk@3.12` with Homebrew or use a Python.org Python build. |
| Intent parsing says Ollama is not reachable | Start Ollama with the macOS app or run `ollama serve`; then pull `qwen3.5:4b`. |
| Intent parsing times out after the first click | The model may still be loading or thinking mode may be active outside the app. Test with `ollama run qwen3.5:4b --think=false`, retry once, or use `qwen3.5:2b`. |
| GUI starts slowly on first run | Whisper may be downloading/loading the local model. |
| Streamer reports no data | Check MindRove power, WiFi connection, and `ping 192.168.4.1`. |
| Live prediction always returns one class | Run `inspect_data.py` and `diagnose_data.py`; retrain with fresh calibration data. |
| `models/clf` is missing | Run `scripts/calibrate.py` or train with `notebooks/04_train.ipynb`. |
| Imports fail despite installed packages | Confirm that `.venv` is active and rerun `python -m pip install -r requirements.txt`. |

## Study Design

The research framing, pilot procedure, scenario table, Wizard-of-Oz protocol, and logging schema are documented separately in [STUDY_DESIGN.md](STUDY_DESIGN.md).
