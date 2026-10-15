"""Exercise the JSON-RPC boundary using contracts published to a client."""

import json
import unittest

import db
import server


def assert_matches_schema(test, value, schema, path="result"):
    """Check the JSON Schema subset used by this server, including nested values."""
    kind = schema["type"]
    if kind == "object":
        test.assertIsInstance(value, dict, path)
        for key in schema.get("required", []):
            test.assertIn(key, value, path)
        for key, child_schema in schema.get("properties", {}).items():
            if key in value:
                assert_matches_schema(test, value[key], child_schema, f"{path}.{key}")
        if schema.get("additionalProperties") is False:
            test.assertFalse(value.keys() - schema.get("properties", {}).keys(), path)
    elif kind == "array":
        test.assertIsInstance(value, list, path)
        for index, item in enumerate(value):
            assert_matches_schema(test, item, schema["items"], f"{path}[{index}]")
    elif kind == "string":
        test.assertIsInstance(value, str, path)
    elif kind == "integer":
        test.assertIs(type(value), int, path)  # bool is not a JSON integer
    elif kind == "number":
        test.assertIn(type(value), (int, float), path)
    else:
        test.fail(f"unsupported published schema type {kind!r} at {path}")


class McpContractTest(unittest.TestCase):
    def setUp(self):
        self.old_store = server._store
        server._store = db.FakeStore()
        self.addCleanup(setattr, server, "_store", self.old_store)

    def request(self, method, request_id, params=None):
        request = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            request["params"] = params
        response_json = server.handle(json.dumps(request))
        response = json.loads(response_json)
        json.dumps(response, allow_nan=False)  # the entire result must be JSON-safe
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], request_id)
        self.assertNotIn("error", response)
        return response["result"]

    def test_client_sequence_and_published_output_contracts(self):
        initialized = self.request("initialize", 1, {
            "protocolVersion": server.PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "contract-test", "version": "1"},
        })
        self.assertEqual(initialized["protocolVersion"], server.PROTOCOL_VERSION)
        self.assertIn("tools", initialized["capabilities"])

        # No credentials: a client must be able to discover the tool contracts.
        published = self.request("tools/list", 2)["tools"]
        arguments = {"get_note": {"note_id": "n1"}, "list_notes": {}}
        self.assertEqual({tool["name"] for tool in published}, set(arguments))

        for request_id, tool in enumerate(published, start=3):
            name = tool["name"]
            with self.subTest(tool=name):
                result = self.request("tools/call", request_id, {
                    "name": name, "arguments": arguments[name],
                })
                self.assertFalse(result.get("isError"), result)
                self.assertIn("structuredContent", result)
                self.assertIn("outputSchema", tool)
                assert_matches_schema(self, result["structuredContent"], tool["outputSchema"])
                self.assertEqual(json.loads(result["content"][0]["text"]),
                                 result["structuredContent"])


if __name__ == "__main__":
    unittest.main()
