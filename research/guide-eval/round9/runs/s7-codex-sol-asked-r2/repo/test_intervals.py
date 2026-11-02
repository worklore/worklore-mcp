"""Local regression checks for the Intervals connection flow."""
import io
import json
import threading
import time
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
        cls.base = f"http://127.0.0.1:{cls.http.server_port}"
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()

    def setUp(self):
        with server.LOCK:
            server.CONNECTIONS.clear()

    def request(self, path, method="GET", token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        req = urllib.request.Request(self.base + path, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, json.loads(response.read()), response.headers
        except urllib.error.HTTPError as error:
            try:
                return error.code, json.loads(error.read()), error.headers
            finally:
                error.close()

    def test_connect_requires_authenticated_post_and_has_unique_scopes(self):
        code, _, _ = self.request("/api/intervals/auth/init")
        self.assertEqual(code, 404)
        code, _, _ = self.request("/api/intervals/auth/init", "POST")
        self.assertEqual(code, 401)
        code, body, _ = self.request("/api/intervals/auth/init", "POST", "tok-okafor")
        self.assertEqual(code, 200)
        url = urllib.parse.urlsplit(body["authorize_url"])
        params = urllib.parse.parse_qs(url.query)
        self.assertEqual(url.path, "/oauth/authorize")
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")

    def test_callback_exchange_and_token_lifetime(self):
        state = server.sign_state("u_rivera")
        token = {"access_token": "provider-token", "scope": config.SCOPES,
                 "athlete": {"id": "i98765", "name": "T. Rivera"}}
        with patch.object(server, "post_form", return_value=token) as exchange:
            req = urllib.request.Request(self.base + "/api/intervals/callback?" +
                                         urllib.parse.urlencode({"code": "abc", "state": state}))
            # urllib follows the redirect to the SPA.
            with urllib.request.urlopen(req) as response:
                self.assertEqual(response.status, 200)
            exchange.assert_called_once_with(server.TOKEN_URL, {
                "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET,
                "code": "abc",
            })
        with patch.object(server.time, "time", return_value=time.time() + 7200):
            code, body, _ = self.request("/api/intervals/status", token="tok-rivera")
        self.assertEqual(code, 200)
        self.assertTrue(body["connected"])
        self.assertNotIn("expires_at", server.CONNECTIONS["u_rivera"])

    def test_api_401_marks_connection_for_reconnect(self):
        server.store_connection("u_okafor", {"access_token": "revoked", "athlete": {"id": "i1"}})
        error = urllib.error.HTTPError("provider", 401, "Unauthorized", {}, io.BytesIO())
        with patch.object(server, "intervals_get", side_effect=error):
            code, _, _ = self.request("/api/intervals/wellness", token="tok-okafor")
        self.assertEqual(code, 401)
        code, body, _ = self.request("/api/intervals/status", token="tok-okafor")
        self.assertEqual(code, 200)
        self.assertFalse(body["connected"])
        self.assertEqual(body["status"], "reconnect")
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])

    def test_reconnect_cannot_replace_athlete_without_disconnect(self):
        server.store_connection("u_okafor", {"access_token": "old", "athlete": {"id": "i1"}})
        with self.assertRaises(server.AccountMismatchError):
            server.store_connection("u_okafor", {"access_token": "new", "athlete": {"id": "i2"}})
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "old")


if __name__ == "__main__":
    unittest.main()
