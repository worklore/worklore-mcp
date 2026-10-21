import json
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

    def test_second_publish_with_related_stories_is_stored(self):
        # Regression: the second publish carries a similarity score, and
        # DynamoDB rejects float values, so this used to return 500.
        table = FakeTable()
        app.publish(table, {"slug": "first-story", "title": "First", "tags": ["cron"], "body": "cron ran twice"})
        stored = app.publish(table, {"slug": "second-story", "title": "Second", "tags": ["cron"], "body": "cron ran twice"})
        self.assertEqual(len(stored["similar"]), 1)
        self.assertEqual(table.scan()["Count"], 2)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        body = lambda slug: json.dumps({"slug": slug, "title": slug, "tags": ["cron"], "body": "cron ran twice"})
        self.assertEqual(app.handler({"body": body("first-story")}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": body("second-story")}, table)["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
