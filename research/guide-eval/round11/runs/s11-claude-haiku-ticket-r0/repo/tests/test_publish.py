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
        # The empty-table path has no similar stories, so it never produces a
        # score. Seed one story first so the scoring path actually runs.
        table = FakeTable()
        app.publish(table, {
            "slug": "first-story",
            "title": "First",
            "tags": ["cron"],
            "body": "cron runs twice",
        })
        stored = app.publish(table, {
            "slug": "second-story",
            "title": "Second",
            "tags": ["cron", "linux"],
            "body": "cron twice again",
        })
        self.assertEqual(len(stored["similar"]), 1)
        self.assertEqual(stored["similar"][0]["slug"], "first-story")
        saved = table.get_item(Key={"slug": "second-story"})["Item"]
        # tags: {cron} vs {cron, linux} -> 1/2; words: 2 shared of 4 -> 1/2
        # score = 0.7 * 0.5 + 0.3 * 0.5 = 0.5
        self.assertEqual(saved["similar"][0]["score"], Decimal("0.5"))

    def test_handler_returns_201_when_table_is_populated(self):
        table = FakeTable()
        seed = {"slug": "first-story", "title": "First", "tags": ["cron"], "body": "cron runs twice"}
        self.assertEqual(app.handler({"body": json.dumps(seed)}, table)["statusCode"], 201)
        second = {"slug": "second-story", "title": "Second", "tags": ["cron", "linux"], "body": "cron twice again"}
        self.assertEqual(app.handler({"body": json.dumps(second)}, table)["statusCode"], 201)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.5, "b": [{"c": 1.25}], "d": 3, "e": "x"})
        self.assertEqual(out, {"a": Decimal("0.5"), "b": [{"c": Decimal("1.25")}], "d": 3, "e": "x"})
        self.assertIsInstance(out["a"], Decimal)


if __name__ == "__main__":
    unittest.main()
