from decimal import Decimal
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

    def test_second_publish_computes_similar_with_decimal_score(self):
        table = FakeTable()
        story1 = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        story2 = {
            "slug": "cron-in-docker",
            "title": "Cron in Docker",
            "tags": ["cron", "docker"],
            "body": "Running cron inside a docker container on linux.",
        }
        app.publish(table, story1)
        stored2 = app.publish(table, story2)

        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual(len(stored2["similar"]), 1)
        self.assertEqual(stored2["similar"][0]["slug"], "why-my-cron-ran-twice")
        score = stored2["similar"][0]["score"]
        self.assertIsInstance(score, Decimal)
        self.assertGreater(score, Decimal(0))

        item2 = table.get_item(Key={"slug": "cron-in-docker"})["Item"]
        self.assertEqual(item2["similar"][0]["slug"], "why-my-cron-ran-twice")
        self.assertIsInstance(item2["similar"][0]["score"], Decimal)

    def test_handler_sequential_publishes_return_201(self):
        table = FakeTable()
        story1 = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        story2 = {
            "slug": "another-story",
            "title": "Another Story",
            "tags": ["cron"],
            "body": "Another cron story.",
        }

        resp1 = app.handler({"body": json.dumps(story1)}, table)
        self.assertEqual(resp1["statusCode"], 201)

        resp2 = app.handler({"body": json.dumps(story2)}, table)
        self.assertEqual(resp2["statusCode"], 201)
        self.assertEqual(json.loads(resp2["body"]), {"slug": "another-story"})


if __name__ == "__main__":
    unittest.main()
