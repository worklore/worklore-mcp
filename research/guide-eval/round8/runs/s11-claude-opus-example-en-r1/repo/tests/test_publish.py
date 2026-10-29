import os
import json
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


CRON = {
    "slug": "why-my-cron-ran-twice",
    "title": "Why my cron ran twice",
    "tags": ["cron", "linux"],
    "body": "Two crontabs, one for root and one for me, both had the line.",
}
SYSTEMD = {
    "slug": "systemd-timers-instead-of-cron",
    "title": "systemd timers instead of cron",
    "tags": ["cron", "systemd", "linux"],
    "body": "A timer unit runs once, and the journal has the line it printed.",
}
UNRELATED = {
    "slug": "sourdough-notes",
    "title": "Sourdough notes",
    "tags": ["baking"],
    "body": "Flour, water, salt.",
}


def seeded_table(*stories):
    """A table that already holds ``stories`` -- the state production is in on every publish but the first."""
    table = FakeTable()
    for s in stories:
        app.publish(table, s)
    return table


class PublishIntoPopulatedTableTest(unittest.TestCase):
    def test_second_publish_stores_scores_as_decimal(self):
        table = seeded_table(CRON)
        stored = app.publish(table, SYSTEMD)
        self.assertEqual(table.scan()["Count"], 2)
        [match] = stored["similar"]
        self.assertEqual(match["slug"], CRON["slug"])
        self.assertIsInstance(match["score"], Decimal)
        self.assertGreater(match["score"], 0)

    def test_zero_score_is_not_a_float_either(self):
        # round(0.7 * 0 + 0.3 * 0, 4) == 0.0 -- unrelated stories crashed too.
        table = seeded_table(CRON)
        stored = app.publish(table, UNRELATED)
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)

    def test_handler_publishes_twice_in_a_row(self):
        table = FakeTable()
        for story in (CRON, SYSTEMD, UNRELATED):
            resp = app.handler({"body": json.dumps(story)}, table)
            self.assertEqual(resp["statusCode"], 201, resp)
        stored = table.get_item(Key={"slug": UNRELATED["slug"]})["Item"]
        self.assertEqual(len(stored["similar"]), 2)

    def test_related_is_ranked_and_capped(self):
        extra = dict(UNRELATED, slug="bread-notes", tags=["baking", "linux"])
        table = seeded_table(CRON, UNRELATED, extra, dict(SYSTEMD, slug="more-cron"))
        stored = app.publish(table, SYSTEMD)
        self.assertEqual(len(stored["similar"]), app.TOP_N)
        scores = [m["score"] for m in stored["similar"]]
        self.assertEqual(scores, sorted(scores, reverse=True))


class BadInputTest(unittest.TestCase):
    def test_wrongly_typed_fields_are_400_not_500(self):
        table = FakeTable()
        for bad in (
            dict(CRON, title=1.5),
            dict(CRON, body=["a"]),
            dict(CRON, tags=[1.5]),
            dict(CRON, tags="cron"),
        ):
            resp = app.handler({"body": json.dumps(bad)}, table)
            self.assertEqual(resp["statusCode"], 400, (bad, resp))
        self.assertEqual(app.handler({"body": "[1]"}, table)["statusCode"], 400)


class ToDynamoTest(unittest.TestCase):
    def test_floats_anywhere_become_decimals(self):
        out = app.to_dynamo({"a": 0.1, "b": [{"c": 2.5}], "d": True, "e": 3, "f": "x"})
        self.assertEqual(out, {"a": Decimal("0.1"), "b": [{"c": Decimal("2.5")}], "d": True, "e": 3, "f": "x"})

    def test_non_finite_rejected(self):
        with self.assertRaises(ValueError):
            app.to_dynamo({"x": float("nan")})


if __name__ == "__main__":
    unittest.main()
