import datetime as dt
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import bot


class FakeToolUse:
    type = "tool_use"
    name = "save_fact"
    id = "tool-1"
    input = {"fact": "Rides on Saturdays"}

    def model_dump(self):
        return {"type": self.type, "name": self.name, "id": self.id, "input": self.input}


class FakeLLM:
    def __init__(self):
        self.requests = []

    def create(self, **request):
        self.requests.append(request)
        usage = SimpleNamespace(input_tokens=0, cache_creation_input_tokens=0,
                                cache_read_input_tokens=0, output_tokens=0)
        if len(self.requests) == 1:
            return SimpleNamespace(content=[FakeToolUse()], stop_reason="tool_use", usage=usage)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="OK")],
                               stop_reason="end_turn", usage=usage)


class CacheLayoutTest(unittest.TestCase):
    def test_save_fact_changes_only_uncached_context_in_next_round(self):
        athlete = bot.Athlete(user_id="test", name="Pat")
        llm = FakeLLM()
        with patch.object(bot, "load_athlete", return_value=athlete), \
             patch.object(bot, "save_athlete"), patch.object(bot, "log_usage"):
            self.assertEqual(bot.reply("test", "I ride on Saturdays", llm=llm), "OK")

        first, second = (request["system"] for request in llm.requests)
        self.assertEqual(first[0], second[0])
        self.assertEqual(first[0]["text"], bot.INSTRUCTIONS)
        self.assertEqual(first[0]["cache_control"], {"type": "ephemeral"})
        self.assertNotIn("cache_control", first[1])
        self.assertNotIn("cache_control", second[1])
        self.assertNotIn("Rides on Saturdays", first[1]["text"])
        self.assertIn("Rides on Saturdays", second[1]["text"])
        self.assertEqual(llm.requests[0]["tools"], llm.requests[1]["tools"])

    def test_static_prefix_is_shared_across_athletes_and_dates(self):
        a = bot.Athlete(user_id="a", name="A")
        b = bot.Athlete(user_id="b", name="B", facts=["Uses a trainer"])
        one = bot.build_system(a, dt.date(2026, 4, 18))
        two = bot.build_system(b, dt.date(2026, 4, 19))
        self.assertEqual(one[0], two[0])
        self.assertNotEqual(one[1], two[1])


if __name__ == "__main__":
    unittest.main()
