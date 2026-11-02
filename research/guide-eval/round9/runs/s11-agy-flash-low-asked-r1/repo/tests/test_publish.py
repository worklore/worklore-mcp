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

    def test_publish_second_story_succeeds_with_similarity(self):
        table = FakeTable()
        story1 = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        story2 = {
            "slug": "cron-troubleshooting-guide",
            "title": "Cron Troubleshooting Guide",
            "tags": ["cron", "monitoring"],
            "body": "Debugging cron issues on linux systems.",
        }
        app.publish(table, story1)
        stored2 = app.publish(table, story2)
        self.assertEqual(stored2["slug"], "cron-troubleshooting-guide")
        self.assertEqual(len(stored2["similar"]), 1)
        self.assertEqual(stored2["similar"][0]["slug"], "why-my-cron-ran-twice")
        item2 = table.get_item(Key={"slug": "cron-troubleshooting-guide"})["Item"]
        self.assertEqual(len(item2["similar"]), 1)

    def test_handler_second_publish(self):
        table = FakeTable()
        event1 = {
            "body": '{"slug": "story-one", "title": "Story One", "tags": ["a"], "body": "hello world"}'
        }
        event2 = {
            "body": '{"slug": "story-two", "title": "Story Two", "tags": ["a"], "body": "hello there"}'
        }
        resp1 = app.handler(event1, table)
        self.assertEqual(resp1["statusCode"], 201)
        resp2 = app.handler(event2, table)
        self.assertEqual(resp2["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
