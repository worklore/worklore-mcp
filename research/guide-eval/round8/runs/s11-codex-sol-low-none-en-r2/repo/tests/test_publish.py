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

    def test_second_publish_stores_decimal_similarity_scores(self):
        table = FakeTable()
        first = {"slug": "first-story", "title": "First", "tags": ["python"], "body": "alpha beta"}
        second = {"slug": "second-story", "title": "Second", "tags": ["python"], "body": "alpha gamma"}
        unrelated = {"slug": "third-story", "title": "Third", "tags": ["other"], "body": "delta"}

        self.assertEqual(app.handler({"body": json.dumps(first)}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": json.dumps(second)}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": json.dumps(unrelated)}, table)["statusCode"], 201)

        related = table.get_item(Key={"slug": "second-story"})["Item"]["similar"]
        self.assertEqual(related, [{"slug": "first-story", "score": Decimal("0.8")}])
        self.assertTrue(all(isinstance(entry["score"], Decimal) for entry in
                            table.get_item(Key={"slug": "third-story"})["Item"]["similar"]))
        self.assertEqual(table.scan()["Count"], 3)


if __name__ == "__main__":
    unittest.main()
