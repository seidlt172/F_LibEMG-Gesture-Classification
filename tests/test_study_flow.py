import unittest
from collections import Counter

from scripts.study_flow import SCENARIOS
from scripts.study_flow import TASK_CATALOG
from scripts.study_flow import fallback_scenarios
from scripts.study_flow import get_condition_guidance
from scripts.study_flow import scenario_from_label
from scripts.study_flow import scenario_id_from_title
from scripts.study_flow import scenario_labels


class StudyFlowTests(unittest.TestCase):
    def test_condition_guidance_separates_voice_and_gesture(self):
        voice = get_condition_guidance("Voice only")
        gesture = get_condition_guidance("Gesture only")
        both = get_condition_guidance("CAN use both")

        self.assertTrue(voice["voice_examples"])
        self.assertFalse(voice["gestures"])
        self.assertFalse(gesture["voice_examples"])
        self.assertTrue(gesture["gestures"])
        self.assertTrue(both["voice_examples"])
        self.assertTrue(both["gestures"])

    def test_exactly_12_primary_study_scenarios_exist(self):
        self.assertEqual(len(SCENARIOS), 12)
        self.assertEqual({scenario.study_ref for scenario in SCENARIOS}, {
            "1.1", "1.2", "1.3",
            "2.1", "2.2", "2.3",
            "3.1", "3.2", "3.3",
            "4.1", "4.2", "4.3",
        })

    def test_9_scenario_fallback_removes_category_4(self):
        fallback = fallback_scenarios()

        self.assertEqual(len(fallback), 9)
        self.assertTrue(all(scenario.category_index <= 3 for scenario in fallback))

    def test_each_condition_has_four_scenarios(self):
        counts = Counter(scenario.condition for scenario in SCENARIOS)

        self.assertEqual(counts["Voice only"], 4)
        self.assertEqual(counts["Gesture only"], 4)
        self.assertEqual(counts["CAN use both"], 4)

    def test_each_category_has_three_scenarios(self):
        counts = Counter(scenario.category_index for scenario in SCENARIOS)

        self.assertEqual(counts, {1: 3, 2: 3, 3: 3, 4: 3})

    def test_every_scenario_has_at_least_two_complete_flow_steps(self):
        for scenario in SCENARIOS:
            self.assertGreaterEqual(len(scenario.flow_steps), 2)
            for step in scenario.flow_steps:
                self.assertTrue(step.task_id)
                self.assertTrue(step.domain)
                self.assertTrue(step.modality)
                self.assertIn(step.expected_status, {"execute", "cancel", "clarify"})
                if step.task_id != "CALL-ENDED":
                    self.assertTrue(step.voice_input or step.gesture_label)
                self.assertTrue(step.accepted_text)
                self.assertTrue(step.unclear_text)

    def test_task_catalog_covers_first_sketch_cards(self):
        required_task_ids = {
            "CALL-INCOMING",
            "CALL-ACTIVE",
            "CALL-ENDED",
            "CALL-VOLUME",
            "AUDIO-SUGGESTION",
            "AUDIO-NEXT",
            "AUDIO-VOLUME-UP",
            "AUDIO-RESUME",
            "MESSAGE-OPEN",
            "MESSAGE-CLOSE",
            "NAV-ACCEPT-ROUTE",
            "NAV-REJECT-ROUTE",
            "NAV-NEXT-ROUTE",
            "NAV-SELECT-SECOND",
            "NAV-VOLUME-UP",
            "AMBIENT-COLOR",
            "AMBIENT-BRIGHTER",
            "AMBIENT-NIGHTMODE",
            "CLIMATE-SEAT-HEAT",
            "CLIMATE-SEAT-WARMER",
        }

        self.assertTrue(required_task_ids.issubset(TASK_CATALOG.keys()))

    def test_scenario_labels_are_unique_and_cover_all_refs(self):
        labels = scenario_labels()

        self.assertEqual(len(labels), 12)
        self.assertEqual(len(set(labels)), 12)
        self.assertEqual(
            {scenario_id_from_title(label) for label in labels},
            {scenario.study_ref for scenario in SCENARIOS},
        )

    def test_audio_study_2_1_uses_volume_up_as_second_step(self):
        scenario = scenario_from_label(next(label for label in scenario_labels() if label.startswith("2.1 |")))

        self.assertEqual([step.task_id for step in scenario.flow_steps], ["AUDIO-NEXT", "AUDIO-VOLUME-UP"])

    def test_scenario_from_label_resolves_selected_scenario(self):
        label = next(label for label in scenario_labels() if label.startswith("4.3 |"))
        scenario = scenario_from_label(label)

        self.assertEqual(scenario.study_ref, "4.3")
        self.assertEqual(scenario.condition, "CAN use both")
        self.assertEqual(scenario.category_name, "Confirm+Modify")


if __name__ == "__main__":
    unittest.main()
