# Sample data

This folder contains pre-recorded EMG data that you can use to test the pipeline without the MindRove armband.

## How to use

Copy the gesture folders from here into `data/raw/`:

```
# Windows
xcopy /E /I data\sample\gesture_0 data\raw\gesture_0
xcopy /E /I data\sample\gesture_1 data\raw\gesture_1
xcopy /E /I data\sample\gesture_2 data\raw\gesture_2

# macOS / Linux
cp -r data/sample/gesture_* data/raw/
```

Then continue from **Step 3** (inspect_data.py) in the main README.

## What's included

- `gesture_0/` — Fist (10 reps, 3 seconds each)
- `gesture_1/` — Open Hand (10 reps, 3 seconds each)
- `gesture_2/` — Index Point (10 reps, 3 seconds each)

Each CSV has 8 columns (ch0–ch7) corresponding to the 8 EMG channels on the MindRove armband, sampled at 500 Hz.

## Important

This data was recorded from a single person with a specific armband placement. Your own recordings will differ — that's expected. The sample data is only meant to verify that the pipeline runs correctly, not as a substitute for your own data collection.
