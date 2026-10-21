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

    def test_stranger_cannot_touch_private_task(self):
        # Task #1 is alice's private task; bob must be refused on every action.
        for method, path, body in [
            ("GET", "/tasks/1", None),
            ("PATCH", "/tasks/1", {"title": "pwned"}),
            ("DELETE", "/tasks/1", None),
            ("POST", "/tasks/1/comments", {"text": "hi"}),
            ("POST", "/tasks/1/complete", None),
            ("POST", "/tasks/1/nudge", None),
            ("POST", "/tasks/1/like", None),
            ("POST", "/tasks/1/view", None),
        ]:
            with self.subTest(action=method + " " + path):
                self.assertIn(self.call(method, path, body, token=BOB)[0], (403, 404))
        # Re-read as the owner: nothing bob sent may have changed the task.
        code, t = self.call("GET", "/tasks/1", token=ALICE)
        self.assertEqual(code, 200)
        self.assertEqual((t["title"], t["likes"], t["views"], t["nudges"], t["done"], t["comments"]),
                         ("Draft the investor update", 0, 0, 0, False, []))

    def test_stranger_can_like_and_view_public_task(self):
        self.assertEqual(self.call("POST", "/tasks/2/like", token=BOB)[1]["likes"], 1)
        self.assertEqual(self.call("POST", "/tasks/2/view", token=BOB)[1]["views"], 1)

    def test_bad_input(self):
        self.assertEqual(self.call("POST", "/tasks", {"visibility": "public"})[0], 400)
        self.assertEqual(self.call("GET", "/nope")[0], 404)


if __name__ == "__main__":
    unittest.main()
