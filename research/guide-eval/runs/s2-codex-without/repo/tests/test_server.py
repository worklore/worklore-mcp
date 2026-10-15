import json
import unittest
from unittest.mock import patch

import db
import server


class ServerProtocolTest(unittest.TestCase):
    def setUp(self):
        # Exercise the same Decimal values the production store returns, while
        # keeping the server's cached store isolated between tests.
        self.store_patch = patch.object(server, "_store", db.DynamoStore())
        self.store_patch.start()
        self.addCleanup(self.store_patch.stop)

    def call(self, method, params=None, request_id=1):
        request = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            request["params"] = params
        response = json.loads(server.handle(json.dumps(request)))
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], request_id)
        return response

    def test_get_note_returns_nested_numbers_as_json_and_structured_content(self):
        result = self.call("tools/call", {
            "name": "get_note", "arguments": {"note_id": "n1"}
        })["result"]

        self.assertNotIn("isError", result)
        note = result["structuredContent"]
        self.assertEqual(json.loads(result["content"][0]["text"]), note)
        self.assertEqual(note["word_count"], 412)
        self.assertIs(type(note["word_count"]), int)
        self.assertEqual(note["stats"], {
            "views": 37, "rating": 4.5, "revisions": [1, 2, 3]
        })
        self.assertIs(type(note["stats"]["views"]), int)
        self.assertIs(type(note["stats"]["rating"]), float)
        self.assertTrue(all(type(n) is int for n in note["stats"]["revisions"]))

    def test_list_notes_returns_json_serializable_items(self):
        result = self.call("tools/call", {
            "name": "list_notes", "arguments": {"tag": "home"}
        }, request_id="list-1")["result"]

        self.assertNotIn("isError", result)
        self.assertEqual(result["structuredContent"], {
            "notes": [{"id": "n2", "title": "Groceries", "word_count": 18}],
            "count": 1,
        })
        self.assertEqual(json.loads(result["content"][0]["text"]),
                         result["structuredContent"])

    def test_missing_note_is_a_tool_error(self):
        result = self.call("tools/call", {
            "name": "get_note", "arguments": {"note_id": "missing"}
        })["result"]
        self.assertTrue(result["isError"])
        self.assertIn("missing", result["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
