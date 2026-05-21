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
- Normalizes real EMG, voice, and Wizard fallback into middleware input events before intent parsing.
- Sends normalized widget decisions to the participant-facing cockpit interface.
- Provides operator-only manual gesture buttons for fallback/Wizard-of-Oz support during pilot sessions.

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
│   ├── study_flow.py          # central study scenario and step catalog
│   └── gesture_gui.py         # multimodal operator GUI implementation
├── car_widgets_react/         # participant-facing React cockpit interface
├── Middleware/
│   ├── audio_recorder.py      # microphone recording
│   ├── input_events.py        # normalized voice/gesture event schema
│   ├── intent_manager.py      # local Ollama intent parser
│   ├── widget_bridge.py       # normalized decisions for car widgets
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
├── tests/                     # unit tests
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

`Middleware/intent_manager.py` is intentionally constrained to structured intent parsing, not free-form chatbot behavior. It sends the latest Whisper transcript, the last confirmed EMG gesture, whether that gesture was manual or EMG-predicted, and the active study scenario context to Ollama. Clear voice commands are treated as the primary semantic signal; a conflicting gesture should not force `unknown`.

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

## Middleware-Centered Pipeline

The integration path is:

```text
EMG source or manual Wizard fallback
        -> Middleware input event normalization
        -> voice transcript + gesture event + study context
        -> local Ollama intent parser / rule fallback
        -> widget decision payload
        -> participant-facing car widgets
```

Future glove or lab EMG hardware should send normalized gesture events into the
middleware with `source=emg`. The current manual buttons remain useful for
operator fallback and Wizard-of-Oz recovery, but they are logged as
`source=manual` and must not be counted as participant EMG recognition.

Widgets do not connect directly to EMG, Whisper, or Ollama. They consume only
middleware decisions:

```json
{
  "decision": "execute",
  "action": "accept",
  "target": "call",
  "condition": "CAN use both",
  "study_ref": "4.3",
  "source": {
    "voice_event": "...",
    "gesture_event": "...",
    "used_modalities": "voice+gesture"
  }
}
```

`decision` describes what the widget should do with the current scenario step,
not the literal semantic action. For example, ending an active call is an
executed step (`decision=execute`) even if a recognizer describes the utterance
as rejecting or stopping a call. The semantic meaning remains in `intent`,
`action`, and `target`. The old `accepted`, `rejected`, and `unclear` labels are
still accepted as compatibility aliases for `execute`, `cancel`, and `clarify`.

### Existing EMG Flow

The live EMG connection is already part of the operator interface. When the
armband stream and trained comparison data/model are available, the current
predicted gesture is shown in the top-right gesture area instead of
`Warte auf Daten...`.

Clicking `Einloggen` confirms the currently displayed armband prediction as a
real EMG event. This creates a structured gesture event with `source=emg`,
`gesture_label`, `gesture_id`, `confidence`, `timestamp`, and
`recognition_outcome`. The intent pipeline uses that structured event through
`last_gesture_event` and the structured study log.

Do not parse visible terminal output or text log rows as middleware input. The
terminal and visible log are only debugging views. The operator/Wizard buttons
remain fallback controls and create `source=manual` events with
`wizard_intervention=true`.

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

Use `Intent auswerten` in the GUI after recording speech and/or confirming a gesture. This calls the local Ollama model and shows a structured in-car intent. In study mode, the active condition determines which inputs are interpreted: `Voice only` ignores gestures as participant input, `Gesture only` ignores speech as participant input, and `CAN use both` allows both.

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
- operator-only manual gesture buttons for fallback/Wizard support
- microphone recording through PyAudio
- local German speech transcription through Whisper
- local Ollama intent parsing for voice + gesture
- a pilot study operator panel for scenario selection, trial timing, and JSONL export

The GUI expects a trained model under `models/clf` and a running streamer on UDP port `12345`. Battery updates are read from UDP port `12346` when available.

The root-level `gesture_gui.py` is the maintained user-facing launcher. Treat `scripts/gesture_gui.py` as an internal implementation detail.

### Pilot Operator Workflow

The manual gesture buttons are for the study team, not for participants. Participants should interact through voice and/or EMG depending on the active condition. Operators use the manual buttons only to annotate or recover a trial when Wizard-of-Oz support is needed.

1. Select `participant_id`, `condition_order`, and the direct study scenario (`1.1` to `4.3`).
2. Click `Trial starten`; this resets the current transcript, gesture, and intent result and sends the first active step to the participant-facing widget.
3. Run the task. Confirm live EMG with `Einloggen`, record speech, or use the `OPERATOR / WIZARD` controls only as fallback.
4. Click `Intent auswerten` to parse the condition-filtered input with the current scenario and step context.
5. Each successful intent advances exactly one step inside the active scenario. A clarification keeps the same step active.
6. After the final step, the widget shows `trial_completed`; end the trial with `Erfolgreich beenden` or `Abbrechen`.
7. Export completed trials with `EXPORT JSONL`.

`No recognition` is logged as a recognition outcome, not as a gesture label. Manual gesture clicks are logged with `gesture_source=manual` and `wizard_intervention=true`; EMG-confirmed gestures are logged with `gesture_source=emg` and `wizard_intervention=false`.

## Participant-Facing React Widgets

The React + TypeScript cockpit frontend lives in `car_widgets_react/`.
It shows all six cockpit domains at once and consumes explicit middleware
events through a small local event server. React is a display client only:
scenario and step state come from the Python operator GUI.

```bash
python -m Middleware.widget_event_server
cd car_widgets_react
npm install
npm run dev
```

Then start the operator GUI in another terminal:

```bash
python gesture_gui.py
```

The old Python widget client has been removed; React is the only
participant-facing widget frontend.

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
