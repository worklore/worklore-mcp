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

    def test_other_user_cannot_touch_private_task(self):
        code, body = self.call("GET", "/tasks", token=BOB)
        self.assertEqual(code, 200)
        self.assertNotIn(1, [task["id"] for task in body["tasks"]])

        attempts = [
            ("GET", "/tasks/1", None),
            ("PATCH", "/tasks/1", {"title": "changed"}),
            ("DELETE", "/tasks/1", None),
            ("POST", "/tasks/1/comments", {"text": "changed"}),
            ("POST", "/tasks/1/complete", None),
            ("POST", "/tasks/1/nudge", None),
            ("POST", "/tasks/1/like", None),
            ("POST", "/tasks/1/view", None),
        ]
        for method, path, body in attempts:
            with self.subTest(method=method, path=path):
                self.assertEqual(self.call(method, path, body, token=BOB)[0], 403)

        code, task = self.call("GET", "/tasks/1")
        self.assertEqual(code, 200)
        self.assertEqual(task["title"], "Draft the investor update")
        self.assertEqual(task["likes"], 0)
        self.assertEqual(task["views"], 0)
        self.assertEqual(task["nudges"], 0)
        self.assertEqual(task["comments"], [])
        self.assertFalse(task["done"])

    def test_other_user_can_interact_with_public_task(self):
        self.assertEqual(self.call("GET", "/tasks/2", token=BOB)[0], 200)
        for action in ("comments", "nudge", "like", "view"):
            body = {"text": "on it"} if action == "comments" else None
            with self.subTest(action=action):
                self.assertIn(self.call("POST", "/tasks/2/" + action, body, token=BOB)[0], (200, 201))
        self.assertEqual(self.call("POST", "/tasks/2/complete", token=BOB)[0], 403)

    def test_bad_input(self):
        self.assertEqual(self.call("POST", "/tasks", {"visibility": "public"})[0], 400)
        self.assertEqual(self.call("GET", "/nope")[0], 404)


if __name__ == "__main__":
    unittest.main()
