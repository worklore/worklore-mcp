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

    def test_second_publish_with_related_stories_is_stored(self):
        # The first publish runs against an empty table and never computes a
        # similarity score, so it cannot catch float scores. The second publish
        # is the one that stores ``similar`` scores, and must succeed too.
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        stored = app.publish(table, {
            "slug": "cron-lock-files",
            "title": "Cron lock files",
            "tags": ["cron"],
            "body": "A lock file stops two crontabs from running the same job.",
        })
        self.assertEqual([s["slug"] for s in stored["similar"]], ["why-my-cron-ran-twice"])
        self.assertEqual(table.scan()["Count"], 2)

    def test_handler_returns_201_on_second_publish(self):
        table = FakeTable()
        first = app.handler({"body": json.dumps({"slug": "first-story", "title": "A", "tags": ["cron"], "body": "cron twice"})}, table)
        second = app.handler({"body": json.dumps({"slug": "second-story", "title": "B", "tags": ["cron"], "body": "cron twice again"})}, table)
        self.assertEqual(first["statusCode"], 201)
        self.assertEqual(second["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
