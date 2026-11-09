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

    def test_second_publish_with_related_story_succeeds(self):
        table = FakeTable()
        first = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        second = {
            "slug": "fixing-duplicate-cron-jobs",
            "title": "Fixing duplicate cron jobs",
            "tags": ["cron", "linux"],
            "body": "Two crontabs both ran the same script; here's how I found the duplicate cron jobs.",
        }
        r1 = app.handler({"body": json.dumps(first)}, table)
        r2 = app.handler({"body": json.dumps(second)}, table)
        self.assertEqual(r1["statusCode"], 201)
        self.assertEqual(r2["statusCode"], 201)
        stored = table.get_item(Key={"slug": "fixing-duplicate-cron-jobs"})["Item"]
        self.assertEqual(
            [s["slug"] for s in stored["similar"]],
            ["why-my-cron-ran-twice"],
        )
        self.assertTrue(all(isinstance(s["score"], Decimal) for s in stored["similar"]))


if __name__ == "__main__":
    unittest.main()
