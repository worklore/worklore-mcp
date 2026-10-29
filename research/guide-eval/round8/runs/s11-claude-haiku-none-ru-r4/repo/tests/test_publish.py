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

    def test_second_publish_with_similar_story_is_stored(self):
        # The first publish has no neighbours; the second one stores a non-empty
        # `similar` list with scores, which is the case that used to fail in prod.
        table = FakeTable()
        app.publish(table, {"slug": "first-story", "title": "First", "tags": ["cron", "linux"],
                            "body": "cron runs twice here"})
        stored = app.publish(table, {"slug": "second-story", "title": "Second", "tags": ["cron"],
                                     "body": "cron runs once"})
        self.assertEqual([s["slug"] for s in stored["similar"]], ["first-story"])
        item = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertEqual(item["similar"][0]["slug"], "first-story")
        self.assertIsInstance(item["similar"][0]["score"], Decimal)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        body = lambda slug, tags: json.dumps({"slug": slug, "title": slug.title(), "tags": tags,
                                              "body": "cron runs twice"})
        first = app.handler({"body": body("first-story", ["cron"])}, table)
        second = app.handler({"body": body("second-story", ["cron"])}, table)
        self.assertEqual(first["statusCode"], 201)
        self.assertEqual(second["statusCode"], 201)

    def test_to_dynamo_converts_floats_recursively(self):
        out = app.to_dynamo({"a": 0.1, "b": [1.5, {"c": 2.0}], "d": "x", "e": 3})
        self.assertEqual(out, {"a": Decimal("0.1"), "b": [Decimal("1.5"), {"c": Decimal("2.0")}], "d": "x", "e": 3})


if __name__ == "__main__":
    unittest.main()
