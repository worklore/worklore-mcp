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

    def test_publish_second_story_calculates_similarity(self):
        table = FakeTable()
        story1 = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        story2 = {
            "slug": "cron-in-docker-gotchas",
            "title": "Cron in Docker Gotchas",
            "tags": ["cron", "docker"],
            "body": "Cron does not receive environment variables in containers by default.",
        }
        app.publish(table, story1)
        stored2 = app.publish(table, story2)
        self.assertEqual(stored2["slug"], "cron-in-docker-gotchas")
        self.assertEqual(len(stored2["similar"]), 1)
        self.assertEqual(stored2["similar"][0]["slug"], "why-my-cron-ran-twice")
        self.assertGreater(stored2["similar"][0]["score"], 0)

        # Also verify handler end-to-end
        event = {
            "body": '{"slug": "cron-debugging-guide", "title": "Cron Guide", "tags": ["cron"], "body": "debugging cron tips"}'
        }
        resp = app.handler(event, table)
        self.assertEqual(resp["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
