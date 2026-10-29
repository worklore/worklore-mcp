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
    "slug": "cron-and-bash-loops",
    "title": "Cron and bash loops",
    "tags": ["cron", "bash"],
    "body": "A bash loop inside a crontab line ran twice because both crontabs had it.",
}


class PublishTest(unittest.TestCase):
    def test_publish_stores_story(self):
        table = FakeTable()
        stored = app.publish(table, FIRST)
        self.assertEqual(stored["slug"], "why-my-cron-ran-twice")
        self.assertEqual(table.get_item(Key={"slug": "why-my-cron-ran-twice"})["Item"]["title"], "Why my cron ran twice")
        self.assertEqual(table.scan()["Count"], 1)

    def test_second_publish_with_existing_stories(self):
        # The first publish runs against an empty table; the second one is the
        # path that computes scores, so it must be tested with a seeded table.
        table = FakeTable()
        app.publish(table, FIRST)
        stored = app.publish(table, SECOND)
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual([s["slug"] for s in stored["similar"]], ["why-my-cron-ran-twice"])
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        first = app.handler({"body": json.dumps(FIRST)}, table)
        second = app.handler({"body": json.dumps(SECOND)}, table)
        self.assertEqual(first["statusCode"], 201)
        self.assertEqual(second["statusCode"], 201, second["body"])

    def test_to_dynamo_converts_floats_recursively(self):
        value = {"a": 0.4286, "b": [1.5, {"c": 2.0}], "d": 3, "e": "x"}
        self.assertEqual(
            app.to_dynamo(value),
            {"a": Decimal("0.4286"), "b": [Decimal("1.5"), {"c": Decimal("2.0")}], "d": 3, "e": "x"},
        )


if __name__ == "__main__":
    unittest.main()
