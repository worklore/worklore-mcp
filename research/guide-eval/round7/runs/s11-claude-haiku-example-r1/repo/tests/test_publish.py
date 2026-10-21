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

    def test_publish_second_story_stores_related_scores(self):
        # The populated path: the first write seeds the table so the second one
        # computes similarity scores. That path is the one that broke in production.
        table = FakeTable()
        app.publish(table, {
            "slug": "first-story",
            "title": "First",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        stored = app.publish(table, {
            "slug": "second-story",
            "title": "Second",
            "tags": ["cron"],
            "body": "The cron line ran twice because two crontabs had it.",
        })
        self.assertEqual([s["slug"] for s in stored["similar"]], ["first-story"])
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)
        self.assertEqual(table.scan()["Count"], 2)

    def test_related_scores_are_never_float(self):
        existing = [
            {"slug": f"story-{i}", "tags": ["cron"], "body": f"cron words {i}"}
            for i in range(5)
        ]
        scored = app.related({"slug": "new-story", "tags": ["cron"], "body": "cron words"}, existing)
        self.assertEqual(len(scored), app.TOP_N)
        for s in scored:
            self.assertIsInstance(s["score"], Decimal)


if __name__ == "__main__":
    unittest.main()
