import json
import os
import unittest

import server


def validate_schema(data, schema):
    """Simple JSON schema validator supporting basic types used in server schemas."""
    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(data, dict):
            return False, f"Expected dict, got {type(data).__name__}"
        for req in schema.get("required", []):
            if req not in data:
                return False, f"Missing required property '{req}'"
        for prop, prop_schema in schema.get("properties", {}).items():
            if prop in data:
                ok, err = validate_schema(data[prop], prop_schema)
                if not ok:
                    return False, f"Property '{prop}': {err}"
        return True, ""
    elif schema_type == "array":
        if not isinstance(data, list):
            return False, f"Expected list, got {type(data).__name__}"
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(data):
                ok, err = validate_schema(item, item_schema)
                if not ok:
                    return False, f"Item {i}: {err}"
        return True, ""
    elif schema_type == "string":
        if not isinstance(data, str):
            return False, f"Expected str, got {type(data).__name__}"
        return True, ""
    elif schema_type == "integer":
        if not isinstance(data, int) or isinstance(data, bool):
            return False, f"Expected int, got {type(data).__name__}"
        return True, ""
    elif schema_type == "number":
        if not isinstance(data, (int, float)) or isinstance(data, bool):
            return False, f"Expected number, got {type(data).__name__}"
        return True, ""
    elif schema_type == "boolean":
        if not isinstance(data, bool):
            return False, f"Expected bool, got {type(data).__name__}"
        return True, ""
    return True, ""


class TestInitialize(unittest.TestCase):
    def test_initialize_standard_handshake(self):
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"},
            },
        }
        res_str = server.handle(json.dumps(req))
        res = json.loads(res_str)
        self.assertEqual(res["jsonrpc"], "2.0")
        self.assertEqual(res["id"], 1)
        result = res["result"]
        self.assertEqual(result["protocolVersion"], "2025-06-18")
        self.assertIn("tools", result["capabilities"])
        self.assertEqual(result["serverInfo"]["name"], "notes-mcp")
        self.assertEqual(result["serverInfo"]["version"], "0.3.1")

    def test_initialize_negotiates_supported_version(self):
        req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        }
        res = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(res["result"]["protocolVersion"], "2024-11-05")

    def test_initialize_falls_back_for_unknown_version(self):
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "initialize",
            "params": {"protocolVersion": "9999-99-99"},
        }
        res = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(res["result"]["protocolVersion"], server.PROTOCOL_VERSION)

    def test_initialize_without_params(self):
        req = {"jsonrpc": "2.0", "id": 4, "method": "initialize"}
        res = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(res["id"], 4)
        self.assertEqual(res["result"]["protocolVersion"], server.PROTOCOL_VERSION)


class TestNotifications(unittest.TestCase):
    def test_notifications_initialized_returns_empty_string(self):
        req = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        res = server.handle(json.dumps(req))
        self.assertEqual(res, "")

    def test_notifications_initialized_with_id_returns_empty_result(self):
        req = {"jsonrpc": "2.0", "id": 10, "method": "notifications/initialized"}
        res = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(res["id"], 10)
        self.assertEqual(res["result"], {})

    def test_other_notifications_return_empty_string(self):
        req = {
            "jsonrpc": "2.0",
            "method": "notifications/cancelled",
            "params": {"requestId": 1},
        }
        res = server.handle(json.dumps(req))
        self.assertEqual(res, "")

    def test_general_notification_without_id_does_not_reply(self):
        req = {"jsonrpc": "2.0", "method": "some/custom/notification"}
        res = server.handle(json.dumps(req))
        self.assertEqual(res, "")


class TestPing(unittest.TestCase):
    def test_ping_returns_empty_result(self):
        req = {"jsonrpc": "2.0", "id": "ping-1", "method": "ping"}
        res = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(res["id"], "ping-1")
        self.assertEqual(res["result"], {})


