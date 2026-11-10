import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import json  # noqa: E402
from decimal import Decimal  # noqa: E402

import app  # noqa: E402
from fake_dynamo import FakeTable  # noqa: E402

CRON = {
    "slug": "why-my-cron-ran-twice",
    "title": "Why my cron ran twice",
    "tags": ["cron", "linux"],
    "body": "Two crontabs, one for root and one for me, both had the line.",
}
SEED = {
    "slug": "cron-basics",
    "title": "Cron basics",
    "tags": ["cron"],
    "body": "A crontab line runs a command on a schedule.",
}


class PublishTest(unittest.TestCase):
    def test_publish_stores_story(self):
        table = FakeTable()
        stored = app.publish(table, CRON)
        self.assertEqual(stored["slug"], "why-my-cron-ran-twice")
        self.assertEqual(table.get_item(Key={"slug": "why-my-cron-ran-twice"})["Item"]["title"], "Why my cron ran twice")
        self.assertEqual(table.scan()["Count"], 1)

    def test_publish_into_populated_table(self):
        # The empty-table path never computes a similarity score, so it cannot
        # exercise the float write. Seed one story first so the score is written.
        table = FakeTable()
        app.publish(table, SEED)
        stored = app.publish(table, CRON)
        self.assertEqual(stored["similar"][0]["slug"], "cron-basics")
        item = table.get_item(Key={"slug": CRON["slug"]})["Item"]
        self.assertIsInstance(item["similar"][0]["score"], Decimal)
        self.assertEqual(item["similar"][0]["score"], Decimal(str(stored["similar"][0]["score"])))
        self.assertEqual(table.scan()["Count"], 2)

    def test_handler_publish_into_populated_table(self):
        table = FakeTable()
        app.publish(table, SEED)
        response = app.handler({"body": json.dumps(CRON)}, table)
        self.assertEqual(response["statusCode"], 201, response["body"])
        self.assertEqual(json.loads(response["body"]), {"slug": CRON["slug"]})

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.4667, "b": [{"s": 1.0}], "c": 3, "d": "x"})
        self.assertEqual(out, {"a": Decimal("0.4667"), "b": [{"s": Decimal("1.0")}], "c": 3, "d": "x"})
        self.assertIsInstance(out["a"], Decimal)


if __name__ == "__main__":
    unittest.main()
