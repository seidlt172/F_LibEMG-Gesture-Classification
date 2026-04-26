"""
diagnose_data.py
================
Run this script to diagnose why classification may be failing.
It checks:
    1. DC offset levels across gestures
    2. Whether features are separable after DC removal
    3. Whether the model file matches the training preprocessing

Usage:
    python scripts/diagnose_data.py

No armband needed — works from saved CSVs.
"""

import os
import glob
import numpy as np
from libemg.feature_extractor import FeatureExtractor
from libemg.utils import get_windows

DATA_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'raw'))
GESTURES  = {0: 'Fist', 1: 'Open Hand', 2: 'Index Point'}

WINDOW_SIZE   = 200
WINDOW_INC    = 100
FEATURE_GROUP = 'HTD'

def load_gesture_data(gesture_id):
    folder = os.path.join(DATA_DIR, f'gesture_{gesture_id}')
    reps = []
    for fname in sorted(os.listdir(folder)):
        if fname.startswith('rep_') and fname.endswith('.csv'):
            arr = np.loadtxt(os.path.join(folder, fname), delimiter=',', skiprows=1)
            reps.append(arr)
    return reps

def main():
    print('=' * 60)
    print('  EMG Data Diagnostic')
    print('=' * 60)

    # ── Check 1: DC Offset Levels ──
    print('\n--- CHECK 1: DC offset levels per gesture ---')
    print('  (Large values here = DC offset present in raw data)\n')

    for gid, gname in GESTURES.items():
        reps = load_gesture_data(gid)
        all_data = np.vstack(reps)
        means = all_data.mean(axis=0)
        print(f'  Gesture {gid} ({gname}):')
        print(f'    Per-channel means: {np.array2string(means, precision=0, separator=", ")}')
        print(f'    Overall mean:      {means.mean():.0f}')
        print()

    # ── Check 2: Feature separability WITHOUT DC removal ──
    print('\n--- CHECK 2: Feature separability ---\n')

    fe = FeatureExtractor()

    for label, remove_dc in [('RAW (no DC removal)', False), ('DC REMOVED', True)]:
        print(f'  {label}:')
        all_features = []
        all_labels = []

        for gid in GESTURES:
            reps = load_gesture_data(gid)
            for arr in reps:
                wins = get_windows(arr, WINDOW_SIZE, WINDOW_INC)
                if remove_dc:
                    wins = wins - wins.mean(axis=2, keepdims=True)
                feats = fe.extract_feature_group(FEATURE_GROUP, wins)
                feat_mat = np.hstack(list(feats.values()))
                all_features.append(feat_mat)
                all_labels.extend([gid] * len(feat_mat))

        X = np.vstack(all_features)
        y = np.array(all_labels)

        # Print feature statistics per class
        for gid, gname in GESTURES.items():
            mask = (y == gid)
            class_feats = X[mask]
            print(f'    Gesture {gid} ({gname}): mean_feat[0]={class_feats[:, 0].mean():.2f}, '
                  f'std_feat[0]={class_feats[:, 0].std():.2f}, '
                  f'n_windows={mask.sum()}')

        # Quick LDA accuracy check
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
        from sklearn.model_selection import cross_val_score
        lda = LinearDiscriminantAnalysis()
        scores = cross_val_score(lda, X, y, cv=5, scoring='accuracy')
        print(f'    5-fold CV accuracy: {scores.mean()*100:.1f}% ± {scores.std()*100:.1f}%')

        # Check if all predictions collapse to one class
        lda.fit(X, y)
        preds = lda.predict(X)
        unique_preds = np.unique(preds)
        if len(unique_preds) == 1:
            print(f'    ⚠ WARNING: All predictions collapse to class {unique_preds[0]}!')
        else:
            print(f'    Predicted classes: {unique_preds} (good — multiple classes predicted)')

        print()

    # ── Check 3: Verify model file ──
    print('\n--- CHECK 3: Model file check ---\n')
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'clf')
    if os.path.exists(model_path):
        import pickle
        with open(model_path, 'rb') as f:
            clf = pickle.load(f)
        print(f'  Model file found: {model_path}')
        print(f'  Model type: {type(clf).__name__}')
        if hasattr(clf, 'model'):
            print(f'  Inner model: {type(clf.model).__name__}')
        # Try to get the model's expected number of features
        if hasattr(clf, 'model') and hasattr(clf.model, 'n_features_in_'):
            print(f'  Expected features: {clf.model.n_features_in_}')
    else:
        print(f'  ⚠ Model file NOT FOUND at {model_path}')
        print(f'  Run the training notebook first!')

    print('\n' + '=' * 60)
    print('  If CHECK 2 shows good accuracy with DC REMOVED but')
    print('  poor accuracy (or single-class predictions) with RAW,')
    print('  then DC offset removal is the fix you need.')
    print('  Re-run the training notebook with the fixed version.')
    print('=' * 60)


if __name__ == '__main__':
    main()