class TestToolsList(unittest.TestCase):
    def test_tools_list_returns_all_tools(self):
        req = {"jsonrpc": "2.0", "id": 100, "method": "tools/list"}
        res = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(res["id"], 100)
        tools_list = res["result"]["tools"]
        tool_names = [t["name"] for t in tools_list]
        self.assertIn("get_note", tool_names)
        self.assertIn("list_notes", tool_names)

        for t in tools_list:
            self.assertIn("name", t)
            self.assertIn("description", t)
            self.assertIn("inputSchema", t)
            self.assertEqual(t["inputSchema"]["type"], "object")


class TestToolsCallGetNote(unittest.TestCase):
    def setUp(self):
        self._orig_prod_db = os.environ.get("PRODUCTION_DB")

    def tearDown(self):
        if self._orig_prod_db is None:
            os.environ.pop("PRODUCTION_DB", None)
        else:
            os.environ["PRODUCTION_DB"] = self._orig_prod_db
        server._store = None

    def test_get_note_success_n1(self):
        req = {
            "jsonrpc": "2.0",
            "id": "c1",
            "method": "tools/call",
            "params": {
                "name": "get_note",
                "arguments": {"note_id": "n1"},
            },
        }
        res = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(res["id"], "c1")
        result = res["result"]
        self.assertNotIn("isError", result)
        self.assertEqual(result["content"][0]["type"], "text")

        content_data = json.loads(result["content"][0]["text"])
        structured = result["structuredContent"]
        self.assertEqual(content_data, structured)
        self.assertEqual(structured["id"], "n1")
        self.assertEqual(structured["title"], "Ship the importer")
        self.assertEqual(structured["word_count"], 412)
        self.assertEqual(structured["stats"]["views"], 37)
        self.assertEqual(structured["stats"]["rating"], 4.5)
        self.assertEqual(structured["stats"]["revisions"], [1, 2, 3])

        valid, err = validate_schema(structured, server.NOTE_SCHEMA)
        self.assertTrue(valid, f"NOTE_SCHEMA validation failed: {err}")

    def test_get_note_success_n2_float_rating(self):
        req = {
            "jsonrpc": "2.0",
            "id": "c2",
            "method": "tools/call",
            "params": {
                "name": "get_note",
                "arguments": {"note_id": "n2"},
            },
        }
        res = json.loads(server.handle(json.dumps(req)))
        structured = res["result"]["structuredContent"]
        self.assertEqual(structured["id"], "n2")
        self.assertIsInstance(structured["stats"]["rating"], float)
        self.assertEqual(structured["stats"]["rating"], 3.0)

        valid, err = validate_schema(structured, server.NOTE_SCHEMA)
        self.assertTrue(valid, f"NOTE_SCHEMA validation failed: {err}")

    def test_get_note_missing_id_argument(self):
        req = {
            "jsonrpc": "2.0",
            "id": "c3",
            "method": "tools/call",
            "params": {"name": "get_note", "arguments": {}},
        }
        res = json.loads(server.handle(json.dumps(req)))
        result = res["result"]
        self.assertTrue(result["isError"])
        self.assertIn("missing required argument", result["content"][0]["text"])

    def test_get_note_nonexistent_id(self):
        req = {
            "jsonrpc": "2.0",
            "id": "c4",
            "method": "tools/call",
            "params": {
                "name": "get_note",
                "arguments": {"note_id": "does_not_exist"},
            },
        }
        res = json.loads(server.handle(json.dumps(req)))
        result = res["result"]
        self.assertTrue(result["isError"])
        self.assertIn("no note 'does_not_exist'", result["content"][0]["text"])


