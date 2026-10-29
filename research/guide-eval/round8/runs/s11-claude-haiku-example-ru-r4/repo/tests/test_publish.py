import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import app  # noqa: E402
from decimal import Decimal  # noqa: E402
from fake_dynamo import FakeTable  # noqa: E402

FIRST = {
    "slug": "why-my-cron-ran-twice",
    "title": "Why my cron ran twice",
    "tags": ["cron", "linux"],
    "body": "Two crontabs, one for root and one for me, both had the line.",
}
SECOND = {
    "slug": "cron-and-systemd-timers",
    "title": "Cron and systemd timers",
    "tags": ["cron", "systemd"],
    "body": "Both run jobs on a schedule; the cron line was still there after the timer.",
}


class PublishTest(unittest.TestCase):
    def test_publish_stores_story(self):
        table = FakeTable()
        stored = app.publish(table, FIRST)
        self.assertEqual(stored["slug"], "why-my-cron-ran-twice")
        self.assertEqual(table.get_item(Key={"slug": "why-my-cron-ran-twice"})["Item"]["title"], "Why my cron ran twice")
        self.assertEqual(table.scan()["Count"], 1)

    def test_second_publish_with_similar_stories_is_stored(self):
        # The first publish sees an empty table and never computes a score.
        # The second one does, so this is the path that used to fail.
        table = FakeTable()
        app.publish(table, FIRST)
        stored = app.publish(table, SECOND)

        self.assertEqual(stored["similar"][0]["slug"], FIRST["slug"])
        self.assertEqual(table.scan()["Count"], 2)
        item = table.get_item(Key={"slug": SECOND["slug"]})["Item"]
        self.assertIsInstance(item["similar"][0]["score"], Decimal)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        app.handler({"body": json.dumps(FIRST)}, table)
        response = app.handler({"body": json.dumps(SECOND)}, table)
        self.assertEqual(response["statusCode"], 201)


class ToDynamoTest(unittest.TestCase):
    def test_converts_nested_floats_to_decimal(self):
        value = {"a": 0.25, "b": [1, {"c": 0.5}], "d": "text", "e": 3}
        self.assertEqual(
            app.to_dynamo(value),
            {"a": Decimal("0.25"), "b": [1, {"c": Decimal("0.5")}], "d": "text", "e": 3},
        )


if __name__ == "__main__":
    unittest.main()
