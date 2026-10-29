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

    def test_second_publish_with_existing_data(self):
        table = FakeTable()
        a = {"slug": "first-story", "title": "A", "tags": ["cron", "linux"], "body": "cron runs twice"}
        b = {"slug": "second-story", "title": "B", "tags": ["cron"], "body": "cron on linux"}
        app.publish(table, a)
        stored = app.publish(table, b)  # populated path: computes similarity
        self.assertEqual(stored["similar"][0]["slug"], "first-story")
        self.assertIsInstance(stored["similar"][0]["score"], int)

    def test_handler_second_publish_returns_201(self):
        import json
        table = FakeTable()
        for slug in ("first-story", "second-story"):
            body = json.dumps({"slug": slug, "title": "T", "tags": ["x"], "body": "same words"})
            self.assertEqual(app.handler({"body": body}, table)["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
