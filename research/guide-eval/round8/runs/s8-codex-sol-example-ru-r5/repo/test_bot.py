import json
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
    input = {"fact": "Prefers morning rides"}

    def model_dump(self):
        return {"type": self.type, "name": self.name, "id": self.id, "input": self.input}


class FakeLLM:
    def __init__(self):
        self.requests = []

    def create(self, **request):
        self.requests.append(request)
        usage = SimpleNamespace(input_tokens=1, cache_creation_input_tokens=0,
                                cache_read_input_tokens=0, output_tokens=1)
        if len(self.requests) == 1:
            return SimpleNamespace(content=[ToolUse()], stop_reason="tool_use", usage=usage)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="Saved.")],
                               stop_reason="end_turn", usage=usage)


class PromptCacheTests(unittest.TestCase):
    def test_memory_write_preserves_static_cache_segment_in_tool_loop(self):
        with tempfile.TemporaryDirectory() as directory:
            athlete_file = Path(directory) / "athletes.json"
            usage_file = Path(directory) / "usage.jsonl"
            llm = FakeLLM()
            with patch.object(bot, "ATHLETES_FILE", str(athlete_file)), \
                 patch.object(bot, "USAGE_LOG", str(usage_file)):
                self.assertEqual(bot.reply("42", "I prefer morning rides", llm=llm), "Saved.")

            first, second = llm.requests
            self.assertEqual(first["tools"], second["tools"])
            self.assertEqual(len(first["system"]), 2)
            self.assertEqual(first["system"][0], second["system"][0])
            self.assertEqual(first["system"][0]["text"], bot.INSTRUCTIONS)
            self.assertEqual(first["system"][0]["cache_control"], {"type": "ephemeral"})
            self.assertEqual(first["system"][1]["cache_control"], {"type": "ephemeral"})
            self.assertNotIn("Prefers morning rides", first["system"][1]["text"])
            self.assertIn("Prefers morning rides", second["system"][1]["text"])
            self.assertEqual(json.loads(athlete_file.read_text())["42"]["facts"],
                             ["Prefers morning rides"])


if __name__ == "__main__":
    unittest.main()
