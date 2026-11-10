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

    def test_second_publish_into_populated_table(self):
        # The first publish always sees an empty table, so scoring never runs there.
        # Seed one story first so the similarity path is exercised.
        table = FakeTable()
        app.publish(table, {
            "slug": "seed-story",
            "title": "Seed",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        story = {
            "slug": "second-story",
            "title": "Second",
            "tags": ["cron"],
            "body": "Two crontabs both had the line, so cron ran twice.",
        }
        stored = app.publish(table, story)
        self.assertEqual(stored["similar"][0]["slug"], "seed-story")
        item = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertIsInstance(item["similar"][0]["score"], Decimal)
        self.assertGreater(item["similar"][0]["score"], 0)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        first = {"slug": "first-story", "title": "First", "tags": ["cron"], "body": "cron ran twice"}
        second = {"slug": "second-story", "title": "Second", "tags": ["cron"], "body": "cron ran twice again"}
        self.assertEqual(app.handler({"body": json.dumps(first)}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": json.dumps(second)}, table)["statusCode"], 201)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.5, "b": [{"score": 0.25}], "c": 3})
        self.assertEqual(out, {"a": Decimal("0.5"), "b": [{"score": Decimal("0.25")}], "c": 3})


if __name__ == "__main__":
    unittest.main()
