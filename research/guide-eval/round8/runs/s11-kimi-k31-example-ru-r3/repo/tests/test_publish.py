import json
import os
import sys
import unittest

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

    def test_second_publish_with_existing_story(self):
        table = FakeTable()
        stories = [
            {
                "slug": "first-story",
                "title": "First story",
                "tags": ["cron", "linux"],
                "body": "The same cron job ran twice.",
            },
            {
                "slug": "second-story",
                "title": "Second story",
                "tags": ["cron", "linux"],
                "body": "The same cron job ran twice.",
            },
        ]

        first = app.handler({"body": json.dumps(stories[0])}, table)
        second = app.handler({"body": json.dumps(stories[1])}, table)

        self.assertEqual(first["statusCode"], 201)
        self.assertEqual(second["statusCode"], 201)
        self.assertEqual(table.scan()["Count"], 2)
        similar = table.get_item(Key={"slug": "second-story"})["Item"]["similar"]
        self.assertEqual(similar, [{"slug": "first-story", "score": 100}])
        self.assertIsInstance(similar[0]["score"], int)


if __name__ == "__main__":
    unittest.main()
