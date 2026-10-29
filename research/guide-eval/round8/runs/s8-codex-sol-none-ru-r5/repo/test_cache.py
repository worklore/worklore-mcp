"""Local checks for the prompt cache boundary; no API calls are made."""
import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bot


class PromptCacheTests(unittest.TestCase):
    def test_save_fact_keeps_cached_prefix_and_updates_context(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(bot, "ATHLETES_FILE", str(Path(tmp) / "athletes.json")):
            athlete = bot.Athlete(user_id="42", name="Marta")
            today = dt.date(2026, 4, 18)
            before = bot.build_request(athlete, [{"role": "user", "content": "hello"}], bot.select_tools("hello"), today)

            bot.run_tool(athlete, "save_fact", {"fact": "Runs before work"})
            after = bot.build_request(athlete, [{"role": "user", "content": "hello"}], bot.select_tools("hello"), today)
            next_message = bot.build_system(bot.load_athlete("42"), today)

            self.assertEqual(before["tools"], after["tools"])
            self.assertEqual(before["system"][0], after["system"][0])
            self.assertEqual(after["system"], next_message)
            self.assertEqual(before["system"][0]["cache_control"], {"type": "ephemeral"})
            self.assertNotIn("Runs before work", before["system"][0]["text"])
            self.assertIn("Runs before work", after["system"][1]["text"])
            self.assertNotIn("cache_control", after["system"][1])

    def test_date_changes_only_uncached_context(self):
        athlete = bot.Athlete(user_id="42", name="Marta")
        before = bot.build_system(athlete, dt.date(2026, 4, 18))
        after = bot.build_system(athlete, dt.date(2026, 4, 19))
        self.assertEqual(before[0], after[0])
        self.assertNotEqual(before[1], after[1])


if __name__ == "__main__":
    unittest.main()