class TestToolsCallListNotes(unittest.TestCase):
    def setUp(self):
        self._orig_prod_db = os.environ.get("PRODUCTION_DB")

    def tearDown(self):
        if self._orig_prod_db is None:
            os.environ.pop("PRODUCTION_DB", None)
        else:
            os.environ["PRODUCTION_DB"] = self._orig_prod_db
        server._store = None

    def test_list_notes_all(self):
        req = {
            "jsonrpc": "2.0",
            "id": "l1",
            "method": "tools/call",
            "params": {"name": "list_notes", "arguments": {}},
        }
        res = json.loads(server.handle(json.dumps(req)))
        result = res["result"]
        self.assertNotIn("isError", result)
        structured = result["structuredContent"]
        self.assertEqual(structured["count"], 2)
        self.assertEqual([n["id"] for n in structured["notes"]], ["n1", "n2"])

        valid, err = validate_schema(structured, server.LIST_SCHEMA)
        self.assertTrue(valid, f"LIST_SCHEMA validation failed: {err}")

    def test_list_notes_with_tag(self):
        req = {
            "jsonrpc": "2.0",
            "id": "l2",
            "method": "tools/call",
            "params": {
                "name": "list_notes",
                "arguments": {"tag": "home"},
            },
        }
        res = json.loads(server.handle(json.dumps(req)))
        structured = res["result"]["structuredContent"]
        self.assertEqual(structured["count"], 1)
        self.assertEqual(structured["notes"][0]["title"], "Groceries")

        valid, err = validate_schema(structured, server.LIST_SCHEMA)
        self.assertTrue(valid, f"LIST_SCHEMA validation failed: {err}")

    def test_list_notes_with_nonexistent_tag(self):
        req = {
            "jsonrpc": "2.0",
            "id": "l3",
            "method": "tools/call",
            "params": {
                "name": "list_notes",
                "arguments": {"tag": "nonexistent"},
            },
        }
        res = json.loads(server.handle(json.dumps(req)))
        structured = res["result"]["structuredContent"]
        self.assertEqual(structured["count"], 0)
        self.assertEqual(structured["notes"], [])

    def test_list_notes_arguments_null(self):
        req = {
            "jsonrpc": "2.0",
            "id": "l4",
            "method": "tools/call",
            "params": {"name": "list_notes", "arguments": None},
        }
        res = json.loads(server.handle(json.dumps(req)))
        result = res["result"]
        self.assertNotIn("isError", result)
        self.assertEqual(result["structuredContent"]["count"], 2)

    def test_list_notes_arguments_omitted(self):
        req = {
            "jsonrpc": "2.0",
            "id": "l5",
            "method": "tools/call",
            "params": {"name": "list_notes"},
        }
        res = json.loads(server.handle(json.dumps(req)))
        result = res["result"]
        self.assertNotIn("isError", result)
        self.assertEqual(result["structuredContent"]["count"], 2)


class TestToolsCallErrors(unittest.TestCase):
    def test_unknown_tool(self):
        req = {
            "jsonrpc": "2.0",
            "id": "e1",
            "method": "tools/call",
            "params": {"name": "magic_wand", "arguments": {}},
        }
        res = json.loads(server.handle(json.dumps(req)))
        result = res["result"]
        self.assertTrue(result["isError"])
        self.assertIn("unknown tool magic_wand", result["content"][0]["text"])

    def test_non_dict_arguments(self):
        req = {
            "jsonrpc": "2.0",
            "id": "e2",
            "method": "tools/call",
            "params": {"name": "list_notes", "arguments": "invalid"},
        }
        res = json.loads(server.handle(json.dumps(req)))
        result = res["result"]
        self.assertTrue(result["isError"])
        self.assertIn("arguments must be an object", result["content"][0]["text"])

    def test_params_null(self):
        req = {
            "jsonrpc": "2.0",
            "id": "e3",
            "method": "tools/call",
            "params": None,
        }
        res = json.loads(server.handle(json.dumps(req)))
        result = res["result"]
        self.assertTrue(result["isError"])
        self.assertIn("unknown tool None", result["content"][0]["text"])

    def test_non_dict_params(self):
        req = {
            "jsonrpc": "2.0",
            "id": "e4",
            "method": "tools/call",
            "params": "not a dict",
        }
        res = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(res["error"]["code"], -32602)


