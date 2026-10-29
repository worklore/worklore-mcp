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


class IntervalsConnectionTests(unittest.TestCase):
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
        server.CONNECTIONS.clear()

    def get(self, path, token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        req = urllib.request.Request(self.base + path, headers=headers)
        with urllib.request.urlopen(req) as response:
            return json.load(response)

    def test_authorize_url_requires_app_auth_and_has_unique_scopes(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get("/api/intervals/auth/init")
        self.assertEqual(error.exception.code, 401)
        error.exception.close()

        data = self.get("/api/intervals/auth/init", "tok-okafor")
        url = urllib.parse.urlsplit(data["authorize_url"])
        params = urllib.parse.parse_qs(url.query)
        self.assertEqual(url.path, "/oauth/authorize")
        self.assertEqual(params["scope"], [config.SCOPES])
        families = [scope.split(":")[0] for scope in config.SCOPES.split(",")]
        self.assertEqual(len(families), len(set(families)))
        self.assertIn("CALENDAR:WRITE", config.SCOPES.split(","))
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")

    def test_callback_token_without_expiry_stays_connected_after_hour(self):
        token = {"access_token": "provider-token", "scope": config.SCOPES,
                 "athlete": {"id": "i98765", "name": "T. Rivera"}}
        with patch.object(server, "exchange_code", return_value=token):
            state = server.sign_state("u_rivera")
            path = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "abc", "state": state})
            with urllib.request.urlopen(self.base + path) as response:
                self.assertEqual(response.geturl(), self.base + "/?connected=1")

        conn = server.CONNECTIONS["u_rivera"]
        self.assertIsNone(conn["expires_at"])
        with patch.object(server.time, "time", return_value=server.time.time() + 7200), \
             patch.object(server, "post_form") as post:
            server.refresh_connections()
            post.assert_not_called()
        self.assertEqual(server.CONNECTIONS["u_rivera"]["access_token"], "provider-token")
        self.assertTrue(self.get("/api/intervals/status", "tok-rivera")["connected"])

    def test_explicit_expiry_without_refresh_token_is_honored(self):
        with patch.object(server.time, "time", return_value=1000):
            server.store_connection("u_okafor", {"access_token": "short-token", "expires_in": 3600})
        with patch.object(server.time, "time", return_value=4500):
            server.refresh_connections()
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "connected")
        with patch.object(server.time, "time", return_value=4600):
            server.refresh_connections()
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "expired, reconnect")


if __name__ == "__main__":
    unittest.main()
