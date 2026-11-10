import os
import sys
import unittest
from decimal import Decimal

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

    def test_second_publish_with_related_story_succeeds(self):
        # Regression: the second publish scores against the first story; the
        # float score made boto3 reject the item (HTTP 500 in production).
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        stored = app.publish(table, {
            "slug": "cron-in-containers",
            "title": "Cron in containers",
            "tags": ["cron", "docker"],
            "body": "My cron job ran twice inside the container too.",
        })
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual(stored["similar"][0]["slug"], "why-my-cron-ran-twice")
        self.assertGreater(stored["similar"][0]["score"], 0)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        first = app.handler({"body": '{"slug": "first-story", "title": "First", "tags": ["cron"], "body": "cron runs"}'}, table)
        second = app.handler({"body": '{"slug": "second-story", "title": "Second", "tags": ["cron"], "body": "cron runs"}'}, table)
        self.assertEqual(first["statusCode"], 201)
        self.assertEqual(second["statusCode"], 201)

    def test_similarity_scores_are_dynamo_safe(self):
        score = app.similarity(
            {"tags": ["a", "b", "c"], "body": "one two three"},
            {"tags": ["a", "x"], "body": "one four"},
        )
        self.assertIsInstance(score, Decimal)
        self.assertEqual(score, Decimal("0.25"))


if __name__ == "__main__":
    unittest.main()
