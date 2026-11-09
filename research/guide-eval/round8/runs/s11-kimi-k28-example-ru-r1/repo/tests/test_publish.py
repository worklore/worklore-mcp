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

    def test_publish_with_existing_story_computes_similarity(self):
        table = FakeTable()
        first = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        app.publish(table, first)

        second = {
            "slug": "cron-dst-bite-me",
            "title": "Cron, DST and me",
            "tags": ["cron", "dst"],
            "body": "The cron job ran twice that night, once before the clock change and once after.",
        }
        response = app.handler({"body": json.dumps(second)}, table)
        self.assertEqual(response["statusCode"], 201)

        stored = table.get_item(Key={"slug": "cron-dst-bite-me"})["Item"]
        self.assertEqual(len(stored["similar"]), 1)
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)


if __name__ == "__main__":
    unittest.main()
