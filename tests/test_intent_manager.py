import json
import unittest
from unittest.mock import patch

from Middleware.intent_manager import OllamaIntentClient


class IntentManagerTests(unittest.TestCase):
    def test_valid_json_is_normalized(self):
        client = OllamaIntentClient()
        response = {
            "message": {
                "content": json.dumps({
                    "intent": "adjust_volume",
                    "action": "increase",
                    "target": "volume",
                    "value": "louder",
                    "needs_clarification": False,
                    "clarification": "",
                    "used_modalities": "voice",
                    "llm_confidence_estimate": 1.5,
                })
            }
        }

        with patch.object(client, "_post_chat", return_value=response):
            result = client.interpret("Mach die Lautstaerke lauter", "", None)

        self.assertEqual(result["intent"], "adjust_volume")
        self.assertEqual(result["action"], "increase")
        self.assertEqual(result["target"], "volume")
        self.assertEqual(result["llm_confidence_estimate"], 1.0)

    def test_ollama_request_disables_thinking_and_limits_output(self):
        client = OllamaIntentClient()
        response = {
            "message": {
                "content": json.dumps({
                    "intent": "adjust_volume",
                    "action": "increase",
                    "target": "volume",
                    "value": "louder",
                    "needs_clarification": False,
                    "clarification": "",
                    "used_modalities": "voice",
                    "llm_confidence_estimate": 0.8,
                })
            }
        }

        with patch.object(client, "_post_chat", return_value=response) as post_chat:
            client.interpret("Mach die Lautstaerke lauter", "", None)

        request_body = post_chat.call_args.args[0]
        self.assertFalse(request_body["think"])
        self.assertEqual(request_body["options"]["num_predict"], 160)
        self.assertEqual(request_body["options"]["num_ctx"], 2048)

    def test_request_includes_manual_gesture_source(self):
        client = OllamaIntentClient()
        response = {
            "message": {
                "content": json.dumps({
                    "intent": "adjust_volume",
                    "action": "increase",
                    "target": "volume",
                    "value": "louder",
                    "needs_clarification": False,
                    "clarification": "",
                    "used_modalities": "voice+gesture",
                    "llm_confidence_estimate": 0.8,
                })
            }
        }

        with patch.object(client, "_post_chat", return_value=response) as post_chat:
            client.interpret(
                "Lautstaerke hoeher machen",
                "Swipe",
                None,
                gesture_source="manual",
            )

        request_body = post_chat.call_args.args[0]
        user_payload = json.loads(request_body["messages"][1]["content"])
        self.assertEqual(user_payload["gesture"], "Swipe")
        self.assertEqual(user_payload["gesture_source"], "manual")

    def test_clear_voice_command_overrides_conflicting_unknown(self):
        client = OllamaIntentClient()
        response = {
            "message": {
                "content": json.dumps({
                    "intent": "unknown",
                    "action": "unknown",
                    "target": "unknown",
                    "value": "",
                    "needs_clarification": True,
                    "clarification": "Meinst du die Lautstaerke oder die Route?",
                    "used_modalities": "voice+gesture",
                    "llm_confidence_estimate": 0.2,
                })
            }
        }

        with patch.object(client, "_post_chat", return_value=response):
            result = client.interpret(
                "Lautstaerke hoeher machen",
                "Swipe",
                None,
                gesture_source="manual",
            )

        self.assertEqual(result["intent"], "adjust_volume")
        self.assertEqual(result["action"], "increase")
        self.assertEqual(result["target"], "volume")
        self.assertEqual(result["used_modalities"], "voice+gesture")
        self.assertFalse(result["needs_clarification"])

    def test_invalid_json_returns_unknown_with_error(self):
        client = OllamaIntentClient()
        response = {"message": {"content": "not json"}}

        with patch.object(client, "_post_chat", return_value=response):
            result = client.interpret("Mach das lauter", "", None)

        self.assertEqual(result["intent"], "unknown")
        self.assertTrue(result["needs_clarification"])
        self.assertIn("JSON", result["error"])

    def test_unknown_values_are_normalized(self):
        client = OllamaIntentClient()
        response = {
            "message": {
                "content": json.dumps({
                    "intent": "launch_rocket",
                    "action": "explode",
                    "target": "moon",
                    "value": "now",
                    "needs_clarification": False,
                    "clarification": "",
                    "used_modalities": "telepathy",
                    "llm_confidence_estimate": 0.7,
                })
            }
        }

        with patch.object(client, "_post_chat", return_value=response):
            result = client.interpret("mach das", "", None)

        self.assertEqual(result["intent"], "unknown")
        self.assertEqual(result["action"], "unknown")
        self.assertEqual(result["target"], "unknown")
        self.assertEqual(result["used_modalities"], "voice")
        self.assertTrue(result["needs_clarification"])

    def test_list_modalities_are_normalized(self):
        client = OllamaIntentClient()
        response = {
            "message": {
                "content": json.dumps({
                    "intent": "confirm",
                    "action": "confirm",
                    "target": "navigation",
                    "value": "",
                    "needs_clarification": False,
                    "clarification": "",
                    "used_modalities": ["voice", "gesture"],
                    "llm_confidence_estimate": 0.7,
                })
            }
        }

        with patch.object(client, "_post_chat", return_value=response):
            result = client.interpret("ja", "Daumen hoch", None)

        self.assertEqual(result["used_modalities"], "voice+gesture")

    def test_empty_input_does_not_call_ollama(self):
        client = OllamaIntentClient()

        with patch.object(client, "_post_chat") as post_chat:
            result = client.interpret("", "Rest", None)

        post_chat.assert_not_called()
        self.assertEqual(result["intent"], "unknown")
        self.assertEqual(result["used_modalities"], "none")
        self.assertTrue(result["needs_clarification"])


if __name__ == "__main__":
    unittest.main()
