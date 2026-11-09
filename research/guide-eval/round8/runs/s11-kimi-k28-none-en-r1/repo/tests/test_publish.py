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

    def test_second_publish_stores_similar_as_decimal(self):
        # Regression: the first publish wrote an empty "similar" list, so the
        # float scores only reached DynamoDB on the second publish and 500'd.
        table = FakeTable()
        first = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        second = {
            "slug": "cron-dst-bite-me",
            "title": "Cron and DST bit me",
            "tags": ["cron"],
            "body": "My cron jobs shifted an hour when DST ended.",
        }
        app.publish(table, first)
        stored = app.publish(table, second)
        self.assertEqual(len(stored["similar"]), 1)
        score = stored["similar"][0]["score"]
        self.assertIsInstance(score, Decimal)
        self.assertEqual(table.get_item(Key={"slug": "cron-dst-bite-me"})["Item"]["similar"][0]["slug"],
                         "why-my-cron-ran-twice")


if __name__ == "__main__":
    unittest.main()
