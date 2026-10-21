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


class AliasOnlyTable(FakeTable):
    """FakeTable that also rejects any bare attribute name in any expression.

    FakeTable only knows a subset of DynamoDB's reserved words, so it would
    let a new bare name through that the real service rejects (or silently
    drops from a projection). The convention in src/app.py is: alias always.
    """

    def _guard(self, kwargs):
        for key in _EXPRESSIONS:
            toks = _tokens(kwargs.get(key) or "")
            for i, t in enumerate(toks):
                if t[0] in "#:" or not (t[0].isalpha() or t[0] == "_") or t.upper() in _SYNTAX:
                    continue
                if i + 1 < len(toks) and toks[i + 1] == "(":
                    continue  # function name
                raise AssertionError(f"bare attribute name {t!r} in {key}: {kwargs[key]!r}")

    def put_item(self, **kw):
        self._guard(kw); return super().put_item(**kw)

    def get_item(self, **kw):
        self._guard(kw); return super().get_item(**kw)

    def update_item(self, **kw):
        self._guard(kw); return super().update_item(**kw)

    def scan(self, **kw):
        self._guard(kw); return super().scan(**kw)


class PagedTable(AliasOnlyTable):
    """Returns scan results one item per page, like a table bigger than 1 MB."""

    def scan(self, ExclusiveStartKey=None, **kw):
        items = super().scan(**kw)["Items"]
        start = 0 if ExclusiveStartKey is None else ExclusiveStartKey["n"]
        resp = {"Items": items[start:start + 1]}
        if start + 1 < len(items):
            resp["LastEvaluatedKey"] = {"n": start + 1}
        return resp


class FeedTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_700_000_000
        self.lib = StoryLibrary(AliasOnlyTable(), clock=lambda: self.now)

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

    def test_hidden_story_leaves_the_feed(self):
        self.lib.publish("keep", "Keep", "...", "ann")
        self.lib.publish("why-i-left-mobx", "Why I left MobX", "...", "vk")
        self.lib.hide("why-i-left-mobx", by="vk")
        self.assertEqual([s["slug"] for s in self.lib.feed()], ["keep"])
        story = self.lib.get("why-i-left-mobx")
        self.assertIs(story["hidden"], True)
        self.assertEqual(story["hidden_by"], "vk")
        self.assertEqual(story["hidden_at"], self.now)

    def test_story_hidden_outside_the_app_leaves_the_feed(self):
        # The staging bug: `hidden` set by hand (AWS CLI), feed still listed it.
        self.lib.publish("my-first-week", "My first week", "...", "dasha")
        self.lib.table.update_item(
            Key={"slug": "my-first-week"}, UpdateExpression="SET #h = :t",
            ExpressionAttributeNames={"#h": "hidden"}, ExpressionAttributeValues={":t": True})
        self.assertEqual(self.lib.feed(), [])

    def test_hide_unknown_story_is_rejected(self):
        with self.assertRaises(ClientError) as cm:
            self.lib.hide("nope", by="vk")
        self.assertEqual(cm.exception.response["Error"]["Code"], "ConditionalCheckFailedException")

    def test_archive_published_story(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.archive("hello")
        self.assertEqual(self.lib.get("hello")["archived_at"], self.now)

    def test_feed_reads_every_scan_page(self):
        lib = StoryLibrary(PagedTable(), clock=lambda: self.now)
        for n, slug in enumerate(["a", "b", "c"]):
            self.now = 1_700_000_000 + n
            lib.publish(slug, slug.upper(), "...", "ann")
        lib.hide("b", by="ann")
        self.assertEqual([s["slug"] for s in lib.feed()], ["c", "a"])


if __name__ == "__main__":
    unittest.main()
