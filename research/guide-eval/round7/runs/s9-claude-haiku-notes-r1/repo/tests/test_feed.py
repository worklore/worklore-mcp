import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.app import StoryLibrary  # noqa: E402
from tests.fake_dynamo import RESERVED, ClientError, FakeTable, _tokens  # noqa: E402

KEYWORDS = {"SET", "REMOVE", "ADD", "DELETE", "AND", "OR", "NOT", "BETWEEN", "IN"}


class StrictTable:
    """FakeTable that also refuses a bare reserved word in ANY expression.

    The fake only raises for bare reserved words in update/condition/filter
    expressions; in a ProjectionExpression the real service drops the attribute
    silently, which is how the hidden flag stopped filtering. This wrapper turns
    that silent case into a test failure."""

    EXPRESSION_ARGS = ("UpdateExpression", "ConditionExpression", "ProjectionExpression", "FilterExpression")

    def __init__(self):
        self._table = FakeTable()

    def __getattr__(self, name):
        method = getattr(self._table, name)

        def checked(*args, **kwargs):
            for arg in self.EXPRESSION_ARGS:
                for tok in _tokens(kwargs.get(arg) or ""):
                    if tok.upper() in RESERVED and tok.upper() not in KEYWORDS and tok[0] not in "#:(),<>=":
                        raise AssertionError(f"{name}: bare reserved word {tok!r} in {arg}")
            return method(*args, **kwargs)

        return checked


class FeedTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_700_000_000
        self.lib = StoryLibrary(StrictTable(), clock=lambda: self.now)

    def slugs(self):
        return [s["slug"] for s in self.lib.feed()]

    def test_publish_then_feed_lists_it(self):
        self.lib.publish("hello", "Hello", "first post", "ann")
        self.assertEqual(self.slugs(), ["hello"])

    def test_feed_is_newest_first(self):
        self.lib.publish("old", "Old", "...", "ann")
        self.now += 60
        self.lib.publish("new", "New", "...", "bob")
        self.assertEqual(self.slugs(), ["new", "old"])

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

    def test_hide_takes_story_out_of_feed(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.publish("other", "Other", "...", "bob")
        self.lib.hide("hello", by="ann")
        self.assertEqual(self.slugs(), ["other"])

    def test_hide_records_who_and_when(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.hide("hello", by="ann")
        item = self.lib.get("hello")
        self.assertEqual((item["hidden"], item["hidden_by"], item["hidden_at"]), (True, "ann", self.now))

    def test_story_hidden_by_hand_leaves_feed(self):
        # The staging case: the flag was written directly with the AWS CLI,
        # so the feed has to honour it without going through hide().
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.table.update_item(
            Key={"slug": "hello"},
            UpdateExpression="SET #h = :t",
            ExpressionAttributeNames={"#h": "hidden"},
            ExpressionAttributeValues={":t": True},
        )
        self.assertEqual(self.slugs(), [])

    def test_archive_sets_archived_at_on_published_story(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.archive("hello")
        self.assertEqual(self.lib.get("hello")["archived_at"], self.now)


if __name__ == "__main__":
    unittest.main()
