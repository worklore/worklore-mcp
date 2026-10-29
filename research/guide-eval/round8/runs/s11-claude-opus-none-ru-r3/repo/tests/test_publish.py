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

    def test_second_publish_with_similar_stories(self):
        # Regression: the first publish has nothing to compare against, so
        # ``similar`` is empty; the second one stored float scores and boto3
        # rejected the item (logs/error.log, POST /stories -> 500).
        table = FakeTable()
        first = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        second = {
            "slug": "cron-and-timezones",
            "title": "Cron and timezones",
            "tags": ["cron"],
            "body": "The line ran at the wrong hour for me.",
        }
        third = {"slug": "untagged-note", "title": "Note", "body": "Nothing shared."}
        for story in (first, second, third):
            resp = app.handler({"body": json.dumps(story)}, table)
            self.assertEqual(resp["statusCode"], 201, resp)
        stored = table.get_item(Key={"slug": "cron-and-timezones"})["Item"]
        self.assertEqual(stored["similar"][0]["slug"], "why-my-cron-ran-twice")
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)
        self.assertEqual(len(table.get_item(Key={"slug": "untagged-note"})["Item"]["similar"]), 2)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.1234, "b": [{"c": 1.5}], "d": 3, "e": True, "f": "x"})
        self.assertEqual(out, {"a": Decimal("0.1234"), "b": [{"c": Decimal("1.5")}], "d": 3, "e": True, "f": "x"})


if __name__ == "__main__":
    unittest.main()
