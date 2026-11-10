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

    def test_second_publish_with_related_story_is_stored(self):
        # The populated path: a second story finds a match, so its item carries a
        # similarity score. Seeding the table first is what exercises that path.
        table = FakeTable()
        app.publish(table, {
            "slug": "first-story",
            "title": "First",
            "tags": ["cron", "linux"],
            "body": "cron runs twice on linux",
        })
        stored = app.publish(table, {
            "slug": "second-story",
            "title": "Second",
            "tags": ["cron"],
            "body": "cron runs twice",
        })
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual(len(stored["similar"]), 1)
        self.assertEqual(stored["similar"][0]["slug"], "first-story")
        saved = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertIsInstance(saved["similar"][0]["score"], Decimal)
        self.assertEqual(saved["similar"][0]["score"], Decimal(str(stored["similar"][0]["score"])))

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        first = app.handler({"body": json.dumps({"slug": "first-story", "title": "First", "tags": ["cron"], "body": "cron twice"})}, table)
        second = app.handler({"body": json.dumps({"slug": "second-story", "title": "Second", "tags": ["cron"], "body": "cron twice again"})}, table)
        self.assertEqual(first["statusCode"], 201)
        self.assertEqual(second["statusCode"], 201)

    def test_to_dynamo_converts_floats_at_any_depth(self):
        value = {"a": 0.5, "b": [{"c": 0.25}], "d": 3, "e": "x", "f": None, "g": True}
        converted = app.to_dynamo(value)
        self.assertEqual(converted, {"a": Decimal("0.5"), "b": [{"c": Decimal("0.25")}], "d": 3, "e": "x", "f": None, "g": True})
        self.assertIsInstance(converted["a"], Decimal)
        self.assertIsInstance(converted["b"][0]["c"], Decimal)


if __name__ == "__main__":
    unittest.main()
