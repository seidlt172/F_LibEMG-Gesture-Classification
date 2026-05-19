# Sample Data

This directory is reserved for optional example EMG recordings, but this repository currently does not include sample gesture CSV files.

Use your own MindRove recordings for the maintained workflow:

```bash
python scripts/mindrove_streamer.py
python scripts/collect_data.py
python scripts/inspect_data.py
```

If sample data is added later, it should follow the same layout as `data/raw/`:

```text
data/sample/
├── gesture_0/
│   ├── rep_0.csv
│   └── ...
├── gesture_1/
└── ...
```

Each CSV should contain 8 EMG channels from the MindRove armband. Gesture IDs must match `scripts/gesture_config.py`.
