"""Checks the prompt-cache layout of bot.build_request without calling the API.

Run: python3 -m unittest test_cache_split -v
"""
import datetime as dt
import unittest

import bot


def request(athlete, today, text="how was my week"):
    tools = bot.select_tools(text)
    return bot.build_request(athlete, [{"role": "user", "content": text}], tools, today)


class CacheLayout(unittest.TestCase):
    def setUp(self):
        self.day1 = dt.date(2026, 4, 18)
        self.day2 = dt.date(2026, 4, 19)
        self.a = bot.Athlete(user_id="42", name="Ana", facts=["Has a knee injury history"])

    def test_exactly_two_markers_both_on_system(self):
        req = request(self.a, self.day1)
        blocks = req["system"]
        self.assertEqual(len(blocks), 2)
        self.assertTrue(all(b["cache_control"] == {"type": "ephemeral"} for b in blocks))
        self.assertEqual(sum(1 for t in req["tools"] if "cache_control" in t), 0)

    def test_static_block_is_identical_across_athletes_days_and_facts(self):
        base = request(self.a, self.day1)["system"][0]["text"]
        other_athlete = bot.Athlete(user_id="77", name="Ben", sport="cycling", goal="climb Ventoux")
        self.assertEqual(base, request(other_athlete, self.day2)["system"][0]["text"])
        self.a.facts.append("Trains on Tuesdays only")
        self.assertEqual(base, request(self.a, self.day1)["system"][0]["text"])

    def test_static_block_contains_no_volatile_values(self):
        static = bot.build_system(self.a, self.day1)[0]["text"]
        for volatile in ("Ana", "42", "2026", "Knee", "Trains on", "Language:", "Today:"):
            self.assertNotIn(volatile, static)

    def test_memory_write_changes_only_the_tail(self):
        before = bot.build_system(self.a, self.day1)
        self.a.facts.append("Owns a road bike")
        after = bot.build_system(self.a, self.day1)
        self.assertEqual(before[0], after[0])
        self.assertNotEqual(before[1], after[1])
        self.assertIn("Owns a road bike", after[1]["text"])

    def test_tail_carries_profile_date_and_language(self):
        tail = bot.build_system(self.a, self.day1)[1]["text"]
        self.assertIn("2026-04-18", tail)
        self.assertIn("Athlete: Ana (id 42)", tail)
        self.assertIn("Language: en", tail)
        self.assertIn("- Has a knee injury history", tail)


if __name__ == "__main__":
    unittest.main()
