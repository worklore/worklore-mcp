import datetime as dt
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bot


class PromptCacheTests(unittest.TestCase):
    def test_memory_write_changes_only_athlete_block(self):
        today = dt.date(2026, 4, 18)
        athlete = bot.load_athlete("42")
        before = bot.build_system(athlete, today)
        athlete.facts.append("Prefers Saturday long rides")
        after = bot.build_system(athlete, today)

        self.assertEqual(len(after), 2)
        self.assertEqual(before[0], after[0])
        self.assertNotEqual(before[1]["text"], after[1]["text"])
        self.assertIn("Prefers Saturday long rides", after[1]["text"])
        self.assertTrue(all(block["cache_control"] == {"type": "ephemeral"} for block in after))

    def test_save_fact_tool_round_keeps_static_prefix(self):
        class FakeLLM:
            def __init__(self):
                self.requests = []

            def create(self, **request):
                self.requests.append(request)
                usage = SimpleNamespace(input_tokens=0, cache_creation_input_tokens=0,
                                        cache_read_input_tokens=0, output_tokens=0)
                if len(self.requests) == 1:
                    tool = SimpleNamespace(type="tool_use", name="save_fact", id="tool-1",
                                           input={"fact": "Prefers Saturday long rides"},
                                           model_dump=lambda: {"type": "tool_use", "id": "tool-1",
                                                               "name": "save_fact", "input": {"fact": "Prefers Saturday long rides"}})
                    return SimpleNamespace(content=[tool], stop_reason="tool_use", usage=usage)
                return SimpleNamespace(content=[SimpleNamespace(type="text", text="Saved.")],
                                       stop_reason="end_turn", usage=usage)

        llm = FakeLLM()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(bot, "ATHLETES_FILE", str(Path(tmp) / "athletes.json")), \
                 patch.object(bot, "USAGE_LOG", str(Path(tmp) / "usage.jsonl")):
                self.assertEqual(bot.reply("new-user", "I prefer Saturday long rides", llm), "Saved.")

        first, second = llm.requests
        self.assertEqual(first["system"][0], second["system"][0])
        self.assertEqual(first["tools"], second["tools"])
        self.assertNotIn("Prefers Saturday long rides", first["system"][1]["text"])
        self.assertIn("Prefers Saturday long rides", second["system"][1]["text"])


if __name__ == "__main__":
    unittest.main()
