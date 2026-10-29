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

    def test_second_publish_stores_related_stories(self):
        # Regression: the second publish has an existing story to score against,
        # so the stored "similar" scores were floats and DynamoDB rejected the put.
        table = FakeTable()
        app.publish(table, {"slug": "first-story", "title": "First", "tags": ["cron", "linux"], "body": "cron ran twice"})
        stored = app.publish(table, {"slug": "second-story", "title": "Second", "tags": ["cron"], "body": "cron ran twice"})
        self.assertEqual([s["slug"] for s in stored["similar"]], ["first-story"])
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual(table.get_item(Key={"slug": "second-story"})["Item"]["similar"][0]["slug"], "first-story")


if __name__ == "__main__":
    unittest.main()
