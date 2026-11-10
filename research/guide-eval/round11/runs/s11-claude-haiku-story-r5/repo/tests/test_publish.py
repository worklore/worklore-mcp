import os
import sys
import unittest

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

    def test_second_publish_scores_against_existing_story(self):
        # The populated path: the first write seeds the table, the second one
        # computes similarity scores (the only place floats come from).
        table = FakeTable()
        app.publish(table, {"slug": "first-story", "title": "First", "tags": ["cron", "linux"],
                            "body": "two crontabs ran the same job"})
        stored = app.publish(table, {"slug": "second-story", "title": "Second", "tags": ["cron"],
                                     "body": "a crontab ran a job twice"})
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual([s["slug"] for s in stored["similar"]], ["first-story"])
        item = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertEqual(item["similar"][0]["slug"], "first-story")

    def test_stored_scores_are_decimal_with_same_value(self):
        from decimal import Decimal
        table = FakeTable()
        app.publish(table, {"slug": "first-story", "title": "First", "tags": ["cron", "linux"],
                            "body": "two crontabs ran the same job"})
        app.publish(table, {"slug": "second-story", "title": "Second", "tags": ["cron"],
                            "body": "a crontab ran a job twice"})
        score = table.get_item(Key={"slug": "second-story"})["Item"]["similar"][0]["score"]
        self.assertIsInstance(score, Decimal)
        self.assertEqual(score, Decimal(str(app.similarity(
            {"tags": ["cron"], "body": "a crontab ran a job twice"},
            {"tags": ["cron", "linux"], "body": "two crontabs ran the same job"}))))

    def test_to_dynamo_converts_nested_floats(self):
        from decimal import Decimal
        out = app.to_dynamo({"a": 0.1429, "b": [{"c": 2.0}], "d": 3, "e": "x", "f": None})
        self.assertEqual(out, {"a": Decimal("0.1429"), "b": [{"c": Decimal("2.0")}], "d": 3, "e": "x", "f": None})


if __name__ == "__main__":
    unittest.main()
