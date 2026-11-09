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

    def test_second_publish_stores_decimal_scores(self):
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        stored = app.publish(table, {
            "slug": "fixing-duplicate-crons",
            "title": "Fixing duplicate crons",
            "tags": ["cron"],
            "body": "Two crontabs both had the same line, so the job ran twice.",
        })
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual([s["slug"] for s in stored["similar"]], ["why-my-cron-ran-twice"])
        for entry in stored["similar"]:
            self.assertIsInstance(entry["score"], Decimal)

    def test_handler_returns_201_on_second_publish(self):
        table = FakeTable()
        first = app.handler({"body": json.dumps({
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron"],
            "body": "Two crontabs both had the line.",
        })}, table)
        second = app.handler({"body": json.dumps({
            "slug": "fixing-duplicate-crons",
            "title": "Fixing duplicate crons",
            "tags": ["cron"],
            "body": "Two crontabs both had the line.",
        })}, table)
        self.assertEqual(first["statusCode"], 201)
        self.assertEqual(second["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
