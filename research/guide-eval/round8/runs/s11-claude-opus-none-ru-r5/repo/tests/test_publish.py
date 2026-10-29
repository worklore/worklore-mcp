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

    def test_second_publish_stores_similar_scores(self):
        # The first publish has nothing to compare against (similar=[]); the
        # second one gets a float similarity score, which boto3 rejects.
        table = FakeTable()
        first = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        second = {
            "slug": "cron-and-timezones",
            "title": "Cron and timezones",
            "tags": ["cron"],
            "body": "The line ran at the wrong hour for me.",
        }
        third = {
            "slug": "systemd-timers",
            "title": "Systemd timers",
            "tags": ["linux", "systemd"],
            "body": "Timers instead of crontabs.",
        }
        for story in (first, second, third):
            resp = app.handler({"body": json.dumps(story)}, table)
            self.assertEqual(resp["statusCode"], 201, resp)
        self.assertEqual(table.scan()["Count"], 3)
        similar = table.get_item(Key={"slug": "systemd-timers"})["Item"]["similar"]
        self.assertEqual(len(similar), 2)
        for entry in similar:
            self.assertIsInstance(entry["score"], Decimal)
        self.assertGreater(similar[0]["score"], 0)

    def test_non_string_tags_are_rejected(self):
        table = FakeTable()
        story = {"slug": "abc", "title": "t", "body": "b", "tags": [1.5, "x"]}
        resp = app.handler({"body": json.dumps(story)}, table)
        self.assertEqual(resp["statusCode"], 400, resp)
        self.assertEqual(table.scan()["Count"], 0)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.35, "b": [{"c": 1.0}], "d": 3, "e": "x"})
        self.assertEqual(out, {"a": Decimal("0.35"), "b": [{"c": Decimal("1.0")}], "d": 3, "e": "x"})


if __name__ == "__main__":
    unittest.main()
