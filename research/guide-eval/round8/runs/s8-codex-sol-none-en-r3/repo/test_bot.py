import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bot


class TextBlock:
    type = "text"

    def __init__(self, text):
        self.text = text


class ToolBlock:
    type = "tool_use"
    name = "save_fact"
    id = "tool-1"
    input = {"fact": "Prefers long rides on Sunday"}

    def model_dump(self):
        return {"type": self.type, "name": self.name, "id": self.id, "input": self.input}


class RecordingLLM:
    def __init__(self):
        self.requests = []

    def create(self, **request):
        self.requests.append(request)
        content = [ToolBlock()] if len(self.requests) == 1 else [TextBlock("Got it.")]
        return SimpleNamespace(
            content=content,
            stop_reason="tool_use" if len(self.requests) == 1 else "end_turn",
            usage=SimpleNamespace(input_tokens=0, cache_creation_input_tokens=0,
                                  cache_read_input_tokens=0, output_tokens=0),
        )


class PromptCacheTests(unittest.TestCase):
    def test_save_fact_extends_cached_prefix_in_tool_loop_and_next_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            athlete_file = Path(tmp) / "athletes.json"
            usage_file = Path(tmp) / "usage.jsonl"
            athlete_file.write_text(json.dumps({"42": {
                "user_id": "42", "name": "Marta",
                "facts": ["Runs before work", "Owns a Garmin 255"],
            }}))
            llm = RecordingLLM()
            with patch.object(bot, "ATHLETES_FILE", str(athlete_file)), patch.object(bot, "USAGE_LOG", str(usage_file)):
                self.assertEqual(bot.reply("42", "Remember this preference", llm=llm), "Got it.")
                next_request = bot.build_request(bot.load_athlete("42"),
                                                 [{"role": "user", "content": "Hello"}],
                                                 bot.select_tools("Hello"), dt.date.today())

            before, after = (request["system"] for request in llm.requests)
            self.assertEqual(llm.requests[0]["tools"], llm.requests[1]["tools"])
            self.assertEqual([block["text"] for block in before],
                             [block["text"] for block in after[:-1]])
            self.assertEqual(after, next_request["system"])
            self.assertEqual(after[-1]["text"], "\n- Prefers long rides on Sunday")
            self.assertEqual(sum("cache_control" in block for block in before), 2)
            self.assertEqual(sum("cache_control" in block for block in after), 2)
            self.assertEqual(before[0], after[0])
            self.assertEqual(before[-1]["cache_control"], {"type": "ephemeral"})
            self.assertEqual(after[-1]["cache_control"], {"type": "ephemeral"})
            self.assertIn("Prefers long rides on Sunday", athlete_file.read_text())

    def test_first_fact_keeps_base_breakpoint(self):
        athlete = bot.Athlete(user_id="new", name="athlete")
        before = bot.build_system(athlete, dt.date(2026, 4, 18))
        athlete.facts.append("Prefers long rides on Sunday")
        after = bot.build_system(athlete, dt.date(2026, 4, 18))
        self.assertEqual(before[0], after[0])
        self.assertNotIn("cache_control", before[1])
        self.assertEqual(after[-1]["cache_control"], {"type": "ephemeral"})


if __name__ == "__main__":
    unittest.main()
