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

    def test_second_publish_with_related_story(self):
        table = FakeTable()
        first = {"slug": "first-story", "title": "First", "tags": ["python"], "body": "shared words"}
        second = {"slug": "second-story", "title": "Second", "tags": ["python"], "body": "shared words"}

        self.assertEqual(app.handler({"body": json.dumps(first)}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": json.dumps(second)}, table)["statusCode"], 201)

        stored = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertEqual(stored["similar"], [{"slug": "first-story", "score": Decimal("1.0000")}])
        self.assertEqual(table.scan()["Count"], 2)

    def test_fractional_score_is_dynamodb_compatible(self):
        table = FakeTable()
        app.publish(table, {"slug": "first-story", "title": "First", "tags": ["python"], "body": "shared"})
        stored = app.publish(table, {"slug": "second-story", "title": "Second", "tags": ["python", "aws"], "body": "different"})

        self.assertEqual(stored["similar"][0]["score"], Decimal("0.3500"))
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)

    def test_float_tag_is_rejected_before_write(self):
        table = FakeTable()
        story = {"slug": "bad-story", "title": "Bad", "tags": [0.5], "body": "Body"}

        self.assertEqual(app.handler({"body": json.dumps(story)}, table)["statusCode"], 400)
        self.assertEqual(table.scan()["Count"], 0)


if __name__ == "__main__":
    unittest.main()
