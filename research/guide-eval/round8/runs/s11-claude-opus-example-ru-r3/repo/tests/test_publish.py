import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import app  # noqa: E402
from fake_dynamo import FakeTable  # noqa: E402

FIRST = {
    "slug": "why-my-cron-ran-twice",
    "title": "Why my cron ran twice",
    "tags": ["cron", "linux"],
    "body": "Two crontabs, one for root and one for me, both had the line.",
}
SECOND = {
    "slug": "systemd-timers-instead-of-cron",
    "title": "systemd timers instead of cron",
    "tags": ["cron", "systemd"],
    "body": "One timer unit, one line in the journal, no second crontab.",
}


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

    def test_second_publish_into_populated_table(self):
        # The empty table never computes a score; the populated path is the real one.
        table = FakeTable()
        app.publish(table, FIRST)
        stored = app.publish(table, SECOND)
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual([s["slug"] for s in stored["similar"]], ["why-my-cron-ran-twice"])
        score = table.get_item(Key={"slug": SECOND["slug"]})["Item"]["similar"][0]["score"]
        self.assertGreater(score, 0)

    def test_handler_returns_201_for_every_publish(self):
        table = FakeTable()
        stories = [FIRST, SECOND, dict(FIRST, slug="cron-again", tags=[]), dict(SECOND, slug="no-tags", tags=[], body="x")]
        for story in stories:
            resp = app.handler({"body": json.dumps(story)}, table)
            self.assertEqual(resp["statusCode"], 201, resp)
        self.assertEqual(table.scan()["Count"], len(stories))

    def test_to_dynamo_converts_nested_floats(self):
        item = app.to_dynamo({"a": 0.5, "b": [{"c": 1.25}], "d": 3, "e": "x"})
        FakeTable().put_item(Item=dict(item, slug="abc"))
        self.assertEqual(str(item["b"][0]["c"]), "1.25")


if __name__ == "__main__":
    unittest.main()
