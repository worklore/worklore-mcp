"""Local HTTP tests for the Intervals connection flow; no provider calls."""
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


class IntervalsFlowTest(unittest.TestCase):
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

    def request(self, path, method="GET", auth=None):
        headers = {"Authorization": f"Bearer {auth}"} if auth else {}
        req = urllib.request.Request(self.base + path, method=method, headers=headers)
        try:
            response = urllib.request.urlopen(req)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def test_connect_and_revocation(self):
        status, _ = self.request("/api/intervals/auth/init", "POST")
        self.assertEqual(status, 401)
        status, _ = self.request("/api/intervals/auth/init", auth="tok-okafor")
        self.assertEqual(status, 404)
        status, data = self.request("/api/intervals/auth/init", "POST", "tok-okafor")
        self.assertEqual(status, 200)
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(data["authorize_url"]).query)
        self.assertEqual(query["scope"], [config.SCOPES])
        self.assertEqual(server.verify_state(query["state"][0]), "u_okafor")

        token = {"access_token": "valid-token", "scope": config.SCOPES,
                 "athlete": {"id": "i123", "name": "C. Okafor"}}
        callback = "/api/intervals/callback?" + urllib.parse.urlencode(
            {"code": "one-time-code", "state": query["state"][0]})
        with patch.object(server, "post_form", return_value=token) as post:
            req = urllib.request.Request(self.base + callback)
            opener = urllib.request.build_opener(urllib.request.HTTPHandler())
            with opener.open(req) as response:
                self.assertEqual(response.status, 200)  # callback redirects to the SPA
            post.assert_called_once_with(server.TOKEN_URL, {
                "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET,
                "code": "one-time-code"})
        status, data = self.request("/api/intervals/status", auth="tok-okafor")
        self.assertTrue(data["connected"])
        self.assertEqual(data["athlete"]["id"], "i123")
        self.assertEqual(status, 200)

        with patch.object(server, "intervals_get", return_value=(200, [{"date": "2026-10-27"}])):
            status, data = self.request("/api/intervals/wellness", auth="tok-okafor")
        self.assertEqual((status, data), (200, [{"date": "2026-10-27"}]))

        revoked = urllib.error.HTTPError("local", 401, "Unauthorized", {}, None)
        with patch.object(server, "intervals_get", side_effect=revoked):
            status, _ = self.request("/api/intervals/wellness", auth="tok-okafor")
        self.assertEqual(status, 401)
        status, data = self.request("/api/intervals/status", auth="tok-okafor")
        self.assertEqual((status, data), (200, {"connected": False, "status": "reconnect"}))
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])

    def test_state_and_account_mismatch(self):
        state = server.sign_state("u_rivera")
        self.assertIsNone(server.verify_state(state[:-2] + "xx"))
        with patch.object(server.time, "time", return_value=server.time.time() + 901):
            self.assertIsNone(server.verify_state(state))
        server.store_connection("u_rivera", {"access_token": "first", "athlete": {"id": "i1"}})
        with self.assertRaisesRegex(ValueError, "does not match"):
            server.store_connection("u_rivera", {"access_token": "second", "athlete": {"id": "i2"}})
        self.assertEqual(server.CONNECTIONS["u_rivera"]["access_token"], "first")


if __name__ == "__main__":
    unittest.main()
