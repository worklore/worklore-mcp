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

    def test_hide_removes_story_from_feed(self):
        self.lib.publish("visible", "Visible Story", "...", "ann")
        self.lib.publish("withdrawn", "Withdrawn Story", "...", "bob")
        self.lib.hide("withdrawn", by="bob")

        feed_slugs = [s["slug"] for s in self.lib.feed()]
        self.assertIn("visible", feed_slugs)
        self.assertNotIn("withdrawn", feed_slugs)

        withdrawn_item = self.lib.get("withdrawn")
        self.assertTrue(withdrawn_item.get("hidden"))
        self.assertEqual(withdrawn_item.get("hidden_by"), "bob")

    def test_feed_excludes_manually_hidden_story(self):
        self.lib.publish("post-1", "Post 1", "...", "ann")
        self.lib.publish("post-2", "Post 2", "...", "bob")
        # Simulate manually setting hidden: True in DynamoDB (e.g. via CLI)
        self.lib.table.update_item(
            Key={"slug": "post-2"},
            UpdateExpression="SET #h = :t",
            ExpressionAttributeNames={"#h": "hidden"},
            ExpressionAttributeValues={":t": True},
        )
        feed_slugs = [s["slug"] for s in self.lib.feed()]
        self.assertEqual(feed_slugs, ["post-1"])

    def test_archive(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.archive("hello")
        item = self.lib.get("hello")
        self.assertEqual(item.get("archived_at"), self.now)


if __name__ == "__main__":
    unittest.main()
