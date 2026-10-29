import json
import os
import sys
import unittest
from decimal import Decimal
from unittest.mock import patch

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
        # Regression: the first publish has nothing to compare against, so the
        # float-score bug only showed up from the second publish on (HTTP 500).
        table = FakeTable()
        stories = [
            {"slug": "why-my-cron-ran-twice", "title": "Why my cron ran twice",
             "tags": ["cron", "linux"], "body": "Two crontabs, one for root and one for me."},
            {"slug": "cron-env-variables", "title": "Cron environment variables",
             "tags": ["cron", "linux"], "body": "Cron runs with a minimal PATH and no shell profile."},
            {"slug": "docker-volume-perms", "title": "Docker volume permissions",
             "tags": ["docker"], "body": "Named volumes keep the uid of the image user."},
        ]
        for story in stories:
            response = app.handler({"body": json.dumps(story)}, table)
            self.assertEqual(response["statusCode"], 201, response)

        similar = table.get_item(Key={"slug": "cron-env-variables"})["Item"]["similar"]
        self.assertEqual([s["slug"] for s in similar], ["why-my-cron-ran-twice"])
        self.assertIsInstance(similar[0]["score"], Decimal)


    def test_float_in_item_is_converted_before_storing(self):
        # Any future float field must not turn into a 500 on the second publish.
        table = FakeTable()
        app.publish(table, {"slug": "first-story", "title": "First", "body": "alpha beta"})
        with patch.object(app, "related", return_value=[{"slug": "first-story", "score": 0.25}]):
            app.publish(table, {"slug": "second-story", "title": "Second", "body": "gamma"})
        self.assertEqual(table.get_item(Key={"slug": "second-story"})["Item"]["similar"][0]["score"], Decimal("0.25"))


class FakeTableTest(unittest.TestCase):
    def test_fake_rejects_float_like_boto3(self):
        # Guards the guard: if the fake stops rejecting floats, the regression test above proves nothing.
        with self.assertRaises(TypeError):
            FakeTable().put_item(Item={"slug": "abc", "score": 0.5})


if __name__ == "__main__":
    unittest.main()
