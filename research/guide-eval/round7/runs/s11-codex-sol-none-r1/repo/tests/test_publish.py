import os
import sys
import unittest
import json
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

    def test_consecutive_publishes_store_decimal_similarity_scores(self):
        table = FakeTable()
        stories = [
            {"slug": "first-story", "title": "First", "tags": ["python", "aws"], "body": "Python runs on AWS"},
            {"slug": "second-story", "title": "Second", "tags": ["python"], "body": "Python runs here"},
            {"slug": "third-story", "title": "Third", "tags": [], "body": "Something else"},
        ]

        for story in stories:
            response = app.handler({"body": json.dumps(story)}, table)
            self.assertEqual(response["statusCode"], 201)

        self.assertEqual(table.scan()["Count"], 3)
        second = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertEqual(second["similar"][0]["slug"], "first-story")
        self.assertEqual(second["similar"][0]["score"], Decimal("0.4700"))
        for slug in ("second-story", "third-story"):
            item = table.get_item(Key={"slug": slug})["Item"]
            self.assertTrue(all(isinstance(match["score"], Decimal) for match in item["similar"]))


if __name__ == "__main__":
    unittest.main()
