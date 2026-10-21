import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import api  # noqa: E402

ALICE = "tok_alice_4f8c2e71b0"
BOB = "tok_bob_9a1d7c3e55"

class PrivateActionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = api.make_server(0)
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        api.seed()

    def call(self, method, path, body=None, token=ALICE):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if token:
            req.add_header("Authorization", "Bearer " + token)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def test_private_like_and_view_forbidden(self):
        # Alice's private task is id 1
        # Bob attempts to like
        code_like, _ = self.call("POST", "/tasks/1/like", token=BOB)
        self.assertEqual(code_like, 403)
        # Bob attempts to view
        code_view, _ = self.call("POST", "/tasks/1/view", token=BOB)
        self.assertEqual(code_view, 403)
        # Verify likes and views remain 0 when accessed by owner
        code_owner, task = self.call("GET", "/tasks/1", token=ALICE)
        self.assertEqual(code_owner, 200)
        self.assertEqual(task["likes"], 0)
        self.assertEqual(task["views"], 0)
