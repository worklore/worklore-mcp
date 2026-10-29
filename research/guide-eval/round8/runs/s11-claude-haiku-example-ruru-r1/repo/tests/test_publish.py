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

    def test_second_publish_with_similar_story_stores(self):
        # The first publish runs against an empty table and never computes a
        # similarity score. The second one does, so this is the path that
        # used to fail with "Float types are not supported".
        table = FakeTable()
        first = {
            "slug": "why-my-cron-ran-twice",
            "title": "Why my cron ran twice",
            "tags": ["cron", "linux"],
            "body": "Two crontabs, one for root and one for me, both had the line.",
        }
        second = {
            "slug": "cron-and-systemd-timers",
            "title": "Cron and systemd timers",
            "tags": ["cron", "systemd"],
            "body": "Two schedulers ran the same job, cron and a systemd timer.",
        }
        app.publish(table, first)
        stored = app.publish(table, second)
        self.assertEqual(stored["similar"][0]["slug"], "why-my-cron-ran-twice")
        self.assertEqual(table.scan()["Count"], 2)

    def test_handler_returns_201_on_second_publish(self):
        # Production symptom: the second POST returned 500. Check the handler
        # result, not just publish(), because the handler turns errors into 500.
        table = FakeTable()
        first = json.dumps({"slug": "first-story", "title": "First", "tags": ["a"], "body": "alpha beta"})
        second = json.dumps({"slug": "second-story", "title": "Second", "tags": ["a"], "body": "alpha gamma"})
        self.assertEqual(app.handler({"body": first}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": second}, table)["statusCode"], 201)

    def test_stored_score_is_decimal_with_same_value(self):
        table = FakeTable()
        app.publish(table, {"slug": "first-story", "title": "First", "tags": ["a"], "body": "alpha beta"})
        app.publish(table, {"slug": "second-story", "title": "Second", "tags": ["a"], "body": "alpha gamma"})
        score = table.get_item(Key={"slug": "second-story"})["Item"]["similar"][0]["score"]
        self.assertIsInstance(score, Decimal)
        self.assertEqual(score, Decimal(str(app.similarity(
            {"tags": ["a"], "body": "alpha gamma"}, {"tags": ["a"], "body": "alpha beta"}))))


class ToDynamoTest(unittest.TestCase):
    def test_converts_nested_floats_only(self):
        item = {"slug": "x", "n": 0.5, "s": "x", "i": 3, "b": True, "none": None,
                "list": [{"score": 0.1}, 2.0], "tup": (1.5,)}
        out = app.to_dynamo(item)
        self.assertEqual(out["n"], Decimal("0.5"))
        self.assertEqual(out["list"][0]["score"], Decimal("0.1"))
        self.assertEqual(out["list"][1], Decimal("2.0"))
        self.assertEqual(out["tup"], [Decimal("1.5")])
        self.assertEqual(out["s"], "x")
        self.assertEqual(out["i"], 3)
        self.assertIs(out["b"], True)
        self.assertIsNone(out["none"])
        FakeTable().put_item(Item=out)  # would raise on any float left behind


if __name__ == "__main__":
    unittest.main()
