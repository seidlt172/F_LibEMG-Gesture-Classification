# Extending the pipeline

This guide tells you **where to edit** and **what to read** when you want to modify the pipeline. Each section is a task; follow only the ones relevant to you.

---

## Adding a new gesture

You need to edit **two files** and re-run the training notebook.

**1. `scripts/collect_data.py`** — add an entry to the `GESTURES` dict (line ~37):

```python
GESTURES = {
    0: "Fist        (close ALL fingers firmly into a fist)",
    1: "Open Hand   (spread fingers wide, palm facing forward)",
    2: "Index Point (extend index finger only, curl the rest)",
    3: "Wrist Flexion (bend wrist downward, fingers relaxed)",  # ← new
}
```

The key (3) becomes the folder name (`gesture_3`) and the class label. The string is the prompt shown during collection.

**2. `scripts/live_demo.py`** — add the same ID to `GESTURE_NAMES` (line ~24):

```python
GESTURE_NAMES = {0: 'Fist', 1: 'Open Hand', 2: 'Index Point', 3: 'Wrist Flexion'}
```

**3. Re-run the notebook.** No changes needed there — it auto-discovers all `gesture_*` folders in `data/raw/`.

**Tips for choosing gestures:**
- Pick gestures that use different muscle groups (e.g. flexors vs extensors)
- Avoid gestures that feel similar when you hold them — if *you* can't tell them apart, the EMG won't either
- More gestures = more data needed. Collect at least 10 reps per gesture.

---

## Changing the classifier

Edit **one cell** in `notebooks/04_train.ipynb`.

In Cell 2 (Configuration), change the `CLASSIFIER` variable:

```python
CLASSIFIER = 'SVM'  # options: 'LDA', 'SVM', 'KNN', 'RF', 'MLP', 'QDA', 'NB'
```

You can also pass a custom scikit-learn model:

```python
from sklearn.ensemble import GradientBoostingClassifier
clf = EMGClassifier(GradientBoostingClassifier(n_estimators=100))
```

**LibEMG docs:** [EMG Prediction — Classifiers](https://libemg.github.io/libemg/documentation/prediction/prediction.html)

| Classifier | When to try it |
|---|---|
| `LDA` | Default. Fast, works well with small data. Start here. |
| `SVM` | When LDA accuracy is low. Handles non-linear boundaries. |
| `KNN` | Simple baseline. Sensitive to the number of training samples. |
| `RF` | Robust to noise, but can overfit with few reps. |

---

## Changing the feature set

Edit `FEATURE_GROUP` in both the notebook and `live_demo.py`. They **must match**.

```python
FEATURE_GROUP = 'LS9'  # options: 'HTD', 'LS9', 'TDPSD'
```

You can also extract individual features instead of a group:

```python
fe = FeatureExtractor()
features = fe.extract_features(['MAV', 'ZC', 'SSC', 'WL'], windows)
```

To see all available features and groups:

```python
fe = FeatureExtractor()
print(fe.get_feature_list())      # individual features
print(fe.get_feature_groups())    # predefined groups
```

**LibEMG docs:** [Feature Extraction](https://libemg.github.io/libemg/documentation/features/features.html)

**Key feature groups:**
- `HTD` — Hudgins time-domain (MAV, ZC, SSC, WL). Default, widely used, fast.
- `LS9` — 9 features designed for low-sampling-rate devices. Good for robustness.
- `TDPSD` — Time-domain power spectral descriptors. More features, sometimes better accuracy.

---

## Changing window parameters

The window size and increment control how the raw signal is segmented before feature extraction. Edit these in the notebook **and** `live_demo.py` — they must match.

```python
WINDOW_SIZE = 200   # samples (200 @ 500Hz = 400ms)
WINDOW_INC  = 100   # samples (100 @ 500Hz = 200ms) — only used in training
```

- Larger windows → more context, higher accuracy, but slower response
- Smaller windows → faster response, but noisier features
- Common range: 150–300 samples at 500 Hz

**LibEMG docs:** [Data Handler — parse_windows](https://libemg.github.io/libemg/emg_toolbox.html#libemg.data_handler.OfflineDataHandler.parse_windows)

---

## Understanding the preprocessing

The most important preprocessing step is **DC offset removal**. The MindRove armband outputs raw ADC values with large constant offsets (thousands of µV) that vary between recording sessions. If you don't remove them, the classifier learns session-specific offsets instead of gesture-specific muscle patterns.

The DC removal happens in two places and **must be identical**:

**Training** (`04_train.ipynb`, Cell 5 — Windowing):
```python
train_windows = train_windows - train_windows.mean(axis=2, keepdims=True)
```

**Live demo** (`live_demo.py`, prediction loop):
```python
window_arr = window_arr - window_arr.mean(axis=2, keepdims=True)
```

`axis=2` is the time axis in LibEMG's window format: `(n_windows, n_channels, window_size)`.

If you add any other preprocessing (filtering, normalization), it must be applied in both places.

**LibEMG docs:** [Filtering](https://libemg.github.io/libemg/documentation/filtering/filtering.html)

---

## Using LibEMG's built-in data handling (optional)

This pipeline uses manual CSV loading for simplicity. LibEMG has a more powerful `OfflineDataHandler` that can auto-discover files using regex patterns. If you want to use it:

```python
from libemg.data_handler import OfflineDataHandler, RegexFilter

odh = OfflineDataHandler()
odh.get_data(
    folder_location='data/raw/',
    regex_filters=[
        RegexFilter(left_bound='gesture_', right_bound='/', values=['0','1','2'], description='classes'),
        RegexFilter(left_bound='rep_', right_bound='.csv', values=[str(i) for i in range(10)], description='reps'),
    ],
    delimiter=',',
    skiprows=1
)
windows, metadata = odh.parse_windows(WINDOW_SIZE, WINDOW_INC)
```

**LibEMG docs:** [Data Handler — OfflineDataHandler](https://libemg.github.io/libemg/emg_toolbox.html#libemg.data_handler.OfflineDataHandler)

---

## Key LibEMG documentation links

| Topic | Link |
|---|---|
| Full API reference | [libemg.github.io/libemg/emg_toolbox.html](https://libemg.github.io/libemg/emg_toolbox.html) |
| Feature list and math | [Feature Extraction docs](https://libemg.github.io/libemg/documentation/features/features.html) |
| Classifier options | [EMG Prediction docs](https://libemg.github.io/libemg/documentation/prediction/prediction.html) |
| Filtering (bandpass, notch) | [Filtering docs](https://libemg.github.io/libemg/documentation/filtering/filtering.html) |
| Supported hardware | [Hardware docs](https://libemg.github.io/libemg/documentation/supported_hardware/supported_hardware.html) |
| Offline analysis example | [Simple Offline Example](https://libemg.github.io/libemg/examples/simple_offline_example/simple_offline_example.html) |
| Online control example | [Snake game example](https://libemg.github.io/libemg/examples/snake_example/snake_example.html) |
| Workshop walkthrough | [MEC24 Workshop repo](https://github.com/LibEMG/LibEMG_MEC24_Workshop) |
