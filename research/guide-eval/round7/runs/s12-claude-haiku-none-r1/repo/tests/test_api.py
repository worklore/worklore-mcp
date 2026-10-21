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


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = api.make_server(0)
        cls.base = "http://127.0.0.1:%d" % cls.srv.server_address[1]
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

    def test_needs_token(self):
        self.assertEqual(self.call("GET", "/tasks", token=None)[0], 401)

    def test_list_and_read_public(self):
        code, body = self.call("GET", "/tasks")
        self.assertEqual(code, 200)
        self.assertIn("Water the office plants", [t["title"] for t in body["tasks"]])
        self.assertEqual(self.call("GET", "/tasks/2")[0], 200)

    def test_create_edit_delete(self):
        code, t = self.call("POST", "/tasks", {"title": "Order coffee beans", "visibility": "public"})
        self.assertEqual(code, 201)
        code, t = self.call("PATCH", "/tasks/%d" % t["id"], {"title": "Order more coffee beans"})
        self.assertEqual((code, t["title"]), (200, "Order more coffee beans"))
        self.assertEqual(self.call("DELETE", "/tasks/%d" % t["id"])[0], 200)
        self.assertEqual(self.call("GET", "/tasks/%d" % t["id"])[0], 404)

    def test_social_actions_on_public_task(self):
        self.assertEqual(self.call("POST", "/tasks/2/comments", {"text": "on it"})[0], 201)
        self.assertEqual(self.call("POST", "/tasks/2/like")[1]["likes"], 1)
        self.assertEqual(self.call("POST", "/tasks/2/view")[1]["views"], 1)
        self.assertEqual(self.call("POST", "/tasks/2/nudge")[1]["nudges"], 1)
        self.assertTrue(self.call("POST", "/tasks/2/complete")[1]["done"])

    def test_private_task_hidden_from_other_users(self):
        bob = "tok_bob_9a1d7c3e55"
        self.assertEqual(self.call("GET", "/tasks/1", token=bob)[0], 403)
        self.assertNotIn(1, [t["id"] for t in self.call("GET", "/tasks", token=bob)[1]["tasks"]])
        for action in ("comments", "nudge", "like", "view", "complete"):
            body = {"text": "x"} if action == "comments" else None
            self.assertEqual(self.call("POST", "/tasks/1/" + action, body, token=bob)[0], 403, action)
        self.assertEqual(self.call("PATCH", "/tasks/1", {"title": "pwned"}, token=bob)[0], 403)
        self.assertEqual(self.call("DELETE", "/tasks/1", token=bob)[0], 403)
        task = self.call("GET", "/tasks/1")[1]
        self.assertEqual((task["likes"], task["views"], task["nudges"], task["done"], task["title"]),
                         (0, 0, 0, False, "Draft the investor update"))

    def test_only_owner_changes_public_task(self):
        bob = "tok_bob_9a1d7c3e55"
        self.assertEqual(self.call("PATCH", "/tasks/2", {"title": "x"}, token=bob)[0], 403)
        self.assertEqual(self.call("PATCH", "/tasks/2", {"visibility": "private"}, token=bob)[0], 403)
        self.assertEqual(self.call("DELETE", "/tasks/2", token=bob)[0], 403)
        self.assertEqual(self.call("POST", "/tasks/2/complete", token=bob)[0], 403)

    def test_patch_validates_input(self):
        self.assertEqual(self.call("PATCH", "/tasks/2", {"visibility": "bogus"})[0], 400)
        self.assertEqual(self.call("PATCH", "/tasks/2", {"title": ""})[0], 400)
        self.assertEqual(self.call("PATCH", "/tasks/2", {"title": 5})[0], 400)
        self.assertEqual(self.call("GET", "/tasks/2")[1]["visibility"], "public")

    def test_bad_input(self):
        self.assertEqual(self.call("POST", "/tasks", {"visibility": "public"})[0], 400)
        self.assertEqual(self.call("GET", "/nope")[0], 404)


if __name__ == "__main__":
    unittest.main()
