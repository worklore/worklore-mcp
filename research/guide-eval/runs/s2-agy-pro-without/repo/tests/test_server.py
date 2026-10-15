import unittest
import json
import os
import server
import db

class ServerTest(unittest.TestCase):
    def setUp(self):
        os.environ.pop("PRODUCTION_DB", None)
        server._store = None

    def test_initialize(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
        resp = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertEqual(resp["id"], 1)
        self.assertIn("protocolVersion", resp["result"])
        self.assertEqual(resp["result"]["protocolVersion"], "2024-11-05")

    def test_ping(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
        resp = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertEqual(resp["id"], 2)
        self.assertEqual(resp["result"], {})

    def test_tools_list(self):
        req = {"jsonrpc": "2.0", "id": 3, "method": "tools/list"}
        resp = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertIn("tools", resp["result"])

    def test_tools_call(self):
        req = {
            "jsonrpc": "2.0", 
            "id": 4, 
            "method": "tools/call", 
            "params": {"name": "get_note", "arguments": {"note_id": "n1"}}
        }
        resp = json.loads(server.handle(json.dumps(req)))
        self.assertIn("result", resp)
        self.assertFalse(resp["result"].get("isError", False))

    def test_tools_call_production_db(self):
        os.environ["PRODUCTION_DB"] = "1"
        server._store = None 
        req = {
            "jsonrpc": "2.0", 
            "id": 5, 
            "method": "tools/call", 
            "params": {"name": "get_note", "arguments": {"note_id": "n1"}}
        }
        resp = json.loads(server.handle(json.dumps(req)))
        self.assertFalse(resp["result"].get("isError", False))

    def test_notification(self):
        req = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        resp = server.handle(json.dumps(req))
        self.assertEqual(resp, "")

    def test_parse_error(self):
        resp_str = server.handle("{invalid json")
        resp = json.loads(resp_str)
        self.assertEqual(resp["error"]["code"], -32700)
        self.assertIsNone(resp["id"])

    def test_method_not_found(self):
        req = {"jsonrpc": "2.0", "id": 6, "method": "unknown/method"}
        resp = json.loads(server.handle(json.dumps(req)))
        self.assertEqual(resp["error"]["code"], -32601)

    def test_invalid_request(self):
        resp_str = server.handle('[]')
        resp = json.loads(resp_str)
        self.assertEqual(resp["error"]["code"], -32600)
        self.assertIsNone(resp["id"])

if __name__ == "__main__":
    unittest.main()
