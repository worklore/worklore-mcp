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
        # Regression: the 2nd story gets non-empty `similar`, whose scores must
        # be Decimal (DynamoDB rejects float). The first publish has no
        # neighbours, so it never exercised this path.
        table = FakeTable()
        app.publish(table, {"slug": "first-story", "title": "First", "tags": ["cron", "linux"], "body": "cron ran twice"})
        resp = app.handler(
            {"body": json.dumps({"slug": "second-story", "title": "Second", "tags": ["cron"], "body": "cron twice again"})},
            table,
        )
        self.assertEqual(resp["statusCode"], 201, resp)
        similar = table.get_item(Key={"slug": "second-story"})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], ["first-story"])
        self.assertIsInstance(similar[0]["score"], Decimal)


if __name__ == "__main__":
    unittest.main()
