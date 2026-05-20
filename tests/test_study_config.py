import unittest

from scripts.study_config import build_intent_context
from scripts.study_config import filter_intent_inputs_for_condition
from scripts.study_config import gesture_recognition_metadata
from scripts.study_config import get_scenario
from scripts.study_config import infer_multimodal_usage_pattern


class StudyConfigTests(unittest.TestCase):
    def test_unknown_is_not_sent_as_gesture_input(self):
        result = filter_intent_inputs_for_condition(
            condition="CAN use both",
            transcript="mach das",
            gesture="Unknown",
            gesture_source="manual",
        )

        self.assertEqual(result["gesture"], "")
        self.assertEqual(result["gesture_source"], "none")

    def test_manual_gesture_is_wizard_intervention(self):
        metadata = gesture_recognition_metadata(
            gesture_label="Swipe",
            source="manual",
            confidence=None,
        )

        self.assertEqual(metadata["gesture_label"], "Swipe")
        self.assertEqual(metadata["gesture_source"], "manual")
        self.assertEqual(metadata["recognition_outcome"], "Wizard intervention")
        self.assertTrue(metadata["wizard_intervention"])

    def test_emg_gesture_is_not_wizard_intervention(self):
        metadata = gesture_recognition_metadata(
            gesture_label="Daumen hoch",
            source="EMG",
            confidence=0.82,
        )

        self.assertEqual(metadata["gesture_source"], "EMG")
        self.assertEqual(metadata["recognition_outcome"], "correct")
        self.assertFalse(metadata["wizard_intervention"])

    def test_voice_only_ignores_gesture_for_intent(self):
        result = filter_intent_inputs_for_condition(
            condition="Voice only",
            transcript="Lautstaerke hoeher",
            gesture="Swipe",
            gesture_source="manual",
        )

        self.assertEqual(result["transcript"], "Lautstaerke hoeher")
        self.assertEqual(result["gesture"], "")
        self.assertTrue(result["ignored_gesture"])

    def test_gesture_only_ignores_transcript_for_intent(self):
        result = filter_intent_inputs_for_condition(
            condition="Gesture only",
            transcript="Lautstaerke hoeher",
            gesture="Handgelenk drehen",
            gesture_source="EMG",
        )

        self.assertEqual(result["transcript"], "")
        self.assertEqual(result["gesture"], "Handgelenk drehen")
        self.assertTrue(result["ignored_voice"])

    def test_scenario_context_contains_study_fields(self):
        scenario = get_scenario("CAN use both", "Browse+Select")
        context = build_intent_context(
            base_context="Cockpit.",
            condition="CAN use both",
            category="Browse+Select",
            scenario_id=scenario["scenario_id"],
            scenario_prompt=scenario["prompt"],
            gesture_source="manual",
            operator_gesture="Swipe",
        )

        self.assertIn("MM-BS", context)
        self.assertIn("Browse+Select", context)
        self.assertIn("Operator/Wizard gesture annotation: Swipe", context)

    def test_multimodal_usage_pattern(self):
        pattern = infer_multimodal_usage_pattern(
            "CAN use both",
            "nimm die route",
            "Daumen hoch",
        )

        self.assertEqual(pattern, "voice->gesture")


if __name__ == "__main__":
    unittest.main()
