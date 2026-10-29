import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import app  # noqa: E402
from fake_dynamo import FakeTable  # noqa: E402
from boto3.dynamodb.types import TypeSerializer  # noqa: E402


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

    def test_second_publish_with_similar_stories_is_stored(self):
        # The first publish always runs against an empty table, so it never
        # produces scores. Seed one story first so the second publish exercises
        # the scoring path that was failing in production.
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        stored = app.publish(table, {
            "slug": "my-cron-jobs-and-root",
            "title": "My cron jobs and root",
            "tags": ["cron"],
            "body": "Root owns the system crontab, I own mine, and both ran the same line.",
        })
        self.assertEqual([s["slug"] for s in stored["similar"]], ["why-my-cron-ran-twice"])
        self.assertEqual(table.scan()["Count"], 2)

    def test_stored_item_is_valid_for_boto3_serializer(self):
        # Runs the same type check boto3 applies on put_item, so a float in any
        # attribute fails here even without a real table.
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        stored = app.publish(table, {
            "slug": "my-cron-jobs-and-root",
            "title": "My cron jobs and root",
            "tags": ["cron", "linux"],
            "body": "Root owns the system crontab, I own mine, and both ran the same line.",
        })
        serializer = TypeSerializer()
        for name, value in stored.items():
            serializer.serialize(value)


if __name__ == "__main__":
    unittest.main()
