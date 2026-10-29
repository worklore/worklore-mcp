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

    def test_repeated_publishes_store_decimal_similarity_scores(self):
        table = FakeTable()
        stories = [
            {"slug": "first-story", "title": "First", "tags": ["python", "aws"], "body": "A story about Python and AWS."},
            {"slug": "second-story", "title": "Second", "tags": ["python", "dynamo"], "body": "A story about Python and DynamoDB."},
            {"slug": "third-story", "title": "Third", "tags": ["aws"], "body": "A story about AWS."},
        ]
        for story in stories:
            response = app.handler({"body": json.dumps(story)}, table)
            self.assertEqual(response["statusCode"], 201)

        self.assertEqual(table.scan()["Count"], 3)
        self.assertEqual(table.get_item(Key={"slug": "first-story"})["Item"]["similar"], [])
        for slug, expected_count in [("second-story", 1), ("third-story", 2)]:
            similar = table.get_item(Key={"slug": slug})["Item"]["similar"]
            self.assertEqual(len(similar), expected_count)
            self.assertTrue(all(isinstance(entry["score"], Decimal) for entry in similar))


if __name__ == "__main__":
    unittest.main()
