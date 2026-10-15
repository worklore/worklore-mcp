import json
import unittest

import server

def validate_schema(instance, schema):
    t = schema.get("type")
    if t == "object":
        if not isinstance(instance, dict):
            raise ValueError(f"Expected object, got {type(instance)}")
        for req in schema.get("required", []):
            if req not in instance:
                raise ValueError(f"Missing required field: {req}")
        for k, v_schema in schema.get("properties", {}).items():
            if k in instance:
                validate_schema(instance[k], v_schema)
    elif t == "array":
        if not isinstance(instance, list):
            raise ValueError(f"Expected array, got {type(instance)}")
        item_schema = schema.get("items")
        if item_schema:
            for item in instance:
                validate_schema(item, item_schema)
    elif t == "string":
        if not isinstance(instance, str):
            raise ValueError(f"Expected string, got {type(instance)}")
    elif t == "integer":
        if not isinstance(instance, int) or isinstance(instance, bool):
            raise ValueError(f"Expected integer, got {type(instance)}")
    elif t == "number":
        if not isinstance(instance, (int, float)) or isinstance(instance, bool):
            raise ValueError(f"Expected number, got {type(instance)}")
    else:
        raise ValueError(f"Unknown schema type: {t}")

class ClientLikeTest(unittest.TestCase):
    def test_client_flow(self):
        # 1. Send initialize
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        resp = json.loads(server.handle(json.dumps(req)))
        self.assertNotIn("error", resp)

        # 2. Ask for tools/list, with no credentials. Keep schemas.
        req2 = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        resp2_str = server.handle(json.dumps(req2))
        resp2 = json.loads(resp2_str)
        self.assertNotIn("error", resp2)
        
        tools = resp2["result"]["tools"]
        self.assertGreater(len(tools), 0, "Server must describe its tools anonymously")
        schemas = {t["name"]: t["outputSchema"] for t in tools if "outputSchema" in t}

        # 3. Call every tool and serialise the whole response
        # 4. Validate each result against the schema from step 2

        # Tool 1: get_note
        req3 = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_note", "arguments": {"note_id": "n1"}}
        }
        # Assert the whole response survives being serialised (which happens inside handle)
        resp3_str = server.handle(json.dumps(req3))
        # Ensure it actually is serialisable, in case handle returned something weird
        resp3 = json.loads(resp3_str)
        self.assertNotIn("error", resp3)
        result3 = resp3["result"]
        # Assert first that a happy-path call did not come back with isError
        self.assertFalse(result3.get("isError", False), f"isError was true, content: {result3.get('content')}")
        
        self.assertIn("structuredContent", result3)
        if "get_note" in schemas:
            validate_schema(result3["structuredContent"], schemas["get_note"])

        # Tool 2: list_notes
        req4 = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "list_notes", "arguments": {}}
        }
        resp4_str = server.handle(json.dumps(req4))
        resp4 = json.loads(resp4_str)
        self.assertNotIn("error", resp4)
        result4 = resp4["result"]
        self.assertFalse(result4.get("isError", False), f"isError was true, content: {result4.get('content')}")
        self.assertIn("structuredContent", result4)
        if "list_notes" in schemas:
            validate_schema(result4["structuredContent"], schemas["list_notes"])

if __name__ == "__main__":
    unittest.main()
