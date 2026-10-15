import unittest

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

    def test_word_count_is_int(self):
        out = tools.list_notes(self.store)
        self.assertIsInstance(out["notes"][0]["word_count"], int)


if __name__ == "__main__":
    unittest.main()
