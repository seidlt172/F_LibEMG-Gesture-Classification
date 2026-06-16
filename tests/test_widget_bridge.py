import json
import unittest
import urllib.error
from unittest.mock import patch

from Middleware.input_events import create_gesture_event
from Middleware.input_events import create_voice_event
from Middleware.widget_bridge import WidgetBridgeClient
from Middleware.widget_bridge import build_widget_payload
from Middleware.widget_bridge import build_scenario_start_payload
from Middleware.widget_bridge import build_trial_completed_payload
from Middleware.widget_bridge import decision_for_step
from Middleware.widget_bridge import decision_from_intent_result
from Middleware.widget_bridge import legacy_status_from_decision
from scripts.study_flow import get_scenario


class FakeResponse:
    status = 202

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return b""


class WidgetBridgeTests(unittest.TestCase):
    def test_intent_result_maps_to_widget_decisions(self):
        self.assertEqual(
            decision_from_intent_result({"intent": "accept_call", "action": "accept"}),
            "execute",
        )
        self.assertEqual(
            decision_from_intent_result({"intent": "reject_route", "action": "reject"}),
            "cancel",
        )
        self.assertEqual(
            decision_from_intent_result({"intent": "unknown", "action": "accept"}),
            "clarify",
        )
        self.assertEqual(
            decision_from_intent_result({"intent": "end_call", "action": "close", "target": "call"}),
            "execute",
        )

    def test_legacy_status_aliases_are_available(self):
        self.assertEqual(legacy_status_from_decision("execute"), "accepted")
        self.assertEqual(legacy_status_from_decision("cancel"), "rejected")
        self.assertEqual(legacy_status_from_decision("clarify"), "unclear")

    def test_payload_contains_original_input_sources(self):
        voice = create_voice_event("Mach lauter")
        gesture = create_gesture_event("Handgelenk drehen", source="emg", confidence=0.77)
        payload = build_widget_payload(
            intent_result={
                "intent": "adjust_volume",
                "action": "increase",
                "target": "volume",
                "value": "louder",
                "used_modalities": "voice+gesture",
            },
            study_context={
                "condition": "CAN use both",
                "category": "Confirm+Modify",
                "scenario_id": "MM-CM",
                "study_ref": "4.3",
                "scenario_prompt": "Accept call and regulate volume.",
            },
            voice_event=voice,
            gesture_event=gesture,
            step_index=1,
        )

        self.assertEqual(payload["decision"], "execute")
        self.assertEqual(payload["status"], "accepted")
        self.assertEqual(payload["study_ref"], "4.3")
        self.assertEqual(payload["domain"], "audio")
        self.assertEqual(payload["source"]["voice_event"], voice)
        self.assertEqual(payload["source"]["gesture_event"], gesture)

    def test_scenario_start_payload_loads_widget_without_decision(self):
        scenario = get_scenario("4.3")
        step = scenario.flow_steps[0]
        payload = build_scenario_start_payload(
            study_context={
                "condition": "CAN use both",
                "category": "Confirm+Modify",
                "scenario_id": "MM-CM",
                "study_ref": "4.3",
                "scenario_prompt": "Accept call and regulate volume.",
            },
            step=step,
            step_index=0,
            step_count=len(scenario.flow_steps),
            trial_id="P001-T001",
        )

        self.assertEqual(payload["event_type"], "scenario_start")
        self.assertEqual(payload["trial_id"], "P001-T001")
        self.assertEqual(payload["study_ref"], "4.3")
        self.assertEqual(payload["step_index"], 0)
        self.assertEqual(payload["step_count"], 2)
        self.assertEqual(payload["task_id"], "CALL-INCOMING")
        self.assertEqual(payload["expected_voice"], "Annehmen")
        self.assertEqual(payload["expected_gesture"], "Daumen hoch")
        self.assertNotIn("decision", payload)

    def test_step_update_payload_contains_active_step_context(self):
        scenario = get_scenario("1.1")
        step = scenario.flow_steps[1]
        payload = build_widget_payload(
            intent_result={
                "intent": "accept_call",
                "action": "accept",
                "target": "call",
            },
            study_context={
                "condition": "Voice only",
                "category": "Accept/Reject",
                "scenario_id": "VO-AR",
                "study_ref": "1.1",
                "scenario_prompt": "Accept call and end it.",
            },
            step=step,
            step_index=1,
            step_count=3,
            trial_id="P001-T001",
            decision_override="execute",
        )

        self.assertEqual(payload["event_type"], "step_update")
        self.assertEqual(payload["trial_id"], "P001-T001")
        self.assertEqual(payload["step_index"], 1)
        self.assertEqual(payload["step_count"], 3)
        self.assertEqual(payload["task_id"], "CALL-ACTIVE")
        self.assertEqual(payload["domain"], "calls")
        self.assertEqual(payload["prompt"], "Call läuft.")
        self.assertEqual(payload["expected_voice"], "Beenden")

    def test_trial_completed_payload_keeps_final_step_and_decision(self):
        scenario = get_scenario("1.1")
        step = scenario.flow_steps[2]
        payload = build_trial_completed_payload(
            intent_result={
                "intent": "end_call",
                "action": "close",
                "target": "call",
            },
            study_context={
                "condition": "Voice only",
                "category": "Accept/Reject",
                "scenario_id": "VO-AR",
                "study_ref": "1.1",
                "scenario_prompt": "Accept call and end it.",
            },
            step=step,
            step_index=2,
            step_count=3,
            trial_id="P001-T001",
            success=True,
        )

        self.assertEqual(payload["event_type"], "trial_completed")
        self.assertEqual(payload["decision"], "execute")
        self.assertTrue(payload["success"])
        self.assertEqual(payload["task_id"], "CALL-ENDED")

    def test_step_specific_decision_treats_call_states_separately(self):
        self.assertEqual(
            decision_for_step(
                "CALL-INCOMING",
                "cancel",
                {"intent": "accept_call", "action": "accept", "target": "call"},
            ),
            "execute",
        )
        self.assertEqual(
            decision_for_step(
                "CALL-INCOMING",
                "execute",
                {"intent": "reject_call", "action": "reject", "target": "call"},
            ),
            "cancel",
        )
        self.assertEqual(
            decision_for_step(
                "CALL-ACTIVE",
                "cancel",
                {"intent": "end_call", "action": "close", "target": "call"},
            ),
            "execute",
        )
        self.assertEqual(
            decision_for_step(
                "CALL-ENDED",
                "cancel",
                {"intent": "reject_call", "action": "reject", "target": "call"},
            ),
            "execute",
        )

    def test_client_posts_json_payload(self):
        client = WidgetBridgeClient(url="http://127.0.0.1:8765/widget-event", timeout=1)
        payload = {"decision": "execute", "study_ref": "1.1"}
        with patch(
            "Middleware.widget_bridge.urllib.request.urlopen",
            return_value=FakeResponse(),
        ) as urlopen:
            result = client.send(payload)

        self.assertTrue(result.sent)
        request = urlopen.call_args.args[0]
        self.assertEqual(json.loads(request.data.decode("utf-8")), payload)
        self.assertEqual(request.full_url, "http://127.0.0.1:8765/widget-event")

    def test_client_handles_unreachable_widget(self):
        client = WidgetBridgeClient(url="http://127.0.0.1:8765/widget-event", timeout=0.1)
        with patch(
            "Middleware.widget_bridge.urllib.request.urlopen",
            side_effect=urllib.error.URLError("refused"),
        ):
            result = client.send({"decision": "execute"})

        self.assertFalse(result.sent)
        self.assertTrue(result.error)


if __name__ == "__main__":
    unittest.main()
