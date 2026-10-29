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

    def test_second_publish_with_similarity_scores(self):
        table = FakeTable()
        story1 = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        app.publish(table, story1)

        story2 = {
            "slug": "crontab-best-practices",
            "title": "Crontab Best Practices",
            "tags": ["cron", "automation"],
            "body": "Tips for managing cron jobs and crontabs on linux servers.",
        }
        stored2 = app.publish(table, story2)
        self.assertEqual(stored2["slug"], "crontab-best-practices")
        self.assertEqual(len(stored2["similar"]), 1)
        self.assertEqual(stored2["similar"][0]["slug"], "why-my-cron-ran-twice")
        self.assertGreater(stored2["similar"][0]["score"], 0)

        # Also test via Lambda handler to verify response format
        story3 = {
            "slug": "third-cron-story",
            "title": "Third Cron Story",
            "tags": ["cron"],
            "body": "Another cron story.",
        }
        response = app.handler({"body": __import__("json").dumps(story3)}, table)
        self.assertEqual(response["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
