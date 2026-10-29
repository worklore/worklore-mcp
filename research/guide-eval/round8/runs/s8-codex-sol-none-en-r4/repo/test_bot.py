"""Local cache-layout and memory-write checks (no API calls)."""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bot


class FakeBlock:
    def __init__(self, kind, *, text=None, name=None, fact=None):
        self.type = kind
        self.text = text
        self.name = name
        self.id = "tool-1"
        self.input = {"fact": fact} if fact else {}

    def model_dump(self):
        return {"type": self.type, "id": self.id, "name": self.name, "input": self.input}


class FakeLLM:
    def __init__(self):
        self.requests = []

    def create(self, **request):
        self.requests.append(request)
        saving = len(self.requests) == 1
        return SimpleNamespace(
            content=[FakeBlock("tool_use", name="save_fact", fact="Prefers morning runs")]
            if saving else [FakeBlock("text", text="Saved.")],
            stop_reason="tool_use" if saving else "end_turn",
            usage=SimpleNamespace(input_tokens=1, cache_creation_input_tokens=0,
                                  cache_read_input_tokens=0, output_tokens=1),
        )


class CacheLayoutTests(unittest.TestCase):
    def test_fact_change_keeps_cached_prefix(self):
        athlete = bot.Athlete(user_id="42", name="Marta")
        before = bot.build_system(athlete, dt.date(2026, 4, 18))
        athlete.facts.append("Prefers morning runs")
        after = bot.build_system(athlete, dt.date(2026, 4, 18))
        self.assertEqual(before[0], after[0])
        self.assertEqual(before[0]["cache_control"], {"type": "ephemeral"})
        self.assertNotIn("cache_control", after[1])
        self.assertNotEqual(before[1], after[1])

    def test_save_fact_updates_next_round_and_next_message(self):
        with tempfile.TemporaryDirectory() as directory:
            athletes = str(Path(directory) / "athletes.json")
            usage = str(Path(directory) / "usage.jsonl")
            llm = FakeLLM()
            with patch.object(bot, "ATHLETES_FILE", athletes), patch.object(bot, "USAGE_LOG", usage):
                self.assertEqual(bot.reply("42", "I prefer morning runs", llm=llm), "Saved.")
                next_message = bot.build_request(bot.load_athlete("42"), [],
                                                 bot.select_tools("Hello"), dt.date.today())
            first, second = llm.requests
            self.assertEqual(first["system"][0], second["system"][0])
            self.assertEqual(first["system"][0], next_message["system"][0])
            self.assertNotIn("Prefers morning runs", first["system"][1]["text"])
            self.assertIn("Prefers morning runs", second["system"][1]["text"])
            self.assertIn("Prefers morning runs", next_message["system"][1]["text"])
            self.assertEqual([tool["name"] for tool in first["tools"]],
                             [tool["name"] for tool in second["tools"]])
            self.assertEqual(json.loads(Path(athletes).read_text())["42"]["facts"],
                             ["Prefers morning runs"])
            self.assertEqual(len(Path(usage).read_text().splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
