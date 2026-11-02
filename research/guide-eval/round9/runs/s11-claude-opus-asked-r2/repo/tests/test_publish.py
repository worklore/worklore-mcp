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

    def test_publish_into_populated_table(self):
        # The first publish sees an empty table, so no scores are computed.
        # Production broke on the second one: similarity scores are floats.
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
            "tags": ["cron"],
            "body": "The server ran cron in UTC and I wrote the line in local time.",
        })
        self.assertEqual(table.scan()["Count"], 2)
        similar = table.get_item(Key={"slug": "cron-and-timezones"})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], ["why-my-cron-ran-twice"])
        self.assertEqual(similar[0]["score"], Decimal(str(app.similarity(
            {"tags": ["cron"], "body": "The server ran cron in UTC and I wrote the line in local time."},
            {"tags": ["cron", "linux"], "body": "Two crontabs, one for root and one for me, both had the line."},
        ))))
        self.assertEqual(stored["similar"], similar)

    def test_handler_second_publish_is_201(self):
        table = FakeTable()
        for slug in ("first-story", "second-story", "third-story"):
            body = '{"slug": "%s", "title": "t", "tags": ["a"], "body": "same words"}' % slug
            self.assertEqual(app.handler({"body": body}, table)["statusCode"], 201)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.1, "b": [{"c": 1.5}], "d": 2, "e": True, "f": "x"})
        self.assertEqual(out, {"a": Decimal("0.1"), "b": [{"c": Decimal("1.5")}], "d": 2, "e": True, "f": "x"})


if __name__ == "__main__":
    unittest.main()