class TestProductionDatabase(unittest.TestCase):
    """Tests simulating production environment with DynamoDB store (Decimals everywhere)."""

    def setUp(self):
        self._orig_prod_db = os.environ.get("PRODUCTION_DB")
        os.environ["PRODUCTION_DB"] = "1"
        server._store = None

    def tearDown(self):
        if self._orig_prod_db is None:
            os.environ.pop("PRODUCTION_DB", None)
        else:
            os.environ["PRODUCTION_DB"] = self._orig_prod_db
        server._store = None

    def test_production_get_note_serializes_without_decimal_error(self):
        req = {
            "jsonrpc": "2.0",
            "id": "prod-1",
            "method": "tools/call",
            "params": {"name": "get_note", "arguments": {"note_id": "n1"}},
        }
        res_str = server.handle(json.dumps(req))
        res = json.loads(res_str)
        self.assertEqual(res["id"], "prod-1")
        result = res["result"]
        self.assertNotIn("isError", result)

        structured = result["structuredContent"]
        self.assertIsInstance(structured["word_count"], int)
        self.assertIsInstance(structured["stats"]["views"], int)
        self.assertIsInstance(structured["stats"]["rating"], float)
        self.assertIsInstance(structured["stats"]["revisions"], list)
        for rev in structured["stats"]["revisions"]:
            self.assertIsInstance(rev, int)

        valid, err = validate_schema(structured, server.NOTE_SCHEMA)
        self.assertTrue(valid, f"NOTE_SCHEMA validation failed in production: {err}")

    def test_production_list_notes_serializes_without_decimal_error(self):
        req = {
            "jsonrpc": "2.0",
            "id": "prod-2",
            "method": "tools/call",
            "params": {"name": "list_notes"},
        }
        res_str = server.handle(json.dumps(req))
        res = json.loads(res_str)
        result = res["result"]
        self.assertNotIn("isError", result)
        structured = result["structuredContent"]
        self.assertEqual(structured["count"], 2)
        self.assertIsInstance(structured["notes"][0]["word_count"], int)

        valid, err = validate_schema(structured, server.LIST_SCHEMA)
        self.assertTrue(valid, f"LIST_SCHEMA validation failed in production: {err}")


class TestJsonRpcProtocolErrors(unittest.TestCase):
    def test_malformed_json_returns_parse_error(self):
        res = json.loads(server.handle("this is not valid json {"))
        self.assertEqual(res["jsonrpc"], "2.0")
        self.assertIsNone(res["id"])
        self.assertEqual(res["error"]["code"], -32700)
        self.assertEqual(res["error"]["message"], "Parse error")

    def test_empty_string_returns_parse_error(self):
        res = json.loads(server.handle(""))
        self.assertEqual(res["error"]["code"], -32700)

    def test_non_object_json_returns_invalid_request(self):
        for payload in ["123", '"hello"', "[1, 2, 3]", "true"]:
            with self.subTest(payload=payload):
                res = json.loads(server.handle(payload))
                self.assertEqual(res["jsonrpc"], "2.0")
                self.assertIsNone(res["id"])
                self.assertEqual(res["error"]["code"], -32600)
                self.assertIn("Invalid Request", res["error"]["message"])

    def test_invalid_jsonrpc_version(self):
        req = {"jsonrpc": "1.0", "id": 1, "method": "initialize"}
        res = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(res["error"]["code"], -32600)

    def test_missing_method(self):
        req = {"jsonrpc": "2.0", "id": 1}
        res = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(res["error"]["code"], -32600)

    def test_non_string_method(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": 12345}
        res = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(res["error"]["code"], -32600)

    def test_unknown_method_returns_method_not_found(self):
        req = {"jsonrpc": "2.0", "id": 99, "method": "nonexistent_rpc_method"}
        res = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(res["id"], 99)
        self.assertEqual(res["error"]["code"], -32601)
        self.assertIn("nonexistent_rpc_method", res["error"]["message"])


class TestIdHandling(unittest.TestCase):
    def test_string_id(self):
        req = {"jsonrpc": "2.0", "id": "custom-uuid-42", "method": "ping"}
        res = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(res["id"], "custom-uuid-42")

    def test_integer_id(self):
        req = {"jsonrpc": "2.0", "id": 12345, "method": "ping"}
        res = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(res["id"], 12345)

    def test_null_id(self):
        req = {"jsonrpc": "2.0", "id": None, "method": "ping"}
        res = json.loads(server.handle(json.dumps(req)))
        self.assertIsNone(res["id"])


if __name__ == "__main__":
    unittest.main()
