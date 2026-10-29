import datetime as dt
import unittest
from unittest.mock import patch

import bot


class PromptCacheTests(unittest.TestCase):
    def test_memory_write_changes_only_athlete_cache_segment(self):
        athlete = bot.Athlete(user_id="42", name="Marta", facts=["Owns a Garmin 255"])
        today = dt.date(2026, 4, 18)
        tools = bot.select_tools("hello")
        before = bot.build_request(athlete, [{"role": "user", "content": "hello"}], tools, today)

        with patch.object(bot, "save_athlete"):
            bot.run_tool(athlete, "save_fact", {"fact": "Runs before work"})

        after = bot.build_request(athlete, [{"role": "user", "content": "hello"}], tools, today)
        self.assertEqual(len(before["system"]), 2)
        self.assertEqual(before["system"][0], after["system"][0])
        self.assertNotEqual(before["system"][1]["text"], after["system"][1]["text"])
        self.assertIn("Runs before work", after["system"][1]["text"])
        self.assertEqual(before["tools"], after["tools"])
        for block in after["system"]:
            self.assertEqual(block["cache_control"], {"type": "ephemeral"})

    def test_static_segment_is_identical_across_athletes_and_dates(self):
        first = bot.build_system(bot.Athlete(user_id="1", name="Marta"), dt.date(2026, 4, 18))
        second = bot.build_system(bot.Athlete(user_id="2", name="Jonas"), dt.date(2026, 4, 19))
        self.assertEqual(first[0], second[0])
        self.assertNotEqual(first[1]["text"], second[1]["text"])
        self.assertEqual(first[0]["text"], bot.INSTRUCTIONS)


if __name__ == "__main__":
    unittest.main()
