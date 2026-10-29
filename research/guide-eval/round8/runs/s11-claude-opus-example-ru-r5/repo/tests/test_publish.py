import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import json  # noqa: E402
from decimal import Decimal  # noqa: E402

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


    def test_second_publish_with_similar_stories(self):
        # The empty-table path happens once in production; seed the table so
        # the similarity scoring actually runs and its scores get stored.
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
            "tags": ["cron", "tz"],
            "body": "The line ran at the wrong hour because the server was in UTC.",
        })
        self.assertEqual(table.scan()["Count"], 2)
        [sim] = stored["similar"]
        self.assertEqual(sim["slug"], "why-my-cron-ran-twice")
        self.assertIsInstance(sim["score"], Decimal)
        self.assertTrue(Decimal(0) < sim["score"] <= Decimal(1))

    def test_handler_publishes_twice(self):
        table = FakeTable()
        for slug, tags in (("first-story", ["a"]), ("second-story", ["a", "b"]),
                           ("third-story", []), ("fourth-story", ["b"])):
            event = {"body": json.dumps({"slug": slug, "title": slug, "tags": tags, "body": "same words here"})}
            self.assertEqual(app.handler(event, table)["statusCode"], 201, slug)
        self.assertEqual(table.scan()["Count"], 4)

    def test_dynamo_safe_converts_floats(self):
        item = app.dynamo_safe({"a": 0.1, "b": [1.5, {"c": 2.0}], "d": True, "e": 3})
        self.assertEqual(item, {"a": Decimal("0.1"), "b": [Decimal("1.5"), {"c": Decimal("2.0")}], "d": True, "e": 3})
        with self.assertRaises(TypeError):
            app.dynamo_safe({"x": float("nan")})


if __name__ == "__main__":
    unittest.main()
