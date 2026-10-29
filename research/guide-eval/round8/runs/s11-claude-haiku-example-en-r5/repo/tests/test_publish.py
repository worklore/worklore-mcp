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

    def test_second_publish_with_related_story_stores(self):
        # The first publish runs against an empty table and never computes a score.
        # The second one is the real path: similarity runs and produces floats.
        table = FakeTable()
        app.publish(table, {
            "slug": "first-story", "title": "First", "tags": ["cron", "linux"],
            "body": "two crontabs one line",
        })
        result = app.handler({"body": '{"slug": "second-story", "title": "Second", '
                                      '"tags": ["cron"], "body": "two crontabs"}'}, table)
        self.assertEqual(result["statusCode"], 201, result["body"])
        stored = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertEqual([s["slug"] for s in stored["similar"]], ["first-story"])
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)

    def test_handler_seeded_table_three_publishes(self):
        table = FakeTable()
        for i in range(4):
            result = app.handler({"body": '{"slug": "story-%d", "title": "T", '
                                          '"tags": ["a", "b"], "body": "x y z %d"}' % (i, i)}, table)
            self.assertEqual(result["statusCode"], 201, result["body"])
        self.assertEqual(table.scan()["Count"], 4)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.25, "b": [{"c": 1.5}], "d": 3, "e": "x"})
        self.assertEqual(out, {"a": Decimal("0.25"), "b": [{"c": Decimal("1.5")}], "d": 3, "e": "x"})
        self.assertIsInstance(out["a"], Decimal)


if __name__ == "__main__":
    unittest.main()
