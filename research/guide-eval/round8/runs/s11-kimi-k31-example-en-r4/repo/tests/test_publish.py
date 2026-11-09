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

    def test_publish_to_populated_table_stores_integer_scores(self):
        table = FakeTable()
        table.put_item(Item={
            "slug": "existing-story",
            "title": "Existing story",
            "tags": ["cron"],
            "body": "A repeated body.",
            "published_at": 1,
            "similar": [],
        })
        story = {
            "slug": "new-story",
            "title": "New story",
            "tags": ["cron"],
            "body": "A repeated body.",
        }

        stored = app.publish(table, story)

        self.assertEqual(stored["similar"], [{"slug": "existing-story", "score": 100}])
        self.assertIsInstance(stored["similar"][0]["score"], int)
        self.assertEqual(table.scan()["Count"], 2)


if __name__ == "__main__":
    unittest.main()
