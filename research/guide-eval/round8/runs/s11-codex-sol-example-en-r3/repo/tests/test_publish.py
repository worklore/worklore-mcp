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

    def test_second_publish_stores_related_score(self):
        table = FakeTable()
        first = {
            "slug": "first-story",
            "title": "First story",
            "tags": ["python", "aws"],
            "body": "Publishing stories with Python",
        }
        second = {
            "slug": "second-story",
            "title": "Second story",
            "tags": ["python", "testing"],
            "body": "Testing stories with Python",
        }

        for story in (first, second):
            response = app.handler({"body": json.dumps(story)}, table)
            self.assertEqual(response["statusCode"], 201)

        self.assertEqual(table.scan()["Count"], 2)
        stored = table.get_item(Key={"slug": second["slug"]})["Item"]
        self.assertEqual(stored["similar"][0]["slug"], first["slug"])
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)
        self.assertGreater(stored["similar"][0]["score"], 0)


if __name__ == "__main__":
    unittest.main()
