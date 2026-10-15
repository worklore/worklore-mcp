import unittest
from datetime import datetime, timezone

import journal


def at(s):
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


class JournalTest(unittest.TestCase):
    def setUp(self):
        journal.reset()

    def test_publish_stores_post(self):
        p = journal.publish({"author": "kim", "title": "t", "body": "b"}, "UTC",
                            now=at("2026-03-10T12:00:00"))
        self.assertEqual(p["title"], "t")
        self.assertEqual(p["date"], "2026-03-10")

    def test_display_date_utc_viewer(self):
        p = journal.publish({"author": "kim", "title": "t", "body": "b"}, "UTC",
                            now=at("2026-03-10T12:00:00"))
        self.assertEqual(journal.display_date(p, "UTC"), "2026-03-10")

    def test_display_date_berlin_midday(self):
        p = journal.publish({"author": "lena", "title": "t", "body": "b"}, "Europe/Berlin",
                            now=at("2026-03-10T09:00:00"))
        self.assertEqual(journal.display_date(p, "Europe/Berlin"), "2026-03-10")

    def test_feed_newest_first(self):
        journal.publish({"author": "kim", "title": "old", "body": ""}, "UTC",
                        now=at("2026-03-09T12:00:00"))
        journal.publish({"author": "kim", "title": "new", "body": ""}, "UTC",
                        now=at("2026-03-10T12:00:00"))
        self.assertEqual([p["title"] for p in journal.feed()], ["new", "old"])

    def test_display_date_berlin_late_night(self):
        # 23:30 UTC on March 10 is 00:30 on March 11 in Europe/Berlin
        p = journal.publish({"author": "lena", "title": "t", "body": "b"}, "Europe/Berlin",
                            now=at("2026-03-10T23:30:00"))
        self.assertEqual(journal.display_date(p, "Europe/Berlin"), "2026-03-11")
        self.assertEqual(journal.display_date(p, "UTC"), "2026-03-10")

    def test_display_date_pacific_evening(self):
        # 04:00 UTC on March 11 is 20:00 on March 10 in America/Los_Angeles
        p = journal.publish({"author": "sam", "title": "t", "body": "b"}, "America/Los_Angeles",
                            now=at("2026-03-11T04:00:00"))
        self.assertEqual(journal.display_date(p, "America/Los_Angeles"), "2026-03-10")
        self.assertEqual(journal.display_date(p, "UTC"), "2026-03-11")

    def test_display_date_tokyo_morning(self):
        # 16:00 UTC on March 10 is 01:00 on March 11 in Asia/Tokyo
        p = journal.publish({"author": "ken", "title": "t", "body": "b"}, "Asia/Tokyo",
                            now=at("2026-03-10T16:00:00"))
        self.assertEqual(journal.display_date(p, "Asia/Tokyo"), "2026-03-11")
        self.assertEqual(journal.display_date(p, "UTC"), "2026-03-10")


if __name__ == "__main__":
    unittest.main()
