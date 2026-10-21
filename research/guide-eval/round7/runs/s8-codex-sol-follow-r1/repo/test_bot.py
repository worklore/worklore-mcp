import datetime as dt
import unittest

from bot import Athlete, INSTRUCTIONS, build_request, build_system, select_tools


class PromptCacheTests(unittest.TestCase):
    def test_memory_write_changes_only_second_cache_segment(self):
        athlete = Athlete(user_id="42", name="Marta")
        today = dt.date(2026, 4, 20)
        before = build_system(athlete, today)

        athlete.facts.append("Runs before work")
        after = build_system(athlete, today)

        self.assertEqual(len(before), 2)
        self.assertEqual([block["cache_control"] for block in after],
                         [{"type": "ephemeral"}] * 2)
        self.assertEqual(before[0], after[0])
        self.assertEqual(before[0]["text"], INSTRUCTIONS)
        self.assertNotEqual(before[1]["text"], after[1]["text"])
        self.assertIn("Runs before work", after[1]["text"])

    def test_request_keeps_selected_tools_and_static_segment_stable(self):
        today = dt.date(2026, 4, 20)
        tools = select_tools("How should I plan my week?")
        first = build_request(Athlete(user_id="42", name="Marta"), [], tools, today)
        second = build_request(Athlete(user_id="77", name="Jonas"), [], tools, today)

        self.assertEqual(first["tools"], second["tools"])
        self.assertEqual(first["system"][0], second["system"][0])
        self.assertNotEqual(first["system"][1], second["system"][1])


if __name__ == "__main__":
    unittest.main()
