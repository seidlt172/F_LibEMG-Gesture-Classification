import unittest
from collections import Counter

from car_widgets.feedback import apply_feedback
from car_widgets.feedback import build_payload
from car_widgets.feedback import coerce_decision
from car_widgets.feedback import decision_from_intent_result
from car_widgets.scenarios import SCENARIOS
from car_widgets.scenarios import TASK_CATALOG
from car_widgets.scenarios import fallback_scenarios
from car_widgets.scenarios import get_condition_guidance
from car_widgets.state import create_initial_state
from car_widgets.state import load_scenario


class CarWidgetTests(unittest.TestCase):
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
                self.assertTrue(step.voice_input or step.gesture_label)
                self.assertTrue(step.accepted_text)
                self.assertTrue(step.unclear_text)

    def test_task_catalog_covers_first_sketch_cards(self):
        required_task_ids = {
            "CALL-INCOMING",
            "CALL-END",
            "CALL-VOLUME",
            "AUDIO-SUGGESTION",
            "AUDIO-NEXT",
            "AUDIO-LOUDER",
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

    def test_load_scenario_sets_first_step(self):
        state = create_initial_state()
        scenario = next(s for s in SCENARIOS if s.study_ref == "3.2")

        load_scenario(state, scenario)

        self.assertEqual(state.active_domain, "navigation")
        self.assertEqual(state.condition, "Gesture only")
        self.assertEqual(state.current_step_index, 0)
        self.assertTrue(state.overlay_visible)
        self.assertEqual(state.current_step().task_id, "NAV-NEXT-ROUTE")

    def test_execute_advances_to_next_step(self):
        state = create_initial_state()
        scenario = next(s for s in SCENARIOS if s.study_ref == "1.1")
        load_scenario(state, scenario)
        payload = build_payload(condition=scenario.condition, scenario=scenario, decision="execute")

        apply_feedback(state, payload)

        self.assertEqual(state.feedback_status, "execute")
        self.assertEqual(state.current_step_index, 1)
        self.assertEqual(state.current_step().task_id, "CALL-END")
        self.assertTrue(state.overlay_visible)

    def test_cancel_advances_to_next_step_when_step_expects_rejection(self):
        state = create_initial_state()
        scenario = next(s for s in SCENARIOS if s.study_ref == "1.3")
        load_scenario(state, scenario)
        apply_feedback(state, build_payload(condition=scenario.condition, scenario=scenario, decision="execute"))

        apply_feedback(state, build_payload(condition=scenario.condition, scenario=scenario, decision="cancel"))

        self.assertEqual(state.feedback_status, "cancel")
        self.assertTrue(state.scenario_complete)
        self.assertFalse(state.route_suggestion_visible)

    def test_clarify_keeps_same_step(self):
        state = create_initial_state()
        scenario = next(s for s in SCENARIOS if s.study_ref == "4.3")
        load_scenario(state, scenario)
        payload = build_payload(condition=scenario.condition, scenario=scenario, decision="clarify")

        apply_feedback(state, payload)

        self.assertEqual(state.feedback_status, "clarify")
        self.assertEqual(state.current_step_index, 0)
        self.assertTrue(state.overlay_visible)
        self.assertIn("Anruf", state.clarification_text)

    def test_intent_result_maps_to_three_widget_decisions(self):
        self.assertEqual(
            decision_from_intent_result({"action": "accept", "intent": "accept_call"}),
            "execute",
        )
        self.assertEqual(
            decision_from_intent_result({"action": "reject", "intent": "reject_call"}),
            "cancel",
        )
        self.assertEqual(
            decision_from_intent_result({"action": "close", "intent": "close_message"}),
            "execute",
        )
        self.assertEqual(
            decision_from_intent_result({"action": "accept", "intent": "unknown"}),
            "clarify",
        )

    def test_legacy_status_aliases_still_work(self):
        self.assertEqual(coerce_decision("accepted"), "execute")
        self.assertEqual(coerce_decision("rejected"), "cancel")
        self.assertEqual(coerce_decision("unclear"), "clarify")


if __name__ == "__main__":
    unittest.main()
