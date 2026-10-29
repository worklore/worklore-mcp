import datetime as dt
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bot


class PromptCacheTest(unittest.TestCase):
    def test_save_fact_changes_only_context_block_in_tool_loop(self):
        class ToolUse:
            type = "tool_use"
            name = "save_fact"
            id = "tool-1"
            input = {"fact": "Prefers morning runs"}

            def model_dump(self):
                return {"type": self.type, "name": self.name, "id": self.id, "input": self.input}

        class FakeLLM:
            def __init__(self):
                self.requests = []

            def create(self, **request):
                self.requests.append(request)
                usage = SimpleNamespace(input_tokens=0, cache_creation_input_tokens=0,
                                        cache_read_input_tokens=0, output_tokens=0)
                if len(self.requests) == 1:
                    return SimpleNamespace(content=[ToolUse()], stop_reason="tool_use", usage=usage)
                return SimpleNamespace(content=[SimpleNamespace(type="text", text="Saved.")],
                                       stop_reason="end_turn", usage=usage)

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(bot, "ATHLETES_FILE", str(Path(tmp) / "athletes.json")), \
                 patch.object(bot, "USAGE_LOG", str(Path(tmp) / "usage.jsonl")):
                llm = FakeLLM()
                self.assertEqual(bot.reply("42", "I prefer morning runs", llm), "Saved.")

                before, after = (request["system"] for request in llm.requests)
                self.assertEqual(len(before), 2)
                self.assertEqual(before[0], after[0])
                self.assertEqual(before[0]["text"], bot.INSTRUCTIONS)
                self.assertEqual(before[1]["cache_control"], {"type": "ephemeral"})
                self.assertEqual(after[1]["cache_control"], {"type": "ephemeral"})
                self.assertNotEqual(before[1]["text"], after[1]["text"])
                self.assertIn("Prefers morning runs", after[1]["text"])
                self.assertEqual(llm.requests[0]["tools"], llm.requests[1]["tools"])

    def test_prompt_text_is_preserved(self):
        athlete = bot.Athlete(user_id="42", name="Marta")
        today = dt.date(2026, 4, 18)
        blocks = bot.build_system(athlete, today)
        self.assertEqual("".join(block["text"] for block in blocks),
                         bot.INSTRUCTIONS + "\n\n" + bot.athlete_context(athlete, today))


if __name__ == "__main__":
    unittest.main()
