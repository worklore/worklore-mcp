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

    def test_author_date_and_viewer_date_across_midnight(self):
        p = journal.publish({"author": "kim", "title": "t", "body": "b"},
                            "America/Los_Angeles", now=at("2026-03-10T00:30:00"))
        self.assertEqual(p["date"], "2026-03-09")
        self.assertEqual(p["created_at"], "2026-03-10T00:30:00+00:00")
        self.assertEqual(journal.display_date(p, "America/Los_Angeles"), "2026-03-09")
        self.assertEqual(journal.display_date(p, "Asia/Tokyo"), "2026-03-10")

    def test_viewer_date_can_be_next_day(self):
        p = journal.publish({"author": "kim", "title": "t", "body": "b"},
                            "UTC", now=at("2026-03-10T23:30:00"))
        self.assertEqual(journal.display_date(p, "Asia/Tokyo"), "2026-03-11")

    def test_feed_newest_first(self):
        journal.publish({"author": "kim", "title": "old", "body": ""}, "UTC",
                        now=at("2026-03-09T12:00:00"))
        journal.publish({"author": "kim", "title": "new", "body": ""}, "UTC",
                        now=at("2026-03-10T12:00:00"))
        self.assertEqual([p["title"] for p in journal.feed()], ["new", "old"])

    def test_feed_uses_creation_instant_across_author_time_zones(self):
        journal.publish({"author": "z", "title": "old", "body": ""},
                        "Asia/Tokyo", now=at("2026-03-10T00:30:00"))
        journal.publish({"author": "a", "title": "new", "body": ""},
                        "America/Los_Angeles", now=at("2026-03-10T01:00:00"))
        self.assertEqual([p["title"] for p in journal.feed()], ["new", "old"])


if __name__ == "__main__":
    unittest.main()
