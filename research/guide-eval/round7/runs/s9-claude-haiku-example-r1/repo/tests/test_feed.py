import ast
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.app import StoryLibrary  # noqa: E402
from tests.fake_dynamo import ClientError, FakeTable  # noqa: E402

# Words that may appear bare in an expression: operators, keywords and
# functions. Anything else bare is an attribute name and must be a #alias.
EXPRESSION_WORDS = {"AND", "OR", "NOT", "SET", "REMOVE", "ADD", "DELETE", "BETWEEN", "IN"}
EXPRESSION_KWARGS = ("UpdateExpression", "ConditionExpression", "ProjectionExpression",
                     "FilterExpression", "KeyConditionExpression")


def bare_attribute_names(expr):
    """Attribute names used without a #alias in one expression string."""
    names = []
    for m in re.finditer(r"(?<![#:\w])([A-Za-z_]\w*)\b(?!\s*\()", expr):
        if m.group(1).upper() not in EXPRESSION_WORDS:
            names.append(m.group(1))
    return names


class ExpressionAliasTests(unittest.TestCase):
    """DynamoDB's reserved-word list is long, and a bare reserved word in a
    ProjectionExpression fails silently. So every attribute name in every
    expression in src/app.py must be a #alias, reserved or not."""

    def test_every_expression_uses_aliases(self):
        with open(os.path.join(ROOT, "src", "app.py")) as f:
            tree = ast.parse(f.read())
        checked, offenders = 0, []
        for node in ast.walk(tree):
            if not isinstance(node, ast.keyword) or node.arg not in EXPRESSION_KWARGS:
                continue
            self.assertIsInstance(node.value, ast.Constant, "expressions must be string literals")
            checked += 1
            for name in bare_attribute_names(node.value.value):
                offenders.append(f"{node.arg}: {name!r} in {node.value.value!r}")
        self.assertGreaterEqual(checked, 8)  # guard against the scan finding nothing
        self.assertEqual(offenders, [])

    def test_guard_catches_bare_names(self):
        self.assertEqual(bare_attribute_names("SET hidden = :h"), ["hidden"])
        self.assertEqual(bare_attribute_names("attribute_exists(#slug) AND status = :s"), ["status"])
        self.assertEqual(bare_attribute_names("SET #hidden = :h, #by = :by"), [])


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

    def test_hide_then_feed_excludes_it(self):
        # The field must be set for the filter to mean anything: write it,
        # then check the feed really drops the story.
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.publish("other", "Other", "...", "bob")
        self.lib.hide("hello", by="ann")
        self.assertEqual([s["slug"] for s in self.lib.feed()], ["other"])

    def test_feed_excludes_story_with_hidden_flag_set_by_hand(self):
        # The same write the staging hand-fix did with the AWS CLI (aliased).
        self.lib.publish("my-first-week", "My first week", "...", "dasha")
        self.lib.table.update_item(
            Key={"slug": "my-first-week"},
            UpdateExpression="SET #h = :t",
            ExpressionAttributeNames={"#h": "hidden"},
            ExpressionAttributeValues={":t": True},
        )
        self.assertEqual(self.lib.get("my-first-week")["hidden"], True)
        self.assertEqual(self.lib.feed(), [])

    def test_hide_records_who_and_when(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.hide("hello", by="vk")
        item = self.lib.get("hello")
        self.assertEqual((item["hidden"], item["hidden_by"], item["hidden_at"]),
                         (True, "vk", self.now))

    def test_archive_sets_archived_at(self):
        self.lib.publish("hello", "Hello", "...", "ann")
        self.lib.archive("hello")
        self.assertEqual(self.lib.get("hello")["archived_at"], self.now)


if __name__ == "__main__":
    unittest.main()
