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


    def test_author_local_dates_and_feed_ordering_different_timezones(self):
        # 23:30 local in Tokyo (UTC+9) on 2026-07-31 -> 14:30 UTC on 2026-07-31
        tokyo_post = journal.publish(
            {"author": "tokyo_author", "title": "Tokyo", "body": "Evening in Tokyo", "date": "2026-07-31"},
            client_tz="Asia/Tokyo",
            now=at("2026-07-31T14:30:00"),
        )
        # 23:30 local in Buenos Aires (UTC-3) on 2026-07-31 -> 02:30 UTC on 2026-08-01
        ba_post = journal.publish(
            {"author": "ba_author", "title": "Buenos Aires", "body": "Evening in BA", "date": "2026-07-31"},
            client_tz="America/Argentina/Buenos_Aires",
            now=at("2026-08-01T02:30:00"),
        )

        # Each author sees their own local calendar date as written
        self.assertEqual(journal.display_date(tokyo_post, "Asia/Tokyo"), "2026-07-31")
        self.assertEqual(journal.display_date(ba_post, "America/Argentina/Buenos_Aires"), "2026-07-31")

        # Viewers across any timezone see the author's local date without conversion
        self.assertEqual(journal.display_date(tokyo_post, "America/Argentina/Buenos_Aires"), "2026-07-31")
        self.assertEqual(journal.display_date(ba_post, "Asia/Tokyo"), "2026-07-31")
        self.assertEqual(journal.display_date(ba_post, "UTC"), "2026-07-31")
        self.assertEqual(journal.display_date(tokyo_post), "2026-07-31")

        # Feed order matches submission order (newest first: BA submitted later in real time)
        feed_authors = [p["author"] for p in journal.feed()]
        self.assertEqual(feed_authors, ["ba_author", "tokyo_author"])

    def test_feed_ordering_fallback_to_date(self):
        # Posts without received_at fall back to date
        p1 = {"author": "a", "title": "day1", "body": "", "date": "2026-07-30"}
        p2 = {"author": "b", "title": "day2", "body": "", "date": "2026-07-31"}
        journal._POSTS.extend([p1, p2])
        self.assertEqual([p["title"] for p in journal.feed()], ["day2", "day1"])

    def test_received_at_stamped_on_publish(self):
        p = journal.publish(
            {"author": "kim", "title": "t", "body": "b", "date": "2026-07-31"},
            now=at("2026-07-31T14:30:00"),
        )
        self.assertEqual(p["received_at"], "2026-07-31T14:30:00+00:00")
        self.assertEqual(p["date"], "2026-07-31")


if __name__ == "__main__":
    unittest.main()
