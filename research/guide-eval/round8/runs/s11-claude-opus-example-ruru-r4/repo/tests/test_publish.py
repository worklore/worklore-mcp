import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import app  # noqa: E402
from fake_dynamo import FakeTable  # noqa: E402

CRON = {
    "slug": "why-my-cron-ran-twice",
    "title": "Why my cron ran twice",
    "tags": ["cron", "linux"],
    "body": "Two crontabs, one for root and one for me, both had the line.",
}
SYSTEMD = {
    "slug": "systemd-timers-instead-of-cron",
    "title": "Systemd timers instead of cron",
    "tags": ["cron", "systemd", "linux"],
    "body": "One timer unit replaced the line in both crontabs.",
}


class PublishTest(unittest.TestCase):
    def test_publish_into_empty_table(self):
        table = FakeTable()
        stored = app.publish(table, CRON)
        self.assertEqual(stored["slug"], "why-my-cron-ran-twice")
        self.assertEqual(stored["similar"], [])
        self.assertEqual(table.get_item(Key={"slug": "why-my-cron-ran-twice"})["Item"]["title"], "Why my cron ran twice")
        self.assertEqual(table.scan()["Count"], 1)

    def test_publish_into_seeded_table(self):
        # The real path: the table already has stories, so similarity scores
        # are computed and stored. The empty-table test never reaches this code.
        table = FakeTable()
        app.publish(table, CRON)
        stored = app.publish(table, SYSTEMD)
        self.assertEqual(table.scan()["Count"], 2)
        similar = table.get_item(Key={"slug": SYSTEMD["slug"]})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], [CRON["slug"]])
        self.assertIsInstance(similar[0]["score"], Decimal)
        self.assertGreater(similar[0]["score"], 0)
        self.assertEqual(stored["similar"], similar)

    def test_handler_second_publish_returns_201(self):
        import json
        table = FakeTable()
        for story in (CRON, SYSTEMD):
            resp = app.handler({"body": json.dumps(story)}, table)
            self.assertEqual(resp["statusCode"], 201, resp)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.5, "b": [{"c": 1.25}], "d": 3, "e": "x", "f": True})
        self.assertEqual(out, {"a": Decimal("0.5"), "b": [{"c": Decimal("1.25")}], "d": 3, "e": "x", "f": True})


if __name__ == "__main__":
    unittest.main()
