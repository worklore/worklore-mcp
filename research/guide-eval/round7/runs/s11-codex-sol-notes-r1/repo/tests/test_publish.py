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

    def test_publish_into_populated_table_stores_dynamodb_compatible_scores(self):
        table = FakeTable()
        first = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs ran the same job.",
        }
        second = {
            "slug": "debugging-a-cron-job",
            "title": "Debugging a cron job",
            "tags": ["cron", "debugging"],
            "body": "The same job ran twice.",
        }

        self.assertEqual(app.handler({"body": json.dumps(first)}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": json.dumps(second)}, table)["statusCode"], 201)

        stored = table.get_item(Key={"slug": second["slug"]})["Item"]
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual(stored["similar"][0]["slug"], first["slug"])
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)
        self.assertGreater(stored["similar"][0]["score"], 0)
        self.assertLessEqual(stored["similar"][0]["score"], 1)


if __name__ == "__main__":
    unittest.main()
