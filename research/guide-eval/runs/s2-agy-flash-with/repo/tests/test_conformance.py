"""MCP Conformance tests.

Talks to the server the way a real MCP client does:
1. Send initialize through the real entry point.
2. Ask for tools/list, with no credentials.
3. Call every tool and serialize the whole response.
4. Validate each result against the published output schema.
"""
import json
import unittest

import server


def validate_schema(data, schema, path=""):
    """Validate data against a JSON schema subset.

    Supports: object, array, string, integer, number, boolean, null.
    Validates required fields, object properties, and array items.
    """
    if not schema:
        return

    location = path or "root"
    schema_type = schema.get("type")

    def check_type(expected_type):
        if expected_type == "object":
            return isinstance(data, dict)
        elif expected_type == "array":
            return isinstance(data, list)
        elif expected_type == "string":
            return isinstance(data, str)
        elif expected_type == "integer":
            return isinstance(data, int) and not isinstance(data, bool)
        elif expected_type == "number":
            return isinstance(data, (int, float)) and not isinstance(data, bool)
        elif expected_type == "boolean":
            return isinstance(data, bool)
        elif expected_type == "null":
            return data is None
        return True

    if schema_type:
        if isinstance(schema_type, list):
            if not any(check_type(t) for t in schema_type):
                raise AssertionError(
                    f"Expected one of types {schema_type} at {location}, got {type(data).__name__} ({data!r})"
                )
        else:
            if not check_type(schema_type):
                raise AssertionError(
                    f"Expected {schema_type} at {location}, got {type(data).__name__} ({data!r})"
                )

    if isinstance(data, dict):
        for req in schema.get("required", []):
            if req not in data:
                raise AssertionError(f"Missing required property '{req}' at {location}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(data.keys()) - set(properties.keys())
            if extra:
                raise AssertionError(f"Undeclared property {extra} at {location}")
        for key, prop_schema in properties.items():
            if key in data:
                validate_schema(data[key], prop_schema, path=f"{location}.{key}")

    elif isinstance(data, list):
        items_schema = schema.get("items")
        if items_schema:
            for idx, item in enumerate(data):
                validate_schema(item, items_schema, path=f"{location}[{idx}]")


TOOL_VALID_ARGUMENTS = {
    "get_note": {"note_id": "n1"},
    "list_notes": {},
}

TOOL_ADDITIONAL_ARGUMENTS = {
    "get_note": [{"note_id": "n2"}],
    "list_notes": [{"tag": "home"}],
}


class MCPTestClient:
    """Client helper invoking the server through its real entry point (server.handle)."""

    def __init__(self, handler=server.handle):
        self.handler = handler
        self.msg_id = 0

    def send(self, method, params=None):
        self.msg_id += 1
        payload = {"jsonrpc": "2.0", "id": self.msg_id, "method": method}
        if params is not None:
            payload["params"] = params
        req_json = json.dumps(payload)
        resp_json = self.handler(req_json)
        # Step 5: Assert the response parses and survives serialization
        resp = json.loads(resp_json)
        json.dumps(resp)
        return resp


class ConformanceTest(unittest.TestCase):
    def setUp(self):
        server._store = None

    def tearDown(self):
        server._store = None

    def test_initialize(self):
        """Step 1: Send initialize through the real entry point."""
        client = MCPTestClient()
        resp = client.send(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )
        self.assertEqual(resp.get("jsonrpc"), "2.0")
        self.assertEqual(resp.get("id"), client.msg_id)
        self.assertNotIn("error", resp)
        result = resp.get("result", {})
        self.assertIn("protocolVersion", result)
        self.assertIn("capabilities", result)
        self.assertIn("serverInfo", result)

    def test_tools_list_without_credentials(self):
        """Step 2: Ask for tools/list, with no credentials."""
        client = MCPTestClient()
        client.send("initialize")
        resp = client.send("tools/list")
        self.assertEqual(resp.get("jsonrpc"), "2.0")
        self.assertNotIn("error", resp)
        result = resp.get("result", {})
        self.assertIn("tools", result)
        tools = result["tools"]
        self.assertGreater(len(tools), 0)
        for tool in tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)

    def test_call_tools_serializes_response(self):
        """Step 3 & 5: Call every tool through real entry point and serialize whole response."""
        client = MCPTestClient()
        client.send("initialize")
        list_resp = client.send("tools/list")
        tools = list_resp["result"]["tools"]

        for tool in tools:
            name = tool["name"]
            self.assertIn(name, TOOL_VALID_ARGUMENTS, f"No test arguments configured for tool '{name}'")
            arg_sets = [TOOL_VALID_ARGUMENTS[name]] + TOOL_ADDITIONAL_ARGUMENTS.get(name, [])
            for args in arg_sets:
                call_resp = client.send("tools/call", {"name": name, "arguments": args})
                self.assertEqual(call_resp.get("jsonrpc"), "2.0")
                self.assertNotIn("error", call_resp)
                result = call_resp.get("result", {})
                # Assert first that a happy-path call did not come back with isError
                self.assertFalse(
                    result.get("isError", False),
                    f"Tool '{name}' with args {args} returned isError: {result.get('content')}",
                )
                # Assert the whole response survives being serialized
                serialized = json.dumps(call_resp)
                self.assertIsInstance(serialized, str)
                self.assertIn("content", result)

    def test_validate_against_published_output_schema(self):
        """Step 4 & 6: Validate each result against published outputSchema; check structuredContent."""
        client = MCPTestClient()
        client.send("initialize")

        # Step 2 & 3: Keep schemas from tools/list response (not from source)
        list_resp = client.send("tools/list")
        tools = list_resp["result"]["tools"]

        for tool in tools:
            name = tool["name"]
            output_schema = tool.get("outputSchema")
            arg_sets = [TOOL_VALID_ARGUMENTS[name]] + TOOL_ADDITIONAL_ARGUMENTS.get(name, [])

            for args in arg_sets:
                call_resp = client.send("tools/call", {"name": name, "arguments": args})
                result = call_resp.get("result", {})

                # Assert first that a happy-path call did not come back with isError
                self.assertFalse(
                    result.get("isError", False),
                    f"Tool '{name}' with args {args} returned isError: {result.get('content')}",
                )

                # Step 6: Treat "declares an outputSchema but returned no structuredContent" as a failure
                if output_schema is not None:
                    self.assertIn(
                        "structuredContent",
                        result,
                        f"Tool '{name}' declares outputSchema but returned no structuredContent",
                    )
                    # Step 4: Validate each result against published schema
                    validate_schema(result["structuredContent"], output_schema)


if __name__ == "__main__":
    unittest.main()
