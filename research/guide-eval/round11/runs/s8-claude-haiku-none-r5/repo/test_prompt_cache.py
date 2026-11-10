"""Checks that a memory write does not change the cached part of the system prompt.

Run: python3 -m unittest test_prompt_cache -v
No API calls: build_system() is pure and is what reply() sends.
"""
import copy
import datetime as dt
import unittest

import bot


def athlete():
    return bot.Athlete(user_id="42", name="Marta", facts=["Runs before work, 06:30, Mon/Wed/Fri"])


class PromptCacheLayout(unittest.TestCase):
    def test_only_first_block_is_cached(self):
        blocks = bot.build_system(athlete(), dt.date(2026, 4, 18))
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["cache_control"], {"type": "ephemeral"})
        self.assertNotIn("cache_control", blocks[1])

    def test_facts_and_date_are_after_the_breakpoint(self):
        blocks = bot.build_system(athlete(), dt.date(2026, 4, 18))
        self.assertNotIn("Long-term facts", blocks[0]["text"])
        self.assertNotIn("Today:", blocks[0]["text"])
        self.assertIn("Runs before work", blocks[1]["text"])
        self.assertIn("Today: 2026-04-18", blocks[1]["text"])

    def test_save_fact_does_not_change_cached_block(self):
        a = athlete()
        day = dt.date(2026, 4, 18)
        before = bot.build_system(a, day)[0]["text"]
        a.facts.append("Owns a Garmin 255")
        after = bot.build_system(a, day)
        self.assertEqual(before, after[0]["text"])
        self.assertIn("Owns a Garmin 255", after[1]["text"])

    def test_new_day_does_not_change_cached_block(self):
        a = athlete()
        self.assertEqual(
            bot.build_system(a, dt.date(2026, 4, 18))[0]["text"],
            bot.build_system(a, dt.date(2026, 4, 19))[0]["text"],
        )

    def test_profile_change_still_changes_cached_block(self):
        a = athlete()
        before = bot.build_system(a, dt.date(2026, 4, 18))[0]["text"]
        a2 = copy.deepcopy(a)
        a2.goal = "sub-1:50 half marathon"
        self.assertNotEqual(before, bot.build_system(a2, dt.date(2026, 4, 18))[0]["text"])


if __name__ == "__main__":
    unittest.main()
