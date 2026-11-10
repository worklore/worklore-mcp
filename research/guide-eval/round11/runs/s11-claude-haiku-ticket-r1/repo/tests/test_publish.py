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

    # The empty-table path never computes scores, so it cannot catch float
    # values reaching put_item. Every write-path test below seeds the table
    # with one existing story first so the scoring path actually runs.

    def _seeded_table(self):
        table = FakeTable()
        table.put_item(Item={
            "slug": "seed-story",
            "title": "Seed",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
            "published_at": 1,
            "similar": [],
        })
        return table

    def test_publish_with_existing_story_stores_scores(self):
        table = self._seeded_table()
        story = {
            "slug": "cron-again",
            "title": "Cron again",
            "tags": ["cron"],
            "body": "Two crontabs both had the line.",
        }
        stored = app.publish(table, story)
        self.assertEqual([s["slug"] for s in stored["similar"]], ["seed-story"])
        self.assertIn("score", stored["similar"][0])
        self.assertEqual(table.get_item(Key={"slug": "cron-again"})["Item"]["similar"][0]["slug"], "seed-story")

    def test_handler_second_publish_returns_201(self):
        table = self._seeded_table()
        event = {"body": json.dumps({
            "slug": "cron-again",
            "title": "Cron again",
            "tags": ["cron"],
            "body": "Two crontabs both had the line.",
        })}
        response = app.handler(event, table)
        self.assertEqual(response["statusCode"], 201, response)

    def test_scores_are_stored_as_decimal_not_float(self):
        table = self._seeded_table()
        app.handler({"body": json.dumps({
            "slug": "cron-again",
            "title": "Cron again",
            "tags": ["cron", "linux", "other"],
            "body": "Two crontabs both had the line and more words here.",
        })}, table)
        stored = table.get_item(Key={"slug": "cron-again"})["Item"]
        score = stored["similar"][0]["score"]
        self.assertIsInstance(score, Decimal)
        self.assertEqual(score, Decimal(str(app.similarity(
            {"tags": ["cron", "linux", "other"], "body": "Two crontabs both had the line and more words here."},
            {"tags": ["cron", "linux"], "body": "Two crontabs, one for root and one for me, both had the line."},
        ))))

    def test_to_dynamo_converts_nested_floats(self):
        value = {"a": 0.5, "b": [{"c": 0.25}, 1, "x"], "d": None}
        converted = app.to_dynamo(value)
        self.assertEqual(converted, {"a": Decimal("0.5"), "b": [{"c": Decimal("0.25")}, 1, "x"], "d": None})
        self.assertIsInstance(converted["a"], Decimal)


if __name__ == "__main__":
    unittest.main()
