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
        # The second publish is the first one that writes similarity scores;
        # floats there were rejected by DynamoDB in production (500).
        table = FakeTable()
        first = {"slug": "first-story", "title": "A", "tags": ["cron", "linux"], "body": "cron runs twice on linux"}
        second = {"slug": "second-story", "title": "B", "tags": ["cron"], "body": "cron on linux"}
        self.assertEqual(app.handler({"body": json.dumps(first)}, table)["statusCode"], 201)
        response = app.handler({"body": json.dumps(second)}, table)
        self.assertEqual(response["statusCode"], 201, response["body"])
        similar = table.get_item(Key={"slug": "second-story"})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], ["first-story"])
        self.assertIsInstance(similar[0]["score"], Decimal)


if __name__ == "__main__":
    unittest.main()
