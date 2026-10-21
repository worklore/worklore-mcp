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


    def _seeded_table(self):
        # The populated table is the real path: with an empty table there are no
        # similarity scores, so the first-ever publish never exercises them.
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        })
        return table

    def test_second_publish_stores_similarity_scores(self):
        table = self._seeded_table()
        stored = app.publish(table, {
            "slug": "cron-and-timezones",
            "title": "Cron and timezones",
            "tags": ["cron", "dst"],
            "body": "The cron line ran twice on the night the clocks changed.",
        })
        similar = table.get_item(Key={"slug": "cron-and-timezones"})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], ["why-my-cron-ran-twice"])
        self.assertIsInstance(similar[0]["score"], Decimal)
        self.assertGreater(similar[0]["score"], 0)
        self.assertEqual(stored["similar"], similar)
        self.assertEqual(table.scan()["Count"], 2)

    def test_handler_publishes_twice(self):
        table = FakeTable()
        for slug in ("first-story", "second-story", "third-story"):
            event = {"body": json.dumps({"slug": slug, "title": slug, "tags": ["x"], "body": "same words"})}
            self.assertEqual(app.handler(event, table)["statusCode"], 201, slug)

    def test_to_dynamo_converts_nested_floats(self):
        item = app.to_dynamo({"a": 0.5, "b": [{"c": 0.1234}], "d": 3, "e": "s", "f": True})
        self.assertEqual(item, {"a": Decimal("0.5"), "b": [{"c": Decimal("0.1234")}], "d": 3, "e": "s", "f": True})
        with self.assertRaises(TypeError):
            app.to_dynamo({"x": float("nan")})


if __name__ == "__main__":
    unittest.main()
