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
        # The first publish has nothing to relate to; the second one stores a
        # score for the first, which is the case that failed in production.
        table = FakeTable()
        app.publish(table, {"slug": "aaa-first", "title": "A", "tags": ["cron"], "body": "cron job runs twice"})
        response = app.handler(
            {"body": json.dumps({"slug": "bbb-second", "title": "B", "tags": ["cron"], "body": "cron job runs once"})},
            table,
        )
        self.assertEqual(response["statusCode"], 201)
        similar = table.get_item(Key={"slug": "bbb-second"})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], ["aaa-first"])
        self.assertIsInstance(similar[0]["score"], Decimal)


if __name__ == "__main__":
    unittest.main()
