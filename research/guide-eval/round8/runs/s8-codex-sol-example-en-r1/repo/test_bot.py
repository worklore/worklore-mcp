"""Local regression checks for prompt caching across memory writes."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bot


class SaveFactResponse:
    type = "tool_use"
    name = "save_fact"
    id = "fact-1"
    input = {"fact": "Prefers morning workouts"}

    def model_dump(self):
        return {"type": self.type, "name": self.name, "id": self.id, "input": self.input}


class RecordingLLM:
    def __init__(self):
        self.requests = []

    def create(self, **request):
        self.requests.append(request)
        content = [SaveFactResponse()] if len(self.requests) == 1 else [SimpleNamespace(type="text", text="Done")]
        return SimpleNamespace(
            content=content,
            stop_reason="tool_use" if len(self.requests) == 1 else "end_turn",
            usage=SimpleNamespace(input_tokens=1, cache_creation_input_tokens=0,
                                  cache_read_input_tokens=0, output_tokens=1),
        )


class CacheTests(unittest.TestCase):
    def test_memory_write_changes_only_context_block(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            with patch.object(bot, "ATHLETES_FILE", str(Path(tmp) / "athletes.json")), \
                 patch.object(bot, "USAGE_LOG", str(Path(tmp) / "usage.jsonl")):
                llm = RecordingLLM()
                self.assertEqual(bot.reply("42", "I prefer morning workouts", llm), "Done")
                before, after = (request["system"] for request in llm.requests)
                self.assertEqual(len(before), 2)
                self.assertEqual(before[0], after[0])
                self.assertNotEqual(before[1]["text"], after[1]["text"])
                self.assertIn("Prefers morning workouts", after[1]["text"])
                self.assertEqual([block["cache_control"] for block in after],
                                 [{"type": "ephemeral"}] * 2)
                self.assertEqual(llm.requests[0]["tools"], llm.requests[1]["tools"])


if __name__ == "__main__":
    unittest.main()
