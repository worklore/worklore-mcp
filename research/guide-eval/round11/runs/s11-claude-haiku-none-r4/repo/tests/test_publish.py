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

    def test_second_publish_stores_related_scores(self):
        # Regression: the second publish has a story to compare against, so the
        # item carries a similarity score. A float there made DynamoDB reject
        # the write and the handler return 500.
        table = FakeTable()
        first = {"slug": "first-story", "title": "First", "tags": ["cron"],
                 "body": "cron jobs run twice"}
        second = {"slug": "second-story", "title": "Second", "tags": ["cron"],
                  "body": "cron jobs run twice again"}
        self.assertEqual(app.publish(table, first)["similar"], [])
        stored = app.publish(table, second)
        self.assertEqual([s["slug"] for s in stored["similar"]], ["first-story"])
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        first = json.dumps({"slug": "first-story", "title": "First", "tags": ["cron"],
                            "body": "cron jobs run twice"})
        second = json.dumps({"slug": "second-story", "title": "Second", "tags": ["cron"],
                             "body": "cron jobs run twice again"})
        self.assertEqual(app.handler({"body": first}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": second}, table)["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
