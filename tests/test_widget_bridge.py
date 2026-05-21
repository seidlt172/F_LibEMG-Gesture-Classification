import json
import unittest
import urllib.error
from unittest.mock import patch

from Middleware.input_events import create_gesture_event
from Middleware.input_events import create_voice_event
from Middleware.widget_bridge import WidgetBridgeClient
from Middleware.widget_bridge import build_widget_payload
from Middleware.widget_bridge import decision_from_intent_result
from Middleware.widget_bridge import legacy_status_from_decision


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
