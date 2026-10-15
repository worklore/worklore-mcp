"""Talk to the server the way an MCP client does.

initialize -> notifications/initialized -> tools/list (no credentials) -> tools/call
for every tool, all through server.handle() with raw JSON strings, validating each
result against the outputSchema the server *published*, not the one in server.py.
"""
import json
import unittest

import db
import server

# One set of valid arguments per tool. A tool missing here fails the suite.
HAPPY_ARGS = {
    "get_note": [{"note_id": "n1"}, {"note_id": "n2"}],
    "list_notes": [{}, {"tag": "home"}],
}

_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def schema_errors(value, schema, path="$"):
    """Validate the JSON Schema subset this server emits. Returns a list of errors."""
    errors = []
    expected = schema.get("type")
    if expected is not None:
        types = expected if isinstance(expected, list) else [expected]
        if not any(_TYPES[t](value) for t in types):
            return [f"{path}: expected {expected}, got {type(value).__name__} {value!r}"]
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required field {key!r}")
        props = schema.get("properties", {})
        for key, sub in props.items():
            if key in value:
                errors.extend(schema_errors(value[key], sub, f"{path}.{key}"))
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errors.append(f"{path}: undeclared field {key!r}")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errors.extend(schema_errors(item, schema["items"], f"{path}[{i}]"))
    return errors


class Client:
    """Minimal in-process MCP client over server.handle()."""

    def __init__(self):
        self._next_id = 0

    def request(self, method, params=None):
        self._next_id += 1
        msg = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        if params is not None:
            msg["params"] = params
        raw = server.handle(json.dumps(msg))
        assert isinstance(raw, str), f"{method}: handle() returned {type(raw).__name__}"
        resp = json.loads(raw)
        assert resp.get("jsonrpc") == "2.0", resp
        assert resp.get("id") == self._next_id, resp
        return resp

    def notify(self, method, params=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        return server.handle(json.dumps(msg))


class ConformanceMixin:
    """The client-path harness; run once per store implementation."""

    store_factory = None

    def setUp(self):
        server._store = self.store_factory()
        self.addCleanup(setattr, server, "_store", None)
        self.client = Client()

    def _handshake(self):
        resp = self.client.request("initialize", {
            "protocolVersion": server.PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "conformance-test", "version": "0"},
        })
        self.assertNotIn("error", resp)
        self.assertIn("tools", resp["result"]["capabilities"])
        self.assertIsNone(self.client.notify("notifications/initialized"),
                          "notifications must not get a response")
        resp = self.client.request("tools/list")
        self.assertNotIn("error", resp, "tools/list must answer without credentials")
        return {t["name"]: t for t in resp["result"]["tools"]}

    def test_every_tool_conforms_to_published_schema(self):
        published = self._handshake()
        self.assertEqual(set(published), set(HAPPY_ARGS),
                         "every published tool needs happy-path args in HAPPY_ARGS")
        for name, tool in published.items():
            self.assertEqual(tool["inputSchema"].get("type"), "object", name)
            for args in HAPPY_ARGS[name]:
                with self.subTest(tool=name, args=args):
                    self.assertEqual(schema_errors(args, tool["inputSchema"]), [])
                    resp = self.client.request("tools/call", {"name": name, "arguments": args})
                    self.assertNotIn("error", resp)
                    result = resp["result"]
                    # Check isError first: an error result has no structuredContent,
                    # so a schema check over it would pass vacuously.
                    self.assertFalse(result.get("isError"),
                                     f"happy-path call failed: {result.get('content')}")
                    if "outputSchema" in tool:
                        self.assertIn("structuredContent", result,
                                      "declares outputSchema but returned no structuredContent")
                        self.assertEqual(
                            schema_errors(result["structuredContent"], tool["outputSchema"]), [])
                        # Spec: structured tools SHOULD also return the serialized JSON as text.
                        texts = [c["text"] for c in result["content"] if c["type"] == "text"]
                        self.assertIn(result["structuredContent"],
                                      [json.loads(t) for t in texts])

    def test_error_paths_are_reported_not_raised(self):
        self._handshake()
        resp = self.client.request("tools/call",
                                   {"name": "get_note", "arguments": {"note_id": "nope"}})
        self.assertTrue(resp["result"]["isError"])
        resp = self.client.request("tools/call", {"name": "no_such_tool", "arguments": {}})
        self.assertTrue("error" in resp or resp["result"].get("isError"))
        resp = self.client.request("no/such/method")
        self.assertEqual(resp["error"]["code"], -32601)

    def test_ping(self):
        self.assertEqual(self.client.request("ping")["result"], {})

    def test_malformed_json_gets_parse_error(self):
        resp = json.loads(server.handle("{not json"))
        self.assertEqual(resp["error"]["code"], -32700)
        self.assertIsNone(resp["id"])


class FakeStoreConformanceTest(ConformanceMixin, unittest.TestCase):
    store_factory = db.FakeStore


class DynamoStoreConformanceTest(ConformanceMixin, unittest.TestCase):
    store_factory = db.DynamoStore


class FakeStoreFidelityTest(unittest.TestCase):
    """The fake must be no kinder than production: same types at every depth."""

    def test_fake_matches_dynamo_types(self):
        def shape(v):
            if isinstance(v, dict):
                return {k: shape(x) for k, x in v.items()}
            if isinstance(v, list):
                return [shape(x) for x in v]
            return type(v)

        fake, real = db.FakeStore(), db.DynamoStore()
        self.assertEqual(shape(fake.scan()), shape(real.scan()))
        self.assertEqual(shape(fake.get("n1")), shape(real.get("n1")))


if __name__ == "__main__":
    unittest.main()
