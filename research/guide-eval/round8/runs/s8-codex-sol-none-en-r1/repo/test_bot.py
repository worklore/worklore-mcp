"""Regression checks for the system prompt cache boundary."""

import datetime as dt
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bot


class FakeToolUse:
    type = "tool_use"
    name = "save_fact"
    id = "tool-1"
    input = {"fact": "Prefers Saturday long rides"}

    def model_dump(self):
        return {"type": self.type, "name": self.name, "id": self.id, "input": self.input}


class FakeLLM:
    def __init__(self):
        self.requests = []

    def create(self, **request):
        self.requests.append(request)
        content = [FakeToolUse()] if len(self.requests) == 1 else [SimpleNamespace(type="text", text="Done")]
        return SimpleNamespace(
            content=content,
            stop_reason="tool_use" if len(self.requests) == 1 else "end_turn",
            usage=SimpleNamespace(input_tokens=1, cache_creation_input_tokens=0,
                                  cache_read_input_tokens=0, output_tokens=1),
        )


class PromptCacheTest(unittest.TestCase):
    def test_save_fact_does_not_change_cached_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            athletes_file = Path(directory) / "athletes.json"
            shutil.copyfile(bot.ATHLETES_FILE, athletes_file)
            with patch.object(bot, "ATHLETES_FILE", str(athletes_file)), \
                 patch.object(bot, "USAGE_LOG", str(Path(directory) / "usage.jsonl")):
                llm = FakeLLM()
                self.assertEqual(bot.reply("77", "I prefer Saturday long rides", llm), "Done")
                first, after_save = (r["system"] for r in llm.requests)
                self.assertEqual(first[0], after_save[0])
                self.assertEqual(first[0]["cache_control"], {"type": "ephemeral"})
                self.assertNotIn("cache_control", after_save[1])
                self.assertNotIn("Prefers Saturday long rides", first[1]["text"])
                self.assertIn("Prefers Saturday long rides", after_save[1]["text"])

                next_request = bot.build_request(bot.load_athlete("77"), [], bot.CORE_TOOLS,
                                                 dt.date.today() + dt.timedelta(days=1))
                self.assertEqual(first[0], next_request["system"][0])
                self.assertIn("Prefers Saturday long rides", next_request["system"][1]["text"])


if __name__ == "__main__":
    unittest.main()
