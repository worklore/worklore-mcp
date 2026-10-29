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

    def test_second_publish_stores_decimal_similarity(self):
        table = FakeTable()
        first = {
            "slug": "first-story",
            "title": "First story",
            "tags": ["python", "testing"],
            "body": "python tests catch bugs",
        }
        second = {
            "slug": "second-story",
            "title": "Second story",
            "tags": ["python", "dynamodb"],
            "body": "python tests find bugs",
        }

        self.assertEqual(app.handler({"body": app.json.dumps(first)}, table)["statusCode"], 201)
        self.assertEqual(app.handler({"body": app.json.dumps(second)}, table)["statusCode"], 201)

        stored = table.get_item(Key={"slug": "second-story"})["Item"]
        self.assertEqual(stored["similar"], [{"slug": "first-story", "score": Decimal("0.4133")}])
        self.assertEqual(table.scan()["Count"], 2)

    def test_numeric_input_cannot_reach_dynamodb(self):
        table = FakeTable()
        valid = {"slug": "story-one", "title": "Story", "body": "Text", "tags": ["python"]}
        for field, value in (("title", 1.5), ("body", 1.5), ("tags", ["python", 1.5])):
            with self.subTest(field=field):
                story = {**valid, field: value}
                response = app.handler({"body": app.json.dumps(story)}, table)
                self.assertEqual(response["statusCode"], 400)
                self.assertEqual(table.scan()["Count"], 0)


if __name__ == "__main__":
    unittest.main()
