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

    def test_second_publish_with_existing_story_is_stored(self):
        # The populated path: the first write seeds the table, so the second
        # one computes similarity scores (floats) and must still be accepted.
        table = FakeTable()
        app.publish(table, {"slug": "first-story", "title": "First", "tags": ["cron"], "body": "cron jobs run twice"})
        stored = app.publish(table, {"slug": "second-story", "title": "Second", "tags": ["cron", "linux"], "body": "cron jobs and linux"})
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual(stored["similar"][0]["slug"], "first-story")
        item = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertIsInstance(item["similar"][0]["score"], Decimal)

    def test_handler_publishes_twice_over_http_shape(self):
        table = FakeTable()
        bodies = [
            {"slug": "story-one", "title": "One", "tags": ["a", "b"], "body": "alpha beta gamma"},
            {"slug": "story-two", "title": "Two", "tags": ["a"], "body": "alpha delta"},
            {"slug": "story-three", "title": "Three", "tags": ["b"], "body": "beta gamma"},
        ]
        for story in bodies:
            resp = app.handler({"body": json.dumps(story)}, table)
            self.assertEqual(resp["statusCode"], 201, resp)
        self.assertEqual(table.scan()["Count"], 3)

    def test_to_dynamo_converts_nested_floats(self):
        value = {"a": 0.1234, "b": [{"score": 0.5}], "c": "x", "d": 3, "e": True, "f": None}
        converted = app.to_dynamo(value)
        self.assertEqual(converted, {"a": Decimal("0.1234"), "b": [{"score": Decimal("0.5")}], "c": "x", "d": 3, "e": True, "f": None})
        self.assertIsInstance(converted["a"], Decimal)
        self.assertIsInstance(converted["b"][0]["score"], Decimal)


if __name__ == "__main__":
    unittest.main()
