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

    def test_second_publish_with_existing_story(self):
        # The first publish runs against an empty table, so no similarity
        # scores are computed. The second one is the path that broke in prod.
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        resp = app.handler({"body": json.dumps({
            "slug": "cron-and-timezones",
            "title": "Cron and timezones",
            "tags": ["cron"],
            "body": "My cron line ran at the wrong hour.",
        })}, table)
        self.assertEqual(resp["statusCode"], 201, resp)
        similar = table.get_item(Key={"slug": "cron-and-timezones"})["Item"]["similar"]
        self.assertEqual(similar[0]["slug"], "why-my-cron-ran-twice")
        self.assertIsInstance(similar[0]["score"], Decimal)
        self.assertGreater(similar[0]["score"], 0)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.5, "b": [{"c": 1.25}], "d": 3, "e": "x", "f": True})
        self.assertEqual(out, {"a": Decimal("0.5"), "b": [{"c": Decimal("1.25")}], "d": 3, "e": "x", "f": True})


if __name__ == "__main__":
    unittest.main()
