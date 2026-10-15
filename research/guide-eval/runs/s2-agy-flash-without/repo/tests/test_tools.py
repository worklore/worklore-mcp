import json
import os
import unittest
from decimal import Decimal

import db
import tools


class GetNoteTest(unittest.TestCase):
    def setUp(self):
        self.store = db.FakeStore()

    def test_returns_note(self):
        note = tools.get_note(self.store, "n1")
        self.assertEqual(note["title"], "Ship the importer")
        self.assertEqual(note["word_count"], 412)
        self.assertEqual(note["stats"]["views"], 37)

    def test_missing_note_raises(self):
        with self.assertRaises(KeyError):
            tools.get_note(self.store, "nope")


class GetNoteDynamoStoreTest(unittest.TestCase):
    """Test DynamoStore behavior where numbers are Decimals at any depth."""

    def setUp(self):
        self.store = db.DynamoStore()

    def test_returns_note_with_coerced_types(self):
        note = tools.get_note(self.store, "n1")
        self.assertEqual(note["title"], "Ship the importer")
        self.assertIsInstance(note["word_count"], int)
        self.assertEqual(note["word_count"], 412)
        self.assertIsInstance(note["stats"]["views"], int)
        self.assertEqual(note["stats"]["views"], 37)
        self.assertIsInstance(note["stats"]["rating"], float)
        self.assertEqual(note["stats"]["rating"], 4.5)
        self.assertIsInstance(note["stats"]["revisions"], list)
        for rev in note["stats"]["revisions"]:
            self.assertIsInstance(rev, int)
        self.assertEqual(note["stats"]["revisions"], [1, 2, 3])

    def test_note_is_json_serializable(self):
        note = tools.get_note(self.store, "n1")
        serialized = json.dumps(note)
        self.assertIn('"views": 37', serialized)
        self.assertIn('"rating": 4.5', serialized)

    def test_rating_float_preserved_for_integer_like_float(self):
        note = tools.get_note(self.store, "n2")
        self.assertIsInstance(note["stats"]["rating"], float)
        self.assertEqual(note["stats"]["rating"], 3.0)

    def test_missing_note_raises(self):
        with self.assertRaises(KeyError):
            tools.get_note(self.store, "nope")


class ListNotesTest(unittest.TestCase):
    def setUp(self):
        self.store = db.FakeStore()

    def test_lists_all(self):
        out = tools.list_notes(self.store)
        self.assertEqual(out["count"], 2)
        self.assertEqual([n["id"] for n in out["notes"]], ["n1", "n2"])

    def test_filters_by_tag(self):
        out = tools.list_notes(self.store, tag="home")
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["notes"][0]["title"], "Groceries")

    def test_filters_by_nonexistent_tag(self):
        out = tools.list_notes(self.store, tag="nonexistent")
        self.assertEqual(out["count"], 0)
        self.assertEqual(out["notes"], [])

    def test_handles_note_with_none_tags(self):
        store = db.FakeStore(items={
            "n1": {"id": "n1", "title": "Note 1", "word_count": 100, "tags": None},
            "n2": {"id": "n2", "title": "Note 2", "word_count": 50, "tags": ["work"]},
        })
        out = tools.list_notes(store, tag="work")
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["notes"][0]["id"], "n2")

    def test_word_count_is_int(self):
        out = tools.list_notes(self.store)
        self.assertIsInstance(out["notes"][0]["word_count"], int)


class ListNotesDynamoStoreTest(unittest.TestCase):
    def setUp(self):
        self.store = db.DynamoStore()

    def test_dynamo_store_notes_are_json_serializable(self):
        out = tools.list_notes(self.store)
        self.assertEqual(out["count"], 2)
        serialized = json.dumps(out)
        self.assertIn('"count": 2', serialized)
        self.assertIsInstance(out["notes"][0]["word_count"], int)


class GetStoreTest(unittest.TestCase):
    def setUp(self):
        self._orig_prod_db = os.environ.get("PRODUCTION_DB")

    def tearDown(self):
        if self._orig_prod_db is None:
            os.environ.pop("PRODUCTION_DB", None)
        else:
            os.environ["PRODUCTION_DB"] = self._orig_prod_db

    def test_returns_fake_store_by_default(self):
        os.environ.pop("PRODUCTION_DB", None)
        self.assertIsInstance(db.get_store(), db.FakeStore)

    def test_returns_dynamo_store_when_production(self):
        os.environ["PRODUCTION_DB"] = "1"
        self.assertIsInstance(db.get_store(), db.DynamoStore)


if __name__ == "__main__":
    unittest.main()

