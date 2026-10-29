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

    def test_second_publish_succeeds_with_similarity_scores(self):
        table = FakeTable()
        first_story = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        second_story = {
            "slug": "crontab-tips-and-tricks",
            "title": "Crontab tips and tricks",
            "tags": ["cron"],
            "body": "Understanding crontabs and schedules.",
        }
        app.publish(table, first_story)
        stored_second = app.publish(table, second_story)
        self.assertEqual(stored_second["slug"], "crontab-tips-and-tricks")
        self.assertEqual(len(stored_second["similar"]), 1)
        self.assertEqual(stored_second["similar"][0]["slug"], "why-my-cron-ran-twice")
        self.assertEqual(table.scan()["Count"], 2)

    def test_handler_second_publish_returns_201(self):
        import json
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
        resp1 = app.handler(event1, table)
        self.assertEqual(resp1["statusCode"], 201)
        resp2 = app.handler(event2, table)
        self.assertEqual(resp2["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
