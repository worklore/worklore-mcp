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

    def test_second_publish_with_existing_stories(self):
        # Similarity scores (floats) only exist once the table has stories;
        # the first publish into an empty table never exercises this path.
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
            "tags": ["cron", "time"],
            "body": "The server ran cron in UTC, and I wrote the line in local time.",
        })
        self.assertEqual(table.scan()["Count"], 2)
        similar = table.get_item(Key={"slug": "cron-and-timezones"})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], ["why-my-cron-ran-twice"])
        self.assertIsInstance(similar[0]["score"], Decimal)
        self.assertGreater(similar[0]["score"], 0)
        self.assertEqual(stored["similar"], similar)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        for slug, tags in (("first-story", ["a", "b"]), ("second-story", ["b", "c"])):
            event = {"body": json.dumps({"slug": slug, "title": slug, "tags": tags, "body": "same words here"})}
            self.assertEqual(app.handler(event, table)["statusCode"], 201)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.1, "b": [{"c": 1.5}], "d": 3, "e": "x"})
        self.assertEqual(out, {"a": Decimal("0.1"), "b": [{"c": Decimal("1.5")}], "d": 3, "e": "x"})


if __name__ == "__main__":
    unittest.main()
