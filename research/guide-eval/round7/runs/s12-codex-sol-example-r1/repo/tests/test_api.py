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

    def test_bad_input(self):
        self.assertEqual(self.call("POST", "/tasks", {"visibility": "public"})[0], 400)
        self.assertEqual(self.call("GET", "/nope")[0], 404)

    def test_private_task_rejects_stranger_for_every_action(self):
        code, task = self.call("POST", "/tasks", {"title": "Private probe"})
        self.assertEqual(code, 201)
        path = "/tasks/%d" % task["id"]
        _, listing = self.call("GET", "/tasks", token=BOB)
        self.assertNotIn(task["id"], [item["id"] for item in listing["tasks"]])

        attempts = [
            ("GET", "", None),
            ("PATCH", "", {"title": "Changed by Bob", "visibility": "public"}),
            ("DELETE", "", None),
            ("POST", "/comments", {"text": "Bob was here"}),
            ("POST", "/complete", None),
            ("POST", "/nudge", None),
            ("POST", "/like", None),
            ("POST", "/view", None),
        ]
        for method, suffix, body in attempts:
            with self.subTest(method=method, suffix=suffix):
                status, _ = self.call(method, path + suffix, body, token=BOB)
                self.assertEqual(status, 403)

        status, after = self.call("GET", path)
        self.assertEqual(status, 200)
        self.assertEqual(after, task)

    def test_stranger_can_interact_with_public_task_but_not_edit_it(self):
        path = "/tasks/2"
        self.assertEqual(self.call("GET", path, token=BOB)[0], 200)
        self.assertEqual(self.call("POST", path + "/comments", {"text": "Hi"}, token=BOB)[0], 201)
        for suffix, field in (("nudge", "nudges"), ("like", "likes"), ("view", "views")):
            with self.subTest(suffix=suffix):
                status, result = self.call("POST", path + "/" + suffix, token=BOB)
                self.assertEqual((status, result[field]), (200, 1))
        self.assertEqual(self.call("PATCH", path, {"title": "Hijacked"}, token=BOB)[0], 403)
        self.assertEqual(self.call("DELETE", path, token=BOB)[0], 403)
        self.assertEqual(self.call("POST", path + "/complete", token=BOB)[0], 403)


if __name__ == "__main__":
    unittest.main()
