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

    def test_second_publish_stores_dynamo_compatible_related_scores(self):
        table = FakeTable()
        first = {"slug": "first-story", "title": "First", "tags": ["python"], "body": "shared words"}
        second = {"slug": "second-story", "title": "Second", "tags": ["python"], "body": "shared more"}
        third = {"slug": "third-story", "title": "Third", "tags": ["other"], "body": "nothing alike"}

        for story in (first, second, third):
            response = app.handler({"body": json.dumps(story)}, table)
            self.assertEqual(response["statusCode"], 201)

        related = table.get_item(Key={"slug": "third-story"})["Item"]["similar"]
        self.assertEqual(len(related), 2)
        self.assertTrue(all(isinstance(match["score"], Decimal) for match in related))
        self.assertTrue(all(match["score"] == Decimal("0.0") for match in related))
        self.assertEqual(table.get_item(Key={"slug": "second-story"})["Item"]["similar"][0]["score"], Decimal("0.8"))


if __name__ == "__main__":
    unittest.main()
