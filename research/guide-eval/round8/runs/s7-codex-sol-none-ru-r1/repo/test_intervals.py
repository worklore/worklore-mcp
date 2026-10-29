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
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.httpd.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join()

    def setUp(self):
        with server.LOCK:
            server.CONNECTIONS.clear()

    def request(self, path, token="tok-okafor"):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return urllib.request.urlopen(
            urllib.request.Request(self.base + path, headers=headers), timeout=2
        )

    def test_authorized_init_and_callback_without_expiry(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request("/api/intervals/auth/init", token=None)
        self.assertEqual(error.exception.code, 401)
        error.exception.close()

        with self.request("/api/intervals/auth/init") as response:
            self.assertEqual(response.status, 200)
            authorize_url = json.load(response)["authorize_url"]
        parsed = urllib.parse.urlsplit(authorize_url)
        params = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ"])
        self.assertEqual(params["redirect_uri"], [config.REDIRECT_URI])
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")

        token = {"access_token": "example-token", "scope": config.SCOPES,
                 "athlete": {"id": "i123", "name": "Example"}}
        callback = "/api/intervals/callback?" + urllib.parse.urlencode(
            {"code": "example-code", "state": params["state"][0]})
        with patch.object(server, "exchange_code", return_value=token):
            with self.request(callback) as response:
                self.assertEqual(response.status, 200)  # follows callback redirect
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["expires_at"])
        server.refresh_connections_once(now=time.time() + 86400)
        with self.request("/api/intervals/status") as response:
            self.assertTrue(json.load(response)["connected"])

    def test_finite_token_without_refresh_expires_only_at_expiry(self):
        server.store_connection("u_okafor", {"access_token": "short", "expires_in": 3600})
        expiry = server.CONNECTIONS["u_okafor"]["expires_at"]
        server.refresh_connections_once(now=expiry - 300)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "connected")
        server.refresh_connections_once(now=expiry + 1)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "expired, reconnect")

    def test_provider_unauthorized_marks_connection_for_reconnect(self):
        server.store_connection("u_okafor", {"access_token": "revoked", "athlete": {"id": "i123"}})
        unauthorized = urllib.error.HTTPError("local mock", 401, "Unauthorized", {}, io.BytesIO())
        with patch.object(server, "intervals_get", side_effect=unauthorized):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request("/api/intervals/wellness")
        self.assertEqual(error.exception.code, 401)
        error.exception.close()
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "expired, reconnect")

    def test_refresh_uses_provider_expiry_and_keeps_refresh_token(self):
        server.store_connection("u_okafor", {"access_token": "old", "refresh_token": "refresh",
                                             "expires_in": 120})
        expiry = server.CONNECTIONS["u_okafor"]["expires_at"]
        with patch.object(server, "post_form", return_value={"access_token": "new"}) as post:
            server.refresh_connections_once(now=expiry - 100)
        self.assertEqual(post.call_count, 1)
        connection = server.CONNECTIONS["u_okafor"]
        self.assertEqual(connection["access_token"], "new")
        self.assertEqual(connection["refresh_token"], "refresh")
        self.assertIsNone(connection["expires_at"])


if __name__ == "__main__":
    unittest.main()
