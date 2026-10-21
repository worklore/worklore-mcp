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

    def test_hide_removes_from_feed(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.publish("other", "Other", "...", "bob")
        self.lib.hide("hello", by="ann")
        self.assertEqual([s["slug"] for s in self.lib.feed()], ["other"])
        self.assertTrue(self.lib.get("hello")["hidden"])

    def test_hand_hidden_story_stays_out_of_feed(self):
        # what the AWS CLI write in the staging report produces
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.table.update_item(
            Key={"slug": "hello"}, UpdateExpression="SET #h = :t",
            ExpressionAttributeNames={"#h": "hidden"}, ExpressionAttributeValues={":t": True})
        self.assertEqual(self.lib.feed(), [])

    def test_hide_unknown_slug_fails(self):
        with self.assertRaises(ClientError) as cm:
            self.lib.hide("nope", by="ann")
        self.assertEqual(cm.exception.response["Error"]["Code"], "ConditionalCheckFailedException")

    def test_archive(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.archive("hello")
        self.assertEqual(self.lib.get("hello")["archived_at"], self.now)

    def test_no_bare_reserved_words_in_any_expression(self):
        """Guard: every expression the library sends must alias reserved words."""
        from tests.fake_dynamo import RESERVED, _tokens
        seen = []

        class Spy(FakeTable):
            def _spy(self, kw):
                for k in ("UpdateExpression", "ConditionExpression", "FilterExpression", "ProjectionExpression"):
                    if kw.get(k):
                        seen.append(kw[k])
            def update_item(self, **kw): self._spy(kw); return super().update_item(**kw)
            def scan(self, **kw): self._spy(kw); return super().scan(**kw)
            def put_item(self, **kw): self._spy(kw); return super().put_item(**kw)

        lib = StoryLibrary(Spy(), clock=lambda: 1)
        lib.publish("a", "A", "b", "x"); lib.rename("a", "B"); lib.hide("a", by="x")
        lib.archive("a"); lib.feed()
        for expr in seen:
            toks = _tokens(expr)
            for i, t in enumerate(toks):
                if t.upper() in RESERVED and not (i + 1 < len(toks) and toks[i + 1] == "(") \
                        and t.upper() not in {"SET", "AND", "OR", "NOT"}:
                    self.fail(f"bare reserved word {t!r} in {expr!r}")


if __name__ == "__main__":
    unittest.main()
