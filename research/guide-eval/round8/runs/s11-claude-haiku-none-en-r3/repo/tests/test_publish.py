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

    def test_publish_second_story_with_related(self):
        # The second publish is the first one that gets a non-empty `similar`
        # list; a float score there used to make DynamoDB reject the write.
        table = FakeTable()
        app.publish(table, {
            "slug": "first-story",
            "title": "First",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me.",
        })
        stored = app.publish(table, {
            "slug": "second-story",
            "title": "Second",
            "tags": ["cron"],
            "body": "Why does my cron job run twice?",
        })
        self.assertEqual([s["slug"] for s in stored["similar"]], ["first-story"])
        self.assertEqual(table.scan()["Count"], 2)


if __name__ == "__main__":
    unittest.main()
