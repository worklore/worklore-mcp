import json
import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import app  # noqa: E402
from fake_dynamo import FakeTable  # noqa: E402

FIRST = {
    "slug": "why-my-cron-ran-twice",
    "title": "Why my cron ran twice",
    "tags": ["cron", "linux"],
    "body": "Two crontabs, one for root and one for me, both had the line.",
}
SECOND = {
    "slug": "cron-and-linux-timezones",
    "title": "Cron and linux timezones",
    "tags": ["cron", "timezones"],
    "body": "Cron runs in the server timezone, so the linux job ran twice on DST.",
}


def post(table, story):
    return app.handler({"body": json.dumps(story)}, table)


class PublishTest(unittest.TestCase):
    def test_publish_stores_story(self):
        table = FakeTable()
        stored = app.publish(table, FIRST)
        self.assertEqual(stored["slug"], "why-my-cron-ran-twice")
        self.assertEqual(table.get_item(Key={"slug": "why-my-cron-ran-twice"})["Item"]["title"], "Why my cron ran twice")
        self.assertEqual(table.scan()["Count"], 1)

    def test_first_publish_on_empty_table_returns_201(self):
        table = FakeTable()
        self.assertEqual(post(table, FIRST)["statusCode"], 201)

    def test_second_publish_on_populated_table_returns_201(self):
        # Regression: the second publish scores against the first story, which
        # produced float scores that DynamoDB rejects (500 in production).
        table = FakeTable()
        self.assertEqual(post(table, FIRST)["statusCode"], 201)
        response = post(table, SECOND)
        self.assertEqual(response["statusCode"], 201, response["body"])

    def test_related_scores_are_stored_as_decimal(self):
        table = FakeTable()
        post(table, FIRST)
        post(table, SECOND)
        item = table.get_item(Key={"slug": SECOND["slug"]})["Item"]
        self.assertEqual(len(item["similar"]), 1)
        self.assertEqual(item["similar"][0]["slug"], FIRST["slug"])
        self.assertIsInstance(item["similar"][0]["score"], Decimal)
        self.assertGreater(item["similar"][0]["score"], 0)

    def test_many_publishes_in_sequence(self):
        table = FakeTable()
        for i in range(5):
            story = dict(FIRST, slug=f"story-number-{i}", title=f"Story {i}")
            self.assertEqual(post(table, story)["statusCode"], 201)
        self.assertEqual(table.scan()["Count"], 5)


class ToDynamoTest(unittest.TestCase):
    def test_floats_become_decimals_at_any_depth(self):
        out = app.to_dynamo({"a": 0.4, "b": [{"c": 1.5}], "d": 3, "e": "x"})
        self.assertEqual(out, {"a": Decimal("0.4"), "b": [{"c": Decimal("1.5")}], "d": 3, "e": "x"})
        self.assertIsInstance(out["a"], Decimal)
        self.assertIsInstance(out["b"][0]["c"], Decimal)


if __name__ == "__main__":
    unittest.main()
