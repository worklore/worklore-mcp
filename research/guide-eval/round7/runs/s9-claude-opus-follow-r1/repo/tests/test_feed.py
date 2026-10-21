import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.app import StoryLibrary  # noqa: E402
from tests.fake_dynamo import _KEYWORDS, _OPERATORS, ClientError, FakeTable, _tokens  # noqa: E402

_EXPRESSIONS = ("UpdateExpression", "ConditionExpression", "FilterExpression",
                "ProjectionExpression", "KeyConditionExpression")


class AliasOnlyTable(FakeTable):
    """FakeTable that also rejects ANY bare attribute name in any expression,
    reserved today or not. Projections never raise on the real service's
    reserved words, they just drop the field, so this is the only thing that
    catches a bare name there."""

    def _guard(self, kwargs):
        for kind in _EXPRESSIONS:
            toks = _tokens(kwargs.get(kind) or "")
            for i, t in enumerate(toks):
                if t.startswith(("#", ":")) or t in _OPERATORS or t.upper() in _KEYWORDS:
                    continue
                if i + 1 < len(toks) and toks[i + 1] == "(":
                    continue  # function name
                raise AssertionError(f"bare attribute name {t!r} in {kind}: {kwargs[kind]!r}")

    def put_item(self, **kw):
        self._guard(kw); return super().put_item(**kw)

    def get_item(self, **kw):
        self._guard(kw); return super().get_item(**kw)

    def update_item(self, **kw):
        self._guard(kw); return super().update_item(**kw)

    def scan(self, **kw):
        self._guard(kw); return super().scan(**kw)


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

    def test_hide_removes_story_from_feed(self):
        self.lib.publish("keep", "Keep", "...", "ann")
        self.lib.publish("gone", "Gone", "...", "ann")
        self.lib.hide("gone", by="ann")
        stored = self.lib.get("gone")
        self.assertIs(stored["hidden"], True)
        self.assertEqual(stored["hidden_by"], "ann")
        self.assertEqual([s["slug"] for s in self.lib.feed()], ["keep"])

    def test_hand_hidden_story_is_not_in_feed(self):
        # The staging case: the flag was written outside hide().
        self.lib.publish("my-first-week", "My first week", "...", "dasha")
        self.lib.table.update_item(
            Key={"slug": "my-first-week"}, UpdateExpression="SET #h = :t",
            ExpressionAttributeNames={"#h": "hidden"}, ExpressionAttributeValues={":t": True},
        )
        self.assertEqual(self.lib.feed(), [])

    def test_hide_unknown_slug_is_rejected(self):
        with self.assertRaises(ClientError) as cm:
            self.lib.hide("nope", by="ann")
        self.assertEqual(cm.exception.response["Error"]["Code"], "ConditionalCheckFailedException")

    def test_archive_published_story(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.archive("hello")
        self.assertEqual(self.lib.get("hello")["archived_at"], self.now)

    def test_feed_follows_scan_pages(self):
        pages = [{"Items": [{"slug": "a", "title": "A", "published_at": 1}], "LastEvaluatedKey": {"slug": "a"}},
                 {"Items": [{"slug": "b", "title": "B", "published_at": 2, "hidden": True},
                            {"slug": "c", "title": "C", "published_at": 3}]}]
        calls = []

        class Paged:
            def scan(self, **kw):
                calls.append(kw.get("ExclusiveStartKey"))
                return pages[len(calls) - 1]

        self.assertEqual([s["slug"] for s in StoryLibrary(Paged()).feed()], ["c", "a"])
        self.assertEqual(calls, [None, {"slug": "a"}])


class FakeTableReservedWordTests(unittest.TestCase):
    """Pins the two failure modes the fake mirrors, so the tests above mean something."""

    def setUp(self):
        self.table = FakeTable()
        self.table.put_item(Item={"slug": "s", "hidden": True})

    def test_bare_reserved_word_in_update_raises(self):
        with self.assertRaises(ClientError) as cm:
            self.table.update_item(Key={"slug": "s"}, UpdateExpression="SET hidden = :h",
                                   ExpressionAttributeValues={":h": True})
        self.assertIn("reserved keyword: hidden", str(cm.exception))

    def test_bare_reserved_word_in_projection_silently_drops_field(self):
        item = self.table.scan(ProjectionExpression="slug, hidden")["Items"][0]
        self.assertEqual(item, {"slug": "s"})


if __name__ == "__main__":
    unittest.main()
