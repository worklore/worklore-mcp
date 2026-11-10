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

    def test_publish_into_populated_table(self):
        # The second write is the one that exercises related() with a real
        # score, so seed one record first and publish a second one.
        table = FakeTable()
        app.publish(table, {
            "slug": "first-story",
            "title": "First",
            "tags": ["cron", "linux"],
            "body": "Two crontabs ran the same job.",
        })
        stored = app.publish(table, {
            "slug": "second-story",
            "title": "Second",
            "tags": ["cron"],
            "body": "A crontab ran the job twice.",
        })
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual([s["slug"] for s in stored["similar"]], ["first-story"])
        self.assertGreater(stored["similar"][0]["score"], 0)
        saved = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertEqual(saved["similar"][0]["slug"], "first-story")

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        first = app.handler({"body": json.dumps({
            "slug": "first-story", "title": "First", "tags": ["cron"],
            "body": "cron jobs run twice",
        })}, table)
        second = app.handler({"body": json.dumps({
            "slug": "second-story", "title": "Second", "tags": ["cron"],
            "body": "cron jobs ran twice",
        })}, table)
        self.assertEqual(first["statusCode"], 201)
        self.assertEqual(second["statusCode"], 201, second["body"])

    def test_for_dynamo_converts_nested_floats(self):
        out = app.for_dynamo({"a": 0.25, "b": [{"c": 1.5}], "d": 3})
        self.assertEqual(out, {"a": Decimal("0.25"), "b": [{"c": Decimal("1.5")}], "d": 3})


if __name__ == "__main__":
    unittest.main()
