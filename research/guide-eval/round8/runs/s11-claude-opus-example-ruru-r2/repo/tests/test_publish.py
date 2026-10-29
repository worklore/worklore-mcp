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
    "slug": "systemd-timer-fired-twice",
    "title": "My systemd timer fired twice",
    "tags": ["linux", "systemd"],
    "body": "The timer and a leftover cron line both had the job.",
}


class PublishTest(unittest.TestCase):
    def test_publish_into_empty_table(self):
        table = FakeTable()
        stored = app.publish(table, CRON)
        self.assertEqual(stored["slug"], "why-my-cron-ran-twice")
        self.assertEqual(table.get_item(Key={"slug": "why-my-cron-ran-twice"})["Item"]["title"], "Why my cron ran twice")
        self.assertEqual(table.scan()["Count"], 1)
        self.assertEqual(stored["similar"], [])

    def test_publish_into_seeded_table(self):
        # The empty-table path never computes a score; this one does (the prod 500).
        table = FakeTable()
        app.publish(table, CRON)
        stored = app.publish(table, SYSTEMD)
        self.assertEqual(table.scan()["Count"], 2)
        similar = table.get_item(Key={"slug": SYSTEMD["slug"]})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], [CRON["slug"]])
        self.assertIsInstance(similar[0]["score"], Decimal)
        self.assertGreater(similar[0]["score"], 0)
        self.assertEqual(stored["similar"], similar)

    def test_handler_second_publish_is_201(self):
        import json
        table = FakeTable()
        self.assertEqual(app.handler({"body": json.dumps(CRON)}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": json.dumps(SYSTEMD)}, table)["statusCode"], 201)

    def test_publish_more_than_top_n(self):
        table = FakeTable()
        for i in range(app.TOP_N + 2):
            app.publish(table, dict(CRON, slug=f"story-{i}", tags=["cron", f"t{i}"]))
        item = table.get_item(Key={"slug": f"story-{app.TOP_N + 1}"})["Item"]
        self.assertEqual(len(item["similar"]), app.TOP_N)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.5, "b": [{"c": 0.25}], "d": 1, "e": "x"})
        self.assertEqual(out, {"a": Decimal("0.5"), "b": [{"c": Decimal("0.25")}], "d": 1, "e": "x"})


if __name__ == "__main__":
    unittest.main()
