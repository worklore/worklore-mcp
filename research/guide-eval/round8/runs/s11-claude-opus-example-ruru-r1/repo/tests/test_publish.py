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

    def test_publish_into_non_empty_table(self):
        # The empty-table path never computes a score; seed one story first so
        # the similarity code runs and its values go through put_item.
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        stored = app.publish(table, {
            "slug": "systemd-timers-instead-of-cron",
            "title": "systemd timers instead of cron",
            "tags": ["cron", "systemd"],
            "body": "One timer unit replaced the line in both crontabs.",
        })
        self.assertEqual(table.scan()["Count"], 2)
        similar = table.get_item(Key={"slug": "systemd-timers-instead-of-cron"})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], ["why-my-cron-ran-twice"])
        self.assertGreater(similar[0]["score"], 0)
        self.assertEqual(stored["similar"], similar)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        for slug in ("first-story", "second-story", "third-story"):
            event = {"body": json.dumps({"slug": slug, "title": slug, "tags": ["x"], "body": "same words here"})}
            self.assertEqual(app.handler(event, table)["statusCode"], 201)


if __name__ == "__main__":
    unittest.main()
