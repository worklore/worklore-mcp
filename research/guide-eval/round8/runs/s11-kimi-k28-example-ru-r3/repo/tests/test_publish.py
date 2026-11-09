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

    def test_publish_with_populated_table(self):
        # Regression: the second publish is the first one that stores a
        # computed similarity score — the empty-table path hides float bugs.
        table = FakeTable()
        first = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        r1 = app.handler({"body": json.dumps(first)}, table)
        self.assertEqual(r1["statusCode"], 201)

        second = {
            "slug": "cron-quirks-and-me",
            "title": "Cron quirks and me",
            "tags": ["cron"],
            "body": "Another cron story, partly about the same crontab line.",
        }
        r2 = app.handler({"body": json.dumps(second)}, table)
        self.assertEqual(r2["statusCode"], 201)

        stored = table.get_item(Key={"slug": "cron-quirks-and-me"})["Item"]
        self.assertEqual(len(stored["similar"]), 1)
        self.assertEqual(stored["similar"][0]["slug"], "why-my-cron-ran-twice")
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)
        self.assertGreater(stored["similar"][0]["score"], 0)


if __name__ == "__main__":
    unittest.main()
