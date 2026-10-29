import os
import sys
import json
import unittest
from decimal import Decimal

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


    def test_second_publish_with_existing_story(self):
        # The populated-table path: related() actually computes scores here.
        # The empty-table test above never reaches it, which is how the
        # float-in-put_item bug shipped (logs/error.log, 2026-07-31).
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        stored = app.publish(table, {
            "slug": "systemd-timers-instead-of-cron",
            "title": "Systemd timers instead of cron",
            "tags": ["cron", "systemd"],
            "body": "I replaced the line in my crontab with a systemd timer.",
        })
        self.assertEqual(table.scan()["Count"], 2)
        similar = table.get_item(Key={"slug": "systemd-timers-instead-of-cron"})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], ["why-my-cron-ran-twice"])
        self.assertIsInstance(similar[0]["score"], Decimal)
        self.assertGreater(similar[0]["score"], 0)
        self.assertEqual(stored["similar"], similar)

    def test_handler_publishes_twice(self):
        table = FakeTable()
        for slug in ("first-story", "second-story", "third-story"):
            body = {"slug": slug, "title": slug, "tags": ["x"], "body": "same words here"}
            resp = app.handler({"body": json.dumps(body)}, table)
            self.assertEqual(resp["statusCode"], 201, resp)

    def test_to_dynamo_removes_floats(self):
        out = app.to_dynamo({"a": 0.5, "b": [{"c": 1 / 3}], "d": 2, "e": "s"})
        self.assertEqual(out, {"a": Decimal("0.5"), "b": [{"c": Decimal(str(1 / 3))}], "d": 2, "e": "s"})


if __name__ == "__main__":
    unittest.main()
