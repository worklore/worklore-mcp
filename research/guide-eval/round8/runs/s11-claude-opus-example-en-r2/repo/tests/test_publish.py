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

    def test_second_publish_with_existing_stories(self):
        # The populated table is the real path: similarity scores (floats)
        # are only computed once there is something to compare against.
        table = FakeTable()
        first = app.handler({"body": json.dumps({
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })}, table)
        self.assertEqual(first["statusCode"], 201)
        second = app.handler({"body": json.dumps({
            "slug": "cron-and-timezones",
            "title": "Cron and timezones",
            "tags": ["cron", "time"],
            "body": "The cron line ran at the wrong hour for me.",
        })}, table)
        self.assertEqual(second["statusCode"], 201, second["body"])
        similar = table.get_item(Key={"slug": "cron-and-timezones"})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], ["why-my-cron-ran-twice"])
        self.assertIsInstance(similar[0]["score"], Decimal)
        self.assertGreater(similar[0]["score"], 0)
        self.assertLessEqual(similar[0]["score"], 1)

    def test_scores_survive_with_full_library(self):
        table = FakeTable()
        for i in range(5):
            app.publish(table, {"slug": f"story-{i}", "title": f"Story {i}",
                                "tags": ["t", f"x{i}"], "body": f"shared words and {i}"})
        stored = app.publish(table, {"slug": "new-one", "title": "New", "tags": ["t"], "body": "shared words"})
        self.assertEqual(len(stored["similar"]), app.TOP_N)
        self.assertEqual(table.scan()["Count"], 6)

    def test_to_dynamo_converts_nested_floats_exactly(self):
        out = app.to_dynamo({"a": 0.1, "b": [{"c": 1.5}], "d": 3, "e": "x"})
        self.assertEqual(out, {"a": Decimal("0.1"), "b": [{"c": Decimal("1.5")}], "d": 3, "e": "x"})


if __name__ == "__main__":
    unittest.main()
