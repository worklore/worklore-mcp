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

    def test_second_publish_with_related_stories_succeeds(self):
        # Regression: the second publish stored a float similarity score in
        # `similar`, which DynamoDB rejects -> 500 in production.
        table = FakeTable()
        app.publish(table, {"slug": "first-story", "title": "First", "tags": ["cron", "linux"], "body": "cron runs twice"})
        status = app.handler(
            {"body": json.dumps({"slug": "second-story", "title": "Second", "tags": ["cron"], "body": "cron runs twice"})},
            table,
        )
        self.assertEqual(status["statusCode"], 201)
        item = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertEqual(len(item["similar"]), 1)
        self.assertEqual(item["similar"][0]["slug"], "first-story")
        self.assertIsInstance(item["similar"][0]["score"], Decimal)
        self.assertEqual(item["similar"][0]["score"], Decimal(str(app.similarity(
            {"tags": ["cron"], "body": "cron runs twice"},
            {"tags": ["cron", "linux"], "body": "cron runs twice"},
        ))))

    def test_floats_are_converted_to_decimal_exactly(self):
        self.assertEqual(app.to_dynamo({"a": [0.1, {"b": 2.5}], "c": 3}),
                         {"a": [Decimal("0.1"), {"b": Decimal("2.5")}], "c": 3})


if __name__ == "__main__":
    unittest.main()
