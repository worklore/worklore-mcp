import datetime as dt
import unittest
from unittest.mock import patch

import bot


class PromptCacheTests(unittest.TestCase):
    def test_memory_write_changes_only_second_cached_block(self):
        athlete = bot.Athlete(user_id="42", name="Alex")
        today = dt.date(2026, 4, 18)
        tools = bot.select_tools("Remember my preferred training day")
        messages = [{"role": "user", "content": "Remember my preferred training day"}]
        before = bot.build_request(athlete, messages, tools, today)

        with patch.object(bot, "save_athlete"):
            bot.run_tool(athlete, "save_fact", {"fact": "Prefers Tuesday training"})
        after = bot.build_request(athlete, messages, tools, today)

        first, second = before["system"]
        self.assertEqual(first, after["system"][0])
        self.assertEqual(first["text"], bot.INSTRUCTIONS)
        self.assertEqual(second["cache_control"], {"type": "ephemeral"})
        self.assertEqual(first["cache_control"], {"type": "ephemeral"})
        self.assertNotEqual(second["text"], after["system"][1]["text"])
        self.assertIn("Prefers Tuesday training", after["system"][1]["text"])
        self.assertEqual(before["tools"], after["tools"])

    def test_static_block_is_shared_across_athletes_and_dates(self):
        first = bot.build_system(bot.Athlete(user_id="1", name="Alex"), dt.date(2026, 4, 18))
        second = bot.build_system(bot.Athlete(user_id="2", name="Sam"), dt.date(2026, 4, 19))

        self.assertEqual(first[0], second[0])
        self.assertNotEqual(first[1]["text"], second[1]["text"])


if __name__ == "__main__":
    unittest.main()
