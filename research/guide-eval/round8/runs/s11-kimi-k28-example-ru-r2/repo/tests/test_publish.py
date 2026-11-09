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

    def test_publish_with_existing_record_stores_similar_scores(self):
        table = FakeTable()
        first = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        second = {
            "slug": "my-second-story",
            "title": "My second story",
            "tags": ["cron"],
            "body": "A second cron story with overlapping tags.",
        }
        app.publish(table, first)
        stored = app.publish(table, second)

        self.assertEqual(table.scan()["Count"], 2)
        self.assertTrue(stored["similar"])
        self.assertTrue(
            all(isinstance(entry["score"], Decimal) for entry in stored["similar"]),
            msg="similarity scores must be DynamoDB-safe (Decimal, not float)",
        )


if __name__ == "__main__":
    unittest.main()
