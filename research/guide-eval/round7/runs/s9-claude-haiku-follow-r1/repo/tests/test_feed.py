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

    def test_hide_writes_the_flag(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.hide("hello", by="ann")
        item = self.lib.get("hello")
        self.assertIs(item["hidden"], True)
        self.assertEqual(item["hidden_by"], "ann")

    def test_hidden_story_leaves_the_feed(self):
        # The flag must be set on the record the feed reads, so the filter is exercised.
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.publish("other", "Other", "...", "bob")
        self.lib.hide("hello", by="ann")
        self.assertEqual([s["slug"] for s in self.lib.feed()], ["other"])

    def test_hide_unknown_story_is_rejected(self):
        with self.assertRaises(ClientError) as cm:
            self.lib.hide("nope", by="ann")
        self.assertEqual(cm.exception.response["Error"]["Code"], "ConditionalCheckFailedException")

    def test_archive_sets_archived_at(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.archive("hello")
        self.assertEqual(self.lib.get("hello")["archived_at"], self.now)

    def test_bare_reserved_word_in_projection_is_loud_in_tests(self):
        # The real service drops it silently; the test table must not.
        table = FakeTable()
        table.put_item(Item={"slug": "a", "hidden": True})
        with self.assertRaises(ClientError):
            table.scan(ProjectionExpression="slug, hidden")


if __name__ == "__main__":
    unittest.main()
