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
            "tags": ["cron", "linux"],
            "body": "A cron job ran twice",
        }
        second = {
            "slug": "second-story",
            "title": "Second story",
            "tags": ["cron"],
            "body": "A cron job ran again",
        }

        self.assertEqual(app.handler({"body": app.json.dumps(first)}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": app.json.dumps(second)}, table)["statusCode"], 201)
        stored = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertEqual(stored["similar"][0]["slug"], "first-story")
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)
        self.assertGreater(stored["similar"][0]["score"], 0)

        third = {
            "slug": "third-story",
            "title": "Third story",
            "tags": ["linux"],
            "body": "A cron job ran today",
        }
        self.assertEqual(app.handler({"body": app.json.dumps(third)}, table)["statusCode"], 201)
        stored = table.get_item(Key={"slug": "third-story"})["Item"]
        self.assertEqual(len(stored["similar"]), 2)
        self.assertTrue(all(isinstance(entry["score"], Decimal) for entry in stored["similar"]))


if __name__ == "__main__":
    unittest.main()
