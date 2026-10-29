import json
import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import app  # noqa: E402
from fake_dynamo import FakeTable  # noqa: E402


class PublishTest(unittest.TestCase):
    def test_publish_stores_story(self):
        table = FakeTable()
        story = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        stored = app.publish(table, story)
        self.assertEqual(stored["slug"], "why-my-cron-ran-twice")
        self.assertEqual(table.get_item(Key={"slug": "why-my-cron-ran-twice"})["Item"]["title"], "Why my cron ran twice")
        self.assertEqual(table.scan()["Count"], 1)

    def test_second_publish_with_existing_story(self):
        # The empty-table path skips similarity scoring entirely; seed one story
        # so the second publish actually computes and stores scores.
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        stored = app.publish(table, {
            "slug": "cron-and-timezones",
            "title": "Cron and timezones",
            "tags": ["cron", "tz"],
            "body": "My cron job ran an hour early after the DST switch.",
        })
        self.assertEqual(table.scan()["Count"], 2)
        similar = table.get_item(Key={"slug": "cron-and-timezones"})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], ["why-my-cron-ran-twice"])
        self.assertIsInstance(similar[0]["score"], Decimal)
        self.assertGreater(similar[0]["score"], 0)
        self.assertEqual(stored["similar"], similar)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        for slug in ("first-story", "second-story", "third-story"):
            body = json.dumps({"slug": slug, "title": slug, "tags": ["x"], "body": "same words here"})
            self.assertEqual(app.handler({"body": body}, table)["statusCode"], 201)
        # Re-publishing an existing slug must work too (scan returns it with Decimal scores).
        body = json.dumps({"slug": "first-story", "title": "again", "tags": ["x"], "body": "same words"})
        self.assertEqual(app.handler({"body": body}, table)["statusCode"], 201)

    def test_to_dynamo_rejects_non_finite(self):
        with self.assertRaises(ValueError):
            app.to_dynamo({"score": float("nan")})


if __name__ == "__main__":
    unittest.main()
