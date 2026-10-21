import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.app import StoryLibrary  # noqa: E402
from tests.fake_dynamo import ClientError, FakeTable  # noqa: E402


class FeedTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_700_000_000
        self.lib = StoryLibrary(FakeTable(), clock=lambda: self.now)

    def test_publish_then_feed_lists_it(self):
        self.lib.publish("hello", "Hello", "first post", "ann")
        self.assertEqual([s["slug"] for s in self.lib.feed()], ["hello"])

    def test_feed_is_newest_first(self):
        self.lib.publish("old", "Old", "...", "ann")
        self.now += 60
        self.lib.publish("new", "New", "...", "bob")
        self.assertEqual([s["slug"] for s in self.lib.feed()], ["new", "old"])

    def test_feed_leaves_bodies_out(self):
        self.lib.publish("hello", "Hello", "a long body", "ann")
        self.assertEqual(set(self.lib.feed()[0]), {"slug", "title", "published_at"})

    def test_publish_twice_is_rejected(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        with self.assertRaises(ClientError) as cm:
            self.lib.publish("hello", "Hello again", "...", "ann")
        self.assertEqual(cm.exception.response["Error"]["Code"], "ConditionalCheckFailedException")

    def test_rename(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.rename("hello", "Hello, world")
        self.assertEqual(self.lib.get("hello")["title"], "Hello, world")

    def test_hide_withdraws_story_from_feed(self):
        self.lib.publish("visible", "Visible", "...", "ann")
        self.lib.publish("hidden", "Hidden", "...", "bob")
        self.lib.hide("hidden", by="bob")

        self.assertEqual([s["slug"] for s in self.lib.feed()], ["visible"])
        self.assertEqual(self.lib.get("hidden")["hidden"], True)
        self.assertEqual(self.lib.get("hidden")["hidden_by"], "bob")
        self.assertEqual(self.lib.get("hidden")["hidden_at"], self.now)

    def test_feed_excludes_story_hidden_outside_library(self):
        self.lib.publish("visible", "Visible", "...", "ann")
        self.lib.publish("hidden", "Hidden", "...", "bob")
        self.lib.table.update_item(
            Key={"slug": "hidden"},
            UpdateExpression="SET #h = :true",
            ExpressionAttributeNames={"#h": "hidden"},
            ExpressionAttributeValues={":true": True},
        )

        self.assertEqual([s["slug"] for s in self.lib.feed()], ["visible"])

    def test_hide_missing_story_does_not_create_it(self):
        with self.assertRaises(ClientError) as cm:
            self.lib.hide("missing", by="ann")
        self.assertEqual(cm.exception.response["Error"]["Code"], "ConditionalCheckFailedException")
        self.assertIsNone(self.lib.get("missing"))

    def test_archive_withdraws_story_from_feed(self):
        self.lib.publish("visible", "Visible", "...", "ann")
        self.lib.publish("archived", "Archived", "...", "bob")
        self.lib.archive("archived")

        self.assertEqual([s["slug"] for s in self.lib.feed()], ["visible"])
        self.assertEqual(self.lib.get("archived")["archived_at"], self.now)


if __name__ == "__main__":
    unittest.main()
