import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.app import StoryLibrary  # noqa: E402
from tests.fake_dynamo import ClientError, FakeTable, _tokens  # noqa: E402

_EXPRESSIONS = ("UpdateExpression", "ConditionExpression", "FilterExpression",
                "ProjectionExpression", "KeyConditionExpression")
_SYNTAX = {"SET", "REMOVE", "ADD", "DELETE", "AND", "OR", "NOT", "BETWEEN", "IN"}


class StrictTable(FakeTable):
    """FakeTable that also rejects any bare attribute name in any expression.

    FakeTable only knows a subset of DynamoDB's ~570 reserved words, so it
    can't catch every bad name; this rule (always use #aliases) catches all.
    """

    def _strict(self, kwargs):
        for key in _EXPRESSIONS:
            expr = kwargs.get(key)
            if not expr:
                continue
            toks = _tokens(expr)
            for i, t in enumerate(toks):
                if t[0] in "#:" or not (t[0].isalpha() or t[0] == "_") or t.upper() in _SYNTAX:
                    continue
                if i + 1 < len(toks) and toks[i + 1] == "(":
                    continue  # function call
                raise AssertionError(f"bare attribute name {t!r} in {key}: {expr!r}; use a #alias")

    def put_item(self, **kw):
        self._strict(kw); return super().put_item(**kw)

    def get_item(self, **kw):
        self._strict(kw); return super().get_item(**kw)

    def update_item(self, **kw):
        self._strict(kw); return super().update_item(**kw)

    def scan(self, **kw):
        self._strict(kw); return super().scan(**kw)


class FeedTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_700_000_000
        self.lib = StoryLibrary(StrictTable(), clock=lambda: self.now)

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
        # prod: hide raised ValidationException (bare reserved word `hidden`)
        self.lib.publish("keep", "Keep", "...", "ann")
        self.lib.publish("gone", "Gone", "...", "ann")
        self.lib.hide("gone", by="ann")
        self.assertEqual([s["slug"] for s in self.lib.feed()], ["keep"])
        item = self.lib.get("gone")
        self.assertIs(item["hidden"], True)
        self.assertEqual((item["hidden_by"], item["hidden_at"]), ("ann", self.now))

    def test_feed_excludes_story_hidden_outside_the_library(self):
        # staging: hidden set by hand (AWS CLI) still showed, because the bare
        # `hidden` in the ProjectionExpression was silently dropped from items
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.table.update_item(
            Key={"slug": "hello"}, UpdateExpression="SET #h = :t",
            ExpressionAttributeNames={"#h": "hidden"}, ExpressionAttributeValues={":t": True},
        )
        self.assertEqual(self.lib.feed(), [])

    def test_hide_unknown_slug_is_rejected(self):
        with self.assertRaises(ClientError) as cm:
            self.lib.hide("nope", by="ann")
        self.assertEqual(cm.exception.response["Error"]["Code"], "ConditionalCheckFailedException")
        self.assertIsNone(self.lib.get("nope"))

    def test_archive(self):
        # archive's ConditionExpression used bare reserved word `status`
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.archive("hello")
        self.assertEqual(self.lib.get("hello")["archived_at"], self.now)


if __name__ == "__main__":
    unittest.main()
