import json
import os
import sys
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

    def test_second_publish_stores_scored_similar(self):
        # Regression: the first publish has no other stories, so ``similar`` is
        # empty; the second one stores a computed score, which used to be a
        # float and made put_item raise (500 in production).
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
            "body": "One timer unit replaced the line in both crontabs.",
        })
        self.assertEqual([s["slug"] for s in stored["similar"]], ["why-my-cron-ran-twice"])
        self.assertGreater(stored["similar"][0]["score"], 0)
        self.assertEqual(table.scan()["Count"], 2)

    def test_handler_second_publish_is_201(self):
        table = FakeTable()
        for slug in ("first-story", "second-story", "third-story"):
            body = json.dumps({"slug": slug, "title": slug, "tags": ["x"], "body": "same words here"})
            self.assertEqual(app.handler({"body": body}, table)["statusCode"], 201)

    def test_bad_tags_are_400_not_500(self):
        body = json.dumps({"slug": "abc", "title": "t", "body": "b", "tags": [1.5]})
        self.assertEqual(app.handler({"body": body}, FakeTable())["statusCode"], 400)

    def test_to_dynamo_converts_nested_floats(self):
        self.assertEqual(app.to_dynamo({"a": [{"b": 0.5}]}), {"a": [{"b": Decimal("0.5")}]})


if __name__ == "__main__":
    unittest.main()
