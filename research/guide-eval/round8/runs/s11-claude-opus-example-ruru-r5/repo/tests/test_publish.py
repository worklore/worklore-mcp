import json
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
TIMER = {
    "slug": "systemd-timer-instead-of-cron",
    "title": "A systemd timer instead of cron",
    "tags": ["cron", "systemd", "linux"],
    "body": "I replaced the line in my crontab with a timer unit.",
}
THIRD = {
    "slug": "logrotate-ate-my-logs",
    "title": "Logrotate ate my logs",
    "tags": ["linux", "logs"],
    "body": "The cron job for logrotate ran with the wrong config.",
}


def seeded_table(*stories):
    """Table that already holds ``stories`` — the path production takes on every publish but the first."""
    table = FakeTable()
    for s in stories:
        app.publish(table, s)
    return table


class PublishTest(unittest.TestCase):
    def test_publish_into_empty_table(self):
        table = FakeTable()
        stored = app.publish(table, CRON)
        self.assertEqual(stored["slug"], "why-my-cron-ran-twice")
        self.assertEqual(stored["similar"], [])
        self.assertEqual(table.get_item(Key={"slug": CRON["slug"]})["Item"]["title"], "Why my cron ran twice")
        self.assertEqual(table.scan()["Count"], 1)

    def test_publish_into_seeded_table_stores_scores(self):
        # Regression for logs/error.log: the second publish computed a float score and put_item rejected it.
        table = seeded_table(CRON)
        stored = app.publish(table, TIMER)
        self.assertEqual(table.scan()["Count"], 2)
        item = table.get_item(Key={"slug": TIMER["slug"]})["Item"]
        self.assertEqual([s["slug"] for s in item["similar"]], [CRON["slug"]])
        score = item["similar"][0]["score"]
        self.assertIsInstance(score, Decimal)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 1)
        self.assertEqual(stored["similar"][0]["score"], score)

    def test_publish_third_story_ranks_related(self):
        table = seeded_table(CRON, TIMER)
        app.publish(table, THIRD)
        similar = table.get_item(Key={"slug": THIRD["slug"]})["Item"]["similar"]
        self.assertEqual(len(similar), 2)
        self.assertGreaterEqual(similar[0]["score"], similar[1]["score"])

    def test_republish_same_slug_excludes_itself(self):
        table = seeded_table(CRON, TIMER)
        app.publish(table, CRON)
        similar = table.get_item(Key={"slug": CRON["slug"]})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], [TIMER["slug"]])

    def test_handler_twice_returns_201_both_times(self):
        table = FakeTable()
        for story in (CRON, TIMER):
            resp = app.handler({"body": json.dumps(story)}, table)
            self.assertEqual(resp["statusCode"], 201, resp)


class ToDynamoTest(unittest.TestCase):
    def test_floats_become_decimals_at_any_depth(self):
        out = app.to_dynamo({"a": 0.1, "b": [{"c": 0.4667}], "d": 3, "e": True, "f": "x"})
        self.assertEqual(out, {"a": Decimal("0.1"), "b": [{"c": Decimal("0.4667")}], "d": 3, "e": True, "f": "x"})
        self.assertIs(out["e"], True)

    def test_non_finite_rejected(self):
        with self.assertRaises(ValueError):
            app.to_dynamo({"x": float("nan")})


if __name__ == "__main__":
    unittest.main()
