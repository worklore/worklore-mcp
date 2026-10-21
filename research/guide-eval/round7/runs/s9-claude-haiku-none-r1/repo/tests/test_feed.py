import ast
import os
import re
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
        # Regression: `hidden` is a DynamoDB reserved word; hide() used to 500 on it.
        self.lib.publish("old", "Old", "...", "ann")
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.hide("hello", by="ann")
        self.assertEqual([s["slug"] for s in self.lib.feed()], ["old"])
        self.assertTrue(self.lib.get("hello")["hidden"])
        self.assertEqual(self.lib.get("hello")["hidden_by"], "ann")

    def test_story_hidden_outside_the_library_leaves_feed(self):
        # Regression: feed() projected `hidden` bare, which DynamoDB (and the fake)
        # silently drops, so a story hidden with the AWS CLI stayed in the feed.
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.table.update_item(
            Key={"slug": "hello"},
            UpdateExpression="SET #h = :t",
            ExpressionAttributeNames={"#h": "hidden"},
            ExpressionAttributeValues={":t": True},
        )
        self.assertEqual(self.lib.feed(), [])

    def test_every_expression_name_is_aliased(self):
        # Guard against the bug coming back: fake_dynamo only knows a subset of
        # DynamoDB's reserved words, so check the rule itself in the source.
        # Each attribute name in an *Expression string must be a #alias.
        # Allowed bare tokens: :values, keywords, operators, and function names.
        allowed = {"SET", "REMOVE", "AND", "OR", "NOT", "attribute_exists", "attribute_not_exists"}
        path = os.path.join(ROOT, "src", "app.py")
        with open(path) as f:
            tree = ast.parse(f.read())
        bare = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.keyword) or not node.arg.endswith("Expression"):
                continue
            if not (isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
                continue
            for tok in re.findall(r"#?[A-Za-z_][A-Za-z0-9_]*|:[A-Za-z_][A-Za-z0-9_]*", node.value.value):
                if tok.startswith(("#", ":")) or tok in allowed:
                    continue
                bare.append((node.lineno, tok))
        self.assertEqual(bare, [], "attribute names must be written as #aliases in expressions")

    def test_archive_sets_archived_at(self):
        # Regression: `status` is reserved too; the condition used to be rejected.
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.archive("hello")
        self.assertEqual(self.lib.get("hello")["archived_at"], self.now)


if __name__ == "__main__":
    unittest.main()
