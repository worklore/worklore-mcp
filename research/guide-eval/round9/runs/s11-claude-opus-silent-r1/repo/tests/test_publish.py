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

    def test_second_publish_stores_float_scores_as_decimal(self):
        # Regression: the first publish has no neighbours (similar=[]); the
        # second computes a float similarity score, which boto3 rejects.
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        stored = app.publish(table, {
            "slug": "cron-and-timezones",
            "title": "Cron and timezones",
            "tags": ["cron"],
            "body": "The server clock was UTC, the crontab line assumed local time.",
        })
        self.assertEqual(table.scan()["Count"], 2)
        [neighbour] = stored["similar"]
        self.assertEqual(neighbour["slug"], "why-my-cron-ran-twice")
        self.assertIsInstance(neighbour["score"], Decimal)
        self.assertGreater(neighbour["score"], 0)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        for slug in ("first-story", "second-story"):
            body = json.dumps({"slug": slug, "title": slug, "tags": ["t"], "body": "same words here"})
            self.assertEqual(app.handler({"body": body}, table)["statusCode"], 201)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.5, "b": [{"c": 1.25}], "d": 3, "e": True})
        self.assertEqual(out, {"a": Decimal("0.5"), "b": [{"c": Decimal("1.25")}], "d": 3, "e": True})


if __name__ == "__main__":
    unittest.main()
