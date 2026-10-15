import unittest
from datetime import datetime, timezone

import journal


def at(s):
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


class JournalTest(unittest.TestCase):
    def setUp(self):
        journal.reset()

    def test_publish_stores_post(self):
        p = journal.publish({"author": "kim", "title": "t", "body": "b"}, "2026-03-10",
                            now=at("2026-03-10T12:00:00"))
        self.assertEqual(p["title"], "t")
        self.assertEqual(p["date"], "2026-03-10")
        self.assertEqual(p["received_at"], "2026-03-10T12:00:00+00:00")

    def test_display_date_utc_viewer(self):
        p = journal.publish({"author": "kim", "title": "t", "body": "b"}, "2026-03-10",
                            now=at("2026-03-10T12:00:00"))
        self.assertEqual(journal.display_date(p, "UTC"), "2026-03-10")

    def test_display_date_berlin_midday(self):
        p = journal.publish({"author": "lena", "title": "t", "body": "b"}, "2026-03-10",
                            now=at("2026-03-10T09:00:00"))
        self.assertEqual(journal.display_date(p, "Europe/Berlin"), "2026-03-10")

    def test_feed_newest_first(self):
        journal.publish({"author": "kim", "title": "old", "body": ""}, "2026-03-09",
                        now=at("2026-03-09T12:00:00"))
        journal.publish({"author": "kim", "title": "new", "body": ""}, "2026-03-10",
                        now=at("2026-03-10T12:00:00"))
        self.assertEqual([p["title"] for p in journal.feed()], ["new", "old"])

    def test_verify_reproduce_scenario(self):
        # Tokyo user (UTC+9) submits at 23:30 local on July 31.
        # 2026-07-31T23:30+09:00 is 2026-07-31T14:30:00Z
        p1 = journal.publish({"author": "tokyo_user", "title": "tokyo post", "body": ""}, "2026-07-31",
                             now=at("2026-07-31T14:30:00"))

        # Buenos Aires user (UTC-3) submits at 23:30 local on July 31.
        # 2026-07-31T23:30-03:00 is 2026-08-01T02:30:00Z
        p2 = journal.publish({"author": "ba_user", "title": "ba post", "body": ""}, "2026-07-31",
                             now=at("2026-08-01T02:30:00"))

        # Each author must see their own local date
        self.assertEqual(journal.display_date(p1, "Asia/Tokyo"), "2026-07-31")
        self.assertEqual(journal.display_date(p2, "America/Argentina/Buenos_Aires"), "2026-07-31")

        # Feed order must match submission order (newest first, so ba_user then tokyo_user)
        self.assertEqual([p["author"] for p in journal.feed()], ["ba_user", "tokyo_user"])


if __name__ == "__main__":
    unittest.main()
