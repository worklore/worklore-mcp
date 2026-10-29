"""Local regression checks for the Intervals OAuth flow."""

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


class IntervalsOAuthTests(unittest.TestCase):
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

    def get(self, path, token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        req = urllib.request.Request(self.base + path, headers=headers)
        with urllib.request.urlopen(req) as response:
            return json.load(response)

    def test_authorize_url_requires_login_and_has_valid_scopes(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get("/api/intervals/auth/init")
        self.assertEqual(error.exception.code, 401)
        error.exception.close()

        result = self.get("/api/intervals/auth/init", "tok-okafor")
        url = urllib.parse.urlsplit(result["authorize_url"])
        params = urllib.parse.parse_qs(url.query)
        self.assertEqual(url.path, "/oauth/authorize")
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(params["redirect_uri"], [config.REDIRECT_URI])
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")

    def test_provider_token_without_expiry_stays_connected(self):
        token = {
            "access_token": "local-test-token",
            "scope": "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE",
            "athlete": {"id": "i98765", "name": "T. Rivera"},
        }
        with patch.object(server, "exchange_code", return_value=token):
            state = urllib.parse.quote(server.sign_state("u_rivera"))
            req = urllib.request.Request(self.base + f"/api/intervals/callback?code=test&state={state}")
            with urllib.request.urlopen(req) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.url, self.base + "/?connected=1")

        self.assertIsNone(server.CONNECTIONS["u_rivera"]["expires_at"])
        self.assertIsNone(server.CONNECTIONS["u_rivera"]["refresh_token"])
        with patch.object(server, "post_form", side_effect=AssertionError("unexpected refresh")):
            server.refresh_due_connections(now=server.time.time() + 7200)
        status = self.get("/api/intervals/status", "tok-rivera")
        self.assertTrue(status["connected"])
        self.assertEqual(status["athlete"]["id"], "i98765")


if __name__ == "__main__":
    unittest.main()
