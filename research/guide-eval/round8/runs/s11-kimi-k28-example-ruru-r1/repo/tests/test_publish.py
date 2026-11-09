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

    def test_publish_with_existing_row(self):
        # The state-dependent path: similarity scores only exist once the
        # table has a row, so the second publish is the one that can fail.
        table = FakeTable()
        first = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        app.publish(table, first)
        second = {
            "slug": "my-backup-ran-twice",
            "title": "My backup ran twice",
            "tags": ["cron"],
            "body": "The cron line again, and the backup script was not idempotent.",
        }
        stored = app.publish(table, second)
        self.assertEqual(len(stored["similar"]), 1)
        score = stored["similar"][0]["score"]
        self.assertIsInstance(score, Decimal)
        self.assertEqual(table.scan()["Count"], 2)


if __name__ == "__main__":
    unittest.main()
