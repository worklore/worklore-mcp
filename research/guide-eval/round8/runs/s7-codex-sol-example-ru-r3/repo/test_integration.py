"""Local OAuth regression tests; no requests to Intervals.icu."""
import json
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import config
import server


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.http.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()

    def setUp(self):
        with server.LOCK:
            server.CONNECTIONS.clear()

    def request(self, path, method="GET", auth=True):
        headers = {"Authorization": "Bearer tok-okafor"} if auth else {}
        req = urllib.request.Request(self.base + path, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as error:
            try:
                return error.code, dict(error.headers), error.read()
            finally:
                error.close()

    def test_init_requires_authenticated_post_and_unique_scopes(self):
        self.assertEqual(self.request("/api/intervals/auth/init")[0], 404)
        self.assertEqual(self.request("/api/intervals/auth/init", "POST", False)[0], 401)
        code, _, body = self.request("/api/intervals/auth/init", "POST")
        self.assertEqual(code, 200)
        url = json.loads(body)["authorize_url"]
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        self.assertEqual(query["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(server.verify_state(query["state"][0]), "u_okafor")

    def test_callback_exchange_and_revocation(self):
        state = server.sign_state("u_okafor")
        token = {"access_token": "valid-token", "scope": config.SCOPES,
                 "athlete": {"id": "i123", "name": "Test Athlete"}}
        with patch.object(server, "post_form", return_value=token) as post:
            code, _, _ = self.request("/api/intervals/callback?" + urllib.parse.urlencode(
                {"code": "test-code", "state": state}), auth=False)
        self.assertEqual(code, 200)  # urllib follows the callback redirect
        self.assertEqual(post.call_args.args[1], {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "test-code"})
        self.assertTrue(json.loads(self.request("/api/intervals/status")[2])["connected"])
        with patch.object(server.time, "time", return_value=server.time.time() + 7200):
            self.assertTrue(json.loads(self.request("/api/intervals/status")[2])["connected"])

        with patch.object(server, "intervals_get", side_effect=urllib.error.HTTPError(
                "local", 401, "Unauthorized", {}, None)):
            self.assertEqual(self.request("/api/intervals/wellness")[0], 401)
        status = json.loads(self.request("/api/intervals/status")[2])
        self.assertFalse(status["connected"])
        self.assertEqual(status["status"], "reconnect required")
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])

    def test_reconnect_cannot_change_athlete(self):
        server.store_connection("u_okafor", {"access_token": "first", "athlete": {"id": "i123"}})
        with self.assertRaisesRegex(ValueError, "does not match"):
            server.store_connection("u_okafor", {"access_token": "second", "athlete": {"id": "i456"}})
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "first")

    def test_state_rejects_tampering_and_expiry(self):
        state = server.sign_state("u_okafor")
        self.assertIsNone(server.verify_state(state[:-3] + "bad"))
        with patch.object(server.time, "time", return_value=server.time.time() + 901):
            self.assertIsNone(server.verify_state(state))


if __name__ == "__main__":
    unittest.main()
