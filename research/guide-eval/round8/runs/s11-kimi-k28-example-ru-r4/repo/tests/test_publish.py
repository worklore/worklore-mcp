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

    def test_publish_into_populated_table(self):
        """The first publish finds an empty table, so only the second publish
        exercises the similarity-score write path that failed in production."""
        table = FakeTable()
        first = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        resp = app.handler({"body": json.dumps(first)}, table)
        self.assertEqual(resp["statusCode"], 201)

        second = {
            "slug": "my-backup-routine",
            "title": "My backup routine",
            "tags": ["cron", "backups"],
            "body": "A cron line and a backup line, close cousins.",
        }
        resp = app.handler({"body": json.dumps(second)}, table)
        self.assertEqual(resp["statusCode"], 201)

        stored = table.get_item(Key={"slug": "my-backup-routine"})["Item"]
        self.assertEqual(len(stored["similar"]), 1)
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)


if __name__ == "__main__":
    unittest.main()
