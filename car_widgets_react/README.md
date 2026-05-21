# React Car Widgets

Participant-facing React + TypeScript cockpit UI.

The React app does not talk to EMG, Whisper, or Ollama. It polls the local
middleware event server and consumes the same normalized widget payloads as the
Python reference client.

## Start

Terminal 1:

```bash
python -m Middleware.widget_event_server
```

Terminal 2:

```bash
cd car_widgets_react
npm install
npm run dev
```

Terminal 3:

```bash
python gesture_gui.py
```

The operator GUI posts payloads to:

```text
http://127.0.0.1:8765/widget-event
```

The React app polls:

```text
http://127.0.0.1:8765/latest
```

`Middleware.widget_event_server` is the only local widget receiver. The old
Python widget client has been removed.

## Before Testing

1. Start the browser event server:

```bash
python -m Middleware.widget_event_server
```

2. Start the React cockpit:

```bash
cd car_widgets_react
npm install
npm run dev
```

3. Start the operator GUI from the repository root:

```bash
python gesture_gui.py
```

4. In the operator GUI, start a trial first. The GUI sends a
`scenario_start` event so the cockpit resets to the correct scenario before
the first intent decision arrives.

5. Then use voice, EMG, or Wizard input depending on the active condition and
click `Intent auswerten`.

During a multi-step scenario, every successful `Intent auswerten` advances the
React cockpit to the next step because the operator GUI sends a `step_update`
event. After the final step, the cockpit receives `trial_completed` and waits
for the next `scenario_start` event. The operator manually chooses the next
scenario and clicks `Trial starten` again.

If port `8765` is already occupied but you need to keep another receiver
running, use a separate port consistently:

```bash
WIDGET_EVENT_PORT=8766 python -m Middleware.widget_event_server
WIDGET_BRIDGE_URL=http://127.0.0.1:8766/widget-event python gesture_gui.py
VITE_WIDGET_EVENT_URL=http://127.0.0.1:8766/latest npm run dev
```

## Current State

This is the first React scaffold. It already shows all six cockpit domains at
once:

- Anrufe
- Navigation
- Audio
- Nachrichten
- Ambientebeleuchtung
- Klima

The UI reacts to explicit middleware events:

- `scenario_start`: load the selected scenario and first step
- `step_update`: render the next active step or a clarification
- `trial_completed`: show the completed state and wait for the next trial

React does not contain the study scenario table anymore. It renders the active
step data sent by the middleware so the Python operator GUI stays the source of
truth. Design details can be replaced later with the Figma version without
changing the middleware contract.

The layout is responsive:

- wide cockpit displays: six tiles in a 3 x 2 grid
- tablet or narrow windows: six tiles in a 2 x 3 grid
- phone-sized windows: single-column scrolling layout
