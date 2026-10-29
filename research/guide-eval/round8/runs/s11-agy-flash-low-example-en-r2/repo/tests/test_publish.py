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

    def test_publish_second_story_succeeds_with_similarity_scores(self):
        table = FakeTable()
        story1 = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        story2 = {
            "slug": "another-cron-adventure",
            "title": "Another cron adventure",
            "tags": ["cron", "monitoring"],
            "body": "Crontab debugging in production on linux systems.",
        }
        app.publish(table, story1)
        stored2 = app.publish(table, story2)
        self.assertEqual(stored2["slug"], "another-cron-adventure")
        self.assertEqual(len(stored2["similar"]), 1)
        self.assertEqual(stored2["similar"][0]["slug"], "why-my-cron-ran-twice")
        self.assertEqual(table.scan()["Count"], 2)

    def test_handler_publish_twice(self):
        table = FakeTable()
        event1 = {
            "body": json.dumps({
                "slug": "story-one",
                "title": "Story One",
                "tags": ["test"],
                "body": "Body one",
            })
        }
        event2 = {
            "body": json.dumps({
                "slug": "story-two",
                "title": "Story Two",
                "tags": ["test"],
                "body": "Body two",
            })
        }
        res1 = app.handler(event1, table)
        self.assertEqual(res1["statusCode"], 201)
        res2 = app.handler(event2, table)
        self.assertEqual(res2["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
