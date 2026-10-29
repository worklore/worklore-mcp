"""Regression checks for prompt cache boundaries."""
import datetime as dt
import unittest
from unittest.mock import patch

import bot


class PromptCacheTests(unittest.TestCase):
    def test_save_fact_changes_only_memory_block(self):
        athlete = bot.Athlete(user_id="42", name="Marta")
        today = dt.date(2026, 4, 18)
        before = bot.build_request(athlete, [], bot.select_tools("hello"), today)["system"]

        with patch.object(bot, "save_athlete"):
            bot.run_tool(athlete, "save_fact", {"fact": "Runs before work"})

        after = bot.build_request(athlete, [], bot.select_tools("hello"), today)["system"]
        self.assertEqual(before[0], after[0])
        self.assertNotEqual(before[1]["text"], after[1]["text"])
        self.assertIn("Runs before work", after[1]["text"])
        self.assertEqual([block["cache_control"] for block in after],
                         [{"type": "ephemeral"}] * 2)

    def test_date_change_keeps_stable_cache_prefix(self):
        athlete = bot.Athlete(user_id="77", name="Jonas", lang="de")
        first = bot.build_system(athlete, dt.date(2026, 4, 18))
        next_day = bot.build_system(athlete, dt.date(2026, 4, 19))
        self.assertEqual(first[0], next_day[0])
        self.assertNotEqual(first[1]["text"], next_day[1]["text"])


if __name__ == "__main__":
    unittest.main()
