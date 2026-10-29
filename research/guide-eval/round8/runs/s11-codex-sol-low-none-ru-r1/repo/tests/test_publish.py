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

    def test_subsequent_publishes_store_decimal_scores(self):
        table = FakeTable()
        for slug in ("first-story", "second-story", "third-story"):
            response = app.handler({"body": json.dumps({
                "slug": slug, "title": slug, "tags": ["python"], "body": "A shared story body"
            })}, table)
            self.assertEqual(response["statusCode"], 201)
        self.assertEqual(table.scan()["Count"], 3)
        for slug in ("second-story", "third-story"):
            scores = [entry["score"] for entry in table.get_item(Key={"slug": slug})["Item"]["similar"]]
            self.assertTrue(scores)
            self.assertTrue(all(isinstance(score, Decimal) for score in scores))


if __name__ == "__main__":
    unittest.main()
