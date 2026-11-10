import json
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

    def test_second_publish_with_related_stories_is_stored(self):
        # Regression: the first publish has no neighbours, so the similarity
        # score (stored inside the item) is only computed from the second one on.
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        stored = app.publish(table, {
            "slug": "cron-and-systemd-timers",
            "title": "Cron and systemd timers",
            "tags": ["cron", "systemd"],
            "body": "When a cron job runs twice, check the crontab and the timers.",
        })
        self.assertEqual(len(stored["similar"]), 1)
        self.assertEqual(stored["similar"][0]["slug"], "why-my-cron-ran-twice")
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)
        self.assertEqual(table.scan()["Count"], 2)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        first = app.handler({"body": json.dumps({"slug": "first-story", "title": "A", "tags": ["cron"], "body": "cron ran twice"})}, table)
        second = app.handler({"body": json.dumps({"slug": "second-story", "title": "B", "tags": ["cron"], "body": "cron twice again"})}, table)
        self.assertEqual(first["statusCode"], 201)
        self.assertEqual(second["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
