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
        # Regression: the second publish produced a float similarity score,
        # which DynamoDB rejects, so the handler returned 500.
        table = FakeTable()
        first = {"slug": "first-story", "title": "A", "tags": ["cron", "linux"],
                 "body": "cron ran twice on linux"}
        second = {"slug": "second-story", "title": "B", "tags": ["cron"],
                  "body": "cron ran once"}
        self.assertEqual(app.handler({"body": json.dumps(first)}, table)["statusCode"], 201)
        resp = app.handler({"body": json.dumps(second)}, table)
        self.assertEqual(resp["statusCode"], 201, resp)
        similar = table.get_item(Key={"slug": "second-story"})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], ["first-story"])
        self.assertIsInstance(similar[0]["score"], Decimal)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.5, "b": [{"c": 1.25}], "d": "x", "e": 3})
        self.assertEqual(out, {"a": Decimal("0.5"), "b": [{"c": Decimal("1.25")}], "d": "x", "e": 3})


if __name__ == "__main__":
    unittest.main()
