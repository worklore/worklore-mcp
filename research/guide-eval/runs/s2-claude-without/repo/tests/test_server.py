"""End-to-end tests through server.handle(), exercised the way an MCP client does:
raw JSON in, raw JSON out, against both the fake and the production (Dynamo) store."""
import json
import unittest

import db
import server


def validate(instance, schema, path="$"):
    """Minimal JSON Schema check for the subset our output schemas use. Validates the
    value as a client would see it, i.e. after a JSON round-trip."""
    t = schema.get("type")
    if t == "object":
        assert isinstance(instance, dict), f"{path}: expected object, got {instance!r}"
        for key in schema.get("required", []):
            assert key in instance, f"{path}: missing required {key!r}"
        for key, sub in schema.get("properties", {}).items():
            if key in instance:
                validate(instance[key], sub, f"{path}.{key}")
    elif t == "array":
        assert isinstance(instance, list), f"{path}: expected array, got {instance!r}"
        for i, item in enumerate(instance):
            validate(item, schema.get("items", {}), f"{path}[{i}]")
    elif t == "string":
        assert isinstance(instance, str), f"{path}: expected string, got {instance!r}"
    elif t == "integer":
        assert isinstance(instance, int) and not isinstance(instance, bool), \
            f"{path}: expected integer, got {instance!r}"
    elif t == "number":
        assert isinstance(instance, (int, float)) and not isinstance(instance, bool), \
            f"{path}: expected number, got {instance!r}"


class _ServerTests:
    """Mixin; concrete subclasses pick the store."""

    store_cls = None

    def setUp(self):
        server._store = self.store_cls()
        self._next_id = 0

    def tearDown(self):
        server._store = None

    def rpc(self, method, params=None):
        self._next_id += 1
        req = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        if params is not None:
            req["params"] = params
        raw = server.handle(json.dumps(req))
        resp = json.loads(raw)
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertEqual(resp["id"], self._next_id)
        return resp

    def call(self, name, arguments=None):
        params = {"name": name}
        if arguments is not None:
            params["arguments"] = arguments
        return self.rpc("tools/call", params)

    def tool_schema(self, name):
        return next(t for t in server.TOOLS if t["name"] == name)["outputSchema"]

    def assert_tool_ok(self, resp, name):
        self.assertNotIn("error", resp)
        result = resp["result"]
        self.assertFalse(result.get("isError", False), result["content"])
        structured = result["structuredContent"]
        validate(structured, self.tool_schema(name))
        # Spec: structured results should also be returned as serialized JSON text.
        self.assertEqual(json.loads(result["content"][0]["text"]), structured)
        return structured

    # --- lifecycle -------------------------------------------------------

    def test_handshake(self):
        resp = self.rpc("initialize", {
            "protocolVersion": server.PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "0"},
        })
        self.assertEqual(resp["result"]["protocolVersion"], server.PROTOCOL_VERSION)
        self.assertIn("tools", resp["result"]["capabilities"])
        # Every client sends this right after initialize; it must not be answered.
        self.assertEqual(server.handle(json.dumps(
            {"jsonrpc": "2.0", "method": "notifications/initialized"})), "")

    def test_unknown_notification_gets_no_reply(self):
        self.assertEqual(server.handle(json.dumps(
            {"jsonrpc": "2.0", "method": "notifications/cancelled",
             "params": {"requestId": 1}})), "")

    def test_ping(self):
        self.assertEqual(self.rpc("ping")["result"], {})

    def test_tools_list_without_params(self):
        tools = self.rpc("tools/list")["result"]["tools"]
        self.assertEqual({t["name"] for t in tools}, {"get_note", "list_notes"})
        for t in tools:
            self.assertEqual(t["inputSchema"]["type"], "object")
            self.assertEqual(t["outputSchema"]["type"], "object")

    # --- tool results match their declared outputSchema --------------------

    def test_get_note_matches_output_schema(self):
        for note_id in db.SEED:
            with self.subTest(note_id=note_id):
                note = self.assert_tool_ok(self.call("get_note", {"note_id": note_id}), "get_note")
                self.assertEqual(note["stats"]["views"], db.SEED[note_id]["stats"]["views"])
                self.assertEqual(note["stats"]["rating"], db.SEED[note_id]["stats"]["rating"])
                self.assertEqual(note["stats"]["revisions"], db.SEED[note_id]["stats"]["revisions"])

    def test_list_notes_matches_output_schema(self):
        for args in (None, {}, {"tag": "home"}, {"tag": "nope"}):
            with self.subTest(args=args):
                out = self.assert_tool_ok(self.call("list_notes", args), "list_notes")
                self.assertEqual(out["count"], len(out["notes"]))

    def test_list_notes_null_tag(self):
        out = self.assert_tool_ok(self.call("list_notes", {"tag": None}), "list_notes")
        self.assertEqual(out["count"], 2)

    # --- errors ------------------------------------------------------------

    def test_missing_note_is_tool_error(self):
        result = self.call("get_note", {"note_id": "nope"})["result"]
        self.assertTrue(result["isError"])
        self.assertEqual(result["content"][0]["text"], "no note 'nope'")

    def test_unknown_tool_is_invalid_params(self):
        self.assertEqual(self.call("nope", {})["error"]["code"], -32602)

    def test_bad_arguments_are_invalid_params(self):
        for args in ({}, {"note_id": 1}, [], "n1"):
            with self.subTest(args=args):
                self.assertEqual(self.call("get_note", args)["error"]["code"], -32602)
        self.assertEqual(self.call("list_notes", {"tag": 5})["error"]["code"], -32602)

    def test_null_params_and_arguments(self):
        self.assertIn("result", self.rpc("tools/list", None))
        resp = server.handle(json.dumps(
            {"jsonrpc": "2.0", "id": "a", "method": "tools/call",
             "params": {"name": "list_notes", "arguments": None}}))
        self.assert_tool_ok(json.loads(resp), "list_notes")

    def test_unknown_method(self):
        self.assertEqual(self.rpc("resources/list")["error"]["code"], -32601)

    def test_string_id_echoed(self):
        resp = json.loads(server.handle(json.dumps(
            {"jsonrpc": "2.0", "id": "abc-1", "method": "ping"})))
        self.assertEqual(resp["id"], "abc-1")

    def test_parse_error(self):
        resp = json.loads(server.handle("{not json"))
        self.assertEqual(resp["error"]["code"], -32700)
        self.assertIsNone(resp["id"])

    def test_invalid_requests(self):
        for body in ("[]", "42", '"x"', "null",
                     json.dumps({"jsonrpc": "2.0", "id": 1}),
                     json.dumps({"id": 1, "method": "ping"}),
                     json.dumps({"jsonrpc": "2.0", "id": 1, "method": 5})):
            with self.subTest(body=body):
                self.assertEqual(json.loads(server.handle(body))["error"]["code"], -32600)

    def test_non_object_params(self):
        self.assertEqual(self.rpc("tools/call", ["get_note"])["error"]["code"], -32602)


class FakeStoreServerTest(_ServerTests, unittest.TestCase):
    store_cls = db.FakeStore


class DynamoStoreServerTest(_ServerTests, unittest.TestCase):
    """Production store: every number comes back as Decimal, at any depth."""
    store_cls = db.DynamoStore


if __name__ == "__main__":
    unittest.main()
