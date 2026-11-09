import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import app  # noqa: E402
from fake_dynamo import FakeTable  # noqa: E402

STORY = {
    "slug": "why-my-cron-ran-twice",
    "title": "Why my cron ran twice",
    "tags": ["cron", "linux"],
    "body": "Two crontabs, one for root and one for me, both had the line.",
}

SECOND_STORY = {
    "slug": "dedupe-cron-output",
    "title": "Dedupe cron output",
    "tags": ["cron"],
    "body": "Two crontabs ran the same line, so the report duplicated.",
}


class PublishTest(unittest.TestCase):
    def test_publish_stores_story(self):
        table = FakeTable()
        stored = app.publish(table, STORY)
        self.assertEqual(stored["slug"], "why-my-cron-ran-twice")
        self.assertEqual(table.get_item(Key={"slug": "why-my-cron-ran-twice"})["Item"]["title"], "Why my cron ran twice")
        self.assertEqual(table.scan()["Count"], 1)

    def test_second_publish_stores_similar_as_decimal(self):
        table = FakeTable()
        app.publish(table, STORY)
        stored = app.publish(table, SECOND_STORY)
        self.assertEqual(table.scan()["Count"], 2)
        (entry,) = stored["similar"]
        self.assertEqual(entry["slug"], "why-my-cron-ran-twice")
        self.assertIsInstance(entry["score"], Decimal)


if __name__ == "__main__":
    unittest.main()
