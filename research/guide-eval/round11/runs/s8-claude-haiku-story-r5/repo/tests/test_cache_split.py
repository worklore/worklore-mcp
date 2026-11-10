"""Offline checks for the prompt-cache layout. Run: python3 -m unittest tests/test_cache_split.py"""
import datetime as dt
import importlib.util
import os
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("bot", os.path.join(_HERE, "..", "bot.py"))
bot = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bot)


class SystemPromptCacheLayout(unittest.TestCase):
    def setUp(self):
        self.day1 = dt.date(2026, 11, 10)
        self.day2 = dt.date(2026, 11, 11)

    def test_two_cached_blocks_static_first(self):
        blocks = bot.build_system(bot.Athlete(user_id="42", name="Sam"), self.day1)
        self.assertEqual(len(blocks), 2)
        self.assertTrue(all(b["cache_control"] == {"type": "ephemeral"} for b in blocks))
        self.assertEqual(blocks[0]["text"], bot.INSTRUCTIONS)

    def test_static_block_identical_across_athletes_and_days(self):
        a = bot.Athlete(user_id="42", name="Sam")
        b = bot.Athlete(user_id="77", name="Lee", facts=["Commutes by bike."], lang="de")
        first = bot.build_system(a, self.day1)[0]["text"]
        self.assertEqual(first, bot.build_system(b, self.day1)[0]["text"])
        self.assertEqual(first, bot.build_system(a, self.day2)[0]["text"])

    def test_memory_write_changes_only_the_tail(self):
        a = bot.Athlete(user_id="42", name="Sam")
        before = bot.build_system(a, self.day1)
        a.facts.append("Has a knee injury history from 2023.")  # what save_fact does
        after = bot.build_system(a, self.day1)
        self.assertEqual(before[0], after[0])
        self.assertNotEqual(before[1], after[1])

    def test_static_block_has_no_interpolated_values(self):
        text = bot.build_system(bot.Athlete(user_id="42", name="Sam"), self.day1)[0]["text"]
        self.assertNotIn("2026", text)
        self.assertNotIn("Sam", text)


if __name__ == "__main__":
    unittest.main()
