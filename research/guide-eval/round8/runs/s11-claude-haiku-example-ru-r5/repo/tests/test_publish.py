import json
import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import app  # noqa: E402
from fake_dynamo import FakeTable  # noqa: E402


def story(slug, tags, body):
    return {"slug": slug, "title": slug.replace("-", " ").capitalize(), "tags": tags, "body": body}


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
        # Regression: the first publish has no related stories, so no scores are
        # computed. The second one has a score, and must still be storable.
        table = FakeTable()
        app.publish(table, story("first-story", ["cron", "linux"], "crontab line runs twice"))
        stored = app.publish(table, story("second-story", ["cron"], "crontab runs once"))

        self.assertEqual(stored["similar"][0]["slug"], "first-story")
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)
        self.assertEqual(table.scan()["Count"], 2)

    def test_handler_publishes_many_stories_in_a_populated_table(self):
        table = FakeTable()
        stories = [
            story("cron-story", ["cron"], "two crontabs both had the line"),
            story("disk-story", ["disk", "linux"], "df says full but du says empty"),
            story("dns-story", ["dns", "linux"], "resolver cached the old record"),
            story("cron-two", ["cron", "linux"], "cron ran the job twice again"),
        ]
        for s in stories:
            resp = app.handler({"body": json.dumps(s)}, table)
            self.assertEqual(resp["statusCode"], 201, resp)

        self.assertEqual(table.scan()["Count"], len(stories))
        self.assertEqual(len(table.get_item(Key={"slug": "cron-two"})["Item"]["similar"]), 3)

    def test_to_dynamo_converts_floats_at_any_depth(self):
        converted = app.to_dynamo({"a": 0.5, "b": [{"c": 0.25}], "d": 3, "e": "x", "f": True})
        self.assertEqual(converted, {"a": Decimal("0.5"), "b": [{"c": Decimal("0.25")}], "d": 3, "e": "x", "f": True})


if __name__ == "__main__":
    unittest.main()
