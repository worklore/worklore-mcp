import unittest
from datetime import datetime, timezone

import journal


def at(s):
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


class JournalTest(unittest.TestCase):
    def setUp(self):
        journal.reset()

    def test_publish_stores_post(self):
        p = journal.publish({"author": "kim", "title": "t", "body": "b",
                             "date": "2026-03-10"}, "UTC",
                            now=at("2026-03-10T12:00:00"))
        self.assertEqual(p["title"], "t")
        self.assertEqual(p["date"], "2026-03-10")
        self.assertEqual(p["received_at"], "2026-03-10T12:00:00+00:00")

    def test_publish_requires_author_date(self):
        with self.assertRaises(ValueError):
            journal.publish({"author": "kim", "title": "t", "body": "b"}, "UTC")
        self.assertEqual(journal.feed(), [])

    def test_display_date_is_authors_date_for_every_viewer(self):
        p = journal.publish({"author": "kim", "title": "t", "body": "b",
                             "date": "2026-07-31"}, "America/Argentina/Buenos_Aires",
                            now=at("2026-08-01T02:30:00"))
        for viewer_tz in ("UTC", "Asia/Tokyo", "America/Argentina/Buenos_Aires"):
            self.assertEqual(journal.display_date(p, viewer_tz), "2026-07-31")

    def test_feed_orders_by_receipt_across_author_dates(self):
        tokyo = journal.publish({"author": "aki", "title": "Tokyo", "body": "",
                                 "date": "2026-08-01"}, "Asia/Tokyo",
                                now=at("2026-07-31T14:30:00"))
        buenos_aires = journal.publish({"author": "ana", "title": "Buenos Aires",
                                        "body": "", "date": "2026-07-31"},
                                       "America/Argentina/Buenos_Aires",
                                       now=at("2026-08-01T02:30:00"))
        self.assertEqual([p["title"] for p in journal.feed()],
                         ["Buenos Aires", "Tokyo"])
        self.assertEqual(journal.display_date(tokyo, "America/Argentina/Buenos_Aires"),
                         "2026-08-01")
        self.assertEqual(journal.display_date(buenos_aires, "Asia/Tokyo"),
                         "2026-07-31")

    def test_feed_falls_back_to_date_for_older_posts(self):
        journal._POSTS.extend([
            {"author": "kim", "title": "old", "date": "2026-03-09"},
            {"author": "kim", "title": "new", "date": "2026-03-10"},
        ])
        self.assertEqual([p["title"] for p in journal.feed()], ["new", "old"])


if __name__ == "__main__":
    unittest.main()
