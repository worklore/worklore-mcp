import json, unittest
import db, server
def check(schema, v):
    t = schema.get("type")
    if t == "integer": assert isinstance(v, int) and not isinstance(v, bool), v
    if t == "number": assert isinstance(v, (int, float)), v
    if t == "string": assert isinstance(v, str)
    if t == "object":
        assert isinstance(v, dict)
        for r in schema.get("required", []): assert r in v, r
        for k, s in schema.get("properties", {}).items():
            if k in v: check(s, v[k])
    if t == "array":
        assert isinstance(v, list)
        for x in v: check(schema.get("items", {}), x)
class ClientPath(unittest.TestCase):
    def test_client(self):
        server._store = db.FakeStore()
        rpc = lambda i, m, p=None: json.loads(server.handle(json.dumps({"jsonrpc": "2.0", "id": i, "method": m, "params": p or {}})))
        self.assertIn("result", rpc(1, "initialize"))
        tools = {t["name"]: t for t in rpc(2, "tools/list")["result"]["tools"]}
        for name, args in {"get_note": {"note_id": "n1"}, "list_notes": {}}.items():
            r = rpc(3, "tools/call", {"name": name, "arguments": args})["result"]
            self.assertFalse(r.get("isError"), r)
            self.assertIn("structuredContent", r)
            check(tools[name]["outputSchema"], r["structuredContent"])
