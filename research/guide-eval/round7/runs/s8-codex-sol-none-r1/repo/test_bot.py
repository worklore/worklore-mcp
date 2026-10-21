import datetime as dt
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import bot


class ToolUse:
    type = "tool_use"
    name = "save_fact"
    id = "save-1"
    input = {"fact": "Prefers Saturday long rides"}

    def model_dump(self):
        return {"type": self.type, "name": self.name, "id": self.id, "input": self.input}


class FakeLLM:
    def __init__(self):
        self.requests = []

    def create(self, **request):
        self.requests.append(request)
        usage = SimpleNamespace(input_tokens=20, cache_creation_input_tokens=0,
                                cache_read_input_tokens=0, output_tokens=20)
        if len(self.requests) == 1:
            return SimpleNamespace(content=[ToolUse()], stop_reason="tool_use", usage=usage)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="Done.")],
                               stop_reason="end_turn", usage=usage)


class PromptCacheTests(unittest.TestCase):
    def test_memory_write_changes_context_but_not_cached_prefix(self):
        with tempfile.TemporaryDirectory(dir=os.path.dirname(__file__)) as tmp:
            athlete_file = os.path.join(tmp, "athletes.json")
            usage_file = os.path.join(tmp, "usage.jsonl")
            llm = FakeLLM()
            with patch.object(bot, "ATHLETES_FILE", athlete_file), patch.object(bot, "USAGE_LOG", usage_file):
                self.assertEqual(bot.reply("42", "I prefer Saturday long rides", llm), "Done.")
                self.assertEqual(bot.reply("42", "What should I do today?", llm), "Done.")
                self.assertEqual(bot.load_athlete("42").facts, ["Prefers Saturday long rides"])
                with open(usage_file) as f:
                    self.assertEqual(len(f.readlines()), 3)

            before, after, next_turn = [r["system"] for r in llm.requests]
            self.assertEqual(before[0], after[0])
            self.assertEqual(after[0], next_turn[0])
            self.assertEqual(before[0]["cache_control"], {"type": "ephemeral"})
            self.assertNotIn("cache_control", before[1])
            self.assertNotIn("Prefers Saturday long rides", before[1]["text"])
            self.assertIn("Prefers Saturday long rides", after[1]["text"])
            self.assertEqual(after[1], next_turn[1])
            self.assertEqual([t["name"] for t in llm.requests[0]["tools"]],
                             [t["name"] for t in llm.requests[1]["tools"]])

    def test_date_and_athlete_changes_do_not_change_cached_instructions(self):
        first = bot.build_system(bot.Athlete(user_id="1", name="A"), dt.date(2026, 4, 20))
        second = bot.build_system(bot.Athlete(user_id="2", name="B"), dt.date(2026, 4, 21))
        self.assertEqual(first[0], second[0])
        self.assertNotEqual(first[1], second[1])


if __name__ == "__main__":
    unittest.main()
