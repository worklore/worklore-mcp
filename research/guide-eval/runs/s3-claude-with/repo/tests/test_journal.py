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

    # --- author-local dates ---

    def test_late_evening_buenos_aires_keeps_local_date(self):
        # 23:30 on Jul 31 in Buenos Aires (UTC-3) is 02:30 Aug 1 UTC.
        p = journal.publish({"author": "val", "title": "t", "body": ""},
                            "America/Argentina/Buenos_Aires",
                            now=at("2026-08-01T02:30:00"))
        self.assertEqual(p["date"], "2026-07-31")

    def test_late_evening_tokyo_keeps_local_date(self):
        # 23:30 on Jul 31 in Tokyo (UTC+9) is 14:30 Jul 31 UTC.
        p = journal.publish({"author": "yui", "title": "t", "body": ""}, "Asia/Tokyo",
                            now=at("2026-07-31T14:30:00"))
        self.assertEqual(p["date"], "2026-07-31")

    def test_early_morning_tokyo_keeps_local_date(self):
        # 00:30 on Aug 1 in Tokyo is still Jul 31 in UTC.
        p = journal.publish({"author": "yui", "title": "t", "body": ""}, "Asia/Tokyo",
                            now=at("2026-07-31T15:30:00"))
        self.assertEqual(p["date"], "2026-08-01")

    def test_client_supplied_date_is_stored_verbatim(self):
        p = journal.publish({"author": "val", "title": "t", "body": "", "date": "2026-07-31"},
                            "America/Argentina/Buenos_Aires",
                            now=at("2026-08-01T02:30:00"))
        self.assertEqual(p["date"], "2026-07-31")

    def test_invalid_client_date_rejected(self):
        with self.assertRaises(ValueError):
            journal.publish({"author": "a", "title": "t", "body": "", "date": "31/07/2026"},
                            "UTC", now=at("2026-08-01T02:30:00"))

    def test_unknown_zone_rejected_when_date_must_be_derived(self):
        with self.assertRaises(ValueError):
            journal.publish({"author": "a", "title": "t", "body": ""}, "Mars/Olympus",
                            now=at("2026-08-01T02:30:00"))

    def test_display_date_is_identical_for_every_viewer(self):
        p = journal.publish({"author": "val", "title": "t", "body": ""},
                            "America/Argentina/Buenos_Aires",
                            now=at("2026-08-01T02:30:00"))
        for tz in ["UTC", "Pacific/Kiritimati", "Pacific/Pago_Pago", "Asia/Tokyo",
                   "America/Argentina/Buenos_Aires", "Europe/Berlin"]:
            self.assertEqual(journal.display_date(p, tz), "2026-07-31", tz)

    def test_publish_records_utc_received_at(self):
        p = journal.publish({"author": "yui", "title": "t", "body": ""}, "Asia/Tokyo",
                            now=at("2026-07-31T14:30:00"))
        self.assertEqual(p["received_at"], "2026-07-31T14:30:00+00:00")

    def test_feed_orders_same_evening_posts_by_submission(self):
        # Both authors publish at 23:30 local on Jul 31; Tokyo submits first in
        # real time, Buenos Aires 12 hours later. Same calendar date, true order.
        tokyo = journal.publish({"author": "yui", "title": "tokyo", "body": ""},
                                "Asia/Tokyo", now=at("2026-07-31T14:30:00"))
        ba = journal.publish({"author": "val", "title": "ba", "body": ""},
                             "America/Argentina/Buenos_Aires", now=at("2026-08-01T02:30:00"))
        self.assertEqual(tokyo["date"], "2026-07-31")
        self.assertEqual(ba["date"], "2026-07-31")
        self.assertEqual([p["title"] for p in journal.feed()], ["ba", "tokyo"])

    def test_feed_uses_receipt_time_not_author_name(self):
        journal.publish({"author": "zed", "title": "first", "body": ""}, "UTC",
                        now=at("2026-03-10T08:00:00"))
        journal.publish({"author": "amy", "title": "second", "body": ""}, "UTC",
                        now=at("2026-03-10T09:00:00"))
        self.assertEqual([p["title"] for p in journal.feed()], ["second", "first"])


if __name__ == "__main__":
    unittest.main()
