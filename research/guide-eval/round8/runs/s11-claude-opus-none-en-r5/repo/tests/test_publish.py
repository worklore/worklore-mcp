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

    def test_second_publish_stores_float_free_scores(self):
        # Regression: the 2nd publish has a non-empty `similar` list whose
        # scores used to be floats, which DynamoDB rejects (500 in prod).
        table = FakeTable()
        app.publish(table, {
            "slug": "why-my-cron-ran-twice", "title": "Why my cron ran twice",
            "tags": ["cron", "linux"], "body": "Two crontabs both had the line.",
        })
        stored = app.publish(table, {
            "slug": "cron-and-timezones", "title": "Cron and timezones",
            "tags": ["cron"], "body": "Cron ran at the wrong hour: two timezones.",
        })
        self.assertEqual([s["slug"] for s in stored["similar"]], ["why-my-cron-ran-twice"])
        self.assertGreater(stored["similar"][0]["score"], 0)
        self.assertEqual(table.scan()["Count"], 2)

    def test_handler_returns_201_for_every_publish(self):
        table = FakeTable()
        for i in range(5):
            body = {"slug": f"story-{i}", "title": f"Story {i}", "tags": ["a", f"t{i}"], "body": "shared words here"}
            resp = app.handler({"body": app.json.dumps(body)}, table)
            self.assertEqual(resp["statusCode"], 201, resp)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.5, "b": [{"c": 1.25}], "d": 3, "e": "x"})
        self.assertEqual(out, {"a": app.Decimal("0.5"), "b": [{"c": app.Decimal("1.25")}], "d": 3, "e": "x"})
        self.assertIsInstance(out["b"][0]["c"], app.Decimal)


if __name__ == "__main__":
    unittest.main()
