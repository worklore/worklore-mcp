import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bot


class SystemCacheTest(unittest.TestCase):
    def test_save_fact_changes_only_athlete_cache_segment(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(bot, "ATHLETES_FILE", str(Path(directory) / "athletes.json")):
                athlete = bot.Athlete(user_id="42", name="Ada")
                today = dt.date(2026, 4, 18)
                tools = bot.select_tools("Remember that I ride on Sundays")
                before = bot.build_request(athlete, [], tools, today)

                bot.run_tool(athlete, "save_fact", {"fact": "Rides on Sundays"})
                after = bot.build_request(bot.load_athlete("42"), [], tools, today)

        self.assertEqual(len(before["system"]), 2)
        self.assertEqual(before["system"][0], after["system"][0])
        self.assertNotEqual(before["system"][1]["text"], after["system"][1]["text"])
        self.assertIn("Rides on Sundays", after["system"][1]["text"])
        self.assertEqual(before["tools"], after["tools"])
        self.assertEqual(
            [block["cache_control"] for block in after["system"]],
            [{"type": "ephemeral"}, {"type": "ephemeral"}],
        )


if __name__ == "__main__":
    unittest.main()
