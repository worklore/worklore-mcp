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

    def test_second_publish_stores_similar_scores(self):
        # The table must be seeded: the first publish ever finds no existing
        # stories, so the code that computes similarity scores only runs on
        # the second write. That is where the float-score crash lived.
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        stored = app.publish(table, {
            "slug": "backups-that-actually-restore",
            "title": "Backups that actually restore",
            "tags": ["cron", "backups"],
            "body": "Test your restore, not just your backup cron.",
        })
        self.assertEqual(len(stored["similar"]), 1)
        (score,) = [s["score"] for s in stored["similar"]]
        self.assertNotIsInstance(score, float)


if __name__ == "__main__":
    unittest.main()
