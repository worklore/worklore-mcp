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

    def test_second_publish_succeeds_with_similarity_scores(self):
        table = FakeTable()
        story1 = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        story2 = {
            "slug": "debugging-cron-jobs",
            "title": "Debugging cron jobs",
            "tags": ["cron", "monitoring"],
            "body": "Checking logs for cron schedule issues.",
        }
        resp1 = app.handler({"body": app.json.dumps(story1)}, table)
        self.assertEqual(resp1["statusCode"], 201)

        resp2 = app.handler({"body": app.json.dumps(story2)}, table)
        self.assertEqual(resp2["statusCode"], 201)

        stored2 = table.get_item(Key={"slug": "debugging-cron-jobs"})["Item"]
        self.assertEqual(len(stored2["similar"]), 1)
        self.assertEqual(stored2["similar"][0]["slug"], "why-my-cron-ran-twice")


if __name__ == "__main__":
    unittest.main()
