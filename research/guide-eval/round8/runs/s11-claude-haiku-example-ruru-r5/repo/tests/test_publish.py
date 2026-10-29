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

    # The write path has two executions: an empty table (no scores, no floats)
    # and a populated one (scores are computed). Only the second one used to
    # break, so every write test seeds one story first and then publishes.
    def seeded_table(self):
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        return table

    def test_publish_with_existing_story_stores_scores(self):
        table = self.seeded_table()
        story = {
            "slug": "why-my-cron-cleared-env",
            "title": "Why my cron lost PATH",
            "tags": ["cron", "linux", "shell"],
            "body": "The crontab ran with a minimal environment and no PATH.",
        }
        stored = app.publish(table, story)
        self.assertEqual([s["slug"] for s in stored["similar"]], ["why-my-cron-ran-twice"])
        self.assertGreater(stored["similar"][0]["score"], 0)
        self.assertEqual(table.scan()["Count"], 2)

    def test_handler_second_publish_returns_201(self):
        table = self.seeded_table()
        event = {"body": '{"slug": "cron-path", "title": "Cron PATH", "tags": ["cron"], "body": "crontab has no PATH"}'}
        response = app.handler(event, table)
        self.assertEqual(response["statusCode"], 201, response["body"])


if __name__ == "__main__":
    unittest.main()
