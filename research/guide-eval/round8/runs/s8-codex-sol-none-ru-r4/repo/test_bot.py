"""Local regression checks for prompt caching and memory updates."""
import datetime as dt
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import bot


class PromptCacheTests(unittest.TestCase):
    def test_save_fact_keeps_cached_prefix_and_updates_context(self):
        athlete = bot.Athlete(user_id="42", name="Marta", facts=["Runs before work"])
        requests = []

        class FakeLLM:
            def create(self, **request):
                requests.append(request)
                if len(requests) == 1:
                    tool_use = SimpleNamespace(
                        type="tool_use", name="save_fact", id="call-1",
                        input={"fact": "Owns a Garmin 255"},
                        model_dump=lambda: {"type": "tool_use", "name": "save_fact", "id": "call-1", "input": {"fact": "Owns a Garmin 255"}},
                    )
                    return SimpleNamespace(content=[tool_use], stop_reason="tool_use", usage=None)
                return SimpleNamespace(
                    content=[SimpleNamespace(type="text", text="Got it.")],
                    stop_reason="end_turn", usage=None,
                )

        with patch.object(bot, "load_athlete", return_value=athlete), \
             patch.object(bot, "save_athlete"), \
             patch.object(bot, "log_usage"):
            self.assertEqual(bot.reply("42", "I own a Garmin 255", llm=FakeLLM()), "Got it.")

        first, second = (request["system"] for request in requests)
        self.assertEqual(first[0], second[0])
        self.assertEqual(first[0]["text"], bot.INSTRUCTIONS)
        self.assertEqual(first[0]["cache_control"], {"type": "ephemeral"})
        self.assertNotIn("cache_control", first[1])
        self.assertNotIn("cache_control", second[1])
        self.assertNotIn("Owns a Garmin 255", first[1]["text"])
        self.assertIn("Owns a Garmin 255", second[1]["text"])
        self.assertEqual(requests[0]["tools"], requests[1]["tools"])

    def test_context_changes_do_not_change_cached_block(self):
        athlete = bot.Athlete(user_id="42", name="Marta")
        day = dt.date(2026, 4, 18)
        first = bot.build_system(athlete, day)
        athlete.facts.append("Runs before work")
        second = bot.build_system(athlete, day + dt.timedelta(days=1))

        self.assertEqual(first[0], second[0])
        self.assertNotEqual(first[1], second[1])


if __name__ == "__main__":
    unittest.main()
