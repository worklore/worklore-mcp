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

    def test_publish_with_seeded_table_computes_similarity(self):
        table = FakeTable()
        seed_story = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        app.publish(table, seed_story)

        second_story = {
            "slug": "cron-troubleshooting-guide",
            "title": "Cron Troubleshooting Guide",
            "tags": ["cron", "scheduling"],
            "body": "When cron jobs run multiple times, check root and user crontabs.",
        }
        stored = app.publish(table, second_story)
        self.assertEqual(stored["slug"], "cron-troubleshooting-guide")
        self.assertEqual(len(stored["similar"]), 1)
        self.assertEqual(stored["similar"][0]["slug"], "why-my-cron-ran-twice")
        self.assertIsInstance(stored["similar"][0]["score"], int)
        self.assertEqual(table.scan()["Count"], 2)

    def test_handler_publish_twice(self):
        import json
        table = FakeTable()
        body1 = {
            "slug": "first-story",
            "title": "First Story",
            "tags": ["python"],
            "body": "A story about python.",
        }
        body2 = {
            "slug": "second-story",
            "title": "Second Story",
            "tags": ["python"],
            "body": "Another story about python.",
        }
        resp1 = app.handler({"body": json.dumps(body1)}, table)
        self.assertEqual(resp1["statusCode"], 201)
        resp2 = app.handler({"body": json.dumps(body2)}, table)
        self.assertEqual(resp2["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
