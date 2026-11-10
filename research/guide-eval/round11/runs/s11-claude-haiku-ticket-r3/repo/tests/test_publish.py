import json
import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import app  # noqa: E402
from fake_dynamo import FakeTable  # noqa: E402

SEED = {
    "slug": "crontab-basics",
    "title": "Crontab basics",
    "tags": ["cron", "linux"],
    "body": "Each user has a crontab; the system has /etc/crontab.",
}

NEW = {
    "slug": "why-my-cron-ran-twice",
    "title": "Why my cron ran twice",
    "tags": ["cron", "linux"],
    "body": "Two crontabs, one for root and one for me, both had the line.",
}


def seeded_table():
    """A table that already holds one story, so the scoring path runs."""
    table = FakeTable()
    app.publish(table, SEED)
    return table


class PublishTest(unittest.TestCase):
    def test_publish_stores_story_into_empty_table(self):
        table = FakeTable()
        stored = app.publish(table, NEW)
        self.assertEqual(stored["slug"], "why-my-cron-ran-twice")
        self.assertEqual(table.get_item(Key={"slug": "why-my-cron-ran-twice"})["Item"]["title"], "Why my cron ran twice")
        self.assertEqual(table.scan()["Count"], 1)

    def test_publish_into_populated_table_stores_scored_similar(self):
        table = seeded_table()
        stored = app.publish(table, NEW)
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual([s["slug"] for s in stored["similar"]], ["crontab-basics"])
        self.assertIsInstance(stored["similar"][0]["score"], float)
        item = table.get_item(Key={"slug": "why-my-cron-ran-twice"})["Item"]
        self.assertEqual(item["similar"][0]["score"], Decimal(str(stored["similar"][0]["score"])))

    def test_second_publish_through_handler_returns_201(self):
        table = seeded_table()
        event = {"body": json.dumps(NEW)}
        response = app.handler(event, table)
        self.assertEqual(response["statusCode"], 201)

    def test_to_dynamo_converts_nested_floats_only(self):
        out = app.to_dynamo({"a": 0.4286, "b": [{"s": 1.0}], "n": 3, "t": "x", "ok": True})
        self.assertEqual(out, {"a": Decimal("0.4286"), "b": [{"s": Decimal("1.0")}], "n": 3, "t": "x", "ok": True})


if __name__ == "__main__":
    unittest.main()
