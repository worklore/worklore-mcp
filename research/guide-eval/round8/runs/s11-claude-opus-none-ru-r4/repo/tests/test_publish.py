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

    def test_second_publish_stores_float_free_similar(self):
        # Regression: the first publish has an empty library (similar=[]), the
        # second one gets float similarity scores, which boto3 rejects.
        table = FakeTable()
        first = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        second = {
            "slug": "systemd-timers-instead-of-cron",
            "title": "systemd timers instead of cron",
            "tags": ["cron", "systemd"],
            "body": "One timer unit replaced the line in both crontabs.",
        }
        self.assertEqual(app.handler({"body": json.dumps(first)}, table)["statusCode"], 201)
        resp = app.handler({"body": json.dumps(second)}, table)
        self.assertEqual(resp["statusCode"], 201, resp)
        similar = table.get_item(Key={"slug": second["slug"]})["Item"]["similar"]
        self.assertEqual(similar[0]["slug"], first["slug"])
        self.assertIsInstance(similar[0]["score"], Decimal)
        self.assertGreater(similar[0]["score"], 0)
        # A third publish scores against items read back from the table.
        third = dict(second, slug="cron-again", title="cron again")
        self.assertEqual(app.handler({"body": json.dumps(third)}, table)["statusCode"], 201)
        self.assertEqual(len(table.get_item(Key={"slug": "cron-again"})["Item"]["similar"]), 2)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.1, "b": [{"c": 1.5}], "d": True, "e": 3})
        self.assertEqual(out, {"a": Decimal("0.1"), "b": [{"c": Decimal("1.5")}], "d": True, "e": 3})


if __name__ == "__main__":
    unittest.main()
