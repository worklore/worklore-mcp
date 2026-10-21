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

    def test_second_publish_with_existing_records(self):
        # The populated-table path computes similarity scores; first-write
        # tests never reach it.
        table = FakeTable()
        app.publish(table, {"slug": "first-story", "title": "First", "tags": ["cron", "linux"],
                            "body": "Two crontabs both had the line."})
        stored = app.publish(table, {"slug": "second-story", "title": "Second", "tags": ["cron"],
                                     "body": "A crontab ran twice."})
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual(len(stored["similar"]), 1)
        score = stored["similar"][0]["score"]
        self.assertIsInstance(score, int)
        self.assertTrue(0 <= score <= 100)

    def test_handler_twice_returns_201(self):
        import json
        table = FakeTable()
        for slug in ("story-one", "story-two"):
            body = json.dumps({"slug": slug, "title": "T", "tags": ["a"], "body": "some body text"})
            self.assertEqual(app.handler({"body": body}, table)["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
