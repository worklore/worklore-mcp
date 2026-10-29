import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bot


class FakeBlock:
    def __init__(self, kind, **fields):
        self.type = kind
        self.__dict__.update(fields)

    def model_dump(self):
        return {"type": self.type, **{k: v for k, v in vars(self).items() if k != "type"}}


class FakeLLM:
    def __init__(self):
        self.requests = []

    def create(self, **request):
        self.requests.append(request)
        if len(self.requests) == 1:
            content = [FakeBlock("tool_use", name="save_fact", id="1", input={"fact": "Runs on Tuesdays"})]
            stop_reason = "tool_use"
        else:
            content = [FakeBlock("text", text="Done")]
            stop_reason = "end_turn"
        usage = SimpleNamespace(input_tokens=1, cache_creation_input_tokens=0,
                                cache_read_input_tokens=0, output_tokens=1)
        return SimpleNamespace(content=content, stop_reason=stop_reason, usage=usage)


class CacheLayoutTest(unittest.TestCase):
    def test_memory_write_keeps_cached_prefix_and_refreshes_facts(self):
        with tempfile.TemporaryDirectory() as temp:
            athlete_file = Path(temp) / "athletes.json"
            athlete_file.write_text(json.dumps({"42": {
                "user_id": "42", "name": "Marta", "facts": ["Runs on Mondays"]
            }}))
            llm = FakeLLM()
            with patch.object(bot, "ATHLETES_FILE", str(athlete_file)), \
                 patch.object(bot, "USAGE_LOG", str(Path(temp) / "usage.jsonl")):
                self.assertEqual(bot.reply("42", "I also run on Tuesdays", llm), "Done")
                self.assertEqual(bot.reply("42", "Thanks", llm), "Done")

            first, after_save, next_message = [r["system"] for r in llm.requests]
            self.assertEqual(first[0], after_save[0])
            self.assertEqual(first[0], next_message[0])
            self.assertEqual(first[0]["cache_control"], {"type": "ephemeral"})
            self.assertNotIn("Runs on Tuesdays", first[1]["text"])
            self.assertIn("Runs on Tuesdays", after_save[1]["text"])
            self.assertIn("Runs on Tuesdays", next_message[1]["text"])
            self.assertNotIn("cache_control", after_save[1])

    def test_date_change_does_not_change_cached_prefix(self):
        athlete = bot.load_athlete("42")
        today = bot.build_system(athlete, dt.date(2026, 4, 20))
        tomorrow = bot.build_system(athlete, dt.date(2026, 4, 21))
        self.assertEqual(today[0], tomorrow[0])
        self.assertNotEqual(today[1], tomorrow[1])


if __name__ == "__main__":
    unittest.main()
