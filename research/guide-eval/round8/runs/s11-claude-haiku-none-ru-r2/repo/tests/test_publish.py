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

    def test_second_publish_with_related_stories_is_stored(self):
        # The first publish has nothing to compare against, so ``similar`` is
        # empty. The second one gets scores, which used to be floats and made
        # DynamoDB reject the item.
        table = FakeTable()
        first = {"slug": "why-my-cron-ran-twice", "title": "Cron", "tags": ["cron", "linux"], "body": "cron ran twice"}
        second = {"slug": "cron-once-again", "title": "Cron again", "tags": ["cron"], "body": "cron ran once"}
        app.publish(table, first)
        stored = app.publish(table, second)
        self.assertEqual([s["slug"] for s in stored["similar"]], ["why-my-cron-ran-twice"])
        self.assertIsInstance(stored["similar"][0]["score"], Decimal)

    def test_handler_returns_201_on_second_publish(self):
        table = FakeTable()
        first = {"slug": "aaa", "title": "A", "body": "cron twice", "tags": ["cron"]}
        second = {"slug": "bbb", "title": "B", "body": "cron once", "tags": ["cron"]}
        self.assertEqual(app.handler({"body": json.dumps(first)}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": json.dumps(second)}, table)["statusCode"], 201)


class FakeTableTest(unittest.TestCase):
    def test_rejects_float_like_dynamodb(self):
        with self.assertRaises(TypeError):
            FakeTable().put_item(Item={"slug": "x", "score": 0.5})


if __name__ == "__main__":
    unittest.main()
