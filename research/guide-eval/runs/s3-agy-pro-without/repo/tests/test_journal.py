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

    def test_viewer_sees_correct_date_different_tz(self):
        p = journal.publish({"author": "kim", "title": "t", "body": "b"}, "Asia/Tokyo",
                            now=at("2026-03-09T21:00:00"))
        self.assertEqual(journal.display_date(p, "Asia/Tokyo"), "2026-03-10")

    def test_feed_newest_first_same_day(self):
        journal.publish({"author": "zack", "title": "older", "body": ""}, "UTC",
                        now=at("2026-03-10T10:00:00"))
        journal.publish({"author": "alice", "title": "newer", "body": ""}, "UTC",
                        now=at("2026-03-10T14:00:00"))
        self.assertEqual([p["title"] for p in journal.feed()], ["newer", "older"])

if __name__ == "__main__":
    unittest.main()
