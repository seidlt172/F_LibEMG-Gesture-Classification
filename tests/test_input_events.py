import unittest

from Middleware.input_events import build_intent_inputs
from Middleware.input_events import create_gesture_event
from Middleware.input_events import create_voice_event


class InputEventTests(unittest.TestCase):
    def test_manual_and_emg_gesture_events_share_schema(self):
        manual = create_gesture_event("Swipe", source="manual")
        emg = create_gesture_event("Swipe", source="EMG", confidence=0.82)

        self.assertEqual(set(manual.keys()), set(emg.keys()))
        self.assertEqual(manual["source"], "manual")
        self.assertEqual(manual["recognition_outcome"], "wizard_intervention")
        self.assertEqual(emg["source"], "emg")
        self.assertEqual(emg["recognition_outcome"], "correct")
        self.assertEqual(emg["confidence"], 0.82)

    def test_unknown_gesture_is_not_actionable(self):
        event = create_gesture_event("Unknown", source="manual")

        self.assertIsNone(event["gesture_label"])
        self.assertEqual(event["recognition_outcome"], "no_recognition")

    def test_voice_only_keeps_voice_and_logs_but_ignores_gesture_for_intent(self):
        voice = create_voice_event("Route annehmen")
        gesture = create_gesture_event("Daumen hoch", source="emg", confidence=0.9)

        result = build_intent_inputs(
            condition="Voice only",
            voice_event=voice,
            gesture_event=gesture,
        )

        self.assertEqual(result["transcript"], "Route annehmen")
        self.assertEqual(result["gesture"], "")
        self.assertTrue(result["ignored_gesture"])
        self.assertEqual(result["gesture_event"], gesture)
        self.assertEqual(result["used_modalities"], "voice")

    def test_gesture_only_keeps_gesture_and_logs_but_ignores_voice_for_intent(self):
        voice = create_voice_event("Mach lauter")
        gesture = create_gesture_event("Handgelenk drehen", source="emg")

        result = build_intent_inputs(
            condition="Gesture only",
            voice_event=voice,
            gesture_event=gesture,
        )

        self.assertEqual(result["transcript"], "")
        self.assertEqual(result["gesture"], "Handgelenk drehen")
        self.assertTrue(result["ignored_voice"])
        self.assertEqual(result["voice_event"], voice)
        self.assertEqual(result["used_modalities"], "gesture")

    def test_can_use_both_passes_voice_and_gesture_to_intent(self):
        voice = create_voice_event("Nimm die Route")
        gesture = create_gesture_event("Daumen hoch", source="emg")

        result = build_intent_inputs(
            condition="CAN use both",
            voice_event=voice,
            gesture_event=gesture,
        )

        self.assertEqual(result["transcript"], "Nimm die Route")
        self.assertEqual(result["gesture"], "Daumen hoch")
        self.assertEqual(result["gesture_source"], "emg")
        self.assertEqual(result["used_modalities"], "voice+gesture")


if __name__ == "__main__":
    unittest.main()
