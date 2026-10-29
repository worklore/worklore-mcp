import json
import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import app  # noqa: E402
from fake_dynamo import FakeTable  # noqa: E402


def _story(slug, tags, body):
    return {"slug": slug, "title": slug.replace("-", " "), "tags": tags, "body": body}


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

    def test_second_publish_with_similar_stories_stores(self):
        # The first publish runs against an empty table and never scores anything,
        # so the scored path only runs when the table already holds stories.
        table = FakeTable()
        app.publish(table, _story("first-story", ["cron", "linux"], "cron runs jobs on linux"))
        stored = app.publish(table, _story("second-story", ["cron"], "cron jobs and linux boxes"))
        self.assertEqual([s["slug"] for s in stored["similar"]], ["first-story"])
        saved = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertIsInstance(saved["similar"][0]["score"], Decimal)

    def test_publish_with_many_existing_stories(self):
        table = FakeTable()
        for i in range(5):
            app.publish(table, _story(f"story-{i}", ["cron", f"t{i}"], f"cron body {i} shared words"))
        stored = app.publish(table, _story("late-story", ["cron", "t1"], "cron body shared words"))
        self.assertEqual(len(stored["similar"]), app.TOP_N)
        self.assertEqual(table.scan()["Count"], 6)

    def test_handler_publishes_twice(self):
        table = FakeTable()
        body = json.dumps(_story("repeat-story", ["cron"], "cron body"))
        other = json.dumps(_story("other-story", ["cron"], "cron body text"))
        self.assertEqual(app.handler({"body": body}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": other}, table)["statusCode"], 201)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.5, "b": [{"c": 0.25}], "d": 3})
        self.assertEqual(out, {"a": Decimal("0.5"), "b": [{"c": Decimal("0.25")}], "d": 3})


if __name__ == "__main__":
    unittest.main()
