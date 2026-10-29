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

    def test_second_publish_with_related_stories(self):
        table = FakeTable()
        app.publish(table, {"slug": "first-story", "title": "A", "tags": ["cron"], "body": "cron twice"})
        stored = app.publish(table, {"slug": "second-story", "title": "B", "tags": ["cron"], "body": "cron once"})
        self.assertEqual(stored["similar"][0]["slug"], "first-story")
        self.assertEqual(table.scan()["Count"], 2)
        # republishing (scan now returns Decimal scores) must also work
        app.publish(table, {"slug": "third-story", "title": "C", "tags": ["cron"], "body": "cron"})


if __name__ == "__main__":
    unittest.main()
