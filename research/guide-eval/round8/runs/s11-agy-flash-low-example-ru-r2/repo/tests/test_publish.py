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

    def test_publish_second_story_succeeds(self):
        table = FakeTable()
        story1 = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        app.publish(table, story1)

        story2 = {
            "slug": "another-cron-story",
            "title": "Another cron story",
            "tags": ["cron", "monitoring"],
            "body": "Testing cron jobs and alerts.",
        }
        stored2 = app.publish(table, story2)
        self.assertEqual(stored2["slug"], "another-cron-story")
        self.assertEqual(table.scan()["Count"], 2)
        self.assertTrue(len(stored2["similar"]) > 0)
        self.assertEqual(stored2["similar"][0]["slug"], "why-my-cron-ran-twice")

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        event1 = {
            "body": '{"slug": "story-one", "title": "Story One", "tags": ["test"], "body": "First story body"}'
        }
        res1 = app.handler(event1, table)
        self.assertEqual(res1["statusCode"], 201)

        event2 = {
            "body": '{"slug": "story-two", "title": "Story Two", "tags": ["test"], "body": "Second story body"}'
        }
        res2 = app.handler(event2, table)
        self.assertEqual(res2["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
