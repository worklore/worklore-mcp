import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.app import StoryLibrary  # noqa: E402
from tests.fake_dynamo import _KEYWORDS, ClientError, FakeTable, _tokens  # noqa: E402


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

    # --- hide: tested with the flag actually set, not just absent ---

    def test_hide_removes_story_from_feed(self):
        self.lib.publish("keep", "Keep", "...", "ann")
        self.lib.publish("why-i-left-mobx", "Why I left MobX", "...", "vk")
        self.lib.hide("why-i-left-mobx", by="vk")
        story = self.lib.get("why-i-left-mobx")
        self.assertIs(story["hidden"], True)
        self.assertEqual(story["hidden_by"], "vk")
        self.assertEqual(story["hidden_at"], self.now)
        self.assertEqual([s["slug"] for s in self.lib.feed()], ["keep"])

    def test_story_hidden_outside_the_library_leaves_feed(self):
        # Staging bug report: hidden set by hand with the AWS CLI.
        self.lib.publish("my-first-week", "My first week", "...", "dasha")
        self.lib.table.update_item(
            Key={"slug": "my-first-week"},
            UpdateExpression="SET #h = :t",
            ExpressionAttributeNames={"#h": "hidden"},
            ExpressionAttributeValues={":t": True},
        )
        self.assertEqual(self.lib.feed(), [])

    def test_hide_unknown_slug_is_rejected(self):
        with self.assertRaises(ClientError) as cm:
            self.lib.hide("nope", by="vk")
        self.assertEqual(cm.exception.response["Error"]["Code"], "ConditionalCheckFailedException")

    def test_archive_published_story(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.archive("hello")
        self.assertEqual(self.lib.get("hello")["archived_at"], self.now)

    def test_archive_unknown_slug_is_rejected(self):
        with self.assertRaises(ClientError) as cm:
            self.lib.archive("nope")
        self.assertEqual(cm.exception.response["Error"]["Code"], "ConditionalCheckFailedException")

    def test_feed_follows_scan_pages(self):
        lib = StoryLibrary(_PagedTable(page_size=2), clock=lambda: self.now)
        for n in range(5):
            self.now += 1
            lib.publish(f"s{n}", f"S{n}", "...", "ann")
        lib.hide("s3", by="ann")
        self.assertEqual([s["slug"] for s in lib.feed()], ["s4", "s2", "s1", "s0"])


class _PagedTable(FakeTable):
    """FakeTable whose scan returns pages, like DynamoDB's 1 MB limit does."""

    def __init__(self, page_size):
        super().__init__()
        self.page_size = page_size

    def scan(self, ExclusiveStartKey=None, **kwargs):
        resp = super().scan(**kwargs)
        start = 0 if ExclusiveStartKey is None else int(ExclusiveStartKey["slug"])
        end = start + self.page_size
        resp["Items"] = resp["Items"][start:end]
        if end < resp["Count"]:
            resp["LastEvaluatedKey"] = {"slug": str(end)}
        return resp


class _RecordingTable(FakeTable):
    def __init__(self):
        super().__init__()
        self.calls = []

    def _record(self, op, kwargs):
        self.calls.append((op, kwargs))

    def put_item(self, **kw):
        self._record("put_item", kw); return super().put_item(**kw)

    def get_item(self, **kw):
        self._record("get_item", kw); return super().get_item(**kw)

    def update_item(self, **kw):
        self._record("update_item", kw); return super().update_item(**kw)

    def scan(self, **kw):
        self._record("scan", kw); return super().scan(**kw)


class NoBareAttributeNamesTests(unittest.TestCase):
    """Every attribute name in every expression must be a #alias.

    Guards against the whole class of reserved-word bugs (DynamoDB has ~570
    of them), including the silent one: a bare reserved word in a
    ProjectionExpression just drops the field, no error.
    """

    EXPRESSIONS = ("UpdateExpression", "ConditionExpression", "FilterExpression",
                   "KeyConditionExpression", "ProjectionExpression")

    def test_every_library_call_aliases_attribute_names(self):
        table = _RecordingTable()
        lib = StoryLibrary(table, clock=lambda: 1_700_000_000)
        lib.publish("a", "A", "...", "ann")
        lib.rename("a", "A2")
        lib.hide("a", by="ann")
        lib.publish("b", "B", "...", "ann")
        lib.archive("b")
        lib.feed()
        lib.get("a")
        ops = {op for op, _ in table.calls}
        self.assertEqual(ops, {"put_item", "update_item", "scan", "get_item"})
        for op, kw in table.calls:
            for name in self.EXPRESSIONS:
                expr = kw.get(name)
                if not expr:
                    continue
                toks = _tokens(expr)
                for i, t in enumerate(toks):
                    is_call = i + 1 < len(toks) and toks[i + 1] == "("
                    if t[0] in "#:" or not t[0].isalpha() or t.upper() in _KEYWORDS or is_call:
                        continue
                    self.fail(f"{op} {name} uses bare attribute name {t!r}: {expr!r}")


if __name__ == "__main__":
    unittest.main()
