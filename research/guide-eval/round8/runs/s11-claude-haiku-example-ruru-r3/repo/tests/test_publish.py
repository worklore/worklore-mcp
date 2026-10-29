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

    def test_publish_into_non_empty_table(self):
        # The first publish never computes similarity scores (the table is
        # empty), so the second publish is the first one that writes them.
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        stored = app.publish(table, {
            "slug": "cron-mail-spam",
            "title": "Cron mail spam",
            "tags": ["cron"],
            "body": "Every cron job mails its output to the crontab owner.",
        })
        self.assertEqual(stored["similar"][0]["slug"], "why-my-cron-ran-twice")
        self.assertEqual(table.scan()["Count"], 2)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        first = {"slug": "why-my-cron-ran-twice", "title": "Why my cron ran twice",
                 "tags": ["cron"], "body": "Two crontabs had the same line."}
        second = {"slug": "cron-mail-spam", "title": "Cron mail spam",
                  "tags": ["cron"], "body": "Every cron job mails its output."}
        self.assertEqual(app.handler({"body": json.dumps(first)}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": json.dumps(second)}, table)["statusCode"], 201)

    def test_to_dynamo_converts_nested_floats(self):
        value = {"a": 0.1234, "b": [{"c": 1.5}], "d": 2, "e": "x"}
        self.assertEqual(app.to_dynamo(value),
                         {"a": Decimal("0.1234"), "b": [{"c": Decimal("1.5")}], "d": 2, "e": "x"})


if __name__ == "__main__":
    unittest.main()
