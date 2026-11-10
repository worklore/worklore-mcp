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

    def test_second_publish_with_seeded_table(self):
        # The populated path: similarity scores are computed and written. The
        # first-write test above never reaches it, which is how the float bug
        # shipped.
        table = FakeTable()
        app.publish(table, {"slug": "seed-story", "title": "Seed", "tags": ["cron", "linux"],
                            "body": "cron runs twice on linux"})
        second = {"slug": "second-story", "title": "Second", "tags": ["cron"],
                  "body": "cron linux job"}
        stored = app.publish(table, second)
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual(len(stored["similar"]), 1)
        item = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertEqual(item["similar"][0]["slug"], "seed-story")
        self.assertIsInstance(item["similar"][0]["score"], Decimal)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        first = app.handler({"body": json.dumps({"slug": "seed-story", "title": "Seed",
                                                 "tags": ["cron"], "body": "cron linux"})}, table)
        second = app.handler({"body": json.dumps({"slug": "second-story", "title": "Second",
                                                  "tags": ["cron"], "body": "cron linux job"})}, table)
        self.assertEqual(first["statusCode"], 201)
        self.assertEqual(second["statusCode"], 201)

    def test_to_dynamo_converts_floats_recursively(self):
        out = app.to_dynamo({"a": 0.1234, "b": [1, 0.5, {"c": 2.0}], "d": "x", "e": 3})
        self.assertEqual(out, {"a": Decimal("0.1234"), "b": [1, Decimal("0.5"), {"c": Decimal("2.0")}],
                               "d": "x", "e": 3})
        self.assertIsInstance(out["a"], Decimal)


if __name__ == "__main__":
    unittest.main()
