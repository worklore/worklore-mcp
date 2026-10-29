import os
import sys
import json
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


    def test_second_publish_with_existing_stories(self):
        # The empty table is the path that runs once in production; every
        # later publish scores against existing stories. Seed, then publish.
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
            "body": "My cron line ran an hour early after the clocks changed.",
        })}, table)
        self.assertEqual(resp["statusCode"], 201, resp)
        similar = table.get_item(Key={"slug": "cron-and-timezones"})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], ["why-my-cron-ran-twice"])
        self.assertIsInstance(similar[0]["score"], Decimal)
        self.assertGreater(similar[0]["score"], 0)

    def test_many_publishes_all_succeed(self):
        table = FakeTable()
        for i in range(6):
            resp = app.handler({"body": json.dumps({
                "slug": f"story-{i}", "title": f"Story {i}",
                "tags": ["a", f"t{i % 2}"], "body": f"words {i} shared",
            })}, table)
            self.assertEqual(resp["statusCode"], 201, resp)
        self.assertEqual(table.scan()["Count"], 6)
        self.assertTrue(all(len(it["similar"]) <= app.TOP_N for it in table.items.values()))


class ToDynamoTest(unittest.TestCase):
    def test_floats_become_decimals_everywhere(self):
        out = app.to_dynamo({"a": 0.1234, "b": [{"c": 1.5}], "d": 3, "e": "x", "f": True})
        self.assertEqual(out, {"a": Decimal("0.1234"), "b": [{"c": Decimal("1.5")}], "d": 3, "e": "x", "f": True})
        self.assertIsInstance(out["d"], int)


if __name__ == "__main__":
    unittest.main()
