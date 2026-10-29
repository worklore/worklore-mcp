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
        # The first write has no related stories, so it never computes a score.
        # The second write does, and that is the path that used to fail.
        table = FakeTable()
        first = {"slug": "first-story", "title": "First", "tags": ["cron", "linux"], "body": "cron runs twice"}
        second = {"slug": "second-story", "title": "Second", "tags": ["cron"], "body": "cron runs once"}
        app.publish(table, first)
        stored = app.publish(table, second)
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual([s["slug"] for s in stored["similar"]], ["first-story"])
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)

    def test_handler_201_on_every_publish(self):
        table = FakeTable()
        for slug in ("alpha-story", "beta-story", "gamma-story"):
            body = json.dumps({"slug": slug, "title": slug, "tags": ["x"], "body": "shared words here"})
            self.assertEqual(app.handler({"body": body}, table)["statusCode"], 201)
        self.assertEqual(table.scan()["Count"], 3)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.5, "b": [{"c": 0.25}], "d": 3, "e": "x"})
        self.assertEqual(out, {"a": Decimal("0.5"), "b": [{"c": Decimal("0.25")}], "d": 3, "e": "x"})


if __name__ == "__main__":
    unittest.main()
