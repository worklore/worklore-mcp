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

    def test_publish_with_existing_record_stores_decimal_scores(self):
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        stored = app.publish(table, {
            "slug": "dynamo-decimals-or-bust",
            "title": "DynamoDB wants Decimals",
            "tags": ["dynamodb", "python"],
            "body": "A float in an item makes put_item raise on the second write.",
        })
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual(len(stored["similar"]), 1)
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)

    def test_handler_publish_twice_returns_201(self):
        table = FakeTable()
        first = json.dumps({
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        second = json.dumps({
            "slug": "dynamo-decimals-or-bust",
            "title": "DynamoDB wants Decimals",
            "tags": ["dynamodb", "python"],
            "body": "A float in an item makes put_item raise on the second write.",
        })
        self.assertEqual(app.handler({"body": first}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": second}, table)["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
