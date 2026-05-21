# Car Widgets Prototype

Participant-facing in-car interface for the EMG + voice pilot study.

Start:

```bash
python -m car_widgets.app
```

The existing `gesture_gui.py` remains the researcher/operator interface. This
package is the visible cockpit UI for participants. Widgets do not talk to EMG,
Whisper, or Ollama directly; they consume normalized middleware decisions.

## Study Flows

`scenarios.py` contains two layers:

- `TASK_CATALOG`: cockpit/widget tasks from the domain sketch.
- `SCENARIOS`: the 12 comparable study flows from the condition sketch.

Each study flow has a reference such as `1.1`, a fixed condition, a category,
and ordered flow steps. The 9-scenario fallback is represented by
`fallback_9=True` and removes category 4.

Each step stores the expected input:

- `voice_input` for voice-only or multimodal steps.
- `gesture_label` and `gesture_ref` for gesture-only or multimodal steps.
- `expected_status`, usually `execute`, with `cancel` for explicit rejection
  tasks such as route rejection.

## Payload Schema

Widgets react to normalized middleware decisions:

```python
{
    "decision": "execute|cancel|clarify",
    "condition": "Voice only|Gesture only|CAN use both",
    "scenario_id": "STUDY-1.3",
    "study_ref": "1.3",
    "domain": "calls|audio|messages|navigation|ambient_light|climate",
    "status": "accepted|rejected|unclear",  # legacy compatibility alias
    "intent": "accept_route",
    "action": "accept",
    "target": "route",
    "value": None,
    "clarification": "",
    "source": {
        "voice_event": {"source": "whisper", "modality": "voice", "...": "..."},
        "gesture_event": {"source": "emg", "modality": "gesture", "...": "..."},
        "used_modalities": "voice+gesture",
    },
}
```

`execute` or `cancel` completes the current flow step and advances to the
next step. `clarify` keeps the current step active and opens a clarification
feedback loop.

For compatibility, `accepted`, `rejected`, and `unclear` are still accepted and
mapped to `execute`, `cancel`, and `clarify`.

## Local Middleware Bridge

When this app is running, it listens for middleware decisions on:

```text
http://127.0.0.1:8765/widget-event
```

The operator GUI sends the normalized widget payload there after every intent
evaluation. Configure the sender with:

```bash
export WIDGET_BRIDGE_URL=http://127.0.0.1:8765/widget-event
export WIDGET_BRIDGE_TIMEOUT_SECONDS=2
```

The same payload schema is intended for the later React + TypeScript widgets.
React should remain participant-facing only and should not connect directly to
the EMG source or Ollama.

## Design Notes

The visual design is intentionally provisional. Replace colors, spacing, and
fonts in `theme.py`, then adapt widget composition in `components.py` and
`app.py` after the Figma design is ready.
