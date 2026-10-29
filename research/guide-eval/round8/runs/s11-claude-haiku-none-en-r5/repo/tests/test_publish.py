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

    def test_second_publish_with_related_story_succeeds(self):
        # The first publish has nothing to compare against, so it never writes a
        # similarity score. The second one does; this is the case that failed in prod.
        table = FakeTable()
        first = {"slug": "first-story", "title": "First", "tags": ["cron", "linux"], "body": "cron runs jobs on linux"}
        second = {"slug": "second-story", "title": "Second", "tags": ["cron"], "body": "cron jobs twice"}
        self.assertEqual(app.handler({"body": json.dumps(first)}, table)["statusCode"], 201)

        response = app.handler({"body": json.dumps(second)}, table)

        self.assertEqual(response["statusCode"], 201)
        similar = table.get_item(Key={"slug": "second-story"})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], ["first-story"])
        self.assertIsInstance(similar[0]["score"], Decimal)

    def test_similarity_is_decimal(self):
        score = app.similarity({"tags": ["a", "b"], "body": "x y"}, {"tags": ["a"], "body": "x z"})
        self.assertIsInstance(score, Decimal)


if __name__ == "__main__":
    unittest.main()
