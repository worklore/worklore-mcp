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

    def test_second_publish_with_existing_stories(self):
        # Regression: the first publish has no neighbours, so no similarity
        # scores (floats) are computed; the crash only shows on a populated table.
        table = FakeTable()
        app.publish(table, {"slug": "why-my-cron-ran-twice", "title": "Cron", "tags": ["cron", "linux"],
                            "body": "Two crontabs both had the line."})
        stored = app.publish(table, {"slug": "systemd-timers", "title": "Timers", "tags": ["linux"],
                                     "body": "Timers replaced the crontab line."})
        self.assertEqual(table.scan()["Count"], 2)
        self.assertEqual(stored["similar"][0]["slug"], "why-my-cron-ran-twice")
        self.assertGreater(stored["similar"][0]["score"], 0)

    def test_handler_second_publish_returns_201(self):
        table = FakeTable()
        for slug in ("first-story", "second-story", "third-story"):
            body = '{"slug": "%s", "title": "T", "tags": ["a"], "body": "same words here"}' % slug
            self.assertEqual(app.handler({"body": body}, table)["statusCode"], 201)

    def test_to_dynamo_converts_nested_floats(self):
        out = app.to_dynamo({"a": 0.5, "b": [{"c": 1.25}], "d": 3, "e": True})
        self.assertEqual(out, {"a": app.Decimal("0.5"), "b": [{"c": app.Decimal("1.25")}], "d": 3, "e": True})


if __name__ == "__main__":
    unittest.main()
