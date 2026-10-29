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

    def test_sequential_publishes_store_decimal_scores(self):
        table = FakeTable()
        stories = [
            {"slug": "first-story", "title": "First", "tags": ["cron"], "body": "cron ran twice"},
            {"slug": "second-story", "title": "Second", "tags": ["cron"], "body": "cron ran again"},
            {"slug": "third-story", "title": "Third", "tags": ["linux"], "body": "cron ran twice"},
        ]
        for story in stories:
            response = app.handler({"body": json.dumps(story)}, table)
            self.assertEqual(response["statusCode"], 201)

        self.assertEqual(table.scan()["Count"], 3)
        second = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertEqual(second["similar"], [{"slug": "first-story", "score": Decimal("0.8500")}])
        third = table.get_item(Key={"slug": "third-story"})["Item"]
        self.assertTrue(all(isinstance(entry["score"], Decimal) for entry in third["similar"]))

    def test_invalid_tags_return_400_before_dynamodb(self):
        table = FakeTable()
        response = app.handler({"body": '{"slug":"bad-tags","title":"Title","body":"Body","tags":[1.2]}'}, table)
        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(table.scan()["Count"], 0)


if __name__ == "__main__":
    unittest.main()
