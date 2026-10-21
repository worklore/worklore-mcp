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


class ConnectionFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_port}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join()

    def setUp(self):
        with server.LOCK:
            server.CONNECTIONS.clear()

    def get(self, path, authenticated=True):
        headers = {"Authorization": "Bearer tok-okafor"} if authenticated else {}
        req = urllib.request.Request(self.base + path, headers=headers)
        with urllib.request.urlopen(req) as response:
            return json.load(response)

    def test_auth_init_requires_app_login(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get("/api/intervals/auth/init", authenticated=False)
        self.assertEqual(error.exception.code, 401)
        error.exception.close()

    def test_auth_init_returns_valid_url_for_authenticated_fetch(self):
        result = self.get("/api/intervals/auth/init")
        url = urllib.parse.urlsplit(result["authorize_url"])
        params = urllib.parse.parse_qs(url.query)
        self.assertEqual(url.path, "/oauth/authorize")
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(params["redirect_uri"], [config.REDIRECT_URI])
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")

    def test_callback_keeps_provider_token_without_invented_expiry(self):
        state = self.get("/api/intervals/auth/init")["authorize_url"]
        state = urllib.parse.parse_qs(urllib.parse.urlsplit(state).query)["state"][0]
        token = {"access_token": "provider-token", "scope": config.SCOPES,
                 "athlete": {"id": "i123", "name": "Athlete"}}
        query = urllib.parse.urlencode({"code": "sample-code", "state": state})
        with patch.object(server, "exchange_code", return_value=token) as exchange:
            # urllib follows the callback's redirect to the SPA.
            urllib.request.urlopen(self.base + "/api/intervals/callback?" + query).close()
        exchange.assert_called_once_with("sample-code")
        self.assertTrue(self.get("/api/intervals/status")["connected"])
        with server.LOCK:
            conn = server.CONNECTIONS["u_okafor"]
        self.assertEqual(conn["access_token"], "provider-token")
        self.assertNotIn("expires_at", conn)
        self.assertNotIn("refresh_token", conn)


if __name__ == "__main__":
    unittest.main()
