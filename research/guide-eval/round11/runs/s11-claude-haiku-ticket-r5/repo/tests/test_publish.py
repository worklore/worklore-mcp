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

    def _story(self, slug, tags, body):
        return {"slug": slug, "title": slug.replace("-", " "), "tags": tags, "body": body}

    def _seeded_table(self):
        # The write path only runs its scoring branch when the table already has
        # stories, so every write-path test starts from a table with one record.
        table = FakeTable()
        app.publish(table, self._story("first-story-here", ["cron"], "crontab entries run twice"))
        return table

    def test_publish_with_existing_story_stores_float_free_item(self):
        table = self._seeded_table()
        stored = app.publish(table, self._story("second-story-here", ["cron", "linux"], "crontab and cron logs"))
        self.assertEqual([s["slug"] for s in stored["similar"]], ["first-story-here"])
        item = table.get_item(Key={"slug": "second-story-here"})["Item"]
        self.assertEqual(item["similar"][0]["slug"], "first-story-here")
        self.assertIsInstance(item["similar"][0]["score"], Decimal)

    def test_handler_second_publish_returns_201(self):
        table = self._seeded_table()
        event = {"body": json.dumps(self._story("second-story-here", ["cron"], "crontab entries"))}
        response = app.handler(event, table)
        self.assertEqual(response["statusCode"], 201, response["body"])

    def test_similar_scores_are_decimal_in_populated_table(self):
        table = self._seeded_table()
        app.publish(table, self._story("second-story-here", ["cron"], "crontab entries"))
        app.publish(table, self._story("third-story-here", ["linux"], "cron and linux"))
        item = table.get_item(Key={"slug": "third-story-here"})["Item"]
        for entry in item["similar"]:
            self.assertIsInstance(entry["score"], Decimal)


if __name__ == "__main__":
    unittest.main()
