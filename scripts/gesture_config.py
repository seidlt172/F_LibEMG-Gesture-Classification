"""
Shared gesture vocabulary for the EMG pipeline.

Keep gesture IDs stable: collected data, trained models, live prediction, and
study documentation all rely on these class numbers.
"""

GESTURE_NAMES = {
    0: "Rest",
    1: "Daumen hoch",
    2: "Swipe",
    3: "Handgelenk drehen",
    4: "Zeigen/Tippen",
}

GESTURE_DISPLAY_NAMES = {
    **GESTURE_NAMES,
    4: "Zeigen / Tippen",
}

GESTURE_COLLECTION_CUES = {
    0: "alle Finger locker eingeklappt, Hand entspannt am Lenkrad",
    1: "Faust schließen, nur Daumen gestreckt nach oben",
    2: "alle Finger zusammen, Handgelenk zügig seitlich schwenken",
    3: "Unterarm rotieren (Pro/Supination), Finger locker gestreckt",
    4: "nur Zeigefinger gestreckt, restliche Finger eingekrallt",
}

COLLECTION_GESTURES = {
    gid: f"{GESTURE_DISPLAY_NAMES[gid]:<17} ({GESTURE_COLLECTION_CUES[gid]})"
    for gid in GESTURE_NAMES
}

GESTURE_DESCRIPTIONS = {
    0: "Alle Finger locker eingeklappt,\nHand entspannt am Lenkrad",
    1: "Faust schließen,\nnur Daumen gestreckt nach oben",
    2: "Alle Finger zusammen,\nHandgelenk zügig seitlich schwenken",
    3: "Unterarm rotieren (Pro/Supination),\nFinger locker gestreckt",
    4: "Nur Zeigefinger gestreckt,\nrestliche Finger eingekrallt",
}

LIVE_GESTURE_NAMES = {
    0: "Rest            (keine Aktion)",
    1: "Annehmen        (Daumen hoch)",
    2: "Ablehnen/Nav    (Swipe)",
    3: "Regulieren      (Handgelenk drehen)",
    4: "Zeigen/Tippen   (nur Zeigefinger gestreckt, restliche Finger eingekrallt)",
}

MANUAL_GESTURE_IDS = tuple(gid for gid in GESTURE_NAMES if gid != 0)
