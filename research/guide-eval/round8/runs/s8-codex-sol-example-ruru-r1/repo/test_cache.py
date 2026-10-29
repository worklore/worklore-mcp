"""Local regression check for prompt boundaries around a memory write."""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bot


class FakeLLM:
    def __init__(self):
        self.requests = []

    def create(self, **request):
        self.requests.append(request)
        usage = SimpleNamespace(input_tokens=1, cache_creation_input_tokens=0,
                                cache_read_input_tokens=0, output_tokens=1)
        if len(self.requests) == 1:
            block = SimpleNamespace(type="tool_use", name="save_fact", id="tool-1",
                                    input={"fact": "Runs before work"},
                                    model_dump=lambda: {"type": "tool_use", "id": "tool-1",
                                                        "name": "save_fact", "input": {"fact": "Runs before work"}})
            return SimpleNamespace(content=[block], stop_reason="tool_use", usage=usage)
        block = SimpleNamespace(type="text", text="Done")
        return SimpleNamespace(content=[block], stop_reason="end_turn", usage=usage)


class CacheBoundaryTest(unittest.TestCase):
    def test_save_fact_changes_only_athlete_block(self):
        with tempfile.TemporaryDirectory() as directory:
            athletes = str(Path(directory) / "athletes.json")
            usage = str(Path(directory) / "usage.jsonl")
            llm = FakeLLM()
            with patch.object(bot, "ATHLETES_FILE", athletes), patch.object(bot, "USAGE_LOG", usage):
                self.assertEqual(bot.reply("42", "I run before work", llm=llm), "Done")
                first, after_save = llm.requests
                self.assertEqual(first["tools"], after_save["tools"])
                self.assertEqual(len(first["system"]), 2)
                for block in first["system"]:
                    self.assertEqual(block["cache_control"], {"type": "ephemeral"})
                self.assertEqual(first["system"][0], after_save["system"][0])
                self.assertNotEqual(first["system"][1], after_save["system"][1])
                self.assertIn("Runs before work", after_save["system"][1]["text"])
                self.assertEqual(json.loads(Path(athletes).read_text())["42"]["facts"],
                                 ["Runs before work"])
                next_message = bot.build_request(bot.load_athlete("42"), [],
                                                 bot.select_tools("hello"), dt.date.today())
                self.assertEqual(after_save["system"], next_message["system"])


if __name__ == "__main__":
    unittest.main()
