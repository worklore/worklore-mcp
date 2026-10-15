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

    def test_date_uses_author_zone_ahead_of_utc(self):
        # 23:30 UTC on Mar 9 is 08:30 on Mar 10 in Tokyo.
        p = journal.publish({"author": "aiko", "title": "t", "body": "b"}, "Asia/Tokyo",
                            now=at("2026-03-09T23:30:00"))
        self.assertEqual(p["date"], "2026-03-10")
        self.assertEqual(journal.display_date(p, "Asia/Tokyo"), "2026-03-10")

    def test_date_uses_author_zone_behind_utc(self):
        # 02:00 UTC on Mar 10 is still Mar 9 evening in Los Angeles.
        p = journal.publish({"author": "sam", "title": "t", "body": "b"}, "America/Los_Angeles",
                            now=at("2026-03-10T02:00:00"))
        self.assertEqual(p["date"], "2026-03-09")
        self.assertEqual(journal.display_date(p, "America/Los_Angeles"), "2026-03-09")

    def test_display_date_stable_for_far_zones(self):
        p = journal.publish({"author": "kim", "title": "t", "body": "b"}, "UTC",
                            now=at("2026-01-10T12:00:00"))
        for tz in ("Pacific/Auckland", "Pacific/Kiritimati", "Pacific/Pago_Pago", "UTC"):
            self.assertEqual(journal.display_date(p, tz), "2026-01-10", tz)

    def test_invalid_client_tz_falls_back_to_utc(self):
        for tz in ("Not/AZone", "", None):
            p = journal.publish({"author": "kim", "title": "t", "body": "b"}, tz,
                                now=at("2026-03-09T23:30:00"))
            self.assertEqual(p["date"], "2026-03-09")

    def test_feed_orders_by_time_across_zones(self):
        # LA post is later in absolute time but has an earlier local date.
        journal.publish({"author": "aiko", "title": "tokyo", "body": ""}, "Asia/Tokyo",
                        now=at("2026-03-09T23:30:00"))
        journal.publish({"author": "sam", "title": "la", "body": ""}, "America/Los_Angeles",
                        now=at("2026-03-10T02:00:00"))
        self.assertEqual([p["title"] for p in journal.feed()], ["la", "tokyo"])

    def test_feed_same_day_newest_first_not_by_author(self):
        journal.publish({"author": "zed", "title": "morning", "body": ""}, "UTC",
                        now=at("2026-03-10T08:00:00"))
        journal.publish({"author": "amy", "title": "evening", "body": ""}, "UTC",
                        now=at("2026-03-10T20:00:00"))
        self.assertEqual([p["title"] for p in journal.feed()], ["evening", "morning"])


if __name__ == "__main__":
    unittest.main()
