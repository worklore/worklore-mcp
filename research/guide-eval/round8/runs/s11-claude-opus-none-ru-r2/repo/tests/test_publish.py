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

    def test_second_publish_stores_scores_as_decimal(self):
        # Regression: the first publish has no neighbours (similar=[]); from the
        # second one on, scores were floats and put_item failed -> 500.
        table = FakeTable()
        stories = [
            {"slug": "why-my-cron-ran-twice", "title": "Cron", "tags": ["cron", "linux"],
             "body": "Two crontabs, one for root and one for me, both had the line."},
            {"slug": "cron-and-timezones", "title": "TZ", "tags": ["cron"],
             "body": "The cron line ran at the wrong hour."},
            {"slug": "unrelated", "title": "Bread", "tags": [], "body": "Flour, water, salt."},
        ]
        for story in stories:
            resp = app.handler({"body": json.dumps(story)}, table)
            self.assertEqual(resp["statusCode"], 201, resp)
        self.assertEqual(table.scan()["Count"], 3)
        similar = table.get_item(Key={"slug": "unrelated"})["Item"]["similar"]
        self.assertEqual(len(similar), 2)
        for s in similar:
            self.assertIsInstance(s["score"], Decimal)
        top = table.get_item(Key={"slug": "cron-and-timezones"})["Item"]["similar"][0]
        self.assertEqual(top["slug"], "why-my-cron-ran-twice")
        self.assertGreater(top["score"], 0)

    def test_to_dynamo_converts_floats(self):
        out = app.to_dynamo({"a": 0.5, "b": [{"c": 1.25}], "d": 3})
        self.assertEqual(out, {"a": Decimal("0.5"), "b": [{"c": Decimal("1.25")}], "d": 3})
        with self.assertRaises(ValueError):
            app.to_dynamo({"x": float("nan")})

    def test_bad_input_is_400_not_500(self):
        table = FakeTable()
        for body in ("[]", '{"slug": "abc", "title": "t", "body": "b", "tags": [[1]]}'):
            self.assertEqual(app.handler({"body": body}, table)["statusCode"], 400)


if __name__ == "__main__":
    unittest.main()
