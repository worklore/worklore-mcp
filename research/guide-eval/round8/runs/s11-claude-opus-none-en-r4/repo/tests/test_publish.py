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
        # Regression: the first publish has no neighbours (similar=[]), the
        # second gets float scores, which DynamoDB/boto3 rejects -> 500.
        table = FakeTable()
        first = {"slug": "why-my-cron-ran-twice", "title": "Cron twice",
                 "tags": ["cron", "linux"], "body": "Two crontabs both had the line."}
        second = {"slug": "cron-and-timezones", "title": "Cron and timezones",
                  "tags": ["cron"], "body": "The line ran at the wrong hour."}
        self.assertEqual(app.handler({"body": json.dumps(first)}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": json.dumps(second)}, table)["statusCode"], 201)
        similar = table.get_item(Key={"slug": "cron-and-timezones"})["Item"]["similar"]
        self.assertEqual(similar[0]["slug"], "why-my-cron-ran-twice")
        self.assertIsInstance(similar[0]["score"], Decimal)
        self.assertGreater(similar[0]["score"], 0)

    def test_many_publishes(self):
        table = FakeTable()
        for i in range(6):
            story = {"slug": f"story-{i}", "title": f"Story {i}",
                     "tags": ["a", f"t{i % 2}"], "body": f"shared words and {i}"}
            self.assertEqual(app.handler({"body": json.dumps(story)}, table)["statusCode"], 201)
        self.assertEqual(table.scan()["Count"], 6)
        self.assertEqual(len(table.get_item(Key={"slug": "story-5"})["Item"]["similar"]), 3)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": [{"s": 0.7}], "b": 1, "c": True})
        self.assertEqual(out, {"a": [{"s": Decimal("0.7")}], "b": 1, "c": True})
        with self.assertRaises(ValueError):
            app.to_dynamo({"x": float("nan")})


if __name__ == "__main__":
    unittest.main()
