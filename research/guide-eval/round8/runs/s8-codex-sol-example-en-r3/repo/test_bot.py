import datetime as dt
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bot


class ToolUse:
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
        usage = SimpleNamespace(input_tokens=10, cache_creation_input_tokens=0,
                                cache_read_input_tokens=0, output_tokens=10)
        if len(self.requests) == 1:
            return SimpleNamespace(content=[ToolUse()], stop_reason="tool_use", usage=usage)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="Done.")],
                               stop_reason="end_turn", usage=usage)


class CacheBoundaryTest(unittest.TestCase):
    def test_fact_write_preserves_static_breakpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(bot, "ATHLETES_FILE", str(Path(directory) / "athletes.json")), \
                 patch.object(bot, "USAGE_LOG", str(Path(directory) / "usage.jsonl")):
                llm = FakeLLM()
                self.assertEqual(bot.reply("test", "I prefer Saturday long rides", llm), "Done.")

                first, after_save = llm.requests
                for request in (first, after_save):
                    self.assertEqual(len(request["system"]), 2)
                    self.assertTrue(all(block["cache_control"] == {"type": "ephemeral"}
                                        for block in request["system"]))

                self.assertEqual(first["system"][0], after_save["system"][0])
                self.assertEqual(first["system"][0]["text"], bot.INSTRUCTIONS)
                self.assertNotEqual(first["system"][1], after_save["system"][1])
                self.assertIn("Prefers Saturday long rides", after_save["system"][1]["text"])
                self.assertEqual(first["tools"], after_save["tools"])

                stored = bot.load_athlete("test")
                next_message = bot.build_request(stored, [{"role": "user", "content": "Hi"}],
                                                 bot.select_tools("Hi"), dt.date.today())
                self.assertEqual(after_save["system"], next_message["system"])


if __name__ == "__main__":
    unittest.main()
