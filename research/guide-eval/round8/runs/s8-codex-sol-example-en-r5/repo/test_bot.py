import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bot


class PromptCacheTests(unittest.TestCase):
    def test_memory_write_preserves_static_cache_prefix(self):
        today = dt.date(2026, 4, 18)
        with tempfile.TemporaryDirectory() as tmp, patch.object(bot, "ATHLETES_FILE", str(Path(tmp) / "athletes.json")):
            athlete = bot.Athlete(user_id="42", name="Marta")
            tools = bot.select_tools("I bought a new bike")
            before = bot.build_request(athlete, [{"role": "user", "content": "Hello"}], tools, today)

            self.assertEqual(len(before["system"]), 2)
            self.assertEqual(before["system"][0]["text"], bot.INSTRUCTIONS)
            self.assertEqual([block["cache_control"] for block in before["system"]],
                             [{"type": "ephemeral"}, {"type": "ephemeral"}])

            bot.run_tool(athlete, "save_fact", {"fact": "Owns a road bike"})
            after = bot.build_request(bot.load_athlete("42"), [{"role": "user", "content": "Hello"}], tools, today)

            self.assertEqual(before["tools"], after["tools"])
            self.assertEqual(before["system"][0], after["system"][0])
            self.assertNotEqual(before["system"][1]["text"], after["system"][1]["text"])
            self.assertIn("Owns a road bike", after["system"][1]["text"])


if __name__ == "__main__":
    unittest.main()
