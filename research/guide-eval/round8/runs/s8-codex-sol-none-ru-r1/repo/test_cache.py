"""Local regression checks for the prompt cache boundary."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import bot


class CacheAfterSaveFactTest(unittest.TestCase):
    def test_saved_fact_changes_context_but_not_cached_instructions(self):
        athlete = bot.Athlete(user_id="test", name="Runner")
        tool_use = SimpleNamespace(
            type="tool_use", name="save_fact", id="call-1",
            input={"fact": "Runs on Thursdays"},
            model_dump=lambda: {
                "type": "tool_use", "name": "save_fact", "id": "call-1",
                "input": {"fact": "Runs on Thursdays"},
            },
        )
        usage = SimpleNamespace(input_tokens=1, cache_creation_input_tokens=0,
                                cache_read_input_tokens=0, output_tokens=1)
        responses = iter([
            SimpleNamespace(content=[tool_use], stop_reason="tool_use", usage=usage),
            SimpleNamespace(content=[SimpleNamespace(type="text", text="Done")],
                            stop_reason="end_turn", usage=usage),
        ])
        requests = []

        class FakeLLM:
            def create(self, **request):
                requests.append(request)
                return next(responses)

        with patch.object(bot, "load_athlete", return_value=athlete), \
             patch.object(bot, "save_athlete"), \
             patch.object(bot, "log_usage"):
            self.assertEqual(bot.reply("test", "I run on Thursdays", llm=FakeLLM()), "Done")

        first, second = requests
        self.assertEqual(first["system"][0], second["system"][0])
        self.assertEqual(first["system"][0]["cache_control"], {"type": "ephemeral"})
        self.assertNotIn("cache_control", second["system"][1])
        self.assertNotIn("Runs on Thursdays", first["system"][1]["text"])
        self.assertIn("Runs on Thursdays", second["system"][1]["text"])
        self.assertEqual(first["tools"], second["tools"])
        self.assertEqual([tool["name"] for tool in first["tools"]],
                         ["save_fact", "log_session"])


if __name__ == "__main__":
    unittest.main()
